"""
filings.update_filed_facts: the filed-facts fetch under its cache rules.

Runs against the copy conftest.py makes of data/portfolio.db, so it passes
only once migrations 302903e3d966 and 97d3708851e5 have been applied. The
provider is a stand-in that records its calls and returns facts built from
Part 12's committed fixture; no network.

The rules, each a test:

  - a first fetch stores one filed_facts row per fact, the value as the
    digits filed, the provider's name as source, and records the time
  - a second call within filings_fetch_interval_days makes no provider call
  - a stale record fetches again, and a fact already stored is not stored
    twice
  - a restatement arrives under a new accession and is a second row
  - the same key with a different value raises and stores nothing: one
    filing's figure never changes, so a difference is a defect upstream,
    not a vintage
  - a provider that fails leaves no record, so the next call retries
  - a config without the interval raises before the provider is reached,
    and config.toml carries it

Every fact the provider returns is stored (decided 13 September 2026): the
field lists are still open (Part 13 E), and storing only named tags would
need a rule to refetch past the interval each time a list changes.
"""

import csv
import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest
import requests
import tomli

from portfolio_tool.database_setup import FiledFact, FiledFetchMetadata, get_session


GOLDEN = Path(__file__).parent / "golden"
CONFIG = Path(__file__).parent.parent / "config.toml"
APPLE = 320193

# Part 12's F3 (a restatement between two filings) and F5 (an instant beside
# the fiscal year end), plus the FY2024 tax rate that D32 is about.
PICKED = {"F3", "F5"}


def _facts():
    from portfolio_tool.provider_models import ProviderFiledFact
    out = []
    with open(GOLDEN / "edgar_facts_aapl.csv", newline="") as fh:
        for row in csv.DictReader(fh):
            wanted = row["section"] in PICKED or (
                row["field"] == "effective_tax_rate" and row["end"] == "2024-09-28")
            if not wanted:
                continue
            out.append(ProviderFiledFact(
                tag=row["tag"], unit=row["unit"],
                start=dt.date.fromisoformat(row["start"]) if row["start"] else None,
                end=dt.date.fromisoformat(row["end"]), value=Decimal(row["val"]),
                accn=row["accn"], fy=int(row["fy"]) if row["fy"] else None,
                fp=row["fp"] or None, form=row["form"],
                filed=dt.date.fromisoformat(row["filed"]), frame=row["frame"] or None,
                source=StandIn.name,
            ))
    return out


class StandIn:
    """Answers annual_facts from a fixed list and records every call."""

    name = "stand-in filings"

    def __init__(self, facts):
        self.facts = list(facts)
        self.calls = []

    def annual_facts(self, cik):
        self.calls.append(cik)
        return list(self.facts)


class Failing(StandIn):
    def annual_facts(self, cik):
        self.calls.append(cik)
        raise requests.HTTPError("503 from the stand-in")


@pytest.fixture(scope="module")
def filings():
    from portfolio_tool import filings
    return filings


def _clear(session):
    session.query(FiledFact).filter(FiledFact.cik == APPLE).delete()
    session.query(FiledFetchMetadata).filter(FiledFetchMetadata.cik == APPLE).delete()
    session.commit()


@pytest.fixture
def session():
    # Closed on every path: a session left open after a failed clear holds
    # SQLite's write lock, and the next test that writes fails as "locked".
    s = get_session()
    try:
        _clear(s)
        yield s
        s.rollback()
        _clear(s)
    finally:
        s.rollback()
        s.close()


def _rows(session):
    return session.query(FiledFact).filter(FiledFact.cik == APPLE).all()


def _record(session):
    return session.get(FiledFetchMetadata, APPLE)


def _age(session, days):
    record = _record(session)
    record.last_fetch_time = record.last_fetch_time - dt.timedelta(days=days)
    session.commit()


def _interval():
    return tomli.load(CONFIG.open("rb"))["data_fetch"]["filings_fetch_interval_days"]


def test_config_toml_carries_the_filings_interval():
    assert isinstance(_interval(), int)


def test_first_fetch_stores_every_fact_as_filed(filings, session):
    facts = _facts()
    provider = StandIn(facts)
    added = filings.update_filed_facts(session, provider, APPLE)

    assert added == len(facts)
    assert provider.calls == [APPLE]
    rows = _rows(session)
    assert len(rows) == len(facts)
    assert {r.source for r in rows} == {StandIn.name}
    rate = [r for r in rows if r.tag == "EffectiveIncomeTaxRateContinuingOperations"]
    assert [r.value for r in rate] == ["0.241"]
    restated = sorted(r.value for r in rows
                      if r.tag == "NetIncomeLoss" and r.end == dt.date(2008, 9, 27))
    assert restated == ["4834000000", "6119000000", "6119000000"]
    assert _record(session).last_fetch_time is not None


def test_a_second_call_within_the_interval_makes_no_provider_call(filings, session):
    provider = StandIn(_facts())
    filings.update_filed_facts(session, provider, APPLE)
    assert filings.update_filed_facts(session, provider, APPLE) == 0
    assert provider.calls == [APPLE]


def test_a_stale_record_fetches_again_and_stores_nothing_twice(filings, session):
    provider = StandIn(_facts())
    filings.update_filed_facts(session, provider, APPLE)
    before = len(_rows(session))
    _age(session, _interval())

    assert filings.update_filed_facts(session, provider, APPLE) == 0
    assert provider.calls == [APPLE, APPLE]
    assert len(_rows(session)) == before


def test_a_restatement_is_a_second_row(filings, session):
    facts = _facts()
    provider = StandIn(facts)
    filings.update_filed_facts(session, provider, APPLE)
    _age(session, _interval())

    equity = next(f for f in facts if f.tag == "StockholdersEquity"
                  and f.end == dt.date(2024, 9, 28))
    later = dict(vars(equity), accn="0000320193-99-000001", filed=dt.date(2026, 10, 30),
                 value=Decimal("57000000000"))
    provider.facts.append(type(equity)(**later))

    assert filings.update_filed_facts(session, provider, APPLE) == 1
    stored = sorted(r.value for r in _rows(session)
                    if r.tag == "StockholdersEquity" and r.end == dt.date(2024, 9, 28))
    assert stored == ["56950000000", "57000000000"]


def test_the_same_key_with_another_value_raises_and_stores_nothing(filings, session):
    facts = _facts()
    provider = StandIn(facts)
    filings.update_filed_facts(session, provider, APPLE)
    fetched_at = _record(session).last_fetch_time
    _age(session, _interval())
    aged = _record(session).last_fetch_time

    rate = next(f for f in facts if f.tag == "EffectiveIncomeTaxRateContinuingOperations")
    changed = dict(vars(rate), value=Decimal("0.242"))
    provider.facts = [type(rate)(**changed) if f is rate else f for f in facts]
    provider.facts.append(type(rate)(**dict(vars(rate), accn="0000320193-99-000002")))

    with pytest.raises(filings.FiledFactsError, match="EffectiveIncomeTaxRateContinuingOperations"):
        filings.update_filed_facts(session, provider, APPLE)
    session.rollback()

    assert len(_rows(session)) == len(facts)
    assert [r.value for r in _rows(session)
            if r.tag == "EffectiveIncomeTaxRateContinuingOperations"] == ["0.241"]
    assert _record(session).last_fetch_time == aged != fetched_at


def test_a_failed_fetch_leaves_no_record(filings, session):
    provider = Failing([])
    with pytest.raises(requests.HTTPError):
        filings.update_filed_facts(session, provider, APPLE)
    session.rollback()
    assert _record(session) is None
    assert _rows(session) == []


def test_a_config_without_the_interval_raises_before_the_provider(filings, session, monkeypatch):
    monkeypatch.setattr(filings, "load_config", lambda: {"data_fetch": {}})
    provider = StandIn(_facts())
    with pytest.raises(filings.FiledFactsError, match="filings_fetch_interval_days"):
        filings.update_filed_facts(session, provider, APPLE)
    assert provider.calls == []
