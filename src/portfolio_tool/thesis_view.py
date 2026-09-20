"""
The model's view of a thesis (case 4.3; decisions 67 and 68;
expected_values.md Part 15 G, D61).

Decision 68 composes case 4.3's outcome from four inputs, and this is the
fourth: whether the thesis still stands, read off the claims of the
latest annual report. It is judgement and is marked as judgement; it
computes nothing, and it can only ever take away.

What the model supplies, and nothing else: the value, one of `stands`,
`strained` and `no_view`; the ids of the claims its view rests on; and an
uncertainty, `stated` or `inferred`. There is no prose field. The claims
cited carry the words, each with the quote its own rules already held, so
the answer has something to print without a sentence from the model and
no digit rule is needed here.

What is held by code and not by the model (D61): the value is one of the
three; the uncertainty is one of the two; every reason is a claim of the
readings; `stands` and `strained` carry at least one reason and `no_view`
carries none, so a reason beside `no_view` is refused rather than
ignored; and a record with a fourth field is refused. One rule that fails
refuses the whole record, the shape a reading has.

The user message is the proposer's, built by `proposer.message` and not
rewritten here, so the view and the prediction rest on the same thesis
and the same claims because it is the same string. The prompt is fixed,
never carries the question asked, and does not say what the view is used
for: telling the model that one of the three values is the only one that
permits an entry is pressure on the answer, and the composition is
decision 68's business, not the model's.

The model is passed in, so this module calls none itself and a test
stands one in; it asks the model only `view(prompt, schema, text)`. A
refusal is a ThesisViewError or the model's own error, raised as it
comes: no second request and nothing stored. A thesis or readings missing
refuse before any request, since the message cannot be written without
them.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Sequence, Tuple

from portfolio_tool import proposer
from portfolio_tool.reading import UNCERTAINTIES, Reading

__all__ = ["ThesisView", "ThesisViewError", "VIEWS", "NEEDS_REASON", "SUPPLIED",
           "PROMPT", "SCHEMA", "record", "ask"]

# The closed set (D61), in the order Part 15 G lists it. `stands` is the
# only value that permits an entry, which decision 68 decides and this
# module does not.
VIEWS = ("stands", "strained", "no_view")
NO_VIEW = "no_view"
# The values that rest on something. `no_view` rests on nothing.
NEEDS_REASON = tuple(v for v in VIEWS if v != NO_VIEW)
# What a model supplies. Anything else is a fourth field, and a sentence
# first of all: prose in the answer that nothing holds.
SUPPLIED = {"thesis_view", "reasons", "uncertainty"}

PROMPT = """You are giving one view of whether an investment thesis about a \
company still stands. The thesis, and claims read from the company's latest \
annual report on Form 10-K, are the whole of the user's message; nothing else \
about the company, and nothing about why the view is asked for, is given.

Choose one of three values.

stands: the claims support the thesis and none of them undercuts it.

strained: a claim undercuts the thesis. You have read something that puts \
pressure on it.

no_view: the claims do not bear on the thesis either way.

reasons: the ids of the claims your view rests on, as they stand in square \
brackets before each claim. At least one for stands and for strained, and \
none for no_view.

uncertainty: "stated" when the claims your view rests on say your view in so \
many words, "inferred" when you read it across them.

Give no figure and no sentence of your own: the value, the reasons and the \
uncertainty are the whole answer. Do not say whether the company is a good \
investment, and do not say what its share price will do."""

SCHEMA = {
    "type": "object",
    "properties": {
        "view": {
            "type": "object",
            "properties": {
                "thesis_view": {"type": "string", "enum": list(VIEWS)},
                "reasons": {"type": "array", "items": {"type": "string"}},
                "uncertainty": {"type": "string", "enum": list(UNCERTAINTIES)},
            },
            "required": sorted(SUPPLIED),
            "additionalProperties": False,
        },
    },
    "required": ["view"],
    "additionalProperties": False,
}


class ThesisViewError(Exception):
    """Raised when a view cannot honestly be recorded."""


@dataclass(frozen=True)
class ThesisView:
    """The model's view of a thesis: the value, the claims it rests on, and
    how sure the model is. Three fields, and the answer prints the claims
    it cites."""
    thesis_view: str
    reasons: Tuple[str, ...]
    uncertainty: str


def record(supplied: Mapping[str, Any], claim_ids: Sequence[str]) -> ThesisView:
    """The view the model supplied, or a refusal naming the rule it broke
    (Part 15 G's rows)."""
    if not isinstance(supplied, Mapping):
        raise ThesisViewError(f"a view is an object of {sorted(SUPPLIED)}, not "
                              f"{type(supplied).__name__}.")
    extra = sorted(set(supplied) - SUPPLIED)
    if extra:
        raise ThesisViewError(f"the view supplies {extra}; a view is {sorted(SUPPLIED)}, and "
                              "the claims it cites carry the words.")
    missing = sorted(SUPPLIED - set(supplied))
    if missing:
        raise ThesisViewError(f"the view states no {', '.join(missing)}.")

    value = supplied["thesis_view"]
    if value not in VIEWS:
        raise ThesisViewError(f"view {value!r} is not one of {', '.join(VIEWS)}.")
    if supplied["uncertainty"] not in UNCERTAINTIES:
        raise ThesisViewError(f"uncertainty {supplied['uncertainty']!r} is not one of "
                              f"{', '.join(UNCERTAINTIES)}.")

    reasons = supplied["reasons"]
    if isinstance(reasons, str) or not isinstance(reasons, Sequence):
        raise ThesisViewError(f"reasons is {type(reasons).__name__}, not a list of claim ids.")
    for reason in reasons:
        if reason not in claim_ids:
            raise ThesisViewError(f"reason {reason!r} is no claim of the readings; a view "
                                  "rests on what the filing says.")
    if value in NEEDS_REASON and not reasons:
        raise ThesisViewError(f"the view is {value!r} and gives no reason; only "
                              f"{NO_VIEW!r} rests on nothing.")
    if value == NO_VIEW and reasons:
        raise ThesisViewError(f"the view is {NO_VIEW!r} and cites {list(reasons)}; a reason is "
                              "what a view rests on, and this one states none.")
    return ThesisView(thesis_view=value, reasons=tuple(reasons),
                      uncertainty=supplied["uncertainty"])


def ask(model, thesis: str, readings: Sequence[Reading]) -> ThesisView:
    """The one view the model gives of `thesis`, read off `readings`
    (D61), or a refusal naming why."""
    if not isinstance(thesis, str) or not thesis.strip():
        raise ThesisViewError("no thesis is stated; a view is a view of one, and nothing "
                              "is asked.")
    claim_ids = [claim.id for reading in readings for claim in reading.claims]
    if not claim_ids:
        raise ThesisViewError("no claim was read; a view rests on what the filing says, and "
                              "nothing is asked.")
    return record(model.view(PROMPT, SCHEMA, proposer.message(thesis, readings)), claim_ids)
