"""
research_agent_node over a synthetic state: what it publishes, what it
asks for and in what order, and what it refuses (cases 4.3 and 4.4;
decisions 60, 61, 65, 66, 67 and 68; expected_values.md Part 15 D47 to
D50, F and G, Part 16, Part 17).

No LLM, no network. The filings provider is test_screening_node's
stand-in, answering from the record, given the two methods the store asks,
the listing's row and tests/golden/edgar_document_goog_excerpt.htm. All
three models are stand-ins that record what they are sent. Runs against
conftest's copy of the database: Alphabet's facts are written through the
store from the fixture's rows, and its stored document and readings are
removed, before and after each test, so every row read here is one this
file wrote.

What the node decides:

  - it answers `asks` "thesis" and "position" and nothing else; it
    requires the screening block and answers on its subject, filer, as-of
    and source; the screen's stop does not stop it
  - a position question adds the weight and its source, my entry
    condition and the model's view, and **no outcome**: the gate holds
    the fourth input and composes it after this node
  - a thesis question adds none of them and pays for no view
  - the entry condition follows the screen's finding on its clause, and
    is not established when the screen reported none
  - the view's request carries the proposer's message and its own prompt;
    a view or a condition refused is recorded and the answer stands, and
    a candidate stating no weight is the node's error
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
VIEW = {"thesis_view": "stands", "reasons": ["1A.2"], "uncertainty": "inferred"}
# What a position question adds (case 4.3, Part 15 G, Part 17).
POSITION_KEYS = {"weight", "weight_source", "entry_condition", "entry_condition_stopped",
                 "judgement", "view_stopped", "entered"}
PASSES = {"clause": "PHI-4.1", "type": "margin_of_safety", "subject": "GOOGL",
          "status": "pass", "distance": -0.1}


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


class Viewer:
    """Answers one fixed view of the thesis and records every request."""

    id = "stand-in-viewer"

    def __init__(self, answer=VIEW, error=None):
        self.answer = answer
        self.error = error
        self.asked = []

    def view(self, prompt, schema, text):
        self.asked.append((prompt, schema, text))
        if self.error is not None:
            raise self.error
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
    chosen = {"reader": Reader(), "proposer": Proposer(), "viewer": Viewer()}
    monkeypatch.setattr(nodes, "reading_model", lambda: chosen["reader"])
    monkeypatch.setattr(nodes, "proposal_model", lambda: chosen["proposer"])
    monkeypatch.setattr(nodes, "view_model", lambda: chosen["viewer"])
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
    s["tool"] = asks
    s["inputs"] = {"ticker": "GOOGL"}
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


@pytest.mark.parametrize("asks", [None, "", "value", "sell"])
async def test_anything_but_the_two_asks_is_refused(edgar, models, asks):
    """Decision 66: extraction sets `asks` from a closed pattern, and the
    node answers the two it names. "position" left this list when case
    4.3's half was built; its own tests are below."""
    out = await nodes.research_agent_node(state(asks=asks))
    assert "research" not in out.get("shared_data", {})
    assert "it answers thesis and position" in out["errors"][-1]
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


# --- a position question: case 4.3's three inputs ---------------------------------

async def test_a_position_question_adds_the_three_and_no_outcome(edgar, models):
    """The block is the thesis question's plus the weight and its source,
    the entry condition and the judgement, each with its stop. **No
    outcome**: the gate holds the fourth input and composes it after this
    node (decision 68)."""
    out = await nodes.research_agent_node(state(asks="position"))
    assert not out.get("errors")
    research = _research(out)
    assert set(research) == BLOCK_KEYS | POSITION_KEYS
    assert research["asks"] == "position"
    assert "outcome" not in research


async def test_a_thesis_question_adds_none_of_them_and_asks_no_view(edgar, models):
    """A thesis question implies no position, so it neither carries the
    fields nor pays for the view's request."""
    research = _research(await nodes.research_agent_node(state()))
    assert set(research) & POSITION_KEYS == set()
    assert models["viewer"].asked == []


async def test_the_weight_and_its_source_are_the_entrys(edgar, models):
    """Decision 65, and the same function the gate reads them with, so
    require_gate holds the two equal."""
    research = _research(await nodes.research_agent_node(state(asks="position")))
    assert research["weight"] == 0.06
    assert research["weight_source"] == "W-1"


async def test_a_candidate_stating_no_weight_is_the_nodes_error(edgar, models, monkeypatch,
                                                                tmp_path):
    """A position question about a candidate whose size I have not decided
    cannot be answered: the weight is mine to state and nothing defaults
    it (decision 65)."""
    path = tmp_path / "watchlist.toml"
    path.write_text('[[candidate]]\nid = "W-1"\nticker = "GOOGL"\nname = "Alphabet"\n'
                    'currency = "USD"\nasset_class = "Equity"\n'
                    'sector = "Communication Services"\ninstrument_type = "share"\n'
                    'status = "active"\nthesis = "A thesis."\n'
                    '\n[candidate.entry_condition]\nkind = "valuation"\n'
                    'clause = "PHI-4.1"\n')
    monkeypatch.setattr(nodes, "WATCHLIST_PATH", str(path))
    out = await nodes.research_agent_node(state(asks="position"))
    assert "research" not in out.get("shared_data", {})
    assert "states no weight" in out["errors"][-1]


# --- the entry condition ----------------------------------------------------------

async def test_a_stopped_screen_leaves_the_condition_not_established(edgar, models):
    """The live shape on Alphabet: the screen stops at PHI-2.1 and reports
    a finding on no clause, so there is no verdict on PHI-4.1 to read
    (Part 17 I's note). None, and not False."""
    research = _research(await nodes.research_agent_node(state(asks="position")))
    assert research["entry_condition"] == {"kind": "valuation", "clause": "PHI-4.1",
                                           "met": None}
    assert research["entry_condition_stopped"] is None


@pytest.mark.parametrize("status, met", [("pass", True), ("fail", False)])
async def test_the_condition_follows_the_screens_finding_on_its_clause(edgar, models,
                                                                       status, met):
    screen = screened(stopped=None, findings=[{**PASSES, "status": status}])
    research = _research(await nodes.research_agent_node(state(asks="position",
                                                              screening=screen)))
    assert research["entry_condition"]["met"] is met


async def test_an_event_condition_is_stopped_and_the_answer_stands(edgar, models,
                                                                   monkeypatch, tmp_path):
    """The stop is recorded, not raised: the rest of the answer holds and
    the outcome reads the condition as not permitting."""
    path = tmp_path / "watchlist.toml"
    path.write_text('[[candidate]]\nid = "W-1"\nticker = "GOOGL"\nname = "Alphabet"\n'
                    'currency = "USD"\nasset_class = "Equity"\n'
                    'sector = "Communication Services"\ninstrument_type = "share"\n'
                    'status = "active"\nthesis = "A thesis."\nweight = 0.06\n'
                    '\n[candidate.entry_condition]\nkind = "event"\n'
                    'event = "the cloud segment turns a full-year profit"\n')
    monkeypatch.setattr(nodes, "WATCHLIST_PATH", str(path))
    out = await nodes.research_agent_node(state(asks="position"))
    assert not out.get("errors")
    research = _research(out)
    assert research["entry_condition"] is None
    assert "'event' is not one this reads" in research["entry_condition_stopped"]
    assert research["judgement"] == VIEW


# --- the model's view -------------------------------------------------------------

async def test_the_view_is_the_models_and_is_asked_once(edgar, models):
    research = _research(await nodes.research_agent_node(state(asks="position")))
    assert research["judgement"] == VIEW
    assert research["view_stopped"] is None
    assert len(models["viewer"].asked) == 1
    assert research["models"] == {"reading": "stand-in-reader",
                                  "proposal": "stand-in-proposer",
                                  "view": "stand-in-viewer"}


async def test_the_view_and_the_proposal_are_sent_one_message(edgar, models):
    """Both requests carry `proposer.message` over the same thesis and the
    same claims, so the view and the prediction rest on one string."""
    await nodes.research_agent_node(state(asks="position"))
    assert models["viewer"].asked[0][2] == models["proposer"].asked[0][2]
    assert models["viewer"].asked[0][0] != models["proposer"].asked[0][0]


async def test_a_refused_view_is_stopped_and_the_answer_stands(edgar, models):
    """Part 15 G: a view that could not be built leaves `view_stopped`
    beside no view; the answer prints and says what it could not
    establish, and check_4_3 reads the case as blocked."""
    models["viewer"] = Viewer(answer={"thesis_view": "holds", "reasons": [],
                                      "uncertainty": "stated"})
    out = await nodes.research_agent_node(state(asks="position"))
    assert not out.get("errors")
    research = _research(out)
    assert research["judgement"] is None
    assert "'holds' is not one of" in research["view_stopped"]
    assert research["predictions"] != []


async def test_the_models_own_refusal_is_recorded_and_not_raised(edgar, models):
    from agents.view_model import ViewModelError
    models["viewer"] = Viewer(error=ViewModelError("the model stopped on 'max_tokens'"))
    out = await nodes.research_agent_node(state(asks="position"))
    assert not out.get("errors")
    assert "max_tokens" in _research(out)["view_stopped"]


async def test_a_reason_that_is_no_claim_of_the_readings_refuses_the_view(edgar, models):
    models["viewer"] = Viewer(answer={**VIEW, "reasons": ["9.9"]})
    research = _research(await nodes.research_agent_node(state(asks="position")))
    assert research["judgement"] is None
    assert "'9.9' is no claim" in research["view_stopped"]


async def test_the_entered_predictions_are_the_files(edgar, models):
    """Decision 69: the case passes on a prediction entered in the ledger,
    cited by id. The block carries the file's rows so that the formatter
    reads no file; `predictions` beside them are the proposals."""
    research = _research(await nodes.research_agent_node(state(asks="position")))
    assert [p["id"] for p in research["entered"]] == ["W-1.1", "W-1.2"]
    assert [p["id"] for p in research["predictions"]] == ["W-1.3"]
    assert all(p.get("author") is None for p in research["entered"])
