"""
EdgarProvider.tickers held to the CIKs expected_values.md Parts 12 and 13
record.

The method fetches the SEC's published ticker file, one document for every
listed filer, and returns one record per (ticker, CIK) pair: the forward map
a ticker-to-CIK question needs (decision 29, question 50). The submissions
document maps the other way, one CIK to its tickers, so it verifies a
resolved CIK and cannot resolve one.

The reference rows are typed here from the record: Apple 320193 with its
one ticker (Part 12; the submissions document carries one ticker, KNOWN_GAPS
16 September), Alphabet 1652044 with GOOGL and GOOG (Part 13 C, the
watchlist's ticker), JPMorgan 19617 with JPM among the nine its document
lists (Part 13 C, KNOWN_GAPS).

What the method decides:

  - every entry yields a ticker, a string, and a CIK, a number; an entry
    without either raises, since a map with a hole in it is not the map
  - one CIK may have several tickers; one ticker may not name two CIKs
  - nothing else in the document is returned: the company title has no
    consumer, the filers row carries EDGAR's name

What the test assumes about the document: a JSON object keyed by position,
each value an object with `cik_str`, `ticker` and `title`, and the same
entries as a JSON list. Both forms are served by the stand-in; the URL and
the shape are from memory, and the first live fetch records which form the
SEC sends, the way the submissions document's `cik` form was recorded.

No network. The module is imported inside a fixture so that, before the
method exists, this file is a list of errors and not an interrupted suite.
"""

import dataclasses
import json

import pytest
import requests


AGENT = "benchmark-suite test@example.invalid"

APPLE, ALPHABET, JPMORGAN = 320193, 1652044, 19617

# (ticker, cik, title as the file might carry it)
ROWS = [
    ("AAPL", APPLE, "Apple Inc."),
    ("GOOGL", ALPHABET, "Alphabet Inc."),
    ("GOOG", ALPHABET, "Alphabet Inc."),
    ("JPM", JPMORGAN, "JPMORGAN CHASE & CO"),
]


def entry(ticker, cik, title, **overrides):
    body = {"cik_str": cik, "ticker": ticker, "title": title}
    body.update(overrides)
    for key, value in overrides.items():
        if value is None:
            del body[key]
    return body


def document(rows=ROWS, as_list=False):
    entries = [entry(*row) for row in rows]
    return entries if as_list else {str(i): e for i, e in enumerate(entries)}


class _Response:
    def __init__(self, body, status=200):
        self.status_code = status
        self.content = json.dumps(body).encode()

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError(f"{self.status_code} from the stand-in")


class _Session:
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


def tickers(edgar, body, status=200):
    session = _Session(body, status)
    return edgar.EdgarProvider(session=session).tickers(), session


# --- every pair comes back ------------------------------------------------------

@pytest.mark.parametrize("as_list", [False, True])
def test_every_pair_comes_back_in_either_form(edgar, agent, as_list):
    records, _ = tickers(edgar, document(as_list=as_list))
    assert sorted((r.ticker, r.cik) for r in records) == \
        sorted((ticker, cik) for ticker, cik, _ in ROWS)


def test_one_cik_may_have_several_tickers(edgar, agent):
    records, _ = tickers(edgar, document())
    assert sorted(r.ticker for r in records if r.cik == ALPHABET) == ["GOOG", "GOOGL"]


def test_nothing_else_comes_back(edgar, agent):
    records, _ = tickers(edgar, document())
    assert {f.name for f in dataclasses.fields(records[0])} == {"ticker", "cik"}


def test_the_ticker_is_a_string_and_the_cik_a_number(edgar, agent):
    records, _ = tickers(edgar, document())
    jpm = next(r for r in records if r.ticker == "JPM")
    assert isinstance(jpm.ticker, str) and isinstance(jpm.cik, int) and jpm.cik == JPMORGAN


def test_a_cik_carried_as_a_string_is_read_as_the_number(edgar, agent):
    records, _ = tickers(edgar, {"0": entry("JPM", "19617", "JPMORGAN CHASE & CO")})
    assert records[0].cik == JPMORGAN


# --- a map with a hole in it is not the map ---------------------------------------

@pytest.mark.parametrize("ticker", [None, "", 12])
def test_an_entry_without_a_ticker_raises(edgar, agent, ticker):
    holed = {"cik_str": JPMORGAN, "title": "x"}
    if ticker is not None:
        holed["ticker"] = ticker
    body = {"0": entry("AAPL", APPLE, "Apple Inc."), "1": holed}
    with pytest.raises(edgar.EdgarError, match="ticker"):
        tickers(edgar, body)


@pytest.mark.parametrize("cik", [None, "", "not a number"])
def test_an_entry_without_a_readable_cik_raises(edgar, agent, cik):
    body = {"0": entry("JPM", JPMORGAN, "x", cik_str=cik)}
    with pytest.raises(edgar.EdgarError, match="JPM"):
        tickers(edgar, body)


def test_one_ticker_naming_two_ciks_raises(edgar, agent):
    body = document([("JPM", JPMORGAN, "a"), ("JPM", APPLE, "b")])
    with pytest.raises(edgar.EdgarError, match="JPM"):
        tickers(edgar, body)


def test_the_same_pair_twice_is_one_record(edgar, agent):
    records, _ = tickers(edgar, document([("JPM", JPMORGAN, "a"), ("JPM", JPMORGAN, "b")]))
    assert [(r.ticker, r.cik) for r in records] == [("JPM", JPMORGAN)]


@pytest.mark.parametrize("body", [{}, []])
def test_an_empty_document_raises(edgar, agent, body):
    with pytest.raises(edgar.EdgarError, match="no"):
        tickers(edgar, body)


@pytest.mark.parametrize("body", ["a string", 42, {"0": "not an entry"}])
def test_a_document_of_another_shape_raises(edgar, agent, body):
    with pytest.raises(edgar.EdgarError):
        tickers(edgar, body)


# --- the request -------------------------------------------------------------------

def test_the_request_names_the_file_and_the_contact(edgar, agent):
    _, session = tickers(edgar, document())
    assert len(session.calls) == 1
    call = session.calls[0]
    assert call["url"] == edgar.TICKERS_URL == "https://www.sec.gov/files/company_tickers.json"
    assert call["headers"]["User-Agent"] == AGENT
    assert call["timeout"] == edgar.TIMEOUT_SECONDS


def test_an_http_failure_raises(edgar, agent):
    with pytest.raises(requests.HTTPError):
        tickers(edgar, {}, status=403)
