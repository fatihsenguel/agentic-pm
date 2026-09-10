"""
The seeded ledger of portfolio 3 is expected_values.md Part 8 A.

Runs against the copy conftest.py makes of data/portfolio.db, like
test_instrument_type.py, so it passes only once migration 65c3de3ff3fd has
been applied and seed_portfolio.py has been run. Before the migration it
fails on the missing portfolio column; after it and before the reseed, on
zero rows.

Part 8 A is copied here as literals, not read from the seed, so the seed
cannot drift from the reference without this noticing. Nine buys, one per
position, no fees, amount = quantity x price (D11, D14), on Part 1's dates.
"""

import datetime

import pytest

from portfolio_tool.database_setup import Asset, Portfolio, Transaction, get_session


BENCHMARK_PORTFOLIO = "Benchmark Portfolio"

# date, type, ticker, quantity, price, fees, amount
PART_8_A = [
    ("2024-01-15", "buy", "SPY",  100, 500.00, 0.00, 50_000.00),
    ("2024-02-20", "buy", "AAPL", 200, 200.00, 0.00, 40_000.00),
    ("2024-03-18", "buy", "MSFT", 100, 400.00, 0.00, 40_000.00),
    ("2024-05-06", "buy", "JNJ",  150, 150.00, 0.00, 22_500.00),
    ("2024-07-15", "buy", "JPM",  100, 200.00, 0.00, 20_000.00),
    ("2024-09-09", "buy", "NEE",  200,  75.00, 0.00, 15_000.00),
    ("2025-01-13", "buy", "TLT",  500,  90.00, 0.00, 45_000.00),
    ("2025-03-10", "buy", "GLD",  100, 250.00, 0.00, 25_000.00),
    ("2025-06-02", "buy", "VNQ",  300,  90.00, 0.00, 27_000.00),
]
TOTAL = 284_500.00
CENT = 0.005


@pytest.fixture(scope="module")
def rows():
    session = get_session()
    try:
        portfolio = (
            session.query(Portfolio)
            .filter(Portfolio.name == BENCHMARK_PORTFOLIO)
            .one()
        )
        found = (
            session.query(Transaction, Asset.ticker)
            .join(Asset, Transaction.asset_id == Asset.id)
            .filter(Transaction.portfolio_id == portfolio.id)
            .order_by(Transaction.date)
            .all()
        )
        return [
            (
                t.date.isoformat(),
                t.type,
                ticker,
                t.quantity,
                t.price_per_unit,
                t.fees,
                t.amount,
            )
            for t, ticker in found
        ]
    finally:
        session.close()


def test_nine_rows(rows):
    assert len(rows) == 9


@pytest.mark.parametrize("expected", PART_8_A, ids=[r[2] for r in PART_8_A])
def test_row_is_part_8_a(rows, expected):
    date, kind, ticker, quantity, price, fees, amount = expected
    matching = [r for r in rows if r[2] == ticker]
    assert len(matching) == 1, f"{ticker}: {len(matching)} rows, not one buy"
    got = matching[0]
    assert got[0] == date
    assert got[1] == kind
    assert got[3] == quantity
    assert got[4] == pytest.approx(price, abs=CENT)
    assert got[5] == pytest.approx(fees, abs=CENT)
    assert got[6] == pytest.approx(amount, abs=CENT)


def test_amounts_sum_to_part_1_total(rows):
    assert sum(r[6] for r in rows) == pytest.approx(TOTAL, abs=CENT)
