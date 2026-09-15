"""
Metrics per fiscal year from a company's reported figures.

Reference: tests/golden/expected_values.md Part 10, computed by hand before
this existed, and its decisions:

  D21  A fiscal year counts when its report was filed on or before the
       as-of date. `years_filed_by` is that selection, in fiscal order; a
       year not yet filed is not a year, and nothing waits for it or fills it.
  D24  A figure is the company's reported figure, as filed, adjusted by
       nobody. A metric is one stated formula over reported figures, and
       the formula here is the definition of the metric key the philosophy
       names (Part 10 B). A different formula is a different key.

Pure functions over the figures block, the shape the screen reads and a
reader tool will one day publish: one company, its fiscal years with their
end and filed dates and reported figures by name, the shares outstanding,
the price and the valuation range with their as-of dates. No database, no
model, no state.

A blank figure is allowed - Part 10 A has them - and the metric that needs
it is then absent for that year, never zero. Whether the absence matters is
the screen's question (D25), not this module's. What does raise here is
arithmetic that would otherwise produce a plausible number: a division by
zero, a figure that is not a number, a year with no dates.

Where a filed figure stops being exact (Part 12 G). The reader's block
carries every figure as a Decimal in the unit it was filed in, and a typed
block carries what was typed; every figure is read as a Decimal, a float
by its written digits, so a sum, a difference and a product with a stated
rate are exact and `net_debt` is a Decimal. A metric is a ratio, and the
ratio is the first place exactness ends: it is returned as a float, which
is what a clause's limit is compared against.

  D33  Debt reaches the block as every borrowing tag, separately; the sum
       is this module's. A borrowing is one of BORROWING_FIELDS, a finance
       lease is not one, and a year in which any of the three did not
       resolve has no net debt and no invested capital: a missing
       borrowing field is never read as 0.
  D32  The rate NOPAT is taxed at is a stated assumption, the philosophy's,
       passed in beside the block; the block's effective_tax_rate is a
       filed figure and is not read. ASSUMPTIONS names, per metric, what
       the caller states; a metric whose assumption is not stated is
       absent for every year, never computed at a rate nobody stated.

The block's figures are the reader's fields (filed_figures.FIELDS, Part 12
C) and nothing else: a year carrying a key no field names is a typed block
in an old shape and raises, rather than being read around.
"""

import datetime as dt
from decimal import Decimal
from typing import Callable, Dict, List, Mapping, Optional, Tuple

from portfolio_tool.filed_figures import FIELDS

Figures = Mapping[str, object]
Assumptions = Mapping[str, object]

# The figure vocabulary: what a year of the block may carry besides its dates.
FIGURE_FIELDS = frozenset(field.name for field in FIELDS)

# Per metric key, the assumptions the caller states (D32). Nothing else is
# an assumption; a key here is read by exactly one formula below.
ASSUMPTIONS: Mapping[str, Tuple[str, ...]] = {
    "return_on_invested_capital": ("tax_rate",),
}

# D33, Part 12 C: the block's borrowing fields, and the definition of debt in
# Part 10 B's formulas. Their sum is arithmetic here, never on the way in.
BORROWING_FIELDS: Tuple[str, ...] = (
    "commercial_paper", "long_term_debt_current", "long_term_debt_noncurrent")


class FundamentalsError(Exception):
    """Raised when the figures block cannot honestly yield a metric."""


def _number(year: str, key: str, value) -> Decimal:
    """A figure as a Decimal: a filed Decimal as it is, an int exactly, a
    typed float by its written digits. A bool or a string is not a figure."""
    if isinstance(value, bool):
        raise FundamentalsError(f"{year}: {key} = {value!r} is not a number.")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    raise FundamentalsError(f"{year}: {key} = {value!r} is not a number.")


def _figure(year: str, figures: Mapping, key: str) -> Optional[Decimal]:
    if key not in figures:
        return None
    return _number(year, key, figures[key])


def _divide(year: str, numerator: Decimal, denominator: Decimal, what: str) -> float:
    """The ratio, and the end of exactness: a float."""
    if denominator == 0:
        raise FundamentalsError(f"{year}: {what} is 0; the ratio is undefined and is not "
                                "reported as anything else.")
    return float(numerator / denominator)


# --- the figures that are sums, Part 12 G --------------------------------------

def _borrowings(year: str, f: Mapping) -> Optional[Decimal]:
    parts = [_figure(year, f, k) for k in BORROWING_FIELDS]
    if any(v is None for v in parts):
        return None
    return sum(parts, Decimal(0))


def net_debt(year: str, figures: Mapping) -> Optional[Decimal]:
    """Borrowings less cash, exact (D33, Part 12 F definition A, Part 12 G).
    None when a borrowing field or cash is not in the year's figures."""
    borrowings, cash = _borrowings(year, figures), _figure(year, figures, "cash")
    if borrowings is None or cash is None:
        return None
    return borrowings - cash


def _stated_rate(assumptions: Assumptions) -> Optional[Decimal]:
    """The tax rate the caller states, a fraction in [0, 1), as a Decimal;
    None when none is stated. A stated rate that is not a fraction raises."""
    if "tax_rate" not in assumptions:
        return None
    rate = assumptions["tax_rate"]
    if isinstance(rate, bool) or not isinstance(rate, (int, float, Decimal)):
        raise FundamentalsError(f"tax_rate = {rate!r} is not a number; a stated rate is a "
                                "fraction in [0, 1), 20% written 0.20.")
    if not 0 <= rate < 1:
        raise FundamentalsError(f"tax_rate = {rate!r} is not a fraction in [0, 1); 20% is "
                                "written 0.20.")
    return _number("the stated assumptions", "tax_rate", rate)


def nopat(year: str, figures: Mapping, assumptions: Assumptions) -> Optional[Decimal]:
    """Operating income less tax at the stated rate, exact (D32, Part 12 G).
    None when the year has no operating income or no rate is stated."""
    operating_income, rate = _figure(year, figures, "operating_income"), _stated_rate(assumptions)
    if operating_income is None or rate is None:
        return None
    return operating_income * (1 - rate)


# --- the formulas, Part 10 B ---------------------------------------------------

def _return_on_invested_capital(year: str, f: Mapping, block: Figures,
                                assumptions: Assumptions) -> Optional[float]:
    inputs = [_figure(year, f, k) for k in ("equity", "cash")]
    borrowings, after_tax = _borrowings(year, f), nopat(year, f, assumptions)
    if any(v is None for v in inputs) or borrowings is None or after_tax is None:
        return None
    equity, cash = inputs
    return _divide(year, after_tax, equity + borrowings - cash, "invested capital (equity + debt - cash)")


def _gross_margin(year: str, f: Mapping, block: Figures, assumptions: Assumptions) -> Optional[float]:
    revenue, gross_profit = _figure(year, f, "revenue"), _figure(year, f, "gross_profit")
    if revenue is None or gross_profit is None:
        return None
    return _divide(year, gross_profit, revenue, "revenue")


def _net_debt_to_ebitda(year: str, f: Mapping, block: Figures, assumptions: Assumptions) -> Optional[float]:
    inputs = [_figure(year, f, k) for k in ("operating_income", "depreciation_amortisation")]
    debt = net_debt(year, f)
    if any(v is None for v in inputs) or debt is None:
        return None
    operating_income, da = inputs
    return _divide(year, debt, operating_income + da, "EBITDA (operating income + D&A)")


def _free_cash_flow_yield(year: str, f: Mapping, block: Figures, assumptions: Assumptions) -> Optional[float]:
    """The year's free cash flow at the as-of price: the one metric that
    needs the price and the shares, which sit on the block, not the year."""
    ocf, capex = _figure(year, f, "operating_cash_flow"), _figure(year, f, "capex")
    price, shares = block.get("price"), block.get("shares_outstanding")
    if ocf is None or capex is None or not isinstance(price, Mapping) or shares is None:
        return None
    price_value = _number(year, "price", price.get("value"))
    market_value = price_value * _number(year, "shares_outstanding", shares)
    return _divide(year, ocf - capex, market_value, "market value (price x shares)")


# The metric vocabulary: the keys a philosophy clause may name. A key here
# is a formula above and nothing else; the loader refuses any other key.
METRICS: Mapping[str, Callable[[str, Mapping, Figures, Assumptions], Optional[float]]] = {
    "return_on_invested_capital": _return_on_invested_capital,
    "gross_margin": _gross_margin,
    "net_debt_to_ebitda": _net_debt_to_ebitda,
    "free_cash_flow_yield": _free_cash_flow_yield,
}

_DATES = ("ends", "filed")


def _years(block: Figures) -> Mapping[str, Mapping]:
    years = block.get("years")
    if not isinstance(years, Mapping) or not years:
        raise FundamentalsError("The figures block has no fiscal years.")
    return years


def _date(year: str, figures: Mapping, key: str) -> dt.date:
    value = figures.get(key)
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise FundamentalsError(f"{year}: no {key} date ({value!r}); a fiscal year has "
                                "an end date and a filed date.")


def years_filed_by(block: Figures, as_of: dt.date) -> List[str]:
    """The fiscal years whose reports were filed on or before `as_of`, in
    fiscal order (D21). A year not yet filed is left out, not counted, not
    estimated."""
    years = _years(block)
    dated = []
    for label, figures in years.items():
        ends, filed = _date(label, figures, "ends"), _date(label, figures, "filed")
        if filed <= as_of:
            dated.append((ends, label))
    return [label for _, label in sorted(dated)]


def metrics_by_year(block: Figures, assumptions: Assumptions) -> Dict[str, Dict[str, float]]:
    """Every metric each fiscal year's figures and the stated assumptions
    allow, by year, by metric key. A metric whose inputs the year lacks, or
    whose assumption is not stated, is absent for that year."""
    unknown = sorted(set(assumptions) - {k for keys in ASSUMPTIONS.values() for k in keys})
    if unknown:
        raise FundamentalsError(f"{unknown} are not assumptions any metric reads; the "
                                f"assumptions are {sorted(k for keys in ASSUMPTIONS.values() for k in keys)}.")
    _stated_rate(assumptions)
    out: Dict[str, Dict[str, float]] = {}
    for label, figures in _years(block).items():
        for key in figures:
            if key in _DATES:
                continue
            if key not in FIGURE_FIELDS:
                raise FundamentalsError(
                    f"{label}: {key} is not a figure the block carries; the figures are "
                    f"the reader's fields ({', '.join(f.name for f in FIELDS)}).")
            _number(label, key, figures[key])
        computed = {}
        for name, formula in METRICS.items():
            value = formula(label, figures, block, assumptions)
            if value is not None:
                computed[name] = value
        out[label] = computed
    return out
