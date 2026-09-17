"""
The valuation range from stated assumptions.

Reference: tests/golden/expected_values.md Part 11, computed by hand before
this existed, and its decisions:

  D37  One formula, a discounted cash flow over the latest fiscal year's
       free cash flow, run once at each of two stated growth rates. The
       low end is the value at growth_low and the high end the value at
       growth_high. There is no midpoint and no spread around a point
       (PHI-4.3).
  D38  Five assumptions, every one stated in a document and carried to the
       record as its name, its value and the id of the clause or entry that
       stated it. None is proposed here, defaulted here or read from
       anywhere but the mapping passed in.
  D39  Every filed input is the latest fiscal year's, the year filed by the
       as-of date (D21): free cash flow is that year's operating cash flow
       less capex; net debt is quant/fundamentals.net_debt on that year, so
       the range and PHI-3.1 share one arithmetic path; the share count is
       the year's own.
  D40  The record carries the two ends, the as-of date, the year with its
       end and filed dates, the source and the assumptions, and no filed
       figure. Six conditions raise, naming which; nothing is sorted,
       clamped, defaulted or filled.

Pure functions over the figures block. No database, no model, no price:
the range needs none, and the margin of safety that reads it against a
price is the screen's (PHI-4.1). Decimal arithmetic throughout; the value
per share is a ratio and, as in quant/fundamentals.py, the ratio is where
exactness ends and a float is returned.
"""

import datetime as dt
from decimal import Decimal
from typing import Dict, Mapping, Optional, Tuple

from portfolio_tool.quant.fundamentals import _date, _figure, net_debt, years_filed_by

# D38: the assumptions the formula reads, and nothing else.
RATES: Tuple[str, ...] = ("required_return", "terminal_growth", "growth_low", "growth_high")
HORIZON = "horizon_years"
ASSUMPTIONS: Tuple[str, ...] = RATES + (HORIZON,)


class ValuationError(Exception):
    """Raised when a range cannot honestly follow from the figures and the
    assumptions given."""


def free_cash_flow(year: str, figures: Mapping) -> Optional[Decimal]:
    """Operating cash flow less capex, exact; None when either is not in
    the year's figures."""
    ocf, capex = _figure(year, figures, "operating_cash_flow"), _figure(year, figures, "capex")
    if ocf is None or capex is None:
        return None
    return ocf - capex


def enterprise_value(fcf0: Decimal, growth: Decimal, required_return: Decimal,
                     terminal_growth: Decimal, horizon: int) -> Tuple[Decimal, Decimal]:
    """D37's formula at one growth rate: the sum of the horizon's discounted
    cash flows, and that sum plus the discounted terminal value. Returns
    both so the reference's intermediate total can be held."""
    years = Decimal(0)
    for t in range(1, horizon + 1):
        years += fcf0 * (1 + growth) ** t / (1 + required_return) ** t
    final = fcf0 * (1 + growth) ** horizon
    terminal = final * (1 + terminal_growth) / (required_return - terminal_growth)
    return years, years + terminal / (1 + required_return) ** horizon


def _stated(assumptions: Mapping) -> Dict[str, object]:
    """The five assumptions as numbers of their kind, each with a source.
    A missing one, an unknown one, a rate that is not a number, a horizon
    that is not a whole number of years, or an entry with no source raises
    naming it (D38, D40)."""
    unknown = sorted(set(assumptions) - set(ASSUMPTIONS))
    if unknown:
        raise ValuationError(f"{unknown} are not assumptions the range reads; the assumptions "
                             f"are {list(ASSUMPTIONS)}.")
    out: Dict[str, object] = {}
    for name in ASSUMPTIONS:
        if name not in assumptions:
            raise ValuationError(f"{name} is not stated; a range follows from stated "
                                 "assumptions and nothing is assumed for you.")
        entry = assumptions[name]
        if not isinstance(entry, Mapping) or "value" not in entry:
            raise ValuationError(f"{name} carries no value.")
        if not isinstance(entry.get("source"), str) or not entry["source"].strip():
            raise ValuationError(f"{name} carries no source; an assumption names the clause "
                                 "or the watchlist entry that states it.")
        value = entry["value"]
        if name == HORIZON:
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValuationError(f"{name} = {value!r} is not a whole number of years of "
                                     "at least 1.")
            out[name] = value
        else:
            if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
                raise ValuationError(f"{name} = {value!r} is not a number; a rate is a fraction, "
                                     "9% written 0.09.")
            out[name] = Decimal(str(value)) if isinstance(value, float) else Decimal(value)
    if out["growth_low"] >= out["growth_high"]:
        raise ValuationError(
            f"growth_low = {out['growth_low']} is not below growth_high = {out['growth_high']}; "
            "two ends that are one number are a point, and reversed ends are contradictory "
            "assumptions, not a range to be sorted (PHI-4.3).")
    if out["required_return"] <= out["terminal_growth"]:
        raise ValuationError(
            f"required_return = {out['required_return']} is not above terminal_growth = "
            f"{out['terminal_growth']}; the terminal value is undefined or negative.")
    return out


def valuation_range(block: Mapping, assumptions: Mapping, as_of: dt.date) -> Dict[str, object]:
    """The range per share on the latest fiscal year filed by `as_of`, as
    D40's record. `assumptions` maps each name to its value and its source."""
    source = block.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValuationError("The figures block names no source; a range over figures of "
                             "unknown origin is a number without a source.")
    stated = _stated(assumptions)

    years = years_filed_by(block, as_of)
    if not years:
        raise ValuationError(f"The figures have no fiscal year filed by {as_of}; a year not "
                             "yet filed is not a year (D21).")
    label = years[-1]
    figures = block["years"][label]

    fcf0 = free_cash_flow(label, figures)
    if fcf0 is None:
        raise ValuationError(f"{label}: operating_cash_flow or capex is not in the figures, "
                             "so there is no free cash flow to value.")
    if fcf0 <= 0:
        raise ValuationError(f"{label}: free cash flow is {fcf0}, not positive; this method "
                             "values a business that generates cash and says nothing about "
                             "one that does not.")
    debt = net_debt(label, figures)
    if debt is None:
        raise ValuationError(f"{label}: a borrowing field or cash is not in the figures, so "
                             "there is no net debt to take from enterprise value (D33).")
    shares = _figure(label, figures, "shares_outstanding")
    if shares is None:
        raise ValuationError(f"{label}: shares_outstanding is not in the figures; nothing "
                             "divides by a count from another date (D39).")
    if shares <= 0:
        raise ValuationError(f"{label}: shares_outstanding = {shares} is not positive.")

    ends: Dict[str, float] = {}
    for end, name in (("low", "growth_low"), ("high", "growth_high")):
        _, enterprise = enterprise_value(fcf0, stated[name], stated["required_return"],
                                         stated["terminal_growth"], stated[HORIZON])
        equity = enterprise - debt
        if equity <= 0:
            raise ValuationError(f"{label}: equity at the {end} end is {equity}, not positive; "
                                 "a value at or below nothing is not an end of a range "
                                 "(PHI-4.1 reads the low end).")
        ends[end] = float(equity / shares)

    return {
        "low": ends["low"],
        "high": ends["high"],
        "as_of": as_of,
        "year": label,
        "ends": _date(label, figures, "ends"),
        "filed": _date(label, figures, "filed"),
        "source": source,
        "assumptions": {name: {"value": assumptions[name]["value"],
                               "source": assumptions[name]["source"]} for name in ASSUMPTIONS},
    }
