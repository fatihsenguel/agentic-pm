"""
screening_agent_node over a synthetic state: what it publishes, the order
it fetches in, and what it refuses.

No LLM, no network. The provider is a stand-in answering the three EDGAR
methods from the record: the ticker pairs Parts 12 and 13 C name, the
filers of edgar_submissions.csv, and the facts of edgar_facts_googl.csv and
edgar_facts_jpm.csv through the real provider over a stand-in session, the
way test_filed_years.py feeds the reader. Runs against conftest's copy of
the database, with every row it writes cleared before and after.

What the node decides (decision 29):

  - the plan brings one ticker, extraction's; none or two is an error, and
    nothing is fetched
  - the order of calls: the ticker file, then the submissions document,
    then the exclusion on the code alone, and only past it the company
    facts, so an excluded company's figures are never asked for
  - the block is the checks' shape (tests/benchmark/run_cases.py): the
    philosophy and its statements, the subject, the as-of, the code with its
    description and its as-of, the years read as dates and nothing else,
    the findings, `stopped`, the source and the facts' pull date; no figure
  - a ScreeningError is a stop, published with its clause, not an error
  - the philosophy is the committed file (decision 30); every pull date is
    the stored UTC instant with its offset written into it
"""

import csv
import datetime as dt
from pathlib import Path

import pytest

from agents import nodes
from agents.state import create_initial_state
from portfolio_tool.database_setup import (
    FiledFact, FiledFetchMetadata, Filer, TickerCik, get_session,
)
from portfolio_tool.provider_models import ProviderFiler, ProviderTicker

from test_filed_years import _rows, facts_for


GOLDEN = Path(__file__).parent / "golden"
APPLE, ALPHABET, JPMORGAN = 320193, 1652044, 19617
BENCHMARK_PORTFOLIO = 3

BLOCK_KEYS = {"philosophy", "statements", "subject", "as_of", "sic", "sic_description",
              "sic_as_of", "years", "findings", "stopped", "source", "facts_as_of"}


def _filers():
    with open(GOLDEN / "edgar_submissions.csv", newline="") as fh:
        rows = {int(r["cik"]): r for r in csv.DictReader(fh)}
    return {cik: ProviderFiler(cik=cik, name=rows[cik]["name"], sic=rows[cik]["sic"],
                               sic_description=rows[cik]["sic_description"])
            for cik in (ALPHABET, JPMORGAN)}


class StandIn:
    """The three EDGAR methods from the record, every call recorded."""

    name = "stand-in filings"

    def __init__(self, facts, filers):
        self.facts, self.filers = facts, filers
        self.calls = []

    def tickers(self):
        self.calls.append("tickers")
        return [ProviderTicker("AAPL", APPLE), ProviderTicker("GOOGL", ALPHABET),
                ProviderTicker("GOOG", ALPHABET), ProviderTicker("JPM", JPMORGAN)]

    def filer(self, cik):
        self.calls.append(("filer", cik))
        return self.filers[cik]

    def annual_facts(self, cik):
        self.calls.append(("annual_facts", cik))
        return self.facts[cik]


def _clear():
    session = get_session()
    try:
        for model in (FiledFact, FiledFetchMetadata, Filer):
            session.query(model).filter(model.cik.in_([ALPHABET, JPMORGAN])).delete(
                synchronize_session=False)
        session.query(TickerCik).delete()
        session.commit()
    finally:
        session.close()


@pytest.fixture
def provider(monkeypatch):
    facts = {
        ALPHABET: facts_for(ALPHABET, _rows("edgar_facts_googl.csv"), monkeypatch),
        JPMORGAN: facts_for(JPMORGAN, _rows("edgar_facts_jpm.csv"), monkeypatch),
    }
    stand_in = StandIn(facts, _filers())
    monkeypatch.setattr(nodes, "edgar_provider", lambda: stand_in)
    _clear()
    yield stand_in
    _clear()


def state_with(tickers, portfolio_id=BENCHMARK_PORTFOLIO):
    state = create_initial_state("Does it clear my philosophy?", portfolio_id=portfolio_id)
    state["agents_to_run"] = ["ScreeningAgent"]
    state["router_decision"] = {"intent": "research", "parameters": {"tickers": list(tickers)}}
    return state


def _block(out):
    return out["shared_data"]["screening"]


# --- a bank: decided on the code, no figure fetched --------------------------------

async def test_a_bank_is_excluded_before_its_facts_are_fetched(provider):
    out = await nodes.screening_agent_node(state_with(["JPM"]))
    assert out.get("errors") is None, out.get("errors")
    assert provider.calls == ["tickers", ("filer", JPMORGAN)]

    block = _block(out)
    assert set(block) == BLOCK_KEYS
    assert block["subject"] == {"ticker": "JPM", "cik": JPMORGAN, "name": "JPMORGAN CHASE & CO"}
    assert (block["sic"], block["sic_description"]) == ("6021", "National Commercial Banks")
    [finding] = block["findings"]
    assert (finding["clause"], finding["status"], finding["sic"], finding["subject"]) == \
        ("PHI-3.2", "excluded", "6021", "JPM")
    assert block["years"] == {}
    assert block["stopped"] is None
    assert block["facts_as_of"] is None
    assert out["sub_results"]["ScreeningAgent"]["screening"] is block
    assert out["sub_results"]["ScreeningAgent"]["success"] is True
    assert out["agents_to_run"] == []


async def test_the_block_carries_the_philosophy_and_exactly_its_statements(provider):
    block = _block(await nodes.screening_agent_node(state_with(["JPM"])))
    assert len(block["philosophy"]) == 17
    assert {c for c, e in block["philosophy"].items() if e["type"] == "statement"} == \
        {s["clause"] for s in block["statements"]}
    assert block["philosophy"]["PHI-3.2"]["type"] == "excluded_industry"
    assert block["philosophy"]["PHI-3.2"]["text"].startswith("A company whose SIC code")


async def test_the_dates_are_on_one_clock_with_the_offset_written_in(provider):
    """The check's as-of is the UTC date of the run; the code's as-of is the
    filers row's pull instant, UTC, with +00:00 in the string so that the
    clock is data and not the formatter's word (decision 29, the clock)."""
    out = await nodes.screening_agent_node(state_with(["JPM"]))
    block = _block(out)
    assert block["as_of"] == dt.datetime.utcnow().date().isoformat()
    session = get_session()
    try:
        pulled = session.get(Filer, JPMORGAN).pulled_at
    finally:
        session.close()
    assert block["sic_as_of"] == pulled.replace(tzinfo=dt.timezone.utc).isoformat()
    assert block["sic_as_of"].endswith("+00:00")
    assert block["source"] == "stand-in filings"


# --- a company the philosophy screens: the facts are fetched and the check runs ------

async def test_alphabet_is_fetched_and_the_check_stops_on_a_missing_figure(provider):
    """Alphabet files no gross profit and no combined D&A, and its FY2021 and
    FY2022 non-current debt only under a wider tag (Part 13 B), so the check
    stops (PHI-1.2, D25) on the first clause in philosophy order whose metric
    a year lacks. A stop is published, not raised: the answer says where the
    check stopped and reports no verdict."""
    out = await nodes.screening_agent_node(state_with(["GOOGL"]))
    assert out.get("errors") is None, out.get("errors")
    assert provider.calls == ["tickers", ("filer", ALPHABET), ("annual_facts", ALPHABET)]

    block = _block(out)
    assert block["subject"] == {"ticker": "GOOGL", "cik": ALPHABET, "name": "Alphabet Inc."}
    assert block["sic"] == "7370"
    assert block["findings"] == []
    assert block["stopped"]["clause"] == "PHI-2.1"
    assert "FY2021" in block["stopped"]["reason"]
    assert sorted(block["years"]) == ["FY2021", "FY2022", "FY2023", "FY2024", "FY2025"]
    assert block["facts_as_of"] is not None and block["facts_as_of"].endswith("+00:00")


async def test_the_years_carry_dates_and_no_figure(provider):
    block = _block(await nodes.screening_agent_node(state_with(["GOOGL"])))
    for label, dates in block["years"].items():
        assert set(dates) == {"ends", "filed"}, label
        for value in dates.values():
            dt.date.fromisoformat(value)
    assert block["years"]["FY2025"] == {"ends": "2025-12-31", "filed": "2026-02-05"}


async def test_a_second_run_asks_the_provider_for_nothing(provider):
    await nodes.screening_agent_node(state_with(["JPM"]))
    provider.calls.clear()
    out = await nodes.screening_agent_node(state_with(["JPM"]))
    assert out.get("errors") is None
    assert provider.calls == []


# --- refusals ----------------------------------------------------------------------

@pytest.mark.parametrize("tickers", [[], ["JPM", "GOOGL"]])
async def test_none_or_two_tickers_is_an_error_and_nothing_is_fetched(provider, tickers):
    out = await nodes.screening_agent_node(state_with(tickers))
    assert "screening" not in (out.get("shared_data") or {})
    [error] = out["errors"]
    assert "one company" in error
    assert provider.calls == []


async def test_a_ticker_the_file_does_not_list_is_an_error(provider):
    out = await nodes.screening_agent_node(state_with(["ZZZZ"]))
    assert "screening" not in (out.get("shared_data") or {})
    [error] = out["errors"]
    assert "ZZZZ" in error and "lists no filer" in error
    assert provider.calls == ["tickers"]


async def test_a_code_edgar_does_not_state_is_a_stop_naming_phi_3_2(provider):
    provider.filers[JPMORGAN] = ProviderFiler(cik=JPMORGAN, name="JPMORGAN CHASE & CO",
                                              sic=None, sic_description=None)
    out = await nodes.screening_agent_node(state_with(["JPM"]))
    assert out.get("errors") is None, out.get("errors")
    block = _block(out)
    assert block["findings"] == []
    assert block["stopped"]["clause"] == "PHI-3.2"
    assert block["sic"] is None
    assert ("annual_facts", JPMORGAN) not in provider.calls
