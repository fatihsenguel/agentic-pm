"""
The EDGAR provider held to expected_values.md Parts 12 and 13.

The provider fetches one company-facts document and returns the facts that
can be a fiscal year's figure, every vintage of each, with their provenance.
It picks no vintage, matches no year end and resolves no field: D28, D29's
"latest" and D30 are the assembler's. What it decides:

  D27  A duration is annual when `end - start` is 350 to 380 days, both
       included, whatever `fp` says. An instant is always kept.
  D29  A figure is filed on a 10-K, 10-Q or 8-K or an amendment of one of
       them; a fact on any other form is not a vintage and is not returned.

Plus the contract the reader rests on: the contact is EDGAR_USER_AGENT in
.env and nothing else, and the provider refuses to be built without it; the
document must be the company asked for; an HTTP failure is a failure, never
an empty list.

No network. The stand-in session serves a company-facts-shaped document
built from the committed fixtures, the pattern of
test_provider_names_its_source.py. D26, `(tag, start, end, accn)`, is not
held here: a check that no two returned facts share a key passed against
every wrong provider tried, and F6's two facts are shorter than a year, so
D27 drops them before the key can matter. The key is the table's, and its
schema test holds it.

The module is imported inside a fixture so that, before it exists, this
file is a list of errors and not an interrupted suite.
"""

import csv
import datetime as dt
import json
from decimal import Decimal
from pathlib import Path

import pytest
import requests


GOLDEN = Path(__file__).parent / "golden"
AGENT = "benchmark-suite test@example.invalid"

APPLE = 320193
ALPHABET = 1652044
JPMORGAN = 19617

# The one fixture row outside us-gaap (Part 13 C). Nothing else in the three
# fixtures is a dei fact.
DEI_TAGS = {"EntityCommonStockSharesOutstanding"}


def _rows(name):
    with open(GOLDEN / name, newline="") as fh:
        return [r for r in csv.DictReader(fh) if r["end"]]


def _fact(row):
    fact = {
        "end": row["end"],
        "val": json.loads(row["val"]),
        "accn": row["accn"],
        "fy": int(row["fy"]) if row["fy"] else None,
        "fp": row["fp"] or None,
        "form": row["form"],
        "filed": row["filed"],
    }
    if row["start"]:
        fact["start"] = row["start"]
    if row["frame"]:
        fact["frame"] = row["frame"]
    return fact


def document(cik, rows):
    """A company-facts document holding exactly `rows`, each fact once."""
    facts, seen = {}, set()
    for row in rows:
        key = (row["tag"], row["unit"], row["start"], row["end"], row["accn"], row["val"])
        if key in seen:
            continue
        seen.add(key)
        taxonomy = "dei" if row["tag"] in DEI_TAGS else "us-gaap"
        units = facts.setdefault(taxonomy, {}).setdefault(row["tag"], {"units": {}})["units"]
        units.setdefault(row["unit"], []).append(_fact(row))
    return {"cik": cik, "entityName": f"CIK {cik}", "facts": facts}


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


def annual_facts(edgar, cik, rows):
    session = _Session(document(cik, rows))
    return edgar.EdgarProvider(session=session).annual_facts(cik), session


def _as_row(fact):
    return {
        "tag": fact.tag, "unit": fact.unit,
        "start": fact.start.isoformat() if fact.start else "",
        "end": fact.end.isoformat(), "val": fact.value, "accn": fact.accn,
        "fy": "" if fact.fy is None else str(fact.fy), "fp": fact.fp or "",
        "form": fact.form, "filed": fact.filed.isoformat(), "frame": fact.frame or "",
    }


def _expected(row):
    keep = ("tag", "unit", "start", "end", "accn", "fy", "fp", "form", "filed", "frame")
    out = {k: row[k] for k in keep}
    out["val"] = Decimal(row["val"])
    return out


# --- Part 12 B and Part 13 B and C: every figure comes back as filed -----------

@pytest.mark.parametrize("fixture, section, cik", [
    ("edgar_facts_aapl.csv", "A", APPLE),
    ("edgar_facts_googl.csv", "B", ALPHABET),
    ("edgar_facts_jpm.csv", "C", JPMORGAN),
])
def test_every_field_row_comes_back_with_its_provenance(edgar, agent, fixture, section, cik):
    rows = _rows(fixture)
    facts, _ = annual_facts(edgar, cik, rows)
    returned = [_as_row(f) for f in facts]
    for row in rows:
        if row["section"] == section and row["field"]:
            assert _expected(row) in returned, row


def test_a_value_is_exact(edgar, agent):
    facts, _ = annual_facts(edgar, APPLE, _rows("edgar_facts_aapl.csv"))
    rates = {f.value for f in facts if f.tag == "EffectiveIncomeTaxRateContinuingOperations"}
    assert Decimal("0.241") in rates
    assert all(isinstance(f.value, Decimal) for f in facts)


# --- D27: the period decides, never the label -----------------------------------

def test_f2_a_quarter_under_fp_fy_is_not_returned(edgar, agent):
    facts, _ = annual_facts(edgar, APPLE, _rows("edgar_facts_aapl.csv"))
    assert not [f for f in facts if f.end == dt.date(2010, 12, 25)]


def test_f6_a_quarter_and_a_half_year_are_not_returned(edgar, agent):
    facts, _ = annual_facts(edgar, ALPHABET, _rows("edgar_facts_googl.csv"))
    assert not [f for f in facts if f.end == dt.date(2025, 6, 30) and f.start is not None]


def _synthetic(start, end, form="10-K", tag="Revenues"):
    return {"section": "", "field": "", "note": "", "tag": tag, "unit": "USD",
            "start": start, "end": end, "val": "1", "accn": f"0000000000-00-{start}{form}",
            "fy": "2025", "fp": "FY", "form": form, "filed": "2026-02-01", "frame": ""}


@pytest.mark.parametrize("days, kept", [(349, False), (350, True), (380, True), (381, False)])
def test_a_year_is_350_to_380_days(edgar, agent, days, kept):
    end = dt.date(2025, 12, 31)
    start = end - dt.timedelta(days=days)
    facts, _ = annual_facts(edgar, 1, [_synthetic(start.isoformat(), end.isoformat())])
    assert bool(facts) is kept


def test_an_instant_is_kept(edgar, agent):
    facts, _ = annual_facts(edgar, APPLE, _rows("edgar_facts_aapl.csv"))
    equity = {f.end for f in facts if f.tag == "StockholdersEquity"}
    assert dt.date(2024, 6, 29) in equity and dt.date(2024, 9, 28) in equity


# --- D29: every vintage, on the forms that file a figure --------------------------

def test_f1_every_vintage_comes_back(edgar, agent):
    facts, _ = annual_facts(edgar, APPLE, _rows("edgar_facts_aapl.csv"))
    fy2015 = [f for f in facts if f.tag == "NetIncomeLoss" and f.end == dt.date(2015, 9, 26)]
    assert sorted(f.fy for f in fy2015) == [2015, 2016, 2017]


def test_f3_the_amendment_and_the_original_both_come_back(edgar, agent):
    facts, _ = annual_facts(edgar, APPLE, _rows("edgar_facts_aapl.csv"))
    fy2008 = {(f.form, f.value) for f in facts
              if f.tag == "NetIncomeLoss" and f.end == dt.date(2008, 9, 27)}
    assert fy2008 == {("10-K", Decimal(4834000000)), ("10-K/A", Decimal(6119000000)),
                      ("10-K", Decimal(6119000000))}


def test_f10_a_proxy_statement_is_not_a_vintage(edgar, agent):
    facts, _ = annual_facts(edgar, JPMORGAN, _rows("edgar_facts_jpm.csv"))
    income = [f for f in facts if f.tag == "NetIncomeLoss"]
    assert {f.form for f in income} == {"10-K"}
    assert Decimal(57048000000) in {f.value for f in income}
    assert Decimal(57000000000) not in {f.value for f in income}


def test_f9_both_share_counts_come_back(edgar, agent):
    facts, _ = annual_facts(edgar, ALPHABET, _rows("edgar_facts_googl.csv"))
    counts = {f.value for f in facts
              if f.tag == "CommonStockSharesOutstanding" and f.end == dt.date(2021, 12, 31)}
    assert counts == {Decimal(662121000), Decimal(13242000000)}


@pytest.mark.parametrize("form, kept", [
    ("10-K", True), ("10-K/A", True), ("10-Q", True), ("10-Q/A", True),
    ("8-K", True), ("8-K/A", True), ("DEF 14A", False), ("424B2", False), ("S-8", False),
])
def test_the_forms_that_file_a_figure(edgar, agent, form, kept):
    facts, _ = annual_facts(edgar, 1, [_synthetic("2025-01-01", "2025-12-31", form=form)])
    assert bool(facts) is kept


# --- the taxonomy -----------------------------------------------------------------

def test_only_us_gaap_is_returned(edgar, agent):
    facts, _ = annual_facts(edgar, JPMORGAN, _rows("edgar_facts_jpm.csv"))
    assert not [f for f in facts if f.tag in DEI_TAGS]


def test_every_fact_names_the_provider(edgar, agent):
    facts, _ = annual_facts(edgar, APPLE, _rows("edgar_facts_aapl.csv"))
    assert facts and {f.source for f in facts} == {edgar.EdgarProvider.name}


# --- the request -------------------------------------------------------------------

def test_the_request_names_the_company_and_the_contact(edgar, agent):
    _, session = annual_facts(edgar, APPLE, _rows("edgar_facts_aapl.csv"))
    assert len(session.calls) == 1
    call = session.calls[0]
    assert call["url"] == "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
    assert call["headers"]["User-Agent"] == AGENT


@pytest.mark.parametrize("value", [None, "", "   "])
def test_no_contact_no_provider(edgar, monkeypatch, value):
    if value is None:
        monkeypatch.delenv("EDGAR_USER_AGENT", raising=False)
    else:
        monkeypatch.setenv("EDGAR_USER_AGENT", value)
    session = _Session(document(APPLE, _rows("edgar_facts_aapl.csv")))
    with pytest.raises(Exception, match="EDGAR_USER_AGENT"):
        edgar.EdgarProvider(session=session)
    assert session.calls == []


def test_a_document_for_another_company_raises(edgar, agent):
    session = _Session(document(ALPHABET, _rows("edgar_facts_googl.csv")))
    with pytest.raises(edgar.EdgarError, match="1652044"):
        edgar.EdgarProvider(session=session).annual_facts(APPLE)


def test_an_http_failure_raises(edgar, agent):
    session = _Session({}, status=403)
    with pytest.raises(requests.HTTPError):
        edgar.EdgarProvider(session=session).annual_facts(APPLE)
