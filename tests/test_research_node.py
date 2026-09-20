"""
research_agent_node over a synthetic state: what it publishes, what it
asks for and in what order, and what it refuses (case 4.4; decisions 60,
66 and 67; expected_values.md Part 15 D47 to D50 and F, Part 16).

No LLM, no network. The filings provider is test_screening_node's
stand-in, answering from the record, given the two methods the store asks,
the listing's row and tests/golden/edgar_document_goog_excerpt.htm. Both
models are stand-ins that record what they are sent. Runs against
conftest's copy of the database: Alphabet's facts are written through the
store from the fixture's rows, and its stored document and readings are
removed, before and after each test, so every row read here is one this
file wrote.

What the node decides:

  - it answers `asks` = "thesis" and nothing else; "position" is refused
    as not built; it requires the screening block and answers on its
    subject, filer, as-of and source; the screen's stop does not stop it
  - the thesis is the watchlist's, word for word
  - Items 1, 1A and 7 are read in order, one request each, and cached; the
    proposal is asked once with the proposer's message over those readings
  - the proposal is P-1 of Part 15 C under the next free id, its value
    from the figures the screen stored, its filing and source beside it
  - a refusal about one section leaves that section in `not_read` and the
    others read; a refusal about the filing leaves all three there with
    one reason, and the document is asked for once
  - a proposal refused is `proposal_stopped`, beside no prediction
  - any other failure is the node's error, nothing published
  - nothing is opened for writing
"""

import datetime as dt
import json

import pytest
import requests

from agents import nodes
from agents.state import create_initial_state
from portfolio_tool import proposer
from portfolio_tool.database_setup import DocumentReading, FiledDocument, get_session
from portfolio_tool.filings import update_filed_facts, update_filer

from test_filed_documents import DOCUMENT, LATEST, _listed
from test_reader import CLAIMS as ITEM_1A
from test_screening_node import ALPHABET, provider  # noqa: F401  the fixture


AS_OF = "2026-09-18"
BLOCK_KEYS = {"asks", "subject", "as_of", "thesis", "models", "readings", "not_read",
              "predictions", "proposal_stopped"}
CLAIMS = {
    "Item 1": [{"claim": "The company tells investors about its results through its website.",
                "quote": "Our investor relations website also provides notifications of news "
                         "or announcements regarding our financial performance",
                "uncertainty": "stated"}],
    "Item 1A": ITEM_1A,
    "Item 7": [{"claim": "Management asks that its discussion be read with the risk factors.",
                "quote": "Please read the following discussion and analysis",
                "uncertainty": "stated"}],
}
FIGURE = {"kind": "figure", "metric": "gross_margin", "bound": "min", "reasons": ["1A.2"]}


class Reader:
    """Supplies each section's fixed claims and records every request;
    `refuse` maps a section to the claims that make the record refuse it,
    `fail` raises something no refusal names."""

    id = "stand-in-reader"

    def __init__(self, refuse=None, fail=False):
        self.refuse = refuse or {}
        self.fail = fail
        self.requests = []

    def read(self, section, prompt, schema, text):
        self.requests.append(section)
        if self.fail:
            raise RuntimeError("the stand-in reader failed")
        return json.loads(json.dumps(self.refuse.get(section, CLAIMS[section])))


class Proposer:
    """Answers one fixed prediction and records every request."""

    id = "stand-in-proposer"

    def __init__(self, answer=FIGURE):
        self.answer = answer
        self.asked = []

    def propose(self, prompt, schema, text):
        self.asked.append((prompt, schema, text))
        return dict(self.answer)


def _clear_documents():
    session = get_session()
    try:
        session.query(DocumentReading).filter(DocumentReading.accn == LATEST).delete()
        session.query(FiledDocument).filter(FiledDocument.accn == LATEST).delete()
        session.commit()
    finally:
        session.close()


@pytest.fixture
def edgar(provider):
    """The screen's stand-in with the listing's row and the document, and
    Alphabet's facts stored through it as the screen stores them."""
    provider.fail = None

    def filing(cik, accn):
        provider.calls.append(("filing", cik, accn))
        return _listed()

    def document(cik, accn, name):
        provider.calls.append(("document", cik, accn, name))
        if provider.fail == "document":
            raise requests.HTTPError("503 from the stand-in")
        return DOCUMENT

    provider.filing, provider.document = filing, document
    _clear_documents()
    session = get_session()
    try:
        update_filer(session, provider, ALPHABET)
        update_filed_facts(session, provider, ALPHABET)
    finally:
        session.close()
    provider.calls.clear()
    yield provider
    _clear_documents()


@pytest.fixture
def models(monkeypatch):
    chosen = {"reader": Reader(), "proposer": Proposer()}
    monkeypatch.setattr(nodes, "reading_model", lambda: chosen["reader"])
    monkeypatch.setattr(nodes, "proposal_model", lambda: chosen["proposer"])
    return chosen


def screened(**changes):
    block = {"subject": {"ticker": "GOOGL", "cik": ALPHABET, "name": "Alphabet Inc."},
             "as_of": AS_OF, "source": "stand-in filings",
             "stopped": {"clause": "PHI-2.1", "reason": "the check stopped at FY2021"}}
    return {**block, **changes}


def state(asks="thesis", screening=None):
    s = create_initial_state("What has to be true in a year for my GOOGL thesis to be right?",
                             portfolio_id=3)
    s["agents_to_run"] = ["ResearchAgent"]
    s["router_decision"] = {"intent": "research",
                            "parameters": {"tickers": ["GOOGL"], "asks": asks}}
    s["shared_data"] = {"screening": screened() if screening is None else screening}
    return s


def _research(out):
    return out["shared_data"]["research"]


def _committed_thesis():
    import tomli
    with open("watchlist.toml", "rb") as f:
        return {c["ticker"]: c["thesis"] for c in tomli.load(f)["candidate"]}["GOOGL"]


# --- the block -------------------------------------------------------------------------

async def test_the_block_is_the_checks_shape(edgar, models):
    out = await nodes.research_agent_node(state())
    assert not out.get("errors")
    research = _research(out)
    assert set(research) == BLOCK_KEYS
    assert research["asks"] == "thesis"
    assert research["subject"] == {"ticker": "GOOGL", "cik": ALPHABET, "name": "Alphabet Inc.",
                                   "candidate": "W-1"}
    assert research["as_of"] == AS_OF
    assert research["models"] == {"reading": "stand-in-reader", "proposal": "stand-in-proposer"}
    assert research["not_read"] == [] and research["proposal_stopped"] is None
    assert out["sub_results"]["ResearchAgent"]["research"] == research


async def test_the_thesis_is_the_watchlists_word_for_word(edgar, models):
    research = _research(await nodes.research_agent_node(state()))
    assert research["thesis"] == {"candidate": "W-1", "text": _committed_thesis()}


async def test_a_thesis_is_published_as_written(edgar, models, monkeypatch, tmp_path):
    path = tmp_path / "watchlist.toml"
    path.write_text('[[candidate]]\nid = "W-1"\nticker = "GOOGL"\nname = "Alphabet"\n'
                    'currency = "USD"\nasset_class = "Equity"\n'
                    'sector = "Communication Services"\ninstrument_type = "share"\n'
                    'status = "active"\nthesis = """\n  A thesis.  \n"""\n'
                    '\n[candidate.entry_condition]\nkind = "valuation"\n'
                    'clause = "PHI-4.1"\n')
    monkeypatch.setattr(nodes, "WATCHLIST_PATH", str(path))
    research = _research(await nodes.research_agent_node(state()))
    assert research["thesis"] == {"candidate": "W-1", "text": "  A thesis.  \n"}
    assert research["predictions"][0]["id"] == "W-1.1"


async def test_the_three_sections_are_read_in_order_as_records(edgar, models):
    research = _research(await nodes.research_agent_node(state()))
    assert models["reader"].requests == ["Item 1", "Item 1A", "Item 7"]
    assert [r["section"] for r in research["readings"]] == ["Item 1", "Item 1A", "Item 7"]
    for r in research["readings"]:
        assert (r["form"], r["accn"], r["filed"], r["fiscal_year"], r["source"]) == (
            "10-K", LATEST, "2026-02-05", "FY2025", "EDGAR filing archive")
    assert [c["id"] for c in research["readings"][1]["claims"]] == ["1A.1", "1A.2", "1A.3"]
    assert set(research["readings"][0]["claims"][0]) == {"id", "claim", "quote", "uncertainty"}
    assert [c[0] for c in edgar.calls] == ["filing", "document"]


async def test_the_proposal_is_asked_once_over_the_readings(edgar, models):
    research = _research(await nodes.research_agent_node(state()))
    [(prompt, schema, text)] = models["proposer"].asked
    assert (prompt, schema) == (proposer.PROMPT, proposer.SCHEMA)
    assert text.startswith("Thesis:\n" + _committed_thesis().strip() + "\n\nClaims:\n")
    for reading in research["readings"]:
        for c in reading["claims"]:
            assert f"[{c['id']}] ({c['uncertainty']}) {c['claim']}" in text


async def test_the_proposal_is_p_1_on_the_figures_the_screen_stored(edgar, models):
    [p] = _research(await nodes.research_agent_node(state()))["predictions"]
    assert (p["id"], p["candidate"], p["author"], p["status"], p["kind"]) == (
        "W-1.3", "W-1", "system", "proposed", "figure")
    assert (p["made_on"], p["due"], p["period"]) == (AS_OF, "2027-09-18", "FY2026")
    assert (p["metric"], p["bound"], p["value"]) == ("gross_margin", "min", 0.5965)
    assert p["statement"] == ("By 18 September 2027 Alphabet will have reported a gross margin "
                              "for fiscal 2026 of at least 59.65%.")
    assert p["reasons"] == ["1A.2"]
    assert p["source"] == {"form": "10-K", "accn": LATEST, "filed": "2026-02-05",
                           "source": "stand-in filings"}


async def test_a_second_run_reads_from_the_cache_and_proposes_again(edgar, models):
    await nodes.research_agent_node(state())
    again = {"reader": Reader(), "proposer": Proposer()}
    models.update(again)
    edgar.calls.clear()
    research = _research(await nodes.research_agent_node(state()))
    assert again["reader"].requests == [] and edgar.calls == []
    assert len(again["proposer"].asked) == 1
    assert len(research["readings"]) == 3


async def test_the_screens_stop_does_not_stop_the_research(edgar, models):
    out = await nodes.research_agent_node(state(screening=screened(stopped=None)))
    stopped = await nodes.research_agent_node(state())
    assert _research(out)["predictions"] == _research(stopped)["predictions"]


# --- refusals ------------------------------------------------------------------------

async def test_a_section_refused_is_not_read_and_the_rest_are(edgar, models):
    digit = [dict(ITEM_1A[0], claim="The company lists twelve risks in 2025.")]
    models["reader"] = Reader(refuse={"Item 1A": digit})
    models["proposer"] = Proposer(dict(FIGURE, reasons=["1.1"]))
    research = _research(await nodes.research_agent_node(state()))
    assert models["reader"].requests == ["Item 1", "Item 1A", "Item 7"]
    assert [r["section"] for r in research["readings"]] == ["Item 1", "Item 7"]
    [entry] = research["not_read"]
    assert entry["section"] == "Item 1A" and "a digit in the claim" in entry["reason"]
    assert len(research["predictions"]) == 1


async def test_a_filing_refused_leaves_all_three_unread_and_asks_once(edgar, models):
    edgar.fail = "document"
    research = _research(await nodes.research_agent_node(state()))
    assert [c[0] for c in edgar.calls] == ["filing", "document"]
    assert models["reader"].requests == []
    assert [e["section"] for e in research["not_read"]] == ["Item 1", "Item 1A", "Item 7"]
    assert len({e["reason"] for e in research["not_read"]}) == 1
    assert "503 from the stand-in" in research["not_read"][0]["reason"]
    assert research["readings"] == [] and research["predictions"] == []
    assert "no claim was read" in research["proposal_stopped"]
    assert models["proposer"].asked == []


async def test_a_proposal_refused_is_published_as_stopped(edgar, models):
    models["proposer"] = Proposer(dict(FIGURE, metric="return_on_invested_capital"))
    out = await nodes.research_agent_node(state())
    research = _research(out)
    assert not out.get("errors")
    assert research["predictions"] == []
    assert "return_on_invested_capital" in research["proposal_stopped"]
    assert len(research["readings"]) == 3 and len(models["proposer"].asked) == 1


@pytest.mark.parametrize("asks, reason", [("position", "what is missing is this node's half"),
                                          (None, "it answers 'thesis'")])
async def test_anything_but_a_thesis_question_is_refused(edgar, models, asks, reason):
    out = await nodes.research_agent_node(state(asks=asks))
    assert "research" not in out.get("shared_data", {})
    assert reason in out["errors"][-1]
    assert models["reader"].requests == [] and edgar.calls == []


async def test_no_screen_is_an_error_and_nothing_is_asked(edgar, models):
    s = state()
    s["shared_data"] = {}
    out = await nodes.research_agent_node(s)
    assert "research" not in out.get("shared_data", {})
    assert "requires the screen" in out["errors"][-1]
    assert models["reader"].requests == [] and edgar.calls == []


async def test_a_ticker_not_on_the_watchlist_is_an_error(edgar, models):
    screening = screened(subject={"ticker": "JPM", "cik": 19617, "name": "JPMorgan"})
    out = await nodes.research_agent_node(state(screening=screening))
    assert "research" not in out.get("shared_data", {})
    assert "JPM is not on the watchlist" in out["errors"][-1]


async def test_a_failure_no_refusal_names_is_the_nodes_error(edgar, models):
    models["reader"] = Reader(fail=True)
    out = await nodes.research_agent_node(state())
    assert "research" not in out.get("shared_data", {})
    assert "the stand-in reader failed" in out["errors"][-1]
    assert models["proposer"].asked == []


async def test_nothing_is_opened_for_writing(edgar, models, monkeypatch):
    import builtins
    modes = []
    real = builtins.open

    def recording(file, mode="r", *args, **kwargs):
        modes.append((str(file), mode))
        return real(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", recording)
    await nodes.research_agent_node(state())
    assert [m for m in modes if set(m[1]) & set("wax+")] == []
