"""
Position P&L checked against tests/golden/expected_values.md Part 1.

Every expected number here is copied from that document, which was computed by
hand in expected_values.xlsx. If a test fails, one of the two is wrong and that
gets resolved deliberately. Do NOT update these figures to match code output.

Same fixture as test_allocation.py: portfolio 3 as seeded, priced at the
2026-09-02 closes. No database is touched. Price return only, per D4.
"""

import pytest

from portfolio_tool.quant.allocation import AllocationError, position_pnl


HOLDINGS = [
    {"ticker": "SPY",  "quantity": 100, "average_price": 500.0, "purchase_date": "2024-01-15"},
    {"ticker": "AAPL", "quantity": 200, "average_price": 200.0, "purchase_date": "2024-02-20"},
    {"ticker": "MSFT", "quantity": 100, "average_price": 400.0, "purchase_date": "2024-03-18"},
    {"ticker": "JNJ",  "quantity": 150, "average_price": 150.0, "purchase_date": "2024-05-06"},
    {"ticker": "JPM",  "quantity": 100, "average_price": 200.0, "purchase_date": "2024-07-15"},
    {"ticker": "NEE",  "quantity": 200, "average_price":  75.0, "purchase_date": "2024-09-09"},
    {"ticker": "TLT",  "quantity": 500, "average_price":  90.0, "purchase_date": "2025-01-13"},
    {"ticker": "GLD",  "quantity": 100, "average_price": 250.0, "purchase_date": "2025-03-10"},
    {"ticker": "VNQ",  "quantity": 300, "average_price":  90.0, "purchase_date": "2025-06-02"},
]

PRICES = {
    "SPY": 765.16, "AAPL": 324.96, "MSFT": 496.82, "JNJ": 275.21, "JPM": 356.22,
    "NEE": 83.10, "TLT": 81.95, "GLD": 402.78, "VNQ": 95.78,
}

# expected_values.md Part 1: cost basis, market value, P&L abs, P&L %.
PART_1 = {
    "SPY":  (50000.00, 76516.00,  26516.00,  0.5303),
    "AAPL": (40000.00, 64992.00,  24992.00,  0.6248),
    "MSFT": (40000.00, 49682.00,   9682.00,  0.2421),
    "JNJ":  (22500.00, 41281.50,  18781.50,  0.8347),
    "JPM":  (20000.00, 35622.00,  15622.00,  0.7811),
    "NEE":  (15000.00, 16620.00,   1620.00,  0.1080),
    "TLT":  (45000.00, 40975.00,  -4025.00, -0.0894),
    "GLD":  (25000.00, 40278.00,  15278.00,  0.6111),
    "VNQ":  (27000.00, 28734.00,   1734.00,  0.0642),
}


@pytest.mark.parametrize("ticker", list(PART_1))
def test_part_1_row(ticker):
    cost, value, pnl_abs, pnl_pct = PART_1[ticker]
    p = position_pnl(HOLDINGS, PRICES)[ticker]
    assert p.cost_basis == pytest.approx(cost, abs=0.005)
    assert p.market_value == pytest.approx(value, abs=0.005)
    assert p.pnl_abs == pytest.approx(pnl_abs, abs=0.005)
    # Part 1 quotes percentages to two decimals, so the honest tolerance is
    # half a unit in the last place. MSFT sits exactly on that boundary
    # (9,682 / 40,000 = 0.24205), hence the extra 1e-6.
    assert p.pnl_pct == pytest.approx(pnl_pct, abs=0.000051)


def test_part_1_total():
    """Total invested 284,500.00 -> 394,700.50, +110,200.50, +38.73%."""
    pnl = position_pnl(HOLDINGS, PRICES).values()
    cost = sum(p.cost_basis for p in pnl)
    value = sum(p.market_value for p in pnl)
    assert cost == pytest.approx(284500.00, abs=0.005)
    assert value == pytest.approx(394700.50, abs=0.005)
    assert value - cost == pytest.approx(110200.50, abs=0.005)
    assert (value - cost) / cost == pytest.approx(0.3873, abs=0.00005)


def test_jpm_carries_the_purchase_date():
    """Benchmark 1.2 passes only when the purchase date is named."""
    p = position_pnl(HOLDINGS, PRICES)["JPM"]
    assert p.purchase_date == "2024-07-15"
    assert p.quantity == 100
    assert p.average_price == 200.0
    assert p.price == 356.22


def test_every_position_is_computed():
    assert set(position_pnl(HOLDINGS, PRICES)) == set(PART_1)


def test_missing_price_raises():
    partial = {k: v for k, v in PRICES.items() if k != "JPM"}
    with pytest.raises(AllocationError):
        position_pnl(HOLDINGS, partial)


def test_zero_cost_basis_raises():
    free = [{"ticker": "SPY", "quantity": 100, "average_price": 0.0}]
    with pytest.raises(AllocationError):
        position_pnl(free, PRICES)
