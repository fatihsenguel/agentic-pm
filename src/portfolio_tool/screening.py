"""
The philosophy applied to a company's figures: the screen.

Pure functions. No database, no model, no state, and no second arithmetic
path: every metric is read from what quant/fundamentals.py computed for the
year, and the only arithmetic here is one subtraction per finding. If the
metrics are wrong the findings are wrong in the same way, which is the
point - one computation, one place to be wrong. The mirror of
compliance.py over the allocation block.

Reference: tests/golden/expected_values.md Part 10, computed by hand before
this existed, and its decisions:

  D21  The years a clause reads are the n most recent filed on or before the
       as-of date. Fewer than n is a stop naming the year that is not there.
  D22  A clause over n years is one finding per bound, decided by the worst
       year: the lowest for a floor, the highest for a ceiling. The years
       read and the deciding year are on the finding.
  D23  Exactly at the limit passes. Strict comparison, nothing rounded.
  D25  A metric a year lacks stops the whole check naming the metric and the
       year: no finding on that clause, none on the others, no verdict on
       the company. PHI-1.2 says a clause is never skipped to let the rest
       of the screen report.

Distances are signed so that positive is a failure (limit - observed
against a floor, observed - limit against a ceiling), in the metric's own
unit. The margin of safety reads the price and the valuation range from the
block on their as-of dates, both carried on the finding; the range is a
pipeline's output (Order 4) and a typed figure until then.
"""

import datetime as dt
import re
from dataclasses import dataclass
from typing import List, Mapping, Optional, Tuple

from portfolio_tool.clauses import Clause, ClauseDocument
from portfolio_tool.quant.fundamentals import metrics_by_year, years_filed_by


PASS = "pass"
FAIL = "fail"
STATUSES = (PASS, FAIL)

DISCOUNT_METRIC = "discount_to_range_low"

_YEAR_LABEL = re.compile(r"^FY(\d{4})$")


class ScreeningError(Exception):
    """Raised when the philosophy cannot be applied honestly to the figures given."""


@dataclass(frozen=True)
class Finding:
    """One clause applied to one company against one bound.

    `observed` and `limit` are in the metric's own unit. `distance` is
    signed, positive = failure. `years_read` are the fiscal years the clause
    read and `deciding_year` the one whose figure decided it; both empty for
    the margin of safety, which reads a price and a range instead and
    carries their as-of dates.
    """

    clause: str
    type: str
    subject: str
    metric: str
    years_read: Tuple[str, ...]
    deciding_year: Optional[str]
    observed: float
    limit: float
    bound: str
    status: str
    distance: float
    price_as_of: Optional[str] = None
    range_as_of: Optional[str] = None


def _finding(clause: Clause, subject: str, metric: str, years: Tuple[str, ...],
             deciding: Optional[str], observed: float, limit: float, bound: str,
             price_as_of: Optional[str] = None, range_as_of: Optional[str] = None) -> Finding:
    signed = (limit - observed) if bound == "min" else (observed - limit)
    return Finding(
        clause=clause.id, type=clause.type, subject=subject, metric=metric,
        years_read=years, deciding_year=deciding, observed=observed, limit=limit,
        bound=bound, status=FAIL if signed > 0 else PASS, distance=signed,
        price_as_of=price_as_of, range_as_of=range_as_of,
    )


def screen(philosophy: ClauseDocument, block: Mapping, as_of: dt.date) -> List[Finding]:
    """Every numeric clause applied to the company, in philosophy order.

    Args:
        philosophy: the loaded philosophy
        block: the figures block - ticker, currency, fiscal years with their
            dates and reported figures, shares, price, valuation range
        as_of: the date the check is asked for; decides which fiscal years
            count (D21) and which price and range are current

    Returns:
        Findings, one per (clause, bound). Statements produce none.
    """
    subject = block.get("ticker")
    if not isinstance(subject, str) or not subject.strip():
        raise ScreeningError("The figures block names no ticker; a screen is of one company.")

    years = years_filed_by(block, as_of)
    metrics = metrics_by_year(block)

    findings: List[Finding] = []
    for clause in philosophy.checkable:
        if clause.type == "metric_band":
            findings += _metric_band(clause, subject, years, metrics)
        elif clause.type == "margin_of_safety":
            findings.append(_margin_of_safety(clause, subject, block))
        else:
            # The loader's vocabulary and this dispatch are two statements of
            # the same set; a type that loads and does not dispatch is a
            # clause silently unscreened.
            raise ScreeningError(f"{clause.id}: no screen for type {clause.type!r}.")
    return findings


def _earliest_needed(latest: str, n: int) -> str:
    m = _YEAR_LABEL.match(latest)
    if m:
        return f"FY{int(m.group(1)) - n + 1}"
    return f"the {n}th most recent fiscal year before {latest}"


def _metric_band(clause: Clause, subject: str, years: List[str],
                 metrics: Mapping[str, Mapping[str, float]]) -> List[Finding]:
    metric, n = clause.params["metric"], clause.params["years"]
    if len(years) < n:
        missing = _earliest_needed(years[-1], n) if years else "any fiscal year"
        raise ScreeningError(
            f"{clause.id} reads {metric} over the last {n} fiscal years and the "
            f"figures have {len(years)} filed by the as-of date: {missing} is not "
            "there. A year not yet filed is not a year (D21), and the clause is not "
            "read over fewer."
        )
    read = tuple(years[-n:])
    values = {}
    for year in read:
        value = metrics.get(year, {}).get(metric)
        if value is None:
            raise ScreeningError(
                f"{clause.id}: {metric} for {year} is not in the figures. The check "
                "stops here and reports no finding on any clause (PHI-1.2, D25)."
            )
        values[year] = value

    out = []
    if "min" in clause.params:
        deciding = min(read, key=lambda y: values[y])
        out.append(_finding(clause, subject, metric, read, deciding, values[deciding],
                            clause.params["min"], "min"))
    if "max" in clause.params:
        deciding = max(read, key=lambda y: values[y])
        out.append(_finding(clause, subject, metric, read, deciding, values[deciding],
                            clause.params["max"], "max"))
    return out


def _margin_of_safety(clause: Clause, subject: str, block: Mapping) -> Finding:
    price, rng = block.get("price"), block.get("valuation_range")
    if not isinstance(price, Mapping) or "value" not in price or "as_of" not in price:
        raise ScreeningError(f"{clause.id}: the figures carry no price with an as-of "
                             "date; the margin of safety is against the last close.")
    if not isinstance(rng, Mapping) or "low" not in rng or "as_of" not in rng:
        raise ScreeningError(f"{clause.id}: the figures carry no valuation_range with a "
                             "low end and an as-of date; the range is a pipeline's "
                             "output from stated assumptions, and without one there is "
                             "no value to be a margin below.")
    low, value = rng["low"], price["value"]
    for name, v in (("price", value), ("range low", low)):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
            raise ScreeningError(f"{clause.id}: {name} = {v!r} is not a positive number.")
    observed = 1 - value / low
    return _finding(clause, subject, DISCOUNT_METRIC, (), None, observed,
                    clause.params["discount"], "min",
                    price_as_of=str(price["as_of"]), range_as_of=str(rng["as_of"]))
