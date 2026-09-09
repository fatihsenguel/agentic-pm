"""
Asset.instrument_type over the seeded database.

Runs against the copy conftest.py makes of data/portfolio.db, so it passes
only once migration 05034c6316c8 has been applied and seed_portfolio.py has
been run. Before that it fails with "no such column" - and so does everything
else that joins Asset, which is why the migration is applied straight after
the commit that adds the column to the model.

The split is expected_values.md Part 7's: the four funds are exempt from
IPS-4.2, the five shares are checked. Copied here as literals, not read from
the seed, so the seed cannot drift from the reference without this noticing.
"""

import pytest

from portfolio_tool.database_setup import Asset, Portfolio, Transaction, get_session
from portfolio_tool.portfolio_manager import PortfolioManager


BENCHMARK_PORTFOLIO = "Benchmark Portfolio"
FUNDS = {"SPY", "TLT", "GLD", "VNQ"}
SHARES = {"AAPL", "MSFT", "JNJ", "JPM", "NEE"}


@pytest.fixture(scope="module")
def types_by_ticker():
    """Through get_holdings, the one reader of what a portfolio holds (D13)."""
    session = get_session()
    try:
        portfolio_id = (
            session.query(Portfolio.id)
            .filter(Portfolio.name == BENCHMARK_PORTFOLIO)
            .scalar()
        )
    finally:
        session.close()
    return {h["ticker"]: h["instrument_type"]
            for h in PortfolioManager().get_holdings(portfolio_id)}


def test_every_benchmark_holding_has_an_instrument_type(types_by_ticker):
    assert set(types_by_ticker) == FUNDS | SHARES
    missing = sorted(t for t, kind in types_by_ticker.items() if kind is None)
    assert missing == [], f"instrument_type is NULL for {missing}; reseed portfolio 3"


def test_funds_and_shares_are_part_7s_split(types_by_ticker):
    assert {t for t, k in types_by_ticker.items() if k == "fund"} == FUNDS
    assert {t for t, k in types_by_ticker.items() if k == "share"} == SHARES


def test_no_holding_anywhere_has_a_type_outside_the_vocabulary():
    """Shared Asset rows: an asset held by any portfolio - any asset with a
    ledger row - carries a type the checker accepts. Anything else on a held
    asset is a value the checker would raise on."""
    session = get_session()
    try:
        rows = (
            session.query(Asset.ticker, Asset.instrument_type)
            .join(Transaction, Transaction.asset_id == Asset.id)
            .distinct()
            .all()
        )
    finally:
        session.close()
    bad = sorted(f"{t}={k!r}" for t, k in rows if k not in ("share", "fund"))
    assert bad == [], bad
