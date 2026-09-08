"""
Compliance: the IPS applied to the allocation PortfolioAnalysisAgent published.

Pure functions over dicts. No database, no LLM, no state, and no second
arithmetic path: every percentage and total is read from the allocation
block exactly as published to shared_data, and the only arithmetic here is
one subtraction per finding. The checker does not know how the block was
computed and does not recompute it; if the block is wrong the findings are
wrong in the same way, which is the point - one computation, one place to
be wrong.

Reference: tests/golden/expected_values.md Part 7, computed by hand before
this existed, and its decisions:

  D2  The denominator for every clause is total portfolio value including
      cash: `by_asset_class.total_value`. Every allocation line carries its
      share of it as `pct_of_total`, and that is the one field every clause
      reads - bands over `by_asset_class`, the concentration clauses over
      `by_position`, the sector clause over `by_sector`. A sector line also
      carries shares of sectored and of invested value; both are wrong for
      IPS-4.3 and both plausible, and neither is read here.
  D9  Exactly at a limit passes. Strict, unrounded comparison - beyond the
      cent rounding the block already carries, which this module does not
      add to.

A finding per (clause, subject, bound): a band clause with two bounds emits
two findings, so the checker never chooses a "nearer" bound. Distances are
signed so that positive is a breach and negative is headroom (the workbook's
convention), in percentage points of total, and in currency at unchanged
total (IPS-5.2's condition, the amount that returns the figure to the limit).

Raise, do not repair. A holding with no instrument type, a clause naming an
asset class the allocation has no line for, a fund inside a sector bucket:
each is a data problem that would otherwise turn into a plausible verdict.
"""

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional

from portfolio_tool.ips import IPS, Clause
from portfolio_tool.quant.allocation import UNSECTORED_LABEL


OK = "ok"
BREACH = "breach"
EXEMPT = "exempt"
REFUSED = "refused"
STATUSES = (OK, BREACH, EXEMPT, REFUSED)

SHARE = "share"
FUND = "fund"
INSTRUMENT_TYPES = (SHARE, FUND)

HYPOTHETICAL = "hypothetical position"


class ComplianceError(Exception):
    """Raised when the policy cannot be applied honestly to the data given."""


@dataclass(frozen=True)
class Finding:
    """One clause applied to one subject against one bound.

    `observed` and `limit` are fractions of total value. `distance_pp` is in
    percentage points, signed, positive = breach. `distance_value` is the
    same distance in currency at unchanged total, None when there is no
    total to price it against (a hypothetical weight). An exempt finding
    carries no arithmetic at all.
    """

    clause: str
    type: str
    subject: str
    observed: Optional[float]
    limit: Optional[float]
    bound: Optional[str]
    status: str
    distance_pp: Optional[float]
    distance_value: Optional[float]


def _finding(
    clause: Clause,
    subject: str,
    observed: float,
    limit: float,
    bound: str,
    total: Optional[float],
    over: str = BREACH,
) -> Finding:
    signed = (observed - limit) if bound == "max" else (limit - observed)
    return Finding(
        clause=clause.id,
        type=clause.type,
        subject=subject,
        observed=observed,
        limit=limit,
        bound=bound,
        status=over if signed > 0 else OK,
        distance_pp=signed * 100,
        distance_value=signed * total if total is not None else None,
    )


def _exempt(clause: Clause, subject: str) -> Finding:
    return Finding(clause.id, clause.type, subject, None, None, None, EXEMPT, None, None)


def check(
    ips: IPS,
    allocation: Mapping,
    instrument_types: Mapping[str, Optional[str]],
) -> List[Finding]:
    """Every checkable clause applied to the portfolio, in policy order.

    Args:
        ips: the loaded policy
        allocation: `shared_data["allocation"]` as PortfolioAnalysisAgent
            publishes it - `by_asset_class`, `by_sector` and `by_position`,
            each line carrying `pct_of_total`
        instrument_types: ticker -> 'share' | 'fund', one per position

    Returns:
        Findings: one per (clause, subject, bound). Statements produce none.
    """
    by_class = allocation.get("by_asset_class") or {}
    by_sector = allocation.get("by_sector") or {}
    by_position = allocation.get("by_position") or {}
    total = by_class.get("total_value")
    if not by_class.get("lines") or total is None:
        raise ComplianceError(
            "No by_asset_class block with a total_value in the allocation; "
            "every clause is measured against total value (D2)."
        )
    if total <= 0:
        raise ComplianceError(f"Total value is {total}; percentages are undefined.")
    if not by_position.get("lines"):
        raise ComplianceError(
            "No by_position lines in the allocation; the concentration clauses "
            "are checked over the positions PortfolioAnalysisAgent published."
        )

    unknown = sorted(
        f"{line['label']}={instrument_types.get(line['label'])!r}"
        for line in by_position["lines"]
        if instrument_types.get(line["label"]) not in INSTRUMENT_TYPES
    )
    if unknown:
        raise ComplianceError(
            f"Instrument type is not one of {INSTRUMENT_TYPES} for: {', '.join(unknown)}.\n"
            "IPS-4.2 counts directly held shares only; a holding of unknown type "
            "cannot be checked and is not assumed to be either."
        )

    class_lines: Dict[str, Mapping] = {line["label"]: line for line in by_class["lines"]}

    findings: List[Finding] = []
    for clause in ips.checkable:
        if clause.type == "asset_class_band":
            findings += _band(clause, class_lines, total)
        elif clause.type == "max_instrument_weight":
            findings += _per_position(clause, by_position, total, instrument_types, exempt_funds=False)
        elif clause.type == "max_issuer_weight":
            findings += _per_position(clause, by_position, total, instrument_types, exempt_funds=True)
        elif clause.type == "max_sector_weight":
            findings += _per_sector(clause, by_sector, total, instrument_types)
        else:
            # The loader's vocabulary and this dispatch are two statements of
            # the same set; a type that loads and does not dispatch is a
            # clause silently unchecked.
            raise ComplianceError(f"{clause.id}: no checker for type {clause.type!r}.")
    return findings


def _band(clause: Clause, class_lines: Mapping[str, Mapping], total: float) -> List[Finding]:
    label = clause.params["asset_class"]
    line = class_lines.get(label)
    if line is None:
        raise ComplianceError(
            f"{clause.id} names asset class {label!r}; the allocation has lines for "
            f"{sorted(class_lines)}. An absent class is zero only if the label is "
            "right, and a wrong label would pass as an empty class."
        )
    observed = line.get("pct_of_total")
    if observed is None:
        raise ComplianceError(
            f"{clause.id}: {label} carries no pct_of_total. The share of total "
            "is published by PortfolioAnalysisAgent, not divided for here."
        )

    out = []
    if "min" in clause.params:
        out.append(_finding(clause, label, observed, clause.params["min"], "min", total))
    if "max" in clause.params:
        out.append(_finding(clause, label, observed, clause.params["max"], "max", total))
    return out


def _per_position(
    clause: Clause,
    by_position: Mapping,
    total: float,
    instrument_types: Mapping[str, Optional[str]],
    exempt_funds: bool,
) -> List[Finding]:
    out = []
    for line in by_position["lines"]:
        ticker = line["label"]
        if exempt_funds and instrument_types[ticker] == FUND:
            out.append(_exempt(clause, ticker))
            continue
        observed = line.get("pct_of_total")
        if observed is None:
            raise ComplianceError(
                f"{clause.id}: {ticker} carries no pct_of_total. The share of total "
                "is published by PortfolioAnalysisAgent, not divided for here."
            )
        out.append(_finding(clause, ticker, observed, clause.params["max"], "max", total))
    return out


def _per_sector(
    clause: Clause,
    by_sector: Mapping,
    total: float,
    instrument_types: Mapping[str, Optional[str]],
) -> List[Finding]:
    lines = by_sector.get("lines")
    if not lines:
        raise ComplianceError(f"{clause.id}: no by_sector lines in the allocation.")

    out = []
    for line in lines:
        label = line["label"]
        if label == UNSECTORED_LABEL:
            continue  # reported, not counted (IPS-4.3)
        funds = sorted(t for t in line.get("tickers", []) if instrument_types.get(t) == FUND)
        if funds:
            raise ComplianceError(
                f"{clause.id}: sector {label!r} contains funds {funds}. Sectors are "
                "counted over directly held shares; a fund with a sector is a data "
                "inconsistency, not a sector exposure."
            )
        # The share of total (D2, Part 7), not either of the sector block's
        # own denominators, and read rather than divided for.
        observed = line.get("pct_of_total")
        if observed is None:
            raise ComplianceError(
                f"{clause.id}: sector {label!r} carries no pct_of_total. The share "
                "of total is published by PortfolioAnalysisAgent, not divided for here."
            )
        out.append(_finding(clause, label, observed, clause.params["max"], "max", total))
    return out


def refuse(ips: IPS, weight: float) -> List[Finding]:
    """A hypothetical weight in one position, against every concentration
    clause. The position is unnamed, so it may be a share or a fund and both
    the instrument and the issuer limit apply. No portfolio, so no total and
    no currency distance. Over a limit is `refused`; at or under is `ok` -
    the policy permits it and the checker says so.
    """
    if not 0 < weight <= 1:
        raise ComplianceError(f"Weight {weight!r} is not a fraction in (0, 1].")
    return [
        _finding(clause, HYPOTHETICAL, weight, clause.params["max"], "max", None, over=REFUSED)
        for clause in ips.checkable
        if clause.type in ("max_instrument_weight", "max_issuer_weight")
    ]
