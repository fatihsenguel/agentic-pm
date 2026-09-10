"""
PortfolioManager.get_holdings reads the ledger, not the holdings table (D13).

The falsifier is a portfolio that exists only as ledger rows: expected_values.md
Part 8 B's KO position, two buys and a partial sale, written straight into
`transactions` with no holdings row. A reader of the holdings table returns
nothing for it; a reader of the ledger returns 250 @ 80.01 bought 2024-09-09.

Runs against the copy conftest.py makes of data/portfolio.db, like
test_instrument_type.py; creates its own portfolio and the KO asset and
removes both afterwards. No prices are fetched: get_holdings is unpriced.
"""

import datetime

import pytest

from portfolio_tool.database_setup import (
    Asset,
    Portfolio,
    Transaction,
    get_session,
)
from portfolio_tool.portfolio_manager import PortfolioManager


BENCHMARK_PORTFOLIO = "Benchmark Portfolio"
CENT = 0.005

# expected_values.md Part 8 B: date, type, quantity, price, fees, amount.
PART_8_B = [
    ("2024-09-09", "buy",  200, 75.00, 0.00, 15_000.00),
    ("2025-02-03", "buy",  100, 90.00, 3.00,  9_003.00),
    ("2025-11-17", "sell",  50, 85.00, 2.00,  4_248.00),
]

# expected_values.md Part 1: quantity, average price, purchase date.
PART_1 = {
    "SPY":  (100, 500.00, "2024-01-15"),
    "AAPL": (200, 200.00, "2024-02-20"),
    "MSFT": (100, 400.00, "2024-03-18"),
    "JNJ":  (150, 150.00, "2024-05-06"),
    "JPM":  (100, 200.00, "2024-07-15"),
    "NEE":  (200,  75.00, "2024-09-09"),
    "TLT":  (500,  90.00, "2025-01-13"),
    "GLD":  (100, 250.00, "2025-03-10"),
    "VNQ":  (300,  90.00, "2025-06-02"),
}

# What build_holdings_summary reads from a holding row.
SUMMARY_KEYS = {"ticker", "quantity", "average_price", "asset_class", "sector",
                "instrument_type", "purchase_date"}


def _stamp(iso):
    return datetime.date.fromisoformat(iso)


@pytest.fixture(scope="module")
def ko_portfolio():
    """A portfolio holding KO as Part 8 B's three ledger rows and nothing else."""
    pm = PortfolioManager()
    portfolio_id = pm.create_portfolio("Ledger Reader Test", currency="USD")
    session = get_session()
    try:
        asset = Asset(ticker="KO", name="The Coca-Cola Company", asset_class="Equity",
                      sector="Consumer Staples", instrument_type="share", currency="USD")
        session.add(asset)
        session.flush()
        for date, kind, qty, price, fees, amount in PART_8_B:
            session.add(Transaction(
                portfolio_id=portfolio_id, asset_id=asset.id, date=_stamp(date),
                type=kind, quantity=qty, price_per_unit=price, fees=fees, amount=amount,
            ))
        session.commit()
        asset_id = asset.id
    finally:
        session.close()

    yield portfolio_id

    session = get_session()
    try:
        session.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).delete()
        session.query(Asset).filter(Asset.id == asset_id).delete()
        session.commit()
    finally:
        session.close()
    pm.delete_portfolio(portfolio_id)


@pytest.fixture(scope="module")
def ko_holding(ko_portfolio):
    holdings = PortfolioManager().get_holdings(ko_portfolio)
    assert len(holdings) == 1, f"expected KO alone from the ledger, got {holdings}"
    return holdings[0]


def test_ledger_only_portfolio_has_its_holding(ko_holding):
    assert ko_holding["ticker"] == "KO"


def test_position_after_tranches_and_sale(ko_holding):
    """Part 8 B: 250 @ 80.01, purchase date the first buy (D13)."""
    assert ko_holding["quantity"] == 250
    assert ko_holding["average_price"] == pytest.approx(80.01, abs=CENT)
    assert ko_holding["purchase_date"] == datetime.date(2024, 9, 9)


def test_asset_metadata_is_joined(ko_holding):
    assert ko_holding["asset_class"] == "Equity"
    assert ko_holding["sector"] == "Consumer Staples"
    assert ko_holding["instrument_type"] == "share"


def test_row_carries_what_the_summary_reads(ko_holding):
    assert SUMMARY_KEYS <= set(ko_holding)
    assert isinstance(ko_holding["purchase_date"], datetime.date)


def test_portfolio_tickers_come_from_the_ledger(ko_portfolio, ko_holding):
    """The router's portfolio context reads get_portfolio_tickers; it must be
    the tickers of get_holdings and nothing else, so one reader, not two."""
    assert PortfolioManager().get_portfolio_tickers(ko_portfolio) == ["KO"]


def test_delete_portfolio_removes_its_ledger():
    """A portfolio's rows go with it. SQLite does not enforce the cascade,
    and a reused portfolio id would inherit orphaned rows as holdings -
    seen in test_strict_nodes.py the day the reader changed."""
    pm = PortfolioManager()
    portfolio_id = pm.create_portfolio("Ledger Delete Test", currency="USD")
    pm.record_transaction(portfolio_id, "SPY", datetime.date(2024, 1, 15), "buy",
                          100, 450.0, 0.0, 45_000.0)
    assert pm.get_portfolio_tickers(portfolio_id) == ["SPY"]
    pm.delete_portfolio(portfolio_id)
    session = get_session()
    try:
        left = session.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).count()
    finally:
        session.close()
    assert left == 0


def test_empty_ledger_is_no_holdings():
    """A portfolio with no rows has no holdings; the node is what refuses it."""
    pm = PortfolioManager()
    portfolio_id = pm.create_portfolio("Empty Ledger Test", currency="USD")
    try:
        assert pm.get_holdings(portfolio_id) == []
    finally:
        pm.delete_portfolio(portfolio_id)


@pytest.mark.parametrize("ticker", list(PART_1))
def test_benchmark_portfolio_reproduces_part_1(ticker):
    """Part 8 A through the reader: the seeded ledger gives Part 1 (the
    invariant Part 8 pins). Passes on either reader, since the seed writes
    both tables the same; the KO tests above are the falsifier."""
    session = get_session()
    try:
        portfolio_id = (session.query(Portfolio.id)
                        .filter(Portfolio.name == BENCHMARK_PORTFOLIO).scalar())
    finally:
        session.close()
    by_ticker = {h["ticker"]: h for h in PortfolioManager().get_holdings(portfolio_id)}
    quantity, average, purchased = PART_1[ticker]
    h = by_ticker[ticker]
    assert h["quantity"] == quantity
    assert h["average_price"] == pytest.approx(average, abs=CENT)
    assert h["purchase_date"] == datetime.date.fromisoformat(purchased)
