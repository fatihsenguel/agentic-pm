"""
portfolio_tool.reader: a reading of one section, from the stored facts to
the record, held to expected_values.md Part 15 D47 and Part 16 D54 to D57.

Runs against the copy conftest.py makes of data/portfolio.db, with the
facts test_filed_documents.py writes for each test and removes after: Part
16 H's annual reports of Alphabet under a CIK no filer has, the latest its
FY2025 10-K. The provider is that file's stand-in, serving
tests/golden/edgar_document_goog_excerpt.htm; the model is a stand-in that
records what it is sent and supplies fixed claims whose quotes are in the
fixture's Item 1A. No network and no model.

The rules, each a test:

  - one request per section, carrying the section's fixed prompt, the
    schema and the section's text, and nothing of a question
  - the record names D54's filing, its fiscal year from the facts and the
    stored document's source, and carries no section text beyond quotes
  - a reading is cached under accession, section, model id and prompt
    version, and read again from the cache with no request; a new model or
    a changed prompt is a new reading
  - a reading `reading.record` refuses, a quote across a page break among
    them, and a model that fails leave no row
  - a stored reading that no longer passes is refused and not asked for again
  - facts that give the report two fiscal years refuse before any request
"""

import datetime as dt
import hashlib
import inspect
import json

import pytest

from portfolio_tool import reader, reading, sections
from portfolio_tool.database_setup import DocumentReading, FiledFact
from portfolio_tool.filing_text import text_of

from test_filed_documents import AS_OF, DOCUMENT, FILER, LATEST, NOBODY, StandIn, seeded


CLAIMS = [
    {"claim": "The company says its risks could harm its business and its results.",
     "quote": "which could harm our business, reputation, financial condition, and operating "
              "results", "uncertainty": "stated"},
    {"claim": "Artificial intelligence is described as competitive and costly to build.",
     "quote": "AI technology and services are highly competitive, rapidly evolving, and "
              "require significant investment", "uncertainty": "stated"},
    {"claim": "Other companies' patents could limit what the company may build.",
     "quote": "Other companies may also have (or in the future may obtain) patents or other "
              "proprietary rights", "uncertainty": "inferred"},
]


class Model:
    """Supplies fixed claims and records every request; `fail` raises."""

    def __init__(self, claims=CLAIMS, id="stand-in-model", fail=False):
        self.claims = claims
        self.id = id
        self.fail = fail
        self.requests = []

    def read(self, section, prompt, schema, text):
        self.requests.append((section, prompt, schema, text))
        if self.fail:
            raise RuntimeError("the stand-in model failed")
        return json.loads(json.dumps(self.claims))


session = pytest.fixture(seeded, name="session")


def _section(name="Item 1A"):
    return sections.section(text_of(DOCUMENT), name)


def _rows(session):
    return session.query(DocumentReading).filter(DocumentReading.accn == LATEST).all()


def _read(session, model, section="Item 1A", provider=None):
    return reader.read(session, provider or StandIn(), model, FILER, AS_OF, section)


# --- the request -------------------------------------------------------------

def test_one_request_carries_the_prompt_the_schema_and_the_section(session):
    model = Model()
    _read(session, model)
    assert model.requests == [("Item 1A", reader.PROMPTS["Item 1A"], reader.SCHEMA, _section())]


def test_the_read_takes_no_question():
    assert list(inspect.signature(reader.read).parameters) == \
        ["session", "provider", "model", "cik", "as_of", "section"]


def test_the_prompts_are_the_sections_read_and_share_their_rules():
    assert tuple(reader.PROMPTS) == reading.SECTIONS
    assert all(prompt.startswith(reader.COMMON) for prompt in reader.PROMPTS.values())
    assert len(set(reader.PROMPTS.values())) == 3
    assert "300 characters" in reader.COMMON and "twelve claims" in reader.COMMON


def test_the_schema_is_the_record_s_three_fields():
    item = reader.SCHEMA["properties"]["claims"]["items"]
    assert set(item["properties"]) == reading.SUPPLIED
    assert item["properties"]["uncertainty"]["enum"] == list(reading.UNCERTAINTIES)
    assert item["additionalProperties"] is False and reader.SCHEMA["additionalProperties"] is False


def test_the_prompt_version_is_the_hash_of_the_prompt_and_the_schema():
    signed = reader.PROMPTS["Item 7"] + json.dumps(reader.SCHEMA, sort_keys=True)
    assert reader.prompt_version("Item 7") == hashlib.sha256(signed.encode("utf-8")).hexdigest()
    assert len({reader.prompt_version(name) for name in reader.PROMPTS}) == 3


def test_a_section_not_read_is_refused_before_anything(session):
    model, provider = Model(), StandIn()
    with pytest.raises(reading.ReadingError, match="not a section that is read"):
        reader.read(session, provider, model, FILER, AS_OF, "Item 7A")
    assert model.requests == [] and provider.calls == []


# --- the record --------------------------------------------------------------

def test_the_record_names_the_filing_its_fiscal_year_and_its_source(session):
    record = _read(session, Model())
    assert (record.form, record.accn, record.filed, record.fiscal_year, record.source,
            record.section) == ("10-K", LATEST, dt.date(2026, 2, 5), "FY2025",
                                "EDGAR filing archive", "Item 1A")
    assert [c.id for c in record.claims] == ["1A.1", "1A.2", "1A.3"]
    assert [c.uncertainty for c in record.claims] == ["stated", "stated", "inferred"]


def test_the_record_carries_no_section_text_beyond_its_quotes(session):
    record = _read(session, Model())
    paragraph = _section().split("\n")[2]
    assert paragraph not in repr(record)
    assert sum(len(c.quote) for c in record.claims) <= reading.QUOTE_CAP * reading.CLAIMS_CAP


# --- the cache ----------------------------------------------------------------

def test_a_reading_is_stored_under_its_key_as_supplied(session):
    _read(session, Model())
    [row] = _rows(session)
    assert (row.accn, row.section, row.model, row.prompt_version) == \
        (LATEST, "Item 1A", "stand-in-model", reader.prompt_version("Item 1A"))
    assert json.loads(row.claims) == CLAIMS


def test_a_second_read_asks_nothing_and_gives_the_same_record(session):
    first = _read(session, Model())
    model, provider = Model(), StandIn()
    again = _read(session, model, provider=provider)
    assert model.requests == [] and provider.calls == []
    assert again == first


def test_the_document_is_fetched_once_for_every_section(session):
    provider = StandIn()
    _read(session, Model(), provider=provider)
    later = StandIn()
    item_7 = Model(claims=[{"claim": "Management discusses its results.",
                            "quote": "Please read the following discussion and analysis",
                            "uncertainty": "stated"}])
    _read(session, item_7, "Item 7", provider=later)
    assert [c[0] for c in provider.calls] == ["filing", "document"]
    assert later.calls == []
    assert item_7.requests == [("Item 7", reader.PROMPTS["Item 7"], reader.SCHEMA,
                                _section("Item 7"))]


def test_another_model_is_another_reading(session):
    _read(session, Model())
    other = Model(id="another-model")
    _read(session, other)
    assert len(other.requests) == 1
    assert sorted(row.model for row in _rows(session)) == ["another-model", "stand-in-model"]


def test_a_changed_prompt_is_another_reading(session, monkeypatch):
    _read(session, Model())
    monkeypatch.setitem(reader.PROMPTS, "Item 1A", reader.PROMPTS["Item 1A"] + " Be brief.")
    changed = Model()
    _read(session, changed)
    assert len(changed.requests) == 1
    assert len(_rows(session)) == 2


# --- refusals ------------------------------------------------------------------

def test_a_refused_reading_leaves_no_row_and_the_next_read_asks_again(session):
    digit = [dict(CLAIMS[0], claim="The company lists twelve risks in 2025.")]
    with pytest.raises(reading.ReadingError, match="a digit in the claim"):
        _read(session, Model(claims=digit))
    session.rollback()
    assert _rows(session) == []
    model = Model()
    _read(session, model)
    assert len(model.requests) == 1


def test_a_quote_across_a_page_break_refuses_the_reading(session):
    across = [{"claim": "Competitors may build similar products.",
               "quote": "other companies may develop AI products and technologies",
               "uncertainty": "stated"}]
    with pytest.raises(reading.ReadingError, match="not in the section"):
        _read(session, Model(claims=across))
    assert _rows(session) == []


def test_a_quote_with_the_page_break_in_it_is_the_sections(session):
    within = [{"claim": "Competitors may build similar products.",
               "quote": "other companies may develop 10. Table of Contents Alphabet Inc. AI "
                        "products and technologies", "uncertainty": "stated"}]
    assert _read(session, Model(claims=within)).claims[0].id == "1A.1"


def test_a_model_that_fails_leaves_no_row(session):
    with pytest.raises(RuntimeError):
        _read(session, Model(fail=True))
    session.rollback()
    assert _rows(session) == []


def test_a_stored_reading_that_no_longer_passes_is_refused_and_kept(session):
    _read(session, Model())
    [row] = _rows(session)
    row.claims = json.dumps([dict(CLAIMS[0], quote="a passage the section does not hold")])
    session.commit()
    model = Model()
    with pytest.raises(reading.ReadingError, match="not in the section"):
        _read(session, model)
    assert model.requests == []
    assert len(_rows(session)) == 1


def test_facts_with_two_fiscal_years_refuse_before_any_request(session):
    for fy in (2024, 2025):
        session.add(FiledFact(cik=NOBODY, tag=f"Revenues{fy}", unit="USD", start=None,
                              end=dt.date(2024, 12, 31), value="1",
                              accn="0009999999-25-000001", fy=fy, fp="FY", form="10-K",
                              filed=dt.date(2025, 2, 1), frame=None, source="stand-in"))
    session.commit()
    model, provider = Model(), StandIn()
    with pytest.raises(reader.filings.FiledFactsError, match=r"fiscal years \[2024, 2025\]"):
        reader.read(session, provider, model, NOBODY, AS_OF, "Item 1A")
    assert model.requests == [] and provider.calls == []
