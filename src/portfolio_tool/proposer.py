"""
The one prediction a model proposes for a thesis (expected_values.md Part
15 F, D58; D49; decision 60).

The path: the user message built from the thesis and the readings' claims;
one request to the model; what it supplied checked against the metrics it
was offered and passed through `proposals.frame`, which supplies every
number and the sentence. The model is passed in, so this module calls none
itself and a test stands one in; it asks the model only
`propose(prompt, schema, text)`.

The prompt is fixed and never carries the question asked; the message
carries the thesis and, for each claim, its id, its uncertainty, its
sentence and its quote, and nothing else: not the candidate's name or id,
not its predictions. A refusal is a ProposalError or the model's own
error, raised as it comes: no second request, no other metric, nothing
stored. A thesis or readings missing refuse before any request, since the
message D58 describes cannot be written without them.
"""

import datetime as dt
from typing import Any, Mapping, Optional, Sequence

from portfolio_tool import proposals
from portfolio_tool.reading import Reading
from portfolio_tool.watchlist import Candidate

__all__ = ["PROMPT", "SCHEMA", "message", "propose"]

PROMPT = f"""You are proposing one prediction that tests an investment thesis \
about a company. The thesis, and claims read from the company's latest annual \
report on Form 10-K, are the whole of the user's message; nothing else about \
the company, and nothing about why the prediction is asked for, is given.

Choose what the company's next annual report could show that would prove the \
thesis right or wrong. Choose one of two kinds.

figure: a figure the company reports. metric is one of {", ".join(proposals.WRITTEN)}. \
bound is "min" when the thesis holds if the figure is at least last year's, \
and "max" when it holds if the figure is at most last year's. You give no \
number: the threshold is last year's reported figure, and it is set for you.

event: something the next annual report will show about the business, in \
words that complete the sentence "The annual report for the next fiscal year \
will show ...". It contains no digits and no number written in words, and \
says nothing about the share price.

reasons: the ids of the claims the prediction rests on, as they stand in \
square brackets before each claim. At least one.

Propose only what the thesis and the claims support. Do not judge whether the \
company is a good investment, and do not say what its share price will do."""

_REASONS = {"type": "array", "items": {"type": "string"}}
SCHEMA = {
    "type": "object",
    "properties": {
        "prediction": {
            "anyOf": [
                {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "enum": ["figure"]},
                        "metric": {"type": "string", "enum": list(proposals.WRITTEN)},
                        "bound": {"type": "string", "enum": list(proposals.BOUNDS)},
                        "reasons": _REASONS,
                    },
                    "required": ["kind", "metric", "bound", "reasons"],
                    "additionalProperties": False,
                },
                {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "enum": ["event"]},
                        "event": {"type": "string"},
                        "reasons": _REASONS,
                    },
                    "required": ["kind", "event", "reasons"],
                    "additionalProperties": False,
                },
            ],
        },
    },
    "required": ["prediction"],
    "additionalProperties": False,
}


def message(thesis: str, readings: Sequence[Reading]) -> str:
    """The one user message: the thesis, then each claim in the order read
    (D58)."""
    lines = ["Thesis:", thesis.strip(), "", "Claims:"]
    for reading in readings:
        for claim in reading.claims:
            lines.append(f"[{claim.id}] ({claim.uncertainty}) {claim.claim}")
            lines.append(f'Quote: "{claim.quote}"')
    return "\n".join(lines)


def propose(model, candidate: Candidate, thesis: str, readings: Sequence[Reading],
            block: Mapping, as_of: dt.date,
            assumptions: Optional[Mapping[str, Any]] = None) -> proposals.Proposed:
    """The one prediction the model proposes for `thesis`, framed under
    `candidate` (D58), or a refusal naming why."""
    if not isinstance(thesis, str) or not thesis.strip():
        raise proposals.ProposalError(f"{candidate.id} states no thesis; a prediction tests "
                                      "one, and nothing is asked.")
    claim_ids = [claim.id for reading in readings for claim in reading.claims]
    if not claim_ids:
        raise proposals.ProposalError("no claim was read; a prediction rests on what the "
                                      "filing says, and nothing is asked.")

    supplied = model.propose(PROMPT, SCHEMA, message(thesis, readings))
    if supplied.get("kind") == "figure" and supplied.get("metric") not in proposals.WRITTEN:
        raise proposals.ProposalError(f"metric {supplied.get('metric')!r} is not one offered; "
                                      f"the offer is {', '.join(proposals.WRITTEN)} (D58).")
    (proposed,) = proposals.frame([supplied], candidate, block, as_of, claim_ids, assumptions)
    return proposed
