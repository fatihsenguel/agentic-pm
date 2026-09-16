"""
filings.update_ticker_ciks and filings.cik_for: the SEC ticker file under
its cache rule, and a ticker resolved through it.

Runs against the copy conftest.py makes of data/portfolio.db, so it passes
only once migration e289a03682f2 has been applied. The provider is a
stand-in that records its calls and answers from typed pairs, the CIKs
Parts 12 and 13 C record; no network.

The rules, each a test, the shape of test_filer_fetch.py:

  - a first fetch stores every pair as the file states it, with the pull
    time, and returns how many rows the table now holds
  - a second call within filings_fetch_interval_days makes no provider call
  - a stale table fetches again and is rewritten as the file now states it:
    a pair the file dropped is gone, a changed CIK is overwritten, every
    row's date moves, since the file is one document and the table is the
    file as of one pull
  - a provider that fails on the first fetch leaves no rows, and on a later
    one leaves the old rows and their dates, so the next call retries
  - a config without the interval raises before the provider is reached
  - cik_for resolves a ticker through the cache, asking the provider only
    when the table is stale, and raises naming a ticker the file does not
    list: never asked is not the same as EDGAR listing no filer, so the
    lookup fetches first; a ticker in another case is the same ticker

`pulled_at` is on the clock the other two records use, UTC, so the three
records a block is built from carry one clock (decision 29).
"""

import datetime as dt
from pathlib import Path

import pytest
import requests
import tomli

from portfolio_tool.database_setup import TickerCik, get_session
from portfolio_tool.provider_models import ProviderTicker


CONFIG = Path(__file__).parent.parent / "config.toml"
APPLE, ALPHABET, JPMORGAN = 320193, 1652044, 19617

PAIRS = [("AAPL", APPLE), ("GOOGL", ALPHABET), ("GOOG", ALPHABET), ("JPM", JPMORGAN)]


def _records(pairs=PAIRS):
    return [ProviderTicker(ticker=t, cik=c) for t, c in pairs]


class StandIn:
    """Answers tickers() from fixed records and records every call."""

    def __init__(self, records):
        self.records = records
        self.calls = 0

    def tickers(self):
        self.calls += 1
        return self.records


class Failing(StandIn):
    def tickers(self):
        self.calls += 1
        raise requests.HTTPError("503 from the stand-in")


@pytest.fixture(scope="module")
def filings():
    from portfolio_tool import filings
    return filings


def _clear(session):
    session.query(TickerCik).delete()
    session.commit()


@pytest.fixture
def session():
    s = get_session()
    try:
        _clear(s)
        yield s
        s.rollback()
        _clear(s)
    finally:
        s.rollback()
        s.close()


def _stored(session):
    return {row.ticker: row for row in session.query(TickerCik)}


def _age(session, days):
    for row in session.query(TickerCik):
        row.pulled_at = row.pulled_at - dt.timedelta(days=days)
    session.commit()


def _interval():
    return tomli.load(CONFIG.open("rb"))["data_fetch"]["filings_fetch_interval_days"]


# --- the cache rule --------------------------------------------------------------

def test_first_fetch_stores_every_pair_as_stated(filings, session):
    provider = StandIn(_records())
    before = dt.datetime.utcnow()
    stored = filings.update_ticker_ciks(session, provider)

    assert provider.calls == 1
    assert stored == len(PAIRS)
    rows = _stored(session)
    assert sorted((t, r.cik) for t, r in rows.items()) == sorted(PAIRS)
    for row in rows.values():
        assert before <= row.pulled_at <= dt.datetime.utcnow()


def test_a_second_call_within_the_interval_makes_no_provider_call(filings, session):
    provider = StandIn(_records())
    filings.update_ticker_ciks(session, provider)
    pulled = {t: r.pulled_at for t, r in _stored(session).items()}
    stored = filings.update_ticker_ciks(session, provider)
    assert provider.calls == 1
    assert stored == 0
    assert {t: r.pulled_at for t, r in _stored(session).items()} == pulled


def test_a_stale_table_is_rewritten_as_the_file_now_states_it(filings, session):
    provider = StandIn(_records())
    filings.update_ticker_ciks(session, provider)
    _age(session, _interval())
    aged = _stored(session)["AAPL"].pulled_at

    # GOOG dropped, JPM's number changed, a new ticker added.
    provider.records = _records([("AAPL", APPLE), ("GOOGL", ALPHABET), ("JPM", 1), ("NEW", 2)])
    stored = filings.update_ticker_ciks(session, provider)

    assert provider.calls == 2
    assert stored == 4
    rows = _stored(session)
    assert sorted((t, r.cik) for t, r in rows.items()) == \
        [("AAPL", APPLE), ("GOOGL", ALPHABET), ("JPM", 1), ("NEW", 2)]
    assert all(r.pulled_at > aged for r in rows.values())


def test_a_failed_first_fetch_leaves_no_rows(filings, session):
    provider = Failing(_records())
    with pytest.raises(requests.HTTPError):
        filings.update_ticker_ciks(session, provider)
    session.rollback()
    assert _stored(session) == {}


def test_a_failed_later_fetch_leaves_the_old_rows_and_their_dates(filings, session):
    filings.update_ticker_ciks(session, StandIn(_records()))
    _age(session, _interval())
    aged = {t: r.pulled_at for t, r in _stored(session).items()}

    provider = Failing(_records())
    with pytest.raises(requests.HTTPError):
        filings.update_ticker_ciks(session, provider)
    session.rollback()

    rows = _stored(session)
    assert provider.calls == 1
    assert sorted((t, r.cik) for t, r in rows.items()) == sorted(PAIRS)
    assert {t: r.pulled_at for t, r in rows.items()} == aged


def test_a_config_without_the_interval_raises_before_the_provider(filings, session, monkeypatch):
    monkeypatch.setattr(filings, "load_config", lambda: {"data_fetch": {}})
    provider = StandIn(_records())
    with pytest.raises(filings.FiledFactsError, match="filings_fetch_interval_days"):
        filings.update_ticker_ciks(session, provider)
    assert provider.calls == 0


# --- the lookup ------------------------------------------------------------------

def test_cik_for_resolves_through_the_cache(filings, session):
    provider = StandIn(_records())
    assert filings.cik_for(session, provider, "JPM") == JPMORGAN
    assert filings.cik_for(session, provider, "GOOGL") == ALPHABET
    assert filings.cik_for(session, provider, "GOOG") == ALPHABET
    assert provider.calls == 1


def test_cik_for_fetches_before_it_says_a_ticker_is_not_listed(filings, session):
    provider = StandIn(_records())
    assert _stored(session) == {}
    assert filings.cik_for(session, provider, "AAPL") == APPLE
    assert provider.calls == 1


def test_cik_for_raises_naming_a_ticker_the_file_does_not_list(filings, session):
    provider = StandIn(_records())
    with pytest.raises(filings.FiledFactsError, match="ZZZZ"):
        filings.cik_for(session, provider, "ZZZZ")
    assert provider.calls == 1


def test_cik_for_reads_a_ticker_in_another_case_as_the_same_ticker(filings, session):
    provider = StandIn(_records())
    assert filings.cik_for(session, provider, "jpm") == JPMORGAN
