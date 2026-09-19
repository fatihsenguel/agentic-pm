"""
filings.latest_annual_report and filings.stored_document, held to
expected_values.md Part 16 H, D54 and D55.

Runs against the copy conftest.py makes of data/portfolio.db, so it passes
only once migration 2445c12e728c has been applied, and it reads the facts
already stored there: Alphabet's three 10-Ks of Part 16 H and Apple's
latest 10-K with its 2010 amendment. The shapes no stored filer has, an
amendment after the latest 10-K and two 10-Ks on one day, are written for
a CIK no filer has and removed after each test. The provider is a stand-in
that records its calls and serves tests/golden/edgar_document_goog_excerpt.htm
for the document; no network.

The rules, each a test:

  - the filing read is the latest 10-K filed by the as-of date, off the
    stored facts, with nothing fetched
  - a 10-K/A filed on or after it refuses naming it; one filed before it or
    after the as-of date refuses nothing
  - no 10-K, and two 10-Ks filed on one day, refuse
  - a first call asks for the listing's row, then for the document, and
    stores the document's text once with the archive as its source
  - a second call asks nothing; there is no interval
  - a filing the facts do not name, and a listing that disagrees with the
    facts about form or filed date, refuse before the document is asked for
  - a provider that fails and a document the extractor refuses leave no row,
    and the next call asks again
"""

import datetime as dt
from pathlib import Path

import pytest
import requests

from portfolio_tool import filing_text
from portfolio_tool.database_setup import FiledDocument, FiledFact, get_session
from portfolio_tool.provider_models import ProviderFiling


GOLDEN = Path(__file__).parent / "golden"
DOCUMENT = (GOLDEN / "edgar_document_goog_excerpt.htm").read_bytes()

ALPHABET = 1652044
APPLE = 320193
LATEST = "0001652044-26-000018"
PREVIOUS = "0001652044-25-000014"
NAME = "goog-20251231.htm"
AS_OF = dt.date(2026, 9, 18)

# A CIK no filer in the store has, for the shapes no stored filer has.
NOBODY = 9_999_999


def _listed(form="10-K", filed=dt.date(2026, 2, 5), name=NAME, accn=LATEST):
    return ProviderFiling(accn=accn, form=form, filed=filed, primary_document=name)


class StandIn:
    """Answers filing() and document() from fixed values and records every
    call; `fail` names the call that raises."""

    def __init__(self, listed=None, body=DOCUMENT, fail=None):
        self.listed = listed or _listed()
        self.body = body
        self.fail = fail
        self.calls = []

    def filing(self, cik, accn):
        self.calls.append(("filing", cik, accn))
        if self.fail == "filing":
            raise requests.HTTPError("503 from the stand-in")
        return self.listed

    def document(self, cik, accn, name):
        self.calls.append(("document", cik, accn, name))
        if self.fail == "document":
            raise requests.HTTPError("404 from the stand-in")
        return self.body


@pytest.fixture(scope="module")
def filings():
    from portfolio_tool import filings
    return filings


def _clear(session):
    session.query(FiledDocument).filter(FiledDocument.accn == LATEST).delete()
    session.query(FiledFact).filter(FiledFact.cik == NOBODY).delete()
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


def _file(session, accn, form, filed):
    session.add(FiledFact(cik=NOBODY, tag="Revenues", unit="USD", start=None,
                          end=dt.date(2024, 12, 31), value="1", accn=accn, fy=2024,
                          fp="FY", form=form, filed=filed, frame=None, source="stand-in"))
    session.commit()


def _stored(accn=LATEST):
    s = get_session()
    try:
        row = s.get(FiledDocument, accn)
        return None if row is None else (row.accn, row.text, row.source)
    finally:
        s.close()


# --- D54: which filing is read ---------------------------------------------

def test_alphabets_latest_annual_report_is_part_16s(filings, session):
    report = filings.latest_annual_report(session, ALPHABET, AS_OF)
    assert (report.accn, report.form, report.filed) == (LATEST, "10-K", dt.date(2026, 2, 5))


def test_the_as_of_date_decides_which_report_is_latest(filings, session):
    report = filings.latest_annual_report(session, ALPHABET, dt.date(2026, 2, 4))
    assert (report.accn, report.filed) == (PREVIOUS, dt.date(2025, 2, 5))


def test_a_report_filed_on_the_as_of_date_is_read(filings, session):
    report = filings.latest_annual_report(session, ALPHABET, dt.date(2026, 2, 5))
    assert report.accn == LATEST


def test_an_amendment_before_the_latest_report_refuses_nothing(filings, session):
    report = filings.latest_annual_report(session, APPLE, AS_OF)
    assert (report.accn, report.filed) == ("0000320193-25-000079", dt.date(2025, 10, 31))


def test_a_filer_with_no_annual_report_is_refused(filings, session):
    with pytest.raises(filings.FiledFactsError, match="name no 10-K"):
        filings.latest_annual_report(session, NOBODY, AS_OF)


def test_an_amendment_after_the_latest_report_refuses_naming_it(filings, session):
    _file(session, "0009999999-25-000001", "10-K", dt.date(2025, 2, 1))
    _file(session, "0009999999-25-000002", "10-K/A", dt.date(2025, 3, 1))
    with pytest.raises(filings.FiledFactsError, match="0009999999-25-000002"):
        filings.latest_annual_report(session, NOBODY, AS_OF)


def test_an_amendment_on_the_same_day_refuses(filings, session):
    _file(session, "0009999999-25-000001", "10-K", dt.date(2025, 2, 1))
    _file(session, "0009999999-25-000002", "10-K/A", dt.date(2025, 2, 1))
    with pytest.raises(filings.FiledFactsError, match="10-K/A"):
        filings.latest_annual_report(session, NOBODY, AS_OF)


def test_an_amendment_after_the_as_of_date_refuses_nothing(filings, session):
    _file(session, "0009999999-25-000001", "10-K", dt.date(2025, 2, 1))
    _file(session, "0009999999-26-000002", "10-K/A", dt.date(2026, 10, 1))
    report = filings.latest_annual_report(session, NOBODY, AS_OF)
    assert report.accn == "0009999999-25-000001"


def test_two_reports_filed_on_one_day_refuse_naming_both(filings, session):
    _file(session, "0009999999-25-000001", "10-K", dt.date(2025, 2, 1))
    _file(session, "0009999999-25-000003", "10-K", dt.date(2025, 2, 1))
    with pytest.raises(filings.FiledFactsError,
                       match="0009999999-25-000001 and 0009999999-25-000003"):
        filings.latest_annual_report(session, NOBODY, AS_OF)


# --- D55: the document, stored once ------------------------------------------

def test_a_first_call_stores_the_documents_text_once(filings, session):
    provider = StandIn()
    row = filings.stored_document(session, provider, ALPHABET, LATEST)

    assert provider.calls == [("filing", ALPHABET, LATEST),
                              ("document", ALPHABET, LATEST, NAME)]
    assert (row.accn, row.source) == (LATEST, "EDGAR filing archive")
    assert row.text == filing_text.text_of(DOCUMENT)
    assert _stored() == (LATEST, filing_text.text_of(DOCUMENT), "EDGAR filing archive")


def test_the_stored_text_is_the_whole_text_and_no_section_of_it(filings, session):
    row = filings.stored_document(session, StandIn(), ALPHABET, LATEST)
    lines = row.text.split("\n")
    assert len(lines) == 228
    assert lines[0] == "DOCUMENTS INCORPORATED BY REFERENCE" and lines[-1] == "98."


def test_a_second_call_asks_nothing(filings, session):
    filings.stored_document(session, StandIn(), ALPHABET, LATEST)
    again = StandIn()
    row = filings.stored_document(session, again, ALPHABET, LATEST)
    assert again.calls == []
    assert row.accn == LATEST


def test_a_filing_the_facts_do_not_name_is_refused_before_any_request(filings, session):
    provider = StandIn()
    with pytest.raises(filings.FiledFactsError, match="no stored fact carries"):
        filings.stored_document(session, provider, ALPHABET, "0001652044-26-999999")
    assert provider.calls == []


@pytest.mark.parametrize("listed", [_listed(form="10-K/A"), _listed(filed=dt.date(2026, 2, 6))],
                         ids=["form", "filed"])
def test_a_listing_that_disagrees_with_the_facts_refuses_before_the_document(
        filings, session, listed):
    provider = StandIn(listed=listed)
    with pytest.raises(filings.FiledFactsError, match="disagree"):
        filings.stored_document(session, provider, ALPHABET, LATEST)
    assert [c[0] for c in provider.calls] == ["filing"]
    assert _stored() is None


@pytest.mark.parametrize("fail", ["filing", "document"])
def test_a_provider_that_fails_leaves_no_row_and_the_next_call_asks_again(
        filings, session, fail):
    with pytest.raises(requests.HTTPError):
        filings.stored_document(session, StandIn(fail=fail), ALPHABET, LATEST)
    session.rollback()
    assert _stored() is None

    provider = StandIn()
    filings.stored_document(session, provider, ALPHABET, LATEST)
    assert [c[0] for c in provider.calls] == ["filing", "document"]


def test_a_document_the_extractor_refuses_leaves_no_row(filings, session):
    refused = DOCUMENT.replace(b"<div", b"<p", 1)
    with pytest.raises(filing_text.FilingTextError, match="<p> element"):
        filings.stored_document(session, StandIn(body=refused), ALPHABET, LATEST)
    session.rollback()
    assert _stored() is None


def test_a_document_that_yields_no_text_leaves_no_row(filings, session):
    empty = b"<?xml version='1.0' encoding='ASCII'?><html><body></body></html>"
    with pytest.raises(filings.FiledFactsError, match="yields no text"):
        filings.stored_document(session, StandIn(body=empty), ALPHABET, LATEST)
    session.rollback()
    assert _stored() is None
