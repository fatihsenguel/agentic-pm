"""
Allocation checked against tests/golden/expected_values.md Parts 2 and 3.

Every expected number here is copied from that document, which was computed by
hand in expected_values.xlsx. If a test fails, one of the two is wrong and that
gets resolved deliberately. Do NOT update these figures to match code output.

Fixture is portfolio 3 as seeded by seed_portfolio.py, priced at the closes
recorded in expected_values.md Part 1. No database is touched.
"""

import pytest

from portfolio_tool.quant.allocation import (
    AllocationError,
    allocation_by_asset_class,
    allocation_by_sector,
)


HOLDINGS = [
    {"ticker": "SPY",  "quantity": 100, "average_price": 500.0, "asset_class": "Equity",       "sector": None},
    {"ticker": "AAPL", "quantity": 200, "average_price": 200.0, "asset_class": "Equity",       "sector": "Technology"},
    {"ticker": "MSFT", "quantity": 100, "average_price": 400.0, "asset_class": "Equity",       "sector": "Technology"},
    {"ticker": "JNJ",  "quantity": 150, "average_price": 150.0, "asset_class": "Equity",       "sector": "Healthcare"},
    {"ticker": "JPM",  "quantity": 100, "average_price": 200.0, "asset_class": "Equity",       "sector": "Financials"},
    {"ticker": "NEE",  "quantity": 200, "average_price":  75.0, "asset_class": "Equity",       "sector": "Utilities"},
    {"ticker": "TLT",  "quantity": 500, "average_price":  90.0, "asset_class": "Fixed Income", "sector": None},
    {"ticker": "GLD",  "quantity": 100, "average_price": 250.0, "asset_class": "Commodity",    "sector": None},
    {"ticker": "VNQ",  "quantity": 300, "average_price":  90.0, "asset_class": "Real Estate",  "sector": None},
]

PRICES = {
    "SPY": 765.16, "AAPL": 324.96, "MSFT": 496.82, "JNJ": 275.21, "JPM": 356.22,
    "NEE": 83.10, "TLT": 81.95, "GLD": 402.78, "VNQ": 95.78,
}

CASH = 15500.0


def _by_label(allocation):
    return {line.label: line for line in allocation.lines}


# --- Part 2: asset class --------------------------------------------------

def test_asset_class_denominators():
    """Invested 394,700.50 plus cash 15,500 gives total 410,200.50."""
    a = allocation_by_asset_class(HOLDINGS, PRICES, CASH)
    assert a.invested_value == pytest.approx(394700.50, abs=0.01)
    assert a.cash_balance == pytest.approx(15500.00, abs=0.01)
    assert a.total_value == pytest.approx(410200.50, abs=0.01)


def test_asset_class_market_values():
    """Part 2, market value column."""
    lines = _by_label(allocation_by_asset_class(HOLDINGS, PRICES, CASH))
    assert lines["Equity"].market_value == pytest.approx(284713.50, abs=0.01)
    assert lines["Fixed Income"].market_value == pytest.approx(40975.00, abs=0.01)
    assert lines["Commodity"].market_value == pytest.approx(40278.00, abs=0.01)
    assert lines["Real Estate"].market_value == pytest.approx(28734.00, abs=0.01)
    assert lines["Cash"].market_value == pytest.approx(15500.00, abs=0.01)


def test_asset_class_cost_basis():
    """Part 2, cost basis column. Totals 300,000 flat including cash."""
    lines = _by_label(allocation_by_asset_class(HOLDINGS, PRICES, CASH))
    assert lines["Equity"].cost_basis == pytest.approx(187500.00, abs=0.01)
    assert lines["Fixed Income"].cost_basis == pytest.approx(45000.00, abs=0.01)
    assert lines["Commodity"].cost_basis == pytest.approx(25000.00, abs=0.01)
    assert lines["Real Estate"].cost_basis == pytest.approx(27000.00, abs=0.01)
    total = sum(l.cost_basis for l in allocation_by_asset_class(HOLDINGS, PRICES, CASH).lines)
    assert total == pytest.approx(300000.00, abs=0.01)


def test_asset_class_percentages_are_the_answer_to_1_1():
    """
    Part 2, market value / % of total. Per D1 and D2 this IS case 1.1's answer.
    """
    lines = _by_label(allocation_by_asset_class(HOLDINGS, PRICES, CASH))
    assert lines["Equity"].pct_of_denominator == pytest.approx(0.6941, abs=0.00005)
    assert lines["Fixed Income"].pct_of_denominator == pytest.approx(0.0999, abs=0.00005)
    assert lines["Commodity"].pct_of_denominator == pytest.approx(0.0982, abs=0.00005)
    assert lines["Real Estate"].pct_of_denominator == pytest.approx(0.0700, abs=0.00005)
    assert lines["Cash"].pct_of_denominator == pytest.approx(0.0378, abs=0.00005)


def test_asset_class_percentages_sum_to_one():
    a = allocation_by_asset_class(HOLDINGS, PRICES, CASH)
    assert sum(l.pct_of_denominator for l in a.lines) == pytest.approx(1.0, abs=1e-9)


def test_cash_has_no_percent_invested():
    """D2 puts cash in the total denominator; it is still not invested."""
    lines = _by_label(allocation_by_asset_class(HOLDINGS, PRICES, CASH))
    assert lines["Cash"].pct_of_invested is None
    assert lines["Equity"].pct_of_invested == pytest.approx(0.7213, abs=0.00005)


# --- Part 3: sector -------------------------------------------------------

def test_sector_market_values():
    """Part 3, market value column."""
    lines = _by_label(allocation_by_sector(HOLDINGS, PRICES))
    assert lines["Technology"].market_value == pytest.approx(114674.00, abs=0.01)
    assert lines["Healthcare"].market_value == pytest.approx(41281.50, abs=0.01)
    assert lines["Financials"].market_value == pytest.approx(35622.00, abs=0.01)
    assert lines["Utilities"].market_value == pytest.approx(16620.00, abs=0.01)
    assert lines["(no sector)"].market_value == pytest.approx(186503.00, abs=0.01)


def test_sector_denominators():
    """Sectored 208,197.50; invested 394,700.50. Cash is excluded from both."""
    a = allocation_by_sector(HOLDINGS, PRICES)
    assert a.total_value == pytest.approx(208197.50, abs=0.01)
    assert a.invested_value == pytest.approx(394700.50, abs=0.01)


def test_sector_percent_of_sectored():
    """Part 3, market value / % sectored."""
    lines = _by_label(allocation_by_sector(HOLDINGS, PRICES))
    assert lines["Technology"].pct_of_denominator == pytest.approx(0.5508, abs=0.00005)
    assert lines["Healthcare"].pct_of_denominator == pytest.approx(0.1983, abs=0.00005)
    assert lines["Financials"].pct_of_denominator == pytest.approx(0.1711, abs=0.00005)
    assert lines["Utilities"].pct_of_denominator == pytest.approx(0.0798, abs=0.00005)


def test_sector_percent_of_invested():
    """Part 3, market value / % invested."""
    lines = _by_label(allocation_by_sector(HOLDINGS, PRICES))
    assert lines["Technology"].pct_of_invested == pytest.approx(0.2905, abs=0.00005)
    assert lines["Healthcare"].pct_of_invested == pytest.approx(0.1046, abs=0.00005)
    assert lines["Financials"].pct_of_invested == pytest.approx(0.0903, abs=0.00005)
    assert lines["Utilities"].pct_of_invested == pytest.approx(0.0421, abs=0.00005)
    assert lines["(no sector)"].pct_of_invested == pytest.approx(0.4725, abs=0.00005)


def test_unsectored_is_reported_not_dropped():
    """
    D3. 47% of this portfolio has no sector. Dropping it silently would roughly
    double every sector figure, which is why the line exists and why it has no
    '% sectored' of its own.
    """
    lines = _by_label(allocation_by_sector(HOLDINGS, PRICES))
    assert "(no sector)" in lines
    assert lines["(no sector)"].pct_of_denominator is None
    assert set(lines["(no sector)"].tickers) == {"SPY", "TLT", "GLD", "VNQ"}


def test_sectored_percentages_sum_to_one():
    a = allocation_by_sector(HOLDINGS, PRICES)
    sectored = [l for l in a.lines if l.pct_of_denominator is not None]
    assert sum(l.pct_of_denominator for l in sectored) == pytest.approx(1.0, abs=1e-9)


# --- Failure modes --------------------------------------------------------

def test_missing_price_raises_rather_than_skipping():
    """
    A skipped holding shrinks the denominator and moves every percentage while
    still looking like a valid answer. That is the failure shape this project
    keeps removing, so it raises.
    """
    partial = {k: v for k, v in PRICES.items() if k != "GLD"}
    with pytest.raises(AllocationError, match="GLD"):
        allocation_by_asset_class(HOLDINGS, partial, CASH)


def test_empty_holdings_raises():
    with pytest.raises(AllocationError):
        allocation_by_asset_class([], PRICES, CASH)
