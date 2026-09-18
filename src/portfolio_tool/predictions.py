"""
Prediction scoring, pure (case 4.5; PHI-6.2; expected_values.md Part 14,
D41 to D45). The ledger is the watchlist's prediction rows; this module
says what each one is as of a date, open, due or scored, and for a due
figure prediction what the filer reported against what was predicted,
with the filing as the source.

What is computed here: a prediction's status by its due date (D43); for a
figure prediction whose date has come, one comparison of the reported
figure against the stated bound and value, strict and unrounded, right or
wrong, no partial credit and no distance (D41); the reported figure taken
from the period's own annual report through the reader's block, a field
as filed or a metric by Part 10 B's formula (D42); and the ledger's
counts, once. What is never computed here: the score in the ledger, which
is written by hand with its outcome and source (D44), reported as written
and, for a figure prediction, set beside the filing's verdict with whether
the two agree. An event prediction has no figure to read and is due until
its outcome is written; it is listed, never skipped and never right.

A designed stop is a PredictionError: a metric no formula computes, a
period not filed by the as-of date, a filed period missing the field, a
block naming no source, fields on two filings. `record` turns it into the
record's stated reason; anything else is a defect and raises through.
Nothing is defaulted, rounded, sorted or filled.
"""

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional, Sequence

from portfolio_tool.quant.fundamentals import (FIGURE_FIELDS, METRICS, READS,
                                               FundamentalsError, metrics_by_year)
from portfolio_tool.watchlist import Prediction, Score

__all__ = ["Filing", "Record", "Ledger", "PredictionError", "OPEN", "DUE", "SCORED",
           "STATUSES", "status", "verdict", "record", "ledger", "SCORABLE"]

OPEN, DUE, SCORED = "open", "due", "scored"
STATUSES = (OPEN, DUE, SCORED)
RIGHT, WRONG = "right", "wrong"
# The figures a prediction may be scored on (D42): a field of the block
# read as filed, or a metric key with a formula. free_cash_flow_yield
# depends on the price and is no prediction metric (invariant 7).
FIELDS_SCORED = ("revenue",)
METRICS_SCORED = tuple(k for k in METRICS if k != "free_cash_flow_yield")
SCORABLE = FIELDS_SCORED + METRICS_SCORED


class PredictionError(Exception):
    """Raised when a prediction cannot honestly be scored on the figures given."""


@dataclass(frozen=True)
class Filing:
    """The filing's verdict on a figure prediction (D44, D45): the figure as
    reported, right or wrong, and the filing it came from."""
    reported: float
    result: str
    form: str
    accn: str
    filed: dt.date
    source: str


@dataclass(frozen=True)
class Record:
    id: str
    candidate: str
    kind: str
    statement: str
    made_on: dt.date
    due: dt.date
    status: str
    metric: Optional[str] = None
    bound: Optional[str] = None
    value: Optional[float] = None
    period: Optional[str] = None
    score: Optional[Score] = None
    filing: Optional[Filing] = None
    unscored: Optional[str] = None
    # For a written score on a figure prediction with a filing's verdict:
    # whether the two results are the same. A disagreement is reported,
    # never repaired (D44).
    agrees: Optional[bool] = None


@dataclass(frozen=True)
class Ledger:
    records: List[Record]
    summary: Dict[str, int]


def status(prediction: Prediction, as_of: dt.date) -> str:
    """Scored when the ledger carries the score; else open before the due
    date and due on and after it (D43)."""
    if prediction.score is not None:
        return SCORED
    return OPEN if as_of < prediction.due else DUE


def _compare(observed, value, bound: str) -> str:
    if bound == "min":
        return RIGHT if observed >= value else WRONG
    if bound == "max":
        return RIGHT if observed <= value else WRONG
    raise PredictionError(f"bound {bound!r} is not min or max.")


def _one_filing(pid: str, period: str, provenance: Mapping, fields: Sequence[str]) -> Dict[str, Any]:
    sources = []
    for field in fields:
        entry = provenance.get(field)
        if not isinstance(entry, Mapping):
            raise PredictionError(f"{pid}: {period}: {field} carries no provenance; the "
                                  "reader records the filing each figure came from.")
        sources.append((entry.get("form"), entry.get("accn"), entry.get("filed")))
    if len(set(sources)) != 1:
        raise PredictionError(f"{pid}: {period}: the fields read are on two filings "
                              f"({sorted(str(s) for s in set(sources))}); no row in Part 14 "
                              "covers a figure across filings.")
    form, accn, filed = sources[0]
    return {"form": form, "accn": accn, "filed": filed}


def verdict(prediction: Prediction, block: Mapping, as_of: dt.date,
            assumptions: Optional[Mapping[str, Any]] = None) -> Filing:
    """The filing's verdict on a figure prediction over the reader's block
    (D41, D42). Raises PredictionError where the figure cannot honestly be
    read; says nothing about the due date, which is `record`'s to check."""
    pid = prediction.id
    if prediction.kind != "figure":
        raise PredictionError(f"{pid} is an event prediction; an event has no figure to score "
                              "and is scored by hand against its source (PHI-6.2).")
    metric, period = prediction.metric, prediction.period
    if metric not in SCORABLE:
        raise PredictionError(f"{pid}: {metric} is not a figure the scorer reads; it reads "
                              f"{', '.join(SCORABLE)}, and a metric is added with its row "
                              "in Part 14 when a prediction asks (D42).")
    source = block.get("source")
    if not source:
        raise PredictionError(f"{pid}: the figures name no source; a verdict cites the filing "
                              "and the source it was read from.")
    years = block.get("years") or {}
    if period not in years:
        raise PredictionError(f"{pid}: {period} is not filed by {as_of}; the prediction is due "
                              "and unscored, never wrong for want of a figure (D42).")
    figures = years[period]
    provenance = (block.get("provenance") or {}).get(period) or {}

    if metric in FIELDS_SCORED:
        if metric not in figures:
            raise PredictionError(f"{pid}: {period}: {metric} is not in the figures. The "
                                  "prediction is not scored and the figure is named (D25).")
        raw = figures[metric]
        if isinstance(raw, bool) or not isinstance(raw, (int, float, Decimal)):
            raise PredictionError(f"{pid}: {period}: {metric} = {raw!r} is not a number.")
        observed = raw if isinstance(raw, Decimal) else Decimal(str(raw))
        result = _compare(observed, Decimal(str(prediction.value)), prediction.bound)
        reported = float(observed)
        fields = (metric,)
    else:
        try:
            computed = metrics_by_year({"years": {period: figures}}, dict(assumptions or {}))
        except FundamentalsError as e:
            raise PredictionError(f"{pid}: {period}: {e}")
        if metric not in computed.get(period, {}):
            missing = [f for f in READS[metric] if f not in figures]
            raise PredictionError(
                f"{pid}: {period}: {metric} cannot be computed; "
                + (f"{', '.join(missing)} not in the figures" if missing
                   else "an assumption it needs is not stated")
                + ". The prediction is not scored and the figure is named (D25).")
        observed = computed[period][metric]
        result = _compare(observed, float(prediction.value), prediction.bound)
        reported = observed
        fields = READS[metric]

    where = _one_filing(pid, period, provenance, fields)
    return Filing(reported=reported, result=result, form=where["form"], accn=where["accn"],
                  filed=where["filed"], source=source)


def record(prediction: Prediction, block: Optional[Mapping], as_of: dt.date,
           assumptions: Optional[Mapping[str, Any]] = None) -> Record:
    """One prediction's record as of `as_of` (D45). Open: nothing read.
    Scored: the written score, and for a figure prediction the filing's
    verdict beside it when a block is given. Due: the filing's verdict, or
    the reason there is none."""
    state = status(prediction, as_of)
    base = dict(id=prediction.id, candidate=prediction.candidate, kind=prediction.kind,
                statement=prediction.statement, made_on=prediction.made_on, due=prediction.due,
                status=state, metric=prediction.metric, bound=prediction.bound,
                value=prediction.value, period=prediction.period, score=prediction.score)
    if state == OPEN:
        return Record(**base)
    if prediction.kind != "figure":
        if state == SCORED:
            return Record(**base)
        return Record(**base, unscored=(
            f"{prediction.id} is due since {prediction.due} and awaits the outcome, which is "
            "written by hand with its source (PHI-6.2)."))
    if block is None:
        if state == SCORED:
            return Record(**base)
        return Record(**base, unscored=(
            f"{prediction.id}: no figures were read for {prediction.candidate}, so the "
            "filing's verdict is not computed."))
    try:
        filing = verdict(prediction, block, as_of, assumptions)
    except PredictionError as e:
        return Record(**base, unscored=str(e))
    if state == SCORED:
        return Record(**base, filing=filing, agrees=(filing.result == prediction.score.result))
    return Record(**base, filing=filing)


def ledger(rows: Sequence[Prediction], blocks: Mapping[str, Mapping], as_of: dt.date,
           assumptions: Optional[Mapping[str, Any]] = None) -> Ledger:
    """Every prediction's record in the order given, and the counts, once:
    the number of predictions and how many are scored, due and open, the
    three summing to the first (Part 14 A)."""
    records = [record(p, blocks.get(p.candidate), as_of, assumptions) for p in rows]
    summary = {"predictions": len(records)}
    for state in STATUSES:
        summary[state] = sum(1 for r in records if r.status == state)
    return Ledger(records=records, summary=summary)
