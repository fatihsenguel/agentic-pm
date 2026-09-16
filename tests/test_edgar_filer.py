"""
EdgarProvider.filer held to expected_values.md Part 13 C.

The method fetches one submissions document and returns what the block's
industry exclusion reads: the filer's number, its name, its SIC code and the
code's description, as EDGAR states them on the pull date. The fourteen rows
of tests/golden/edgar_submissions.csv are the reference: Alphabet and the
thirteen financial filers Part 13 C pulled on 13 and 14 September 2026.

What the method decides:

  - the document must be the company asked for, as with company facts
  - a code that is missing, empty or not four digits comes back as None, and
    so does a missing or empty description; the screen stops on a block
    whose code is not four digits (D35), so nothing is repaired here
  - nothing else in the document is returned: `entityType`, `ownerOrg`,
    `fiscalYearEnd` and the filings index have no consumer (decision 49)

What the test assumes about the document's `cik` field: the stand-in serves
it as the csv keeps it, a ten-digit zero-padded string, and the check also
accepts the bare digits and an integer. The first live fetch through this
method, 16 September 2026, Apple and JPMorgan, found the ten-digit
zero-padded string, and `sic` a string, as Part 13 C transcribed it; the
other two forms stay accepted because nothing says EDGAR will not change
its mind, and the check would still be right.

No network. The stand-in session serves a submissions-shaped document built
from one csv row, the pattern of test_edgar_provider.py. The module is
imported inside a fixture so that, before the method exists, this file is a
list of errors and not an interrupted suite.
"""

import csv
import dataclasses
import json
from pathlib import Path

import pytest
import requests


GOLDEN = Path(__file__).parent / "golden"
AGENT = "benchmark-suite test@example.invalid"

ALPHABET = 1652044
JPMORGAN = 19617


def _rows():
    with open(GOLDEN / "edgar_submissions.csv", newline="") as fh:
        return list(csv.DictReader(fh))


ROWS = {int(r["cik"]): r for r in _rows()}


def document(row, **overrides):
    """A submissions document holding one csv row's fields under EDGAR's
    names, plus the fields the method must ignore."""
    body = {
        "cik": row["cik"],
        "entityType": row["entity_type"],
        "sic": row["sic"],
        "sicDescription": row["sic_description"],
        "ownerOrg": row["owner_org"],
        "name": row["name"],
        "fiscalYearEnd": row["fiscal_year_end"],
        "filings": {"recent": {}, "files": []},
    }
    body.update(overrides)
    for key, value in overrides.items():
        if value is None:
            del body[key]
    return body


class _Response:
    def __init__(self, body, status=200):
        self.status_code = status
        self.content = json.dumps(body).encode()

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError(f"{self.status_code} from the stand-in")


class _Session:
    """Stands in for requests.Session for the one call the provider makes."""

    def __init__(self, body, status=200):
        self.body, self.status = body, status
        self.calls = []

    def get(self, url, headers=None, timeout=None):
        self.calls.append({"url": url, "headers": dict(headers or {}), "timeout": timeout})
        return _Response(self.body, self.status)


@pytest.fixture(scope="module")
def edgar():
    from portfolio_tool.providers import edgar
    return edgar


@pytest.fixture
def agent(monkeypatch):
    monkeypatch.setenv("EDGAR_USER_AGENT", AGENT)


def filer(edgar, cik, body, status=200):
    session = _Session(body, status)
    return edgar.EdgarProvider(session=session).filer(cik), session


# --- Part 13 C: every row comes back as EDGAR states it -------------------------

@pytest.mark.parametrize("cik", sorted(ROWS))
def test_every_row_comes_back(edgar, agent, cik):
    row = ROWS[cik]
    record, _ = filer(edgar, cik, document(row))
    assert (record.cik, record.name, record.sic, record.sic_description) == \
        (cik, row["name"], row["sic"], row["sic_description"])


def test_nothing_else_comes_back(edgar, agent):
    record, _ = filer(edgar, ALPHABET, document(ROWS[ALPHABET]))
    assert {f.name for f in dataclasses.fields(record)} == \
        {"cik", "name", "sic", "sic_description"}


def test_the_code_is_a_string_of_four_digits(edgar, agent):
    record, _ = filer(edgar, JPMORGAN, document(ROWS[JPMORGAN]))
    assert record.sic == "6021" and isinstance(record.sic, str)


# --- a code EDGAR does not state, or states in a form the screen cannot read ------

@pytest.mark.parametrize("sic", [None, "", "602", "60210", "abcd", 6021])
def test_a_missing_or_malformed_code_is_none(edgar, agent, sic):
    record, _ = filer(edgar, JPMORGAN, document(ROWS[JPMORGAN], sic=sic))
    assert record.sic is None
    assert record.name == ROWS[JPMORGAN]["name"]


@pytest.mark.parametrize("description", [None, ""])
def test_a_missing_or_empty_description_is_none(edgar, agent, description):
    record, _ = filer(edgar, JPMORGAN, document(ROWS[JPMORGAN], sicDescription=description))
    assert record.sic_description is None
    assert record.sic == "6021"


# --- the document's cik: the forms the check accepts; EDGAR sends the padded string ---

@pytest.mark.parametrize("cik_field", ["0001652044", "1652044", 1652044])
def test_the_document_cik_in_each_form_is_the_company(edgar, agent, cik_field):
    record, _ = filer(edgar, ALPHABET, document(ROWS[ALPHABET], cik=cik_field))
    assert record.cik == ALPHABET


def test_a_document_for_another_company_raises(edgar, agent):
    session = _Session(document(ROWS[JPMORGAN]))
    with pytest.raises(edgar.EdgarError, match="19617"):
        edgar.EdgarProvider(session=session).filer(ALPHABET)


@pytest.mark.parametrize("cik_field", [None, "", "not a number"])
def test_a_document_without_a_readable_cik_raises(edgar, agent, cik_field):
    session = _Session(document(ROWS[ALPHABET], cik=cik_field))
    with pytest.raises(edgar.EdgarError):
        edgar.EdgarProvider(session=session).filer(ALPHABET)


def test_a_document_without_a_name_raises(edgar, agent):
    session = _Session(document(ROWS[ALPHABET], name=None))
    with pytest.raises(edgar.EdgarError, match="name"):
        edgar.EdgarProvider(session=session).filer(ALPHABET)


# --- the request -------------------------------------------------------------------

def test_the_request_names_the_company_and_the_contact(edgar, agent):
    _, session = filer(edgar, JPMORGAN, document(ROWS[JPMORGAN]))
    assert len(session.calls) == 1
    call = session.calls[0]
    assert call["url"] == "https://data.sec.gov/submissions/CIK0000019617.json"
    assert call["headers"]["User-Agent"] == AGENT
    assert call["timeout"] == edgar.TIMEOUT_SECONDS


def test_an_http_failure_raises(edgar, agent):
    with pytest.raises(requests.HTTPError):
        filer(edgar, JPMORGAN, {}, status=403)
