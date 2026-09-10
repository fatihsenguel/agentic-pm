"""
DataManager.update_fx_rates: the rate fetch beside the price fetch, under
the price fetch's cache rules (D17: a spot rate is a price source).

Runs against the copy conftest.py makes of data/portfolio.db, so it passes
only once migrations 0f3f60d44ce0 and ee845dad889a have been applied. The
provider is a stub that records its calls and returns dated synthetic rates;
no network, and no rate here is a market rate.

The rules, each a test:

  - a first fetch stores one fx_rates row per provider row, as given, with
    the provider's name as source, and records how far back it asked
  - a second call within price_fetch_interval_days makes no provider call
  - a call asking further back than ever asked fetches again and extends
    the record; coverage is "have we asked this far back", never "is there
    a row on that date" (the price cache's Labor Day lesson)
  - covered but stale fetches only from the newest stored date forward
  - base equal to quote makes no call and stores nothing (D17: no lookup,
    so no fetch)
  - a provider with nothing for the pair stores nothing and says so, the
    way the price fetch does; the raise on a missing rate is the lookup's
  - fetching the same window twice leaves one row per day, not two

Nothing here asserts a rate against the reference: the lookup Part 8 C pins
is quant/fx.py's (tests/test_fx.py).
"""

import datetime
from decimal import Decimal

import pytest

from portfolio_tool.data_manager import DataManager
from portfolio_tool.database_setup import FxFetchMetadata, FxRate, get_session


BASE, QUOTE = "EUR", "USD"

# Synthetic euros per dollar on four weekdays. Not market rates.
RATES = {
    datetime.date(2026, 9, 1): Decimal("0.9100"),
    datetime.date(2026, 9, 2): Decimal("0.9150"),
    datetime.date(2026, 9, 3): Decimal("0.9200"),
    datetime.date(2026, 9, 4): Decimal("0.9250"),
}
FIRST, LAST = min(RATES), max(RATES)


@pytest.fixture
def provider_rows():
    """The DTO the provider returns, imported per test so a missing class
    fails each test for its own reason and not the collection."""
    from portfolio_tool.provider_models import ProviderFxRate
    return [ProviderFxRate(date=d, rate=r) for d, r in sorted(RATES.items())]


class StubProvider:
    """Answers get_fx_rates from a fixed table and records every call."""

    name = "stub"

    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def get_fx_rates(self, base, quote, start, end):
        self.calls.append((base, quote, start, end))
        return [r for r in self.rows if start <= r.date <= end]


def _clear(session):
    session.query(FxRate).filter(FxRate.base == BASE, FxRate.quote == QUOTE).delete()
    session.query(FxFetchMetadata).filter(
        FxFetchMetadata.base == BASE, FxFetchMetadata.quote == QUOTE).delete()
    session.commit()


@pytest.fixture
def dm(provider_rows):
    session = get_session()
    _clear(session)
    manager = DataManager(session=session, provider=StubProvider(provider_rows))
    yield manager
    _clear(session)
    session.close()


def _stored(session):
    rows = (session.query(FxRate)
            .filter(FxRate.base == BASE, FxRate.quote == QUOTE)
            .order_by(FxRate.date).all())
    return {r.date: r for r in rows}


def _record(session):
    return session.get(FxFetchMetadata, (BASE, QUOTE))


def test_first_fetch_stores_the_rows_as_given_with_their_source(dm):
    result = dm.update_fx_rates(BASE, QUOTE, start_date=FIRST)
    assert result.success, result.error_message
    assert result.affected_count == len(RATES)

    stored = _stored(dm.session)
    assert set(stored) == set(RATES)
    for d, row in stored.items():
        assert row.rate == pytest.approx(float(RATES[d]), abs=1e-9)
        assert row.source == "stub"
        assert (row.base, row.quote) == (BASE, QUOTE)

    record = _record(dm.session)
    assert record.earliest_start == FIRST
    assert record.last_fetch_time is not None
    assert dm.provider.calls == [(BASE, QUOTE, FIRST, datetime.date.today())]


def test_second_call_within_the_interval_makes_no_provider_call(dm):
    dm.update_fx_rates(BASE, QUOTE, start_date=FIRST)
    calls_before = len(dm.provider.calls)
    result = dm.update_fx_rates(BASE, QUOTE, start_date=FIRST)
    assert result.success
    assert result.affected_count == 0
    assert result.metadata.get("status") == "cached"
    assert len(dm.provider.calls) == calls_before


def test_asking_further_back_fetches_again_and_extends_the_record(dm):
    dm.update_fx_rates(BASE, QUOTE, start_date=FIRST)
    earlier = FIRST - datetime.timedelta(days=31)
    result = dm.update_fx_rates(BASE, QUOTE, start_date=earlier)
    assert result.success
    assert dm.provider.calls[-1][2] == earlier
    assert _record(dm.session).earliest_start == earlier


def test_coverage_is_what_was_asked_not_what_was_stored(dm):
    """A start on a weekend has no row and never will; the record says the
    provider was asked from there, so the pair does not refetch on every
    call. 2026-08-29 is a Saturday."""
    saturday = datetime.date(2026, 8, 29)
    assert saturday.weekday() == 5
    dm.update_fx_rates(BASE, QUOTE, start_date=saturday)
    assert saturday not in _stored(dm.session)
    calls_before = len(dm.provider.calls)
    result = dm.update_fx_rates(BASE, QUOTE, start_date=saturday)
    assert result.metadata.get("status") == "cached"
    assert len(dm.provider.calls) == calls_before


def test_covered_but_stale_fetches_from_the_newest_stored_date(dm):
    dm.update_fx_rates(BASE, QUOTE, start_date=FIRST)
    record = _record(dm.session)
    record.last_fetch_time = datetime.datetime.utcnow() - datetime.timedelta(days=3)
    dm.session.commit()

    result = dm.update_fx_rates(BASE, QUOTE, start_date=FIRST)
    assert result.success
    assert dm.provider.calls[-1][2] == LAST


def test_same_currency_makes_no_call_and_stores_nothing(dm):
    result = dm.update_fx_rates(BASE, BASE, start_date=FIRST)
    assert result.success
    assert result.affected_count == 0
    assert result.metadata.get("status") == "same_currency"
    assert dm.provider.calls == []
    assert dm.session.query(FxRate).filter(FxRate.base == BASE, FxRate.quote == BASE).count() == 0


def test_provider_with_nothing_for_the_pair_stores_nothing_and_says_so(dm):
    dm.provider.rows = []
    result = dm.update_fx_rates(BASE, QUOTE, start_date=FIRST)
    assert result.success
    assert result.affected_count == 0
    assert result.metadata.get("status") == "no_new_data_from_provider"
    assert _stored(dm.session) == {}


def test_fetching_twice_leaves_one_row_per_day(dm):
    dm.update_fx_rates(BASE, QUOTE, start_date=FIRST)
    dm.update_fx_rates(BASE, QUOTE, start_date=FIRST, force_update=True)
    assert len(dm.provider.calls) == 2
    assert len(_stored(dm.session)) == len(RATES)
