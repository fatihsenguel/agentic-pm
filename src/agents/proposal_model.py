"""
The model behind a proposed prediction (expected_values.md Part 15 F, D58;
decisions 60 and 67).

One request: the fixed prompt as the system prompt, the thesis and the
readings' claims as the one user message, and the answer held to the
schema the caller passes by the API's structured output. No temperature:
the model refuses one. The model is the one `ANTHROPIC_SONNET` names in
`agents/config.py`, as for a reading.

What comes back is the one prediction the model supplied, and nothing here
checks it: that is `portfolio_tool.proposer`'s and `proposals.frame`'s.
What is refused here is an answer that is not the schema's shape: a stop
for any reason but `end_turn`, text that is not JSON, or an object that is
not `prediction` holding one object. The API's own refusal of a request is
raised as it comes. Nothing is asked a second time.

`proposal_model()` is the function the proposer's caller asks for the
model, so a test stands one in, as `reading_model()` is for a reading.
"""

import json
from typing import Any, Mapping

import anthropic

from agents.config import ANTHROPIC_SONNET

__all__ = ["ProposalModelError", "ProposalModel", "MAX_TOKENS", "proposal_model"]

MAX_TOKENS = 16_000


class ProposalModelError(Exception):
    """Raised when the model's answer is not a proposal's shape."""


class ProposalModel:
    """Sends the thesis and the claims to the model and returns the one
    prediction it supplied."""

    def __init__(self, client, model: str):
        self.client = client
        self.id = model

    def propose(self, prompt: str, schema: Mapping[str, Any], text: str) -> Mapping[str, Any]:
        try:
            response = self.client.messages.create(
                model=self.id,
                max_tokens=MAX_TOKENS,
                system=prompt,
                messages=[{"role": "user", "content": text}],
                output_config={"format": {"type": "json_schema", "schema": dict(schema)}},
            )
        except anthropic.APIStatusError as error:
            raise ProposalModelError(f"the model refused the request, {error.status_code}: "
                                     f"{error.message}") from error

        if response.stop_reason != "end_turn":
            raise ProposalModelError(f"the model stopped on {response.stop_reason!r}, not at "
                                     "the end of its answer; nothing is proposed.")
        texts = [block.text for block in response.content if block.type == "text"]
        if len(texts) != 1:
            raise ProposalModelError(f"the answer carries {len(texts)} text blocks, not one.")
        try:
            answer = json.loads(texts[0])
        except ValueError as error:
            raise ProposalModelError("the answer is not JSON.") from error
        if not isinstance(answer, dict) or set(answer) != {"prediction"} \
                or not isinstance(answer["prediction"], dict):
            raise ProposalModelError("the answer is not one object holding one prediction.")
        return answer["prediction"]


def proposal_model() -> ProposalModel:
    """The model a proposal runs on (decision 67)."""
    return ProposalModel(anthropic.Anthropic(api_key=ANTHROPIC_SONNET.api_key),
                         ANTHROPIC_SONNET.model)
