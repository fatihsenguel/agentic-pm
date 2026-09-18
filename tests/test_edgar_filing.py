"""
EdgarProvider.filing and EdgarProvider.document held to expected_values.md
Part 16 H, D55.

`filing` reads one accession's row out of the submissions document's
`filings.recent`: its form, its filed date and the name of its primary
document. `document` fetches that document from the archive as bytes. The
six rows of tests/golden/edgar_filings_goog.csv are the reference, Alphabet's
listing as pulled on 18 September 2026: the first and the last row of
`recent`, a 10-Q and the three 10-Ks.

What the methods decide:

  - the submissions document must be the company asked for, as for `filer`
  - an accession `recent` does not hold is refused stating how many filings
    the listing holds and from when; the older files are not asked for
  - columns that are missing or of different lengths, an accession listed
    twice, a name that is not a file's name, a missing form and a filed
    date that is not a date are each refused
  - the archive's address is the CIK without padding, the accession without
    hyphens and the name, and one request carries the contact
  - nothing about what the bytes say is decided here

No network. The stand-in session is test_edgar_filer.py's, serving a
submissions-shaped document built from the csv's rows, or fixed bytes for
the archive.
"""

import csv
import datetime as dt
from pathlib import Path

import pytest
import requests

from test_edgar_filer import AGENT, ALPHABET, _Response, _Session


GOLDEN = Path(__file__).parent / "golden"
LATEST = "0001652044-26-000018"
OUTSIDE_RECENT = "0001652044-23-000016"


def _rows():
    with open(GOLDEN / "edgar_filings_goog.csv", newline="") as fh:
        return list(csv.DictReader(fh))


ROWS = _rows()


def submissions(rows=ROWS, cik="0001652044", **columns):
    """A submissions document whose `recent` holds the csv's rows under
    EDGAR's names, with the columns the method does not read beside them."""
    recent = {
        "accessionNumber": [r["accession"] for r in rows],
        "filingDate": [r["filed"] for r in rows],
        "reportDate": [r["report_date"] for r in rows],
        "form": [r["form"] for r in rows],
        "primaryDocument": [r["primary_document"] for r in rows],
        "size": [0 for _ in rows],
    }
    recent.update(columns)
    for key, value in columns.items():
        if value is None:
            del recent[key]
    return {"cik": cik, "name": "Alphabet Inc.",
            "filings": {"recent": recent, "files": [{"name": "CIK0001652044-submissions-001.json"}]}}


class _Bytes(_Session):
    """Serves fixed bytes, for the archive."""

    def get(self, url, headers=None, timeout=None):
        self.calls.append({"url": url, "headers": dict(headers or {}), "timeout": timeout})
        response = _Response({}, self.status)
        response.content = self.body
        return response


@pytest.fixture(scope="module")
def edgar():
    from portfolio_tool.providers import edgar
    return edgar


@pytest.fixture
def agent(monkeypatch):
    monkeypatch.setenv("EDGAR_USER_AGENT", AGENT)


def filing(edgar, accn, body, status=200, cik=ALPHABET):
    session = _Session(body, status)
    return edgar.EdgarProvider(session=session).filing(cik, accn), session


# --- Part 16 H: every row comes back as the listing states it ---------------

@pytest.mark.parametrize("row", ROWS, ids=[r["accession"] for r in ROWS])
def test_every_row_comes_back(edgar, agent, row):
    record, _ = filing(edgar, row["accession"], submissions())
    assert (record.accn, record.form, record.filed, record.primary_document) == \
        (row["accession"], row["form"], dt.date.fromisoformat(row["filed"]),
         row["primary_document"])


def test_the_latest_annual_report_is_the_row_part_16_names(edgar, agent):
    record, _ = filing(edgar, LATEST, submissions())
    assert (record.form, record.filed, record.primary_document) == \
        ("10-K", dt.date(2026, 2, 5), "goog-20251231.htm")


def test_nothing_else_comes_back(edgar, agent):
    record, _ = filing(edgar, LATEST, submissions())
    assert set(vars(record)) == {"accn", "form", "filed", "primary_document"}


def test_the_request_names_the_company_and_the_contact(edgar, agent):
    _, session = filing(edgar, LATEST, submissions())
    assert [c["url"] for c in session.calls] == \
        ["https://data.sec.gov/submissions/CIK0001652044.json"]
    assert session.calls[0]["headers"]["User-Agent"] == AGENT


# --- what is refused -------------------------------------------------------

def test_an_accession_outside_recent_is_refused_stating_what_the_listing_holds(edgar, agent):
    with pytest.raises(edgar.EdgarError) as refused:
        filing(edgar, OUTSIDE_RECENT, submissions())
    message = str(refused.value)
    assert OUTSIDE_RECENT in message
    assert "6 recent filings" in message
    assert "2023-06-29 to 2026-09-16" in message
    assert "not asked for" in message


def test_an_accession_outside_recent_makes_one_request_and_no_other(edgar, agent):
    session = _Session(submissions())
    with pytest.raises(edgar.EdgarError):
        edgar.EdgarProvider(session=session).filing(ALPHABET, OUTSIDE_RECENT)
    assert len(session.calls) == 1


@pytest.mark.parametrize("accn", ["", "0001652044-26-18", "000165204426000018", "../x"])
def test_what_is_not_an_accession_is_refused_before_any_request(edgar, agent, accn):
    session = _Session(submissions())
    with pytest.raises(edgar.EdgarError, match="not an accession"):
        edgar.EdgarProvider(session=session).filing(ALPHABET, accn)
    assert session.calls == []


def test_a_document_for_another_company_raises(edgar, agent):
    with pytest.raises(edgar.EdgarError, match="CIK 320193"):
        filing(edgar, LATEST, submissions(cik="0000320193"))


def test_a_document_without_recent_filings_raises(edgar, agent):
    body = submissions()
    del body["filings"]["recent"]
    with pytest.raises(edgar.EdgarError, match="no recent filings"):
        filing(edgar, LATEST, body)


@pytest.mark.parametrize("column", ["accessionNumber", "form", "filingDate", "primaryDocument"])
def test_a_missing_column_raises_naming_it(edgar, agent, column):
    with pytest.raises(edgar.EdgarError, match=column):
        filing(edgar, LATEST, submissions(**{column: None}))


def test_columns_of_different_lengths_raise(edgar, agent):
    short = [r["form"] for r in ROWS][:-1]
    with pytest.raises(edgar.EdgarError, match="different lengths"):
        filing(edgar, LATEST, submissions(form=short))


def test_an_accession_listed_twice_raises(edgar, agent):
    with pytest.raises(edgar.EdgarError, match="2 times"):
        filing(edgar, LATEST, submissions(rows=ROWS + [ROWS[2]]))


@pytest.mark.parametrize("name", ["", None, "../../etc/passwd", "goog 20251231.htm",
                                  "goog-20251231.htm?x=1"])
def test_a_name_that_is_not_a_files_name_raises(edgar, agent, name):
    names = [name if r["accession"] == LATEST else r["primary_document"] for r in ROWS]
    with pytest.raises(edgar.EdgarError, match="not a file's name"):
        filing(edgar, LATEST, submissions(primaryDocument=names))


def test_a_missing_form_raises(edgar, agent):
    forms = ["" if r["accession"] == LATEST else r["form"] for r in ROWS]
    with pytest.raises(edgar.EdgarError, match="without a form"):
        filing(edgar, LATEST, submissions(form=forms))


@pytest.mark.parametrize("filed", ["", None, "05.02.2026"])
def test_a_filed_date_that_is_not_a_date_raises(edgar, agent, filed):
    dates = [filed if r["accession"] == LATEST else r["filed"] for r in ROWS]
    with pytest.raises(edgar.EdgarError, match="not a date"):
        filing(edgar, LATEST, submissions(filingDate=dates))


def test_an_http_failure_raises(edgar, agent):
    with pytest.raises(requests.HTTPError):
        filing(edgar, LATEST, submissions(), status=503)


# --- the archive -----------------------------------------------------------

def test_the_document_comes_back_as_the_bytes_served(edgar, agent):
    served = b"<?xml version='1.0' encoding='ASCII'?><html></html>"
    session = _Bytes(served)
    assert edgar.EdgarProvider(session=session).document(
        ALPHABET, LATEST, "goog-20251231.htm") == served


def test_the_archive_address_is_part_16s(edgar, agent):
    session = _Bytes(b"x")
    edgar.EdgarProvider(session=session).document(ALPHABET, LATEST, "goog-20251231.htm")
    assert [c["url"] for c in session.calls] == [
        "https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm"]
    assert session.calls[0]["headers"]["User-Agent"] == AGENT


@pytest.mark.parametrize("accn, name", [("000165204426000018", "goog-20251231.htm"),
                                        (LATEST, "../goog-20251231.htm"),
                                        (LATEST, "goog.htm#top"), (LATEST, "")])
def test_the_archive_is_not_asked_for_what_is_not_an_address(edgar, agent, accn, name):
    session = _Bytes(b"x")
    with pytest.raises(edgar.EdgarError):
        edgar.EdgarProvider(session=session).document(ALPHABET, accn, name)
    assert session.calls == []


def test_an_archive_failure_raises(edgar, agent):
    session = _Bytes(b"x", status=404)
    with pytest.raises(requests.HTTPError):
        edgar.EdgarProvider(session=session).document(ALPHABET, LATEST, "goog-20251231.htm")


def test_the_archives_source_is_not_the_facts(edgar):
    assert edgar.ARCHIVE_NAME == "EDGAR filing archive"
    assert edgar.ARCHIVE_NAME != edgar.EdgarProvider.name
