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
"""

import datetime as dt
from typing import Callable, Dict, List, Mapping, Optional

Figures = Mapping[str, object]


class FundamentalsError(Exception):
    """Raised when the figures block cannot honestly yield a metric."""


def _number(year: str, key: str, value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FundamentalsError(f"{year}: {key} = {value!r} is not a number.")
    return float(value)


def _figure(year: str, figures: Mapping, key: str) -> Optional[float]:
    if key not in figures:
        return None
    return _number(year, key, figures[key])


def _divide(year: str, numerator: float, denominator: float, what: str) -> float:
    if denominator == 0:
        raise FundamentalsError(f"{year}: {what} is 0; the ratio is undefined and is not "
                                "reported as anything else.")
    return numerator / denominator


# --- the formulas, Part 10 B ---------------------------------------------------

def _return_on_invested_capital(year: str, f: Mapping, block: Figures) -> Optional[float]:
    inputs = [_figure(year, f, k) for k in ("operating_income", "tax_rate", "equity", "debt", "cash")]
    if any(v is None for v in inputs):
        return None
    operating_income, tax_rate, equity, debt, cash = inputs
    nopat = operating_income * (1 - tax_rate)
    return _divide(year, nopat, equity + debt - cash, "invested capital (equity + debt - cash)")


def _gross_margin(year: str, f: Mapping, block: Figures) -> Optional[float]:
    revenue, gross_profit = _figure(year, f, "revenue"), _figure(year, f, "gross_profit")
    if revenue is None or gross_profit is None:
        return None
    return _divide(year, gross_profit, revenue, "revenue")


def _net_debt_to_ebitda(year: str, f: Mapping, block: Figures) -> Optional[float]:
    inputs = [_figure(year, f, k) for k in ("debt", "cash", "operating_income", "depreciation_amortisation")]
    if any(v is None for v in inputs):
        return None
    debt, cash, operating_income, da = inputs
    return _divide(year, debt - cash, operating_income + da, "EBITDA (operating income + D&A)")


def _free_cash_flow_yield(year: str, f: Mapping, block: Figures) -> Optional[float]:
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
METRICS: Mapping[str, Callable[[str, Mapping, Figures], Optional[float]]] = {
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


def metrics_by_year(block: Figures) -> Dict[str, Dict[str, float]]:
    """Every metric each fiscal year's figures allow, by year, by metric key.
    A metric whose inputs the year lacks is absent for that year."""
    out: Dict[str, Dict[str, float]] = {}
    for label, figures in _years(block).items():
        for key in figures:
            if key not in _DATES:
                _number(label, key, figures[key])
        computed = {}
        for name, formula in METRICS.items():
            value = formula(label, figures, block)
            if value is not None:
                computed[name] = value
        out[label] = computed
    return out
