"""
The transaction ledger checked against tests/golden/expected_values.md Part 8.

Every expected number here is copied from that document, which was computed by
hand before the ledger existed (decisions D10 to D14). If a test fails, one of
the two is wrong and that gets resolved deliberately. Do NOT update these
figures to match code output.

Pure, like test_allocation.py: rows in, holdings out, no database. A row is a
dict with Part 8's columns - portfolio_id, date, type, ticker, quantity, price,
fees, amount - and a derived holding carries what a holding row carries today
(ticker, quantity, average_price, purchase_date) plus its cost basis and the
realized gain D12 defines.

What this file cannot see: in Part 8 A and B the `amount` column equals
quantity x price +/- fees by construction, so whether the derivation sums
`amount` or recomputes the arithmetic passes here either way. The FX column
of Order 2 item 2 is that decision's falsifier, not this file.
"""

from dataclasses import asdict

import pytest

from portfolio_tool.quant.allocation import position_pnl


@pytest.fixture
def ledger():
    """The module under test, imported per test rather than at collection.

    An import at module level would be a collection error, and pytest stops
    the whole run on one: 405 tests would go unrun until the module exists.
    Importing here makes each of these tests fail on its own for the honest
    reason while the rest of the suite still runs.
    """
    from portfolio_tool.quant import ledger as module
    return module


PORTFOLIO = 3


def _row(date, type_, ticker, quantity, price, fees, amount, portfolio_id=PORTFOLIO):
    return {
        "portfolio_id": portfolio_id,
        "date": date,
        "type": type_,
        "ticker": ticker,
        "quantity": quantity,
        "price": price,
        "fees": fees,
        "amount": amount,
    }


# expected_values.md Part 8 A: portfolio 3 as a ledger, one buy per position,
# no fees, the dates and prices of Part 1.
PART_8_A = [
    _row("2024-01-15", "buy", "SPY",  100, 500.00, 0.00, 50_000.00),
    _row("2024-02-20", "buy", "AAPL", 200, 200.00, 0.00, 40_000.00),
    _row("2024-03-18", "buy", "MSFT", 100, 400.00, 0.00, 40_000.00),
    _row("2024-05-06", "buy", "JNJ",  150, 150.00, 0.00, 22_500.00),
    _row("2024-07-15", "buy", "JPM",  100, 200.00, 0.00, 20_000.00),
    _row("2024-09-09", "buy", "NEE",  200,  75.00, 0.00, 15_000.00),
    _row("2025-01-13", "buy", "TLT",  500,  90.00, 0.00, 45_000.00),
    _row("2025-03-10", "buy", "GLD",  100, 250.00, 0.00, 25_000.00),
    _row("2025-06-02", "buy", "VNQ",  300,  90.00, 0.00, 27_000.00),
]

# expected_values.md Part 1: quantity, average price, cost basis, purchase date.
PART_1 = {
    "SPY":  (100, 500.00, 50_000.00, "2024-01-15"),
    "AAPL": (200, 200.00, 40_000.00, "2024-02-20"),
    "MSFT": (100, 400.00, 40_000.00, "2024-03-18"),
    "JNJ":  (150, 150.00, 22_500.00, "2024-05-06"),
    "JPM":  (100, 200.00, 20_000.00, "2024-07-15"),
    "NEE":  (200,  75.00, 15_000.00, "2024-09-09"),
    "TLT":  (500,  90.00, 45_000.00, "2025-01-13"),
    "GLD":  (100, 250.00, 25_000.00, "2025-03-10"),
    "VNQ":  (300,  90.00, 27_000.00, "2025-06-02"),
}
PART_1_TOTAL_INVESTED = 284_500.00

# expected_values.md Part 1, the 2026-09-02 closes and the P&L columns.
PRICES_09_02 = {
    "SPY": 765.16, "AAPL": 324.96, "MSFT": 496.82, "JNJ": 275.21, "JPM": 356.22,
    "NEE": 83.10, "TLT": 81.95, "GLD": 402.78, "VNQ": 95.78,
}
PART_1_PNL = {
    "SPY":  (76_516.00,  26_516.00,  0.5303),
    "AAPL": (64_992.00,  24_992.00,  0.6248),
    "MSFT": (49_682.00,   9_682.00,  0.2421),
    "JNJ":  (41_281.50,  18_781.50,  0.8347),
    "JPM":  (35_622.00,  15_622.00,  0.7811),
    "NEE":  (16_620.00,   1_620.00,  0.1080),
    "TLT":  (40_975.00,  -4_025.00, -0.0894),
    "GLD":  (40_278.00,  15_278.00,  0.6111),
    "VNQ":  (28_734.00,   1_734.00,  0.0642),
}

# expected_values.md Part 8 B: one synthetic position built in two tranches
# and partly sold, fees chosen so every figure is exact to the cent.
PART_8_B = [
    _row("2024-09-09", "buy",  "KO", 200, 75.00, 0.00, 15_000.00),
    _row("2025-02-03", "buy",  "KO", 100, 90.00, 3.00,  9_003.00),
    _row("2025-11-17", "sell", "KO",  50, 85.00, 2.00,  4_248.00),
]

CENT = 0.005


# ---------------------------------------------------------------------------
# Part 8 A - the invariant: portfolio 3's ledger reproduces Part 1
# ---------------------------------------------------------------------------

def test_part_8_a_derives_nine_holdings(ledger):
    holdings = ledger.derive_holdings(PART_8_A)
    assert set(holdings) == set(PART_1)


@pytest.mark.parametrize("ticker", list(PART_1))
def test_part_8_a_row_matches_part_1(ledger, ticker):
    quantity, average, cost, purchased = PART_1[ticker]
    h = ledger.derive_holdings(PART_8_A)[ticker]
    assert h.ticker == ticker
    assert h.quantity == quantity
    assert h.average_price == pytest.approx(average, abs=CENT)
    assert h.cost_basis == pytest.approx(cost, abs=CENT)
    assert h.purchase_date == purchased


def test_part_8_a_total_cost_basis(ledger):
    total = sum(h.cost_basis for h in ledger.derive_holdings(PART_8_A).values())
    assert total == pytest.approx(PART_1_TOTAL_INVESTED, abs=CENT)


def test_part_8_a_single_buys_realize_nothing(ledger):
    for h in ledger.derive_holdings(PART_8_A).values():
        assert h.realized == 0.0


@pytest.mark.parametrize("ticker", list(PART_1_PNL))
def test_derived_holding_is_what_position_pnl_reads(ledger, ticker):
    """A derived holding feeds the existing P&L computation unchanged, and
    reproduces Part 1's P&L columns at the 09-02 closes. Pins the shape:
    the ledger's output is a holding as the rest of the code knows one."""
    holdings = [asdict(h) for h in ledger.derive_holdings(PART_8_A).values()]
    p = position_pnl(holdings, PRICES_09_02)[ticker]
    value, pnl_abs, pnl_pct = PART_1_PNL[ticker]
    assert p.market_value == pytest.approx(value, abs=CENT)
    assert p.pnl_abs == pytest.approx(pnl_abs, abs=CENT)
    # Part 1 quotes percentages to two decimals; half a unit in the last
    # place, plus the margin test_position_pnl.py needs for MSFT.
    assert p.pnl_pct == pytest.approx(pnl_pct, abs=0.000051)
    assert p.purchase_date == PART_1[ticker][3]


# ---------------------------------------------------------------------------
# Part 8 B - tranches and a partial sale, D10 to D13
# ---------------------------------------------------------------------------

def test_part_8_b_position_after_sale(ledger):
    h = ledger.derive_holdings(PART_8_B)["KO"]
    assert h.quantity == 250
    assert h.average_price == pytest.approx(80.01, abs=CENT)
    assert h.cost_basis == pytest.approx(20_002.50, abs=CENT)
    assert h.purchase_date == "2024-09-09"


def test_part_8_b_realized_gain(ledger):
    """D12: proceeds 4,248.00 minus the basis released, 50 x 80.01 = 4,000.50."""
    h = ledger.derive_holdings(PART_8_B)["KO"]
    assert h.realized == pytest.approx(247.50, abs=CENT)


def test_part_8_b_average_unchanged_by_sale(ledger):
    """D12: a sale moves quantity and basis, never the average price."""
    before = ledger.derive_holdings(PART_8_B[:2])["KO"]
    after = ledger.derive_holdings(PART_8_B)["KO"]
    assert before.quantity == 300
    assert before.cost_basis == pytest.approx(24_003.00, abs=CENT)
    assert after.average_price == pytest.approx(before.average_price, abs=1e-9)


def test_part_8_b_pnl_at_88(ledger):
    """Part 8 B at a price of 88.00: +1,997.50, +9.99%, price return per D4."""
    holdings = [asdict(h) for h in ledger.derive_holdings(PART_8_B).values()]
    p = position_pnl(holdings, {"KO": 88.00})["KO"]
    assert p.market_value == pytest.approx(22_000.00, abs=CENT)
    assert p.pnl_abs == pytest.approx(1_997.50, abs=CENT)
    assert p.pnl_pct == pytest.approx(0.099863, abs=0.0000005)


# ---------------------------------------------------------------------------
# Raise, do not repair
# ---------------------------------------------------------------------------

def test_sale_larger_than_position_raises(ledger):
    """300 are held after the two buys; 350 is more than the position. The
    first version of this test sold exactly 300, which closes the position
    and is not an error - see the next test."""
    rows = PART_8_B[:2] + [_row("2025-11-17", "sell", "KO", 350, 85.00, 2.00, 29_748.00)]
    with pytest.raises(ledger.LedgerError, match="KO"):
        ledger.derive_holdings(rows)


def test_sale_of_whole_position_closes_it(ledger):
    """A position sold down to nothing is not a holding: KO is absent, not
    present with quantity zero, which position_pnl would raise on."""
    rows = PART_8_B[:2] + [_row("2025-11-17", "sell", "KO", 300, 85.00, 2.00, 25_498.00)]
    assert "KO" not in ledger.derive_holdings(rows)


def test_sale_before_any_buy_raises(ledger):
    rows = [_row("2024-09-09", "sell", "KO", 50, 85.00, 2.00, 4_248.00)]
    with pytest.raises(ledger.LedgerError, match="KO"):
        ledger.derive_holdings(rows)


def test_rows_from_two_portfolios_raise(ledger):
    """D14: a row belongs to a portfolio, and a derivation is one portfolio's."""
    rows = PART_8_A + [_row("2024-09-09", "buy", "KO", 200, 75.00, 0.00, 15_000.00,
                            portfolio_id=1)]
    with pytest.raises(ledger.LedgerError, match="portfolio"):
        ledger.derive_holdings(rows)


def test_unknown_row_type_raises(ledger):
    rows = [_row("2024-09-09", "dividend", "KO", 200, 75.00, 0.00, 15_000.00)]
    with pytest.raises(ledger.LedgerError, match="dividend"):
        ledger.derive_holdings(rows)
