"""
Allocation checked against tests/golden/expected_values.md Parts 2, 3 and 7.

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
    allocation_by_position,
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


def test_asset_class_percent_of_total_is_the_same_column():
    """
    Part 2, market value / % of total, under its own name. On an asset-class
    line the denominator IS the total, so `pct_of_total` and
    `pct_of_denominator` carry the same figure; the checker reads the first
    for every clause so that one name means one quantity in every view.
    """
    lines = _by_label(allocation_by_asset_class(HOLDINGS, PRICES, CASH))
    assert lines["Equity"].pct_of_total == pytest.approx(0.6941, abs=0.00005)
    assert lines["Cash"].pct_of_total == pytest.approx(0.0378, abs=0.00005)
    for line in lines.values():
        assert line.pct_of_total == line.pct_of_denominator


# --- Part 3: sector -------------------------------------------------------

def test_sector_market_values():
    """Part 3, market value column."""
    lines = _by_label(allocation_by_sector(HOLDINGS, PRICES, CASH))
    assert lines["Technology"].market_value == pytest.approx(114674.00, abs=0.01)
    assert lines["Healthcare"].market_value == pytest.approx(41281.50, abs=0.01)
    assert lines["Financials"].market_value == pytest.approx(35622.00, abs=0.01)
    assert lines["Utilities"].market_value == pytest.approx(16620.00, abs=0.01)
    assert lines["(no sector)"].market_value == pytest.approx(186503.00, abs=0.01)


def test_sector_denominators():
    """
    Sectored 208,197.50; invested 394,700.50; total 410,200.50 with cash.
    Cash is outside the sectored and invested denominators and inside the
    total (D2), which the sector view carries so that the IPS-4.3 share of
    total is computed here and not by a reader dividing.
    """
    a = allocation_by_sector(HOLDINGS, PRICES, CASH)
    assert a.sectored_value == pytest.approx(208197.50, abs=0.01)
    assert a.invested_value == pytest.approx(394700.50, abs=0.01)
    assert a.cash_balance == pytest.approx(15500.00, abs=0.01)
    assert a.total_value == pytest.approx(410200.50, abs=0.01)


def test_asset_class_view_has_no_sectored_value():
    a = allocation_by_asset_class(HOLDINGS, PRICES, CASH)
    assert a.sectored_value is None


def test_sector_percent_of_sectored():
    """Part 3, market value / % sectored."""
    lines = _by_label(allocation_by_sector(HOLDINGS, PRICES, CASH))
    assert lines["Technology"].pct_of_denominator == pytest.approx(0.5508, abs=0.00005)
    assert lines["Healthcare"].pct_of_denominator == pytest.approx(0.1983, abs=0.00005)
    assert lines["Financials"].pct_of_denominator == pytest.approx(0.1711, abs=0.00005)
    assert lines["Utilities"].pct_of_denominator == pytest.approx(0.0798, abs=0.00005)


def test_sector_percent_of_invested():
    """Part 3, market value / % invested."""
    lines = _by_label(allocation_by_sector(HOLDINGS, PRICES, CASH))
    assert lines["Technology"].pct_of_invested == pytest.approx(0.2905, abs=0.00005)
    assert lines["Healthcare"].pct_of_invested == pytest.approx(0.1046, abs=0.00005)
    assert lines["Financials"].pct_of_invested == pytest.approx(0.0903, abs=0.00005)
    assert lines["Utilities"].pct_of_invested == pytest.approx(0.0421, abs=0.00005)
    assert lines["(no sector)"].pct_of_invested == pytest.approx(0.4725, abs=0.00005)


def test_sector_percent_of_total_is_the_ips_4_3_column():
    """
    Part 7, IPS-4.3, % of total: the sector's market value over total
    portfolio value including cash. Neither of Part 3's columns is this
    figure. The unsectored line carries it too - Part 7 reports it and does
    not count it.
    """
    lines = _by_label(allocation_by_sector(HOLDINGS, PRICES, CASH))
    assert lines["Technology"].pct_of_total == pytest.approx(0.2796, abs=0.00005)
    assert lines["Healthcare"].pct_of_total == pytest.approx(0.1006, abs=0.00005)
    assert lines["Financials"].pct_of_total == pytest.approx(0.0868, abs=0.00005)
    assert lines["Utilities"].pct_of_total == pytest.approx(0.0405, abs=0.00005)
    assert lines["(no sector)"].pct_of_total == pytest.approx(0.4547, abs=0.00005)


def test_sector_shares_of_total_and_cash_sum_to_one():
    """Every sector line plus the asset-class view's cash line is the whole."""
    sectors = allocation_by_sector(HOLDINGS, PRICES, CASH)
    cash = _by_label(allocation_by_asset_class(HOLDINGS, PRICES, CASH))["Cash"]
    total = sum(l.pct_of_total for l in sectors.lines) + cash.pct_of_total
    assert total == pytest.approx(1.0, abs=1e-9)


def test_unsectored_is_reported_not_dropped():
    """
    D3. 47% of this portfolio has no sector. Dropping it silently would roughly
    double every sector figure, which is why the line exists and why it has no
    '% sectored' of its own.
    """
    lines = _by_label(allocation_by_sector(HOLDINGS, PRICES, CASH))
    assert "(no sector)" in lines
    assert lines["(no sector)"].pct_of_denominator is None
    assert set(lines["(no sector)"].tickers) == {"SPY", "TLT", "GLD", "VNQ"}


def test_sectored_percentages_sum_to_one():
    a = allocation_by_sector(HOLDINGS, PRICES, CASH)
    sectored = [l for l in a.lines if l.pct_of_denominator is not None]
    assert sum(l.pct_of_denominator for l in sectored) == pytest.approx(1.0, abs=1e-9)


# --- Part 7: position (IPS-4.1 column) --------------------------------------

# Part 7, IPS-4.1, every holding, % of total - in the table's order, which is
# market value descending.
IPS_4_1 = [
    ("SPY", 0.1865), ("AAPL", 0.1584), ("MSFT", 0.1211), ("JNJ", 0.1006),
    ("TLT", 0.0999), ("GLD", 0.0982), ("JPM", 0.0868), ("VNQ", 0.0700),
    ("NEE", 0.0405),
]


def test_position_denominators():
    """The same three denominators as the other views; no sectored value."""
    a = allocation_by_position(HOLDINGS, PRICES, CASH)
    assert a.invested_value == pytest.approx(394700.50, abs=0.01)
    assert a.cash_balance == pytest.approx(15500.00, abs=0.01)
    assert a.total_value == pytest.approx(410200.50, abs=0.01)
    assert a.sectored_value is None


def test_position_lines_are_the_ips_4_1_column_largest_first():
    """Part 7, IPS-4.1: one line per holding, share of total, largest first,
    so "what is my biggest position" is the first line and no reader sorts."""
    a = allocation_by_position(HOLDINGS, PRICES, CASH)
    assert [l.label for l in a.lines] == [t for t, _ in IPS_4_1]
    for line, (ticker, share) in zip(a.lines, IPS_4_1):
        assert line.pct_of_total == pytest.approx(share, abs=0.00005), ticker
        assert line.pct_of_denominator == line.pct_of_total
        assert line.tickers == [ticker]


def test_position_market_value_and_cost_basis():
    """Part 1, SPY and NEE rows."""
    lines = _by_label(allocation_by_position(HOLDINGS, PRICES, CASH))
    assert lines["SPY"].market_value == pytest.approx(76516.00, abs=0.01)
    assert lines["SPY"].cost_basis == pytest.approx(50000.00, abs=0.01)
    assert lines["NEE"].market_value == pytest.approx(16620.00, abs=0.01)
    assert lines["NEE"].cost_basis == pytest.approx(15000.00, abs=0.01)


def test_position_percent_of_invested():
    """Part 5, 1.4: AAPL 16.47% and MSFT 12.59% of invested."""
    lines = _by_label(allocation_by_position(HOLDINGS, PRICES, CASH))
    assert lines["AAPL"].pct_of_invested == pytest.approx(0.1647, abs=0.00005)
    assert lines["MSFT"].pct_of_invested == pytest.approx(0.1259, abs=0.00005)


def test_position_view_has_no_cash_line():
    """Cash is not a holding (IPS-4.1 is about instruments); it is in the
    denominator and in the header, not a line."""
    a = allocation_by_position(HOLDINGS, PRICES, CASH)
    assert "Cash" not in {l.label for l in a.lines}
    assert len(a.lines) == 9


def test_position_shares_of_total_and_cash_sum_to_one():
    positions = allocation_by_position(HOLDINGS, PRICES, CASH)
    cash = _by_label(allocation_by_asset_class(HOLDINGS, PRICES, CASH))["Cash"]
    total = sum(l.pct_of_total for l in positions.lines) + cash.pct_of_total
    assert total == pytest.approx(1.0, abs=1e-9)


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


def test_position_missing_price_raises():
    partial = {k: v for k, v in PRICES.items() if k != "GLD"}
    with pytest.raises(AllocationError, match="GLD"):
        allocation_by_position(HOLDINGS, partial, CASH)
