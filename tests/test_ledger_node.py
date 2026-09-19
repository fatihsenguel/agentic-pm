"""
ledger_agent_node over a synthetic state: what it publishes, what it
fetches and when, and what it refuses (case 4.5; Part 14).

No LLM, no network. The filings provider is test_screening_node's
stand-in, answering from the record, and the date is pinned through
nodes.utc_today. Runs against conftest's copy of the database with every
row the stand-in writes cleared before and after.

What the node decides:

  - nothing is fetched for an open prediction or for an event; a figure
    prediction whose date has come has its candidate's facts read through
    the filings path the screen uses, under the seven-day interval
  - the block is the check's shape (tests/benchmark/run_cases.py): as_of,
    the ledger's path, one record per prediction in document order, the
    summary, and per candidate read the source and the pull instant
  - the filing's verdict on the fixture's Alphabet rows is Part 14 C's,
    the seam between the scorer's typed block and the reader's live one
  - a ticker the file lacks is an error, nothing published
  - no Decimal and no filed figure beyond the reported one reaches the
    block; the written score comes out as it went in, dates as strings
"""

import datetime as dt
from decimal import Decimal

import pytest

from agents import nodes
from agents.state import create_initial_state

from test_screening_node import provider, _watchlist, ALPHABET  # noqa: F401  the fixture


TODAY = dt.date(2026, 9, 18)
BLOCK_KEYS = {"as_of", "watchlist", "records", "summary", "figures"}
RECORD_KEYS = {"id", "candidate", "kind", "statement", "made_on", "due", "status", "metric",
               "bound", "value", "period", "score", "filing", "unscored", "agrees"}

SYNTHETIC = '''
[[candidate]]
id = "W-1"
ticker = "GOOGL"
name = "Alphabet"
currency = "USD"
status = "active"
thesis = "A thesis."

[[candidate.prediction]]
id = "W-1.1"
made_on = 2026-01-01
due = 2026-03-01
kind = "figure"
metric = "revenue"
bound = "min"
value = 400000000000
period = "FY2025"
statement = "Revenue of at least 400 billion for fiscal 2025."

[[candidate.prediction]]
id = "W-1.2"
made_on = 2026-01-01
due = 2026-03-01
kind = "event"
statement = "Something about the business."
'''

WRITTEN = '''
outcome = "The segment note shows it."
source = "10-K, segment note"
scored_on = 2026-03-02
result = "right"
'''


@pytest.fixture
def today(monkeypatch):
    def _pin(day):
        monkeypatch.setattr(nodes, "utc_today", lambda: day)
    _pin(TODAY)
    return _pin


def state():
    s = create_initial_state("How have my predictions done?", portfolio_id=3)
    s["agents_to_run"] = ["LedgerAgent"]
    s["router_decision"] = {"intent": "ledger", "parameters": {}}
    return s


def _block(out):
    return out["shared_data"]["ledger"]


def _walk(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from _walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk(v)
    else:
        yield value


# --- the committed ledger today: four open, nothing fetched ---------------------

async def test_today_four_open_and_nothing_fetched(provider, today):
    out = await nodes.ledger_agent_node(state())
    assert not out.get("errors")
    block = _block(out)
    assert set(block) == BLOCK_KEYS
    assert block["as_of"] == "2026-09-18"
    assert block["watchlist"].endswith("watchlist.toml")
    assert [r["id"] for r in block["records"]] == ["W-1.1", "W-1.2", "W-2.1", "W-2.2"]
    assert all(r["status"] == "open" for r in block["records"])
    assert block["summary"] == {"predictions": 4, "scored": 0, "due": 0, "open": 4}
    assert block["figures"] == {}
    assert provider.calls == [], "an open prediction fetches nothing"
    for r in block["records"]:
        assert set(r) == RECORD_KEYS
        assert r["filing"] is None and r["unscored"] is None and r["score"] is None
        assert r["due"] in ("2027-03-01", "2027-02-01") and r["made_on"] == "2026-09-10"


async def test_the_result_is_published_under_the_agent_too(provider, today):
    out = await nodes.ledger_agent_node(state())
    assert out["sub_results"]["LedgerAgent"]["ledger"] == _block(out)


# --- a due figure prediction: the facts are read, the verdict is Part 14 C's --------

async def test_a_due_figure_prediction_reads_the_facts_and_the_verdict_is_part_14_c(
        provider, today, monkeypatch, tmp_path):
    _watchlist(monkeypatch, tmp_path, SYNTHETIC)
    out = await nodes.ledger_agent_node(state())
    assert not out.get("errors")
    block = _block(out)
    assert provider.calls == ["tickers", ("filer", ALPHABET), ("annual_facts", ALPHABET)], \
        "the ticker file, the submissions document the filers row needs, then the facts"
    assert block["summary"] == {"predictions": 2, "scored": 0, "due": 2, "open": 0}
    figure, event = block["records"]
    assert figure["status"] == "due" and figure["score"] is None and figure["unscored"] is None
    assert figure["filing"] == {"reported": 402_836_000_000.0, "result": "right", "form": "10-K",
                                "accn": "0001652044-26-000018", "filed": "2026-02-05",
                                "source": provider.name}
    assert isinstance(figure["filing"]["reported"], float)
    assert event["status"] == "due" and event["filing"] is None
    assert "2026-03-01" in event["unscored"] and "outcome" in event["unscored"]
    assert set(block["figures"]) == {"W-1"}
    assert block["figures"]["W-1"]["ticker"] == "GOOGL" and block["figures"]["W-1"]["cik"] == ALPHABET
    assert block["figures"]["W-1"]["name"] == "Alphabet Inc."
    assert block["figures"]["W-1"]["source"] == provider.name
    assert block["figures"]["W-1"]["facts_as_of"].endswith("+00:00")


async def test_a_second_run_asks_the_provider_for_nothing(provider, today, monkeypatch, tmp_path):
    _watchlist(monkeypatch, tmp_path, SYNTHETIC)
    await nodes.ledger_agent_node(state())
    provider.calls.clear()
    out = await nodes.ledger_agent_node(state())
    assert not out.get("errors")
    assert provider.calls == []
    assert _block(out)["records"][0]["filing"]["result"] == "right"


async def test_before_the_due_date_nothing_is_fetched_though_the_period_is_filed(
        provider, today, monkeypatch, tmp_path):
    today(dt.date(2026, 2, 28))
    _watchlist(monkeypatch, tmp_path, SYNTHETIC)
    out = await nodes.ledger_agent_node(state())
    assert provider.calls == []
    assert all(r["status"] == "open" for r in _block(out)["records"])


async def test_no_decimal_and_no_filed_figure_beyond_the_reported_one_reaches_the_block(
        provider, today, monkeypatch, tmp_path):
    _watchlist(monkeypatch, tmp_path, SYNTHETIC)
    block = _block(await nodes.ledger_agent_node(state()))
    assert not any(isinstance(v, Decimal) for v in _walk(block))
    assert not any(isinstance(v, dt.date) for v in _walk(block))
    for r in block["records"]:
        assert "years" not in r and "cost_of_revenue" not in str(r)


# --- a written score comes out as it went in ------------------------------------------

async def test_a_written_score_is_reported_as_written_and_a_figure_gets_the_filing_beside_it(
        provider, today, monkeypatch, tmp_path):
    text = SYNTHETIC + WRITTEN
    text = text.replace('statement = "Revenue of at least 400 billion for fiscal 2025."\n',
                        'statement = "Revenue of at least 400 billion for fiscal 2025."\n'
                        'outcome = "Revenue 402,836 million."\nsource = "10-K"\n'
                        'scored_on = 2026-03-01\nresult = "right"\n')
    _watchlist(monkeypatch, tmp_path, text)
    block = _block(await nodes.ledger_agent_node(state()))
    figure, event = block["records"]
    assert block["summary"] == {"predictions": 2, "scored": 2, "due": 0, "open": 0}
    assert figure["score"] == {"outcome": "Revenue 402,836 million.", "source": "10-K",
                               "scored_on": "2026-03-01", "result": "right"}
    assert figure["filing"]["result"] == "right" and figure["agrees"] is True
    assert event["score"] == {"outcome": "The segment note shows it.", "source": "10-K, segment note",
                              "scored_on": "2026-03-02", "result": "right"}
    assert event["filing"] is None and event["agrees"] is None


# --- what the node refuses -------------------------------------------------------------

async def test_a_ticker_the_file_lacks_is_an_error_and_nothing_is_published(
        provider, today, monkeypatch, tmp_path):
    _watchlist(monkeypatch, tmp_path, SYNTHETIC.replace('ticker = "GOOGL"', 'ticker = "ZZZZ"'))
    out = await nodes.ledger_agent_node(state())
    assert out["errors"] and "ZZZZ" in out["errors"][0]
    assert "ledger" not in (out.get("shared_data") or {})


async def test_a_watchlist_that_does_not_load_is_an_error(provider, today, monkeypatch, tmp_path):
    _watchlist(monkeypatch, tmp_path, SYNTHETIC.replace('kind = "event"', 'kind = "guess"'))
    out = await nodes.ledger_agent_node(state())
    assert out["errors"] and "guess" in out["errors"][0]
