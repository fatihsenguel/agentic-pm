"""
The model behind a reading (expected_values.md Part 16 J, D56; decision 67).

One request per section: the section's fixed prompt as the system prompt,
the section's text as the one user message, and the answer held to the
schema the caller passes by the API's structured output. No temperature:
the model refuses one. The model is the one `ANTHROPIC_SONNET` names in
`agents/config.py`; the router's model is unchanged.

What comes back is the list of claims as the model wrote them, and nothing
here checks a claim: that is `portfolio_tool.reading.record`'s, against the
section's text. What is refused here is an answer that is not the schema's
shape: a stop for any reason but `end_turn`, text that is not JSON, or an
object that is not `claims` and a list. The API's own refusal of a request
is raised naming the section.

`reading_model()` is the function the reader's caller asks for the model,
so a test stands one in, as `nodes.price_provider` is for prices.
"""

import json
from typing import Any, List, Mapping

import anthropic

from agents.config import ANTHROPIC_SONNET

__all__ = ["ReadingModelError", "ReadingModel", "MAX_TOKENS", "reading_model"]

MAX_TOKENS = 16_000


class ReadingModelError(Exception):
    """Raised when the model's answer is not a reading's shape."""


class ReadingModel:
    """Sends one section to the model and returns the claims it supplied."""

    def __init__(self, client, model: str):
        self.client = client
        self.id = model

    def read(self, section: str, prompt: str, schema: Mapping[str, Any],
             text: str) -> List[Any]:
        try:
            response = self.client.messages.create(
                model=self.id,
                max_tokens=MAX_TOKENS,
                system=prompt,
                messages=[{"role": "user", "content": text}],
                output_config={"format": {"type": "json_schema", "schema": dict(schema)}},
            )
        except anthropic.APIStatusError as error:
            raise ReadingModelError(f"{section}: the model refused the request, "
                                    f"{error.status_code}: {error.message}") from error

        if response.stop_reason != "end_turn":
            raise ReadingModelError(f"{section}: the model stopped on {response.stop_reason!r}, "
                                    "not at the end of its answer; nothing is read.")
        texts = [block.text for block in response.content if block.type == "text"]
        if len(texts) != 1:
            raise ReadingModelError(f"{section}: the answer carries {len(texts)} text blocks, "
                                    "not one.")
        try:
            answer = json.loads(texts[0])
        except ValueError as error:
            raise ReadingModelError(f"{section}: the answer is not JSON.") from error
        if not isinstance(answer, dict) or set(answer) != {"claims"} \
                or not isinstance(answer["claims"], list):
            raise ReadingModelError(f"{section}: the answer is not one object holding a list "
                                    "of claims.")
        return answer["claims"]


def reading_model() -> ReadingModel:
    """The model a reading runs on (decision 67)."""
    return ReadingModel(anthropic.Anthropic(api_key=ANTHROPIC_SONNET.api_key),
                        ANTHROPIC_SONNET.model)
