"""
A prediction the system proposes, pure (cases 4.3 and 4.4; PHI-6.1 and
PHI-6.2; expected_values.md Part 15, D49 and D50).

A model chooses what to test and this module supplies every number. What
the model supplies is a kind; for a figure a metric the scorer computes
and a bound; for an event the event in words; and its reasons, the ids of
claims of the readings. What is computed here: the period, the fiscal
year after the latest one filed by the as-of date; `made_on`, the as-of
date, and `due`, the same day and month a year later; the value, the
latest filed year's figure for the metric through the scorer's own lookup,
a field as filed and a ratio cut to four decimal places toward the side
that makes "holds at last year's level" right; the next free id under the
candidate; and the sentence, from a template around those figures.

A designed stop is a ProposalError naming what stopped: a key the model
may not supply, a value among them; a digit or a price phrase in an
event; a reason that is no claim of the readings; a metric the scorer
does not compute or one the price enters; a figure the latest year lacks;
a metric with no sentence row in Part 15. No other metric is tried and
nothing is defaulted. Nothing here writes a file: a proposal is printed
and entered by hand, or not at all (D50).

Not covered yet: a proposal the ledger already carries (Part 15 F9). The
loader reads no `author`, so a system row in the file cannot be told from
mine; the row and its test come with the loader's field.
"""

import datetime as dt
import re
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from portfolio_tool.predictions import SCORABLE, PredictionError, reported_figure
from portfolio_tool.quant.fundamentals import METRICS, years_filed_by
from portfolio_tool.watchlist import Candidate

__all__ = ["Proposed", "ProposalError", "SYSTEM", "PROPOSED", "WRITTEN", "frame",
           "one_year_later"]

SYSTEM = "system"
PROPOSED = "proposed"
KINDS = ("figure", "event")
BOUNDS = {"min": "at least", "max": "at most"}
# What a model may supply, by kind (D49). Anything else, a value first of
# all, is a number or a sentence in a model's hands.
SUPPLIED = {"figure": {"kind", "metric", "bound", "reasons"},
            "event": {"kind", "event", "reasons"}}
# The phrases tests/test_watchlist.py refuses in a prediction's statement.
PRICE_PHRASES = ("share price", "stock price", "price target", "will be at", "will trade")
RATIO_PLACES = Decimal("0.0001")
# The sentence rows Part 15 C carries: the words for the metric and how its
# value prints. A metric without a row stops until its row is written.
_WORDS = {"revenue": "revenue", "gross_margin": "a gross margin"}
# The metrics a model is offered: the ones a sentence can be written for (D58).
WRITTEN = tuple(_WORDS)
_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December")
_DIGIT = re.compile(r"\d")
_YEAR_LABEL = re.compile(r"FY(\d{4})")


class ProposalError(Exception):
    """Raised when a proposal cannot honestly be framed as a prediction."""


@dataclass(frozen=True)
class Proposed:
    """A proposed prediction: the ledger's row, the system's by its author,
    with the reasons it rests on and, for a figure, the filing its value
    came from."""
    id: str
    candidate: str
    made_on: dt.date
    due: dt.date
    kind: str
    statement: str
    reasons: Tuple[str, ...]
    metric: Optional[str] = None
    bound: Optional[str] = None
    value: Optional[float] = None
    period: Optional[str] = None
    source: Optional[Mapping[str, Any]] = None
    author: str = SYSTEM
    status: str = PROPOSED


def one_year_later(day: dt.date) -> dt.date:
    """The same day and month a year later, 28 February for a 29 February,
    so that the prediction falls within a year (PHI-6.1; Part 15 F4)."""
    try:
        return day.replace(year=day.year + 1)
    except ValueError:
        return dt.date(day.year + 1, 2, 28)


def _day(day: dt.date) -> str:
    return f"{day.day} {_MONTHS[day.month - 1]} {day.year}"


def _next_period(block: Mapping, as_of: dt.date) -> Tuple[str, str]:
    filed = years_filed_by(block, as_of)
    if not filed:
        raise ProposalError(f"no fiscal year is filed by {as_of}; a threshold is the last "
                            "filed year's figure and there is none.")
    latest = filed[-1]
    match = _YEAR_LABEL.fullmatch(latest)
    if not match:
        raise ProposalError(f"the latest filed year is labelled {latest!r}, not like FY2025.")
    return latest, f"FY{int(match.group(1)) + 1}"


def _threshold(observed, bound: str):
    """A field as filed, to the unit; a ratio cut to four places, down for
    `min` and up for `max` (D49, F2 and F3)."""
    if isinstance(observed, Decimal):
        return int(observed) if observed == observed.to_integral_value() else float(observed)
    rounding = ROUND_FLOOR if bound == "min" else ROUND_CEILING
    return float(Decimal(repr(observed)).quantize(RATIO_PLACES, rounding=rounding))


def _printed(metric: str, value) -> str:
    if metric == "revenue":
        return f"{value:,}"
    return f"{Decimal(repr(value)) * 100:.2f}%"


def _checked(supplied: Mapping, claim_ids: Sequence[str]) -> Tuple[str, Tuple[str, ...]]:
    kind = supplied.get("kind")
    if kind not in KINDS:
        raise ProposalError(f"kind {kind!r} is not one of {', '.join(KINDS)}.")
    extra = sorted(set(supplied) - SUPPLIED[kind])
    if extra:
        raise ProposalError(f"a {kind} proposal supplies {extra}; a model supplies "
                            f"{sorted(SUPPLIED[kind])} and the pipeline every number and "
                            "the sentence (D49).")
    reasons = supplied.get("reasons")
    if not isinstance(reasons, (list, tuple)) or not reasons:
        raise ProposalError("a proposal gives no reasons; a prediction is attached to what "
                            "was read.")
    unknown = [r for r in reasons if r not in claim_ids]
    if unknown:
        raise ProposalError(f"reasons {unknown} are not claims of the readings.")
    return kind, tuple(reasons)


def frame(supplied: Sequence[Mapping], candidate: Candidate, block: Mapping, as_of: dt.date,
          claim_ids: Sequence[str],
          assumptions: Optional[Mapping[str, Any]] = None) -> List[Proposed]:
    """The proposals framed as prediction rows under the candidate, in the
    order given (Part 15 C). Raises ProposalError at the first one that
    cannot be framed; the rest are not tried."""
    latest, period = _next_period(block, as_of)
    year = period[2:]
    due = one_year_later(as_of)
    taken = max((int(p.id.rsplit(".", 1)[1]) for p in candidate.predictions), default=0)

    out: List[Proposed] = []
    for n, entry in enumerate(supplied, start=1):
        kind, reasons = _checked(entry, claim_ids)
        pid = f"{candidate.id}.{taken + n}"
        base: Dict[str, Any] = dict(id=pid, candidate=candidate.id, made_on=as_of, due=due,
                                    kind=kind, reasons=reasons)
        if kind == "event":
            event = entry.get("event")
            if not isinstance(event, str) or not event.strip():
                raise ProposalError(f"{pid}: an event proposal states no event.")
            if _DIGIT.search(event):
                raise ProposalError(f"{pid}: a digit in the event; the pipeline supplies "
                                    "every number (D49).")
            priced = [p for p in PRICE_PHRASES if p in event.lower()]
            if priced:
                raise ProposalError(f"{pid}: the event names a price ({', '.join(priced)}); a "
                                    "prediction is about the business (PHI-6.2).")
            out.append(Proposed(**base, statement=(
                f"By {_day(due)} {candidate.name}'s annual report for fiscal {year} will "
                f"show {event.strip()}.")))
            continue

        metric, bound = entry.get("metric"), entry.get("bound")
        if metric in METRICS and metric not in SCORABLE:
            raise ProposalError(f"{pid}: the price enters {metric}; no prediction rests on a "
                                "price (DIRECTION.md invariant 7).")
        if bound not in BOUNDS:
            raise ProposalError(f"{pid}: bound {bound!r} is not min or max.")
        try:
            observed, where = reported_figure(pid, metric, latest, block, as_of, assumptions)
        except PredictionError as e:
            raise ProposalError(str(e))
        if metric not in _WORDS:
            raise ProposalError(f"{pid}: {metric} has no sentence row in Part 15; the row "
                                "comes with the first proposal that asks.")
        value = _threshold(observed, bound)
        out.append(Proposed(**base, metric=metric, bound=bound, value=value, period=period,
                            source=where, statement=(
            f"By {_day(due)} {candidate.name} will have reported {_WORDS[metric]} for fiscal "
            f"{year} of {BOUNDS[bound]} {_printed(metric, value)}.")))
    return out
