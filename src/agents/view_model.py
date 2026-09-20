"""
The model behind the view of a thesis (expected_values.md Part 15 G, D61;
decisions 67 and 68).

One request, the shape `proposal_model` makes: the fixed prompt as the
system prompt, the thesis and the readings' claims as the one user
message, and the answer held to the schema the caller passes by the API's
structured output. No temperature: the model refuses one. The model is
the one `ANTHROPIC_SONNET` names in `agents/config.py`, as for a reading
and for a proposal.

**A second request and not the proposal's.** Decided 20 September, on its
own word: the view goes to the model on its own rather than sharing the
proposal's request. A shared request would make case 4.4, which passes
today, depend on a field it never reads, and one refused key would sink
both answers where D58 allows no second request. The two requests carry
the same user message, `proposer.message`, so the view and the prediction
rest on the same thesis and the same claims. Rejected with it: the view
folded into each section's reading, which gives three views and composes
none; a view computed from the claims by a rule, which is judgement
dressed as arithmetic; and the view on the router's cheaper model, when
decision 67 puts the judgement on the stronger one.

What comes back is the view the model supplied, and nothing here checks
it: that is `portfolio_tool.thesis_view.record`'s. What is refused here is
an answer that is not the schema's shape: a stop for any reason but
`end_turn`, text that is not JSON, or an object that is not `view`
holding one object. The API's own refusal of a request is raised as it
comes. Nothing is asked a second time.

`view_model()` is the function the caller asks for the model, so a test
stands one in, as `reading_model()` and `proposal_model()` are.
"""

import json
from typing import Any, Mapping

import anthropic

from agents.config import ANTHROPIC_SONNET

__all__ = ["ViewModelError", "ViewModel", "MAX_TOKENS", "view_model"]

MAX_TOKENS = 16_000


class ViewModelError(Exception):
    """Raised when the model's answer is not a view's shape."""


class ViewModel:
    """Sends the thesis and the claims to the model and returns the one
    view it supplied."""

    def __init__(self, client, model: str):
        self.client = client
        self.id = model

    def view(self, prompt: str, schema: Mapping[str, Any], text: str) -> Mapping[str, Any]:
        try:
            response = self.client.messages.create(
                model=self.id,
                max_tokens=MAX_TOKENS,
                system=prompt,
                messages=[{"role": "user", "content": text}],
                output_config={"format": {"type": "json_schema", "schema": dict(schema)}},
            )
        except anthropic.APIStatusError as error:
            raise ViewModelError(f"the model refused the request, {error.status_code}: "
                                 f"{error.message}") from error

        if response.stop_reason != "end_turn":
            raise ViewModelError(f"the model stopped on {response.stop_reason!r}, not at the "
                                 "end of its answer; there is no view.")
        texts = [block.text for block in response.content if block.type == "text"]
        if len(texts) != 1:
            raise ViewModelError(f"the answer carries {len(texts)} text blocks, not one.")
        try:
            answer = json.loads(texts[0])
        except ValueError as error:
            raise ViewModelError("the answer is not JSON.") from error
        if not isinstance(answer, dict) or set(answer) != {"view"} \
                or not isinstance(answer["view"], dict):
            raise ViewModelError("the answer is not one object holding one view.")
        return answer["view"]


def view_model() -> ViewModel:
    """The model a view runs on (decision 67)."""
    return ViewModel(anthropic.Anthropic(api_key=ANTHROPIC_SONNET.api_key),
                     ANTHROPIC_SONNET.model)
