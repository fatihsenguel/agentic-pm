"""
filings.update_filer: the filer fetch under its cache rule.

Runs against the copy conftest.py makes of data/portfolio.db, so it passes
only once migration c8dd6b3dc535 has been applied. The provider is a
stand-in that records its calls and answers from one row of
tests/golden/edgar_submissions.csv; no network.

The rules, each a test, the shape of test_filed_facts_fetch.py:

  - a first fetch stores one filers row as the provider states it, with the
    pull time, and the row is what the call returns
  - a second call within filings_fetch_interval_days makes no provider call
  - a stale record fetches again; the row is rewritten as the document now
    states it and the pull time moves, whether or not the code changed,
    since EDGAR keeps no history and the row is the code as of its pull
  - a code the document does not state is stored empty: the fact EDGAR
    states, which the screen stops on (D35)
  - a provider that fails on the first fetch leaves no row, and on a later
    one leaves the old row and its date untouched, so the next call retries
  - a config without the interval raises before the provider is reached

`pulled_at` is on the clock `update_filed_facts` uses, UTC, so the two
records a block is built from carry one clock; which clock a pull date is on
is decided where an answer first prints one (KNOWN_GAPS, the UTC entry).
"""

import csv
import datetime as dt
from pathlib import Path

import pytest
import requests
import tomli

from portfolio_tool.database_setup import Filer, get_session
from portfolio_tool.provider_models import ProviderFiler


GOLDEN = Path(__file__).parent / "golden"
CONFIG = Path(__file__).parent.parent / "config.toml"
JPMORGAN = 19617


def _row(cik):
    with open(GOLDEN / "edgar_submissions.csv", newline="") as fh:
        return next(r for r in csv.DictReader(fh) if int(r["cik"]) == cik)


def _filer(cik=JPMORGAN, **overrides):
    row = _row(cik)
    record = {"cik": cik, "name": row["name"], "sic": row["sic"],
              "sic_description": row["sic_description"]}
    record.update(overrides)
    return ProviderFiler(**record)


class StandIn:
    """Answers filer() from a fixed record and records every call."""

    def __init__(self, record):
        self.record = record
        self.calls = []

    def filer(self, cik):
        self.calls.append(cik)
        return self.record


class Failing(StandIn):
    def filer(self, cik):
        self.calls.append(cik)
        raise requests.HTTPError("503 from the stand-in")


@pytest.fixture(scope="module")
def filings():
    from portfolio_tool import filings
    return filings


def _clear(session):
    session.query(Filer).filter(Filer.cik == JPMORGAN).delete()
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
    return session.get(Filer, JPMORGAN)


def _age(session, days):
    row = _stored(session)
    row.pulled_at = row.pulled_at - dt.timedelta(days=days)
    session.commit()


def _interval():
    return tomli.load(CONFIG.open("rb"))["data_fetch"]["filings_fetch_interval_days"]


def test_first_fetch_stores_the_filer_as_stated(filings, session):
    provider = StandIn(_filer())
    before = dt.datetime.utcnow()
    returned = filings.update_filer(session, provider, JPMORGAN)

    assert provider.calls == [JPMORGAN]
    row = _stored(session)
    assert returned is row
    assert (row.cik, row.name, row.sic, row.sic_description) == \
        (JPMORGAN, "JPMORGAN CHASE & CO", "6021", "National Commercial Banks")
    assert before <= row.pulled_at <= dt.datetime.utcnow()


def test_a_second_call_within_the_interval_makes_no_provider_call(filings, session):
    provider = StandIn(_filer())
    first = filings.update_filer(session, provider, JPMORGAN)
    pulled = first.pulled_at
    again = filings.update_filer(session, provider, JPMORGAN)
    assert provider.calls == [JPMORGAN]
    assert again is _stored(session) and again.pulled_at == pulled


def test_a_stale_record_with_a_changed_code_is_overwritten(filings, session):
    provider = StandIn(_filer())
    filings.update_filer(session, provider, JPMORGAN)
    _age(session, _interval())
    aged = _stored(session).pulled_at

    provider.record = _filer(sic="6022", sic_description="State Commercial Banks",
                             name="JPMORGAN CHASE & CO (renamed)")
    filings.update_filer(session, provider, JPMORGAN)

    assert provider.calls == [JPMORGAN, JPMORGAN]
    row = _stored(session)
    assert (row.name, row.sic, row.sic_description) == \
        ("JPMORGAN CHASE & CO (renamed)", "6022", "State Commercial Banks")
    assert row.pulled_at > aged
    assert session.query(Filer).filter(Filer.cik == JPMORGAN).count() == 1


def test_a_stale_record_with_the_same_code_moves_the_date_only(filings, session):
    provider = StandIn(_filer())
    filings.update_filer(session, provider, JPMORGAN)
    _age(session, _interval())
    aged = _stored(session).pulled_at

    filings.update_filer(session, provider, JPMORGAN)

    assert provider.calls == [JPMORGAN, JPMORGAN]
    row = _stored(session)
    assert (row.name, row.sic, row.sic_description) == \
        ("JPMORGAN CHASE & CO", "6021", "National Commercial Banks")
    assert row.pulled_at > aged


def test_a_code_the_document_does_not_state_is_stored_empty(filings, session):
    provider = StandIn(_filer(sic=None, sic_description=None))
    filings.update_filer(session, provider, JPMORGAN)
    row = _stored(session)
    assert row.name == "JPMORGAN CHASE & CO"
    assert row.sic is None and row.sic_description is None


def test_a_failed_first_fetch_leaves_no_row(filings, session):
    provider = Failing(_filer())
    with pytest.raises(requests.HTTPError):
        filings.update_filer(session, provider, JPMORGAN)
    session.rollback()
    assert _stored(session) is None


def test_a_failed_later_fetch_leaves_the_old_row_and_its_date(filings, session):
    filings.update_filer(session, StandIn(_filer()), JPMORGAN)
    _age(session, _interval())
    aged = _stored(session).pulled_at

    provider = Failing(_filer())
    with pytest.raises(requests.HTTPError):
        filings.update_filer(session, provider, JPMORGAN)
    session.rollback()

    row = _stored(session)
    assert provider.calls == [JPMORGAN]
    assert (row.sic, row.pulled_at) == ("6021", aged)


def test_a_config_without_the_interval_raises_before_the_provider(filings, session, monkeypatch):
    monkeypatch.setattr(filings, "load_config", lambda: {"data_fetch": {}})
    provider = StandIn(_filer())
    with pytest.raises(filings.FiledFactsError, match="filings_fetch_interval_days"):
        filings.update_filer(session, provider, JPMORGAN)
    assert provider.calls == []
