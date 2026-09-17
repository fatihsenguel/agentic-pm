"""
The investment philosophy, loaded from philosophy.toml.

The IPS pattern for the second question. The IPS (ips.py) says what may be
held and how much; the philosophy (docs/PHILOSOPHY.md, philosophy.toml)
says what is worth wanting: numbered clauses, a derived config, numeric
criteria screened deterministically and cited by clause, statements citable
but not computed. Two documents because they change for different reasons
(DIRECTION.md Order 3). Synthetic for now; a personal one replaces it as a
file with no code change.

This module states what a philosophy is and loads nothing itself: the id
prefix, the type table, the checks on each type's parameters. The loading
is clauses.py, shared with the IPS. It computes nothing; the screen does
that (screening.py), over the metrics quant/fundamentals.py computes.

The type vocabulary is closed, four types: a statement; a metric_band, one
named figure held to a floor, a ceiling or both over a stated number of
latest fiscal years; a margin_of_safety, the price against the low end of
the valuation range less a discount; an excluded_industry, the SIC codes of
companies the philosophy does not screen at all (expected_values.md Part 10
F). The margin_of_safety may carry the range's three investor assumptions,
required_return, terminal_growth and horizon_years, all three or none
(Part 11 D38): they sit on the clause that reads the range the way
tax_rate sits on the clause that names its metric (decision 46), and a
statement carries no number. And every `metric` key is one
quant/fundamentals.METRICS computes: a key
nothing computes fails to load, so a philosophy that loads is one every
numeric clause of which can be screened. The vocabulary grows one clause at
a time, reference first, the way the IPS's does (ips.py's docstring has the
order).
"""

import re
from types import MappingProxyType
from typing import Any, Mapping

from portfolio_tool.clauses import (
    STATEMENT, Clause, ClauseDocument, ClauseError, DocumentSpec, load_clauses,
    normalise_topic, resolve_path,
)
from portfolio_tool.quant.fundamentals import ASSUMPTIONS, METRICS

__all__ = ["Philosophy", "PhilosophyError", "Clause", "CLAUSE_TYPES", "STATEMENT",
           "CLAUSE_ID", "load_philosophy", "normalise_topic", "resolve_path"]

Philosophy = ClauseDocument

CLAUSE_ID = re.compile(r"^PHI-\d+\.\d+$")

# type -> (required parameters, optional parameters). A statement takes none.
# A metric_band needs at least one bound, checked below.
CLAUSE_TYPES: Mapping[str, tuple] = MappingProxyType({
    STATEMENT: ((), ()),
    "metric_band": (("metric", "years"), ("min", "max", "tax_rate")),
    "margin_of_safety": (("discount",), ("required_return", "terminal_growth", "horizon_years")),
    "excluded_industry": (("sic_codes",), ()),
})

_BOUNDS = ("min", "max")
# Part 11 D38: the range's assumptions a margin_of_safety may state, together.
_RANGE_ASSUMPTIONS = ("required_return", "terminal_growth", "horizon_years")
_ASSUMPTION_KEYS = tuple(sorted({k for keys in ASSUMPTIONS.values() for k in keys}))

# A SIC code as EDGAR's submissions document carries it (expected_values.md
# Part 13 C): a string of four digits, compared as written.
_SIC_CODE = re.compile(r"^\d{4}$")


class PhilosophyError(ClauseError):
    """Raised when the philosophy file cannot be loaded as a valid philosophy."""


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _validate_params(where: str, clause_type: str, params: Mapping[str, Any]) -> None:
    if clause_type == "metric_band":
        metric = params["metric"]
        if metric not in METRICS:
            raise PhilosophyError(
                f"{where}: no formula computes {metric!r}. The metric keys are "
                f"{', '.join(METRICS)}; a key is one formula in quant/fundamentals.py, "
                "and a clause on a figure nothing computes cannot be screened."
            )
        years = params["years"]
        if not isinstance(years, int) or isinstance(years, bool) or years < 1:
            raise PhilosophyError(f"{where}: years = {years!r} is not a positive whole "
                                  "number of fiscal years.")
        if not any(k in params for k in _BOUNDS):
            raise PhilosophyError(f"{where}: a metric_band needs min, max or both.")
        for k in _BOUNDS:
            if k in params and not _is_number(params[k]):
                raise PhilosophyError(f"{where}: {k} = {params[k]!r} is not a number; "
                                      "limits are in the metric's own unit.")
        if "min" in params and "max" in params and params["min"] >= params["max"]:
            raise PhilosophyError(f"{where}: min {params['min']} is not below max {params['max']}.")
        # D32: the assumptions a metric reads are the clause's to state, and
        # only a clause whose metric reads one carries it.
        needed = ASSUMPTIONS.get(metric, ())
        absent = [k for k in needed if k not in params]
        if absent:
            raise PhilosophyError(f"{where}: {metric} needs {absent}; the rate NOPAT is taxed "
                                  "at is stated in the clause, never read from the company.")
        unread = sorted(k for k in _ASSUMPTION_KEYS if k in params and k not in needed)
        if unread:
            raise PhilosophyError(f"{where}: {metric} does not take {unread}.")
        if "tax_rate" in params:
            rate = params["tax_rate"]
            if not _is_number(rate) or not 0 <= rate < 1:
                raise PhilosophyError(f"{where}: tax_rate = {rate!r} is not a fraction in "
                                      "[0, 1); a 20% rate is 0.20.")

    elif clause_type == "excluded_industry":
        codes = params["sic_codes"]
        if not isinstance(codes, list):
            raise PhilosophyError(f"{where}: sic_codes = {codes!r} is not a list of codes.")
        if not codes:
            raise PhilosophyError(f"{where}: sic_codes needs at least one code; a clause that "
                                  "excludes nothing is a statement.")
        for code in codes:
            if not isinstance(code, str) or not _SIC_CODE.match(code):
                raise PhilosophyError(f"{where}: {code!r} is not a SIC code as EDGAR states one, "
                                      "a string of four digits.")
        repeated = sorted({c for c in codes if codes.count(c) > 1})
        if repeated:
            raise PhilosophyError(f"{where}: {', '.join(repeated)} listed twice.")

    elif clause_type == "margin_of_safety":
        discount = params["discount"]
        if not _is_number(discount) or not 0 < discount < 1:
            raise PhilosophyError(f"{where}: discount = {discount!r} is not a fraction in "
                                  "(0, 1); a 25% discount is 0.25.")
        stated = [k for k in _RANGE_ASSUMPTIONS if k in params]
        if stated and len(stated) < len(_RANGE_ASSUMPTIONS):
            raise PhilosophyError(f"{where}: the range's assumptions are stated all three or "
                                  f"none, {list(_RANGE_ASSUMPTIONS)}; {stated} alone is not "
                                  "a range anyone can compute.")
        if stated:
            r, g, n = (params[k] for k in _RANGE_ASSUMPTIONS)
            if not _is_number(r) or not 0 < r < 1:
                raise PhilosophyError(f"{where}: required_return = {r!r} is not a fraction in "
                                      "(0, 1); a 9% return is 0.09.")
            if not _is_number(g):
                raise PhilosophyError(f"{where}: terminal_growth = {g!r} is not a number; a "
                                      "3% growth is 0.03.")
            if r <= g:
                raise PhilosophyError(f"{where}: required_return {r} is not above terminal_growth "
                                      f"{g}; the terminal value is undefined or negative.")
            if not isinstance(n, int) or isinstance(n, bool) or n < 1:
                raise PhilosophyError(f"{where}: horizon_years = {n!r} is not a positive whole "
                                      "number of fiscal years.")


SPEC = DocumentSpec(
    noun="philosophy",
    id_pattern=CLAUSE_ID,
    id_form="PHI-<section>.<number>",
    types=CLAUSE_TYPES,
    validate_params=_validate_params,
    error=PhilosophyError,
)


def load_philosophy(path: str) -> Philosophy:
    """Load and validate the philosophy.toml at `path`, relative to the
    project root or absolute. Raises PhilosophyError on anything short of a
    philosophy every clause of which the screen can either screen or cite.
    No default path."""
    return load_clauses(path, SPEC)
