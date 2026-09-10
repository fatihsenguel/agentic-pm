"""
DataManager.update_prices_for_asset writes the source of every close
(expected_values.md D17, D19, Part 9), the way update_fx_rates does.

Runs against the copy conftest.py makes of data/portfolio.db, so it passes
only once migration 2ee0c9249a9f has been applied. The provider is a stub
that returns dated synthetic closes and records its calls; no network, and
no figure here is a market price. The asset is a throwaway created for the
test and removed after it, with its rows and its fetch record.

  - a first fetch stores one daily_prices row per provider row, with the
    provider's name as source, and the result names the provider by its
    name rather than by a literal
  - a second call within price_fetch_interval_days makes no provider call

The cache rules beyond that are the rate fetch's, tested in
test_fx_fetch.py; this file asserts the one thing the price fetch lacked.
"""

import datetime
from decimal import Decimal

import pytest

from portfolio_tool.data_manager import DataManager
from portfolio_tool.database_setup import Asset, AssetFetchMetadata, DailyPrice, get_session


TICKER = "ZZPRICETEST"

# Synthetic closes on four weekdays. Not market prices.
CLOSES = {
    datetime.date(2026, 9, 1): Decimal("100.10"),
    datetime.date(2026, 9, 2): Decimal("100.20"),
    datetime.date(2026, 9, 3): Decimal("100.30"),
    datetime.date(2026, 9, 4): Decimal("100.40"),
}
FIRST = min(CLOSES)


@pytest.fixture
def provider_rows():
    from portfolio_tool.provider_models import ProviderPriceData
    return [ProviderPriceData(date=d, open=c, high=c, low=c, close=c, volume=1)
            for d, c in sorted(CLOSES.items())]


class StubProvider:
    """Answers get_daily_prices from a fixed table and records every call."""

    name = "stub"

    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def get_daily_prices(self, ticker, start, end):
        self.calls.append((ticker, start, end))
        return [r for r in self.rows if start <= r.date <= end]


def _clear(session):
    asset = session.query(Asset).filter_by(ticker=TICKER).first()
    if asset is not None:
        session.query(DailyPrice).filter(DailyPrice.asset_id == asset.id).delete()
        session.query(AssetFetchMetadata).filter(AssetFetchMetadata.asset_id == asset.id).delete()
        session.delete(asset)
    session.commit()


@pytest.fixture
def dm(provider_rows):
    session = get_session()
    _clear(session)
    asset = Asset(ticker=TICKER, name="Price fetch test", asset_class="Equity",
                  currency="USD", instrument_type="share")
    session.add(asset)
    session.commit()
    manager = DataManager(session=session, provider=StubProvider(provider_rows))
    manager.asset = asset
    yield manager
    _clear(session)
    session.close()


def _stored(session, asset):
    rows = (session.query(DailyPrice)
            .filter(DailyPrice.asset_id == asset.id)
            .order_by(DailyPrice.date).all())
    return {r.date: r for r in rows}


def test_first_fetch_stores_the_rows_with_their_source(dm):
    result = dm.update_prices_for_asset(dm.asset, start_date=FIRST)
    assert result.success, result.error_message
    assert result.affected_count == len(CLOSES)
    assert result.metadata.get("provider") == "stub"

    stored = _stored(dm.session, dm.asset)
    assert set(stored) == set(CLOSES)
    for d, row in stored.items():
        assert row.close == pytest.approx(float(CLOSES[d]), abs=1e-9)
        assert row.source == "stub"
    assert dm.provider.calls == [(TICKER, FIRST, datetime.date.today())]


def test_second_call_within_the_interval_makes_no_provider_call(dm):
    dm.update_prices_for_asset(dm.asset, start_date=FIRST)
    calls_before = len(dm.provider.calls)
    result = dm.update_prices_for_asset(dm.asset, start_date=FIRST)
    assert result.success
    assert result.affected_count == 0
    assert result.metadata.get("status") == "cached"
    assert len(dm.provider.calls) == calls_before
