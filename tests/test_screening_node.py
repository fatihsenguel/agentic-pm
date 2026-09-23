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

And, for case 4.2 (Part 11, decisions 57 and 48 item 7):

  - past the exclusion the node puts the provider's name on the block as
    its source, gathers the five assumptions, three from PHI-4.1's
    parameters and two from the watchlist entry, calls valuation_range and
    publishes D40's record as `valuation`; the ends on the fixture's
    Alphabet rows are Part 11 C's, since the seam between pytest's typed
    blocks and the live block is the node's assembly
  - the price is the last close the existing price path stores for the
    ticker the question named, on an assets row the node creates from
    what it knows and nothing more; published as `price` with its date
    and source, the row's figure Part 9 C's
  - a candidate stating no growth pair, or a ticker not on the watchlist,
    is a `valuation_stopped` naming why, never a default; a ticker neither
    held nor on the watchlist is a `price_stopped`; both stops are
    published beside the screen, which still runs
  - an excluded company gets neither a price nor a range: its figures
    are never asked for, and neither is its close
"""

import csv
import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from agents import nodes
from agents.state import create_initial_state
from portfolio_tool.database_setup import (
    Asset, AssetFetchMetadata, DailyPrice, FiledFact, FiledFetchMetadata, Filer, TickerCik,
    get_session,
)
from portfolio_tool.provider_models import ProviderFiler, ProviderPriceData, ProviderTicker

from test_filed_years import _rows, facts_for


GOLDEN = Path(__file__).parent / "golden"
APPLE, ALPHABET, JPMORGAN = 320193, 1652044, 19617
BENCHMARK_PORTFOLIO = 3

BLOCK_KEYS = {"philosophy", "statements", "subject", "as_of", "sic", "sic_description",
              "sic_as_of", "years", "findings", "stopped", "source", "facts_as_of",
              "price", "price_stopped", "valuation", "valuation_stopped"}
# D40: the record carries the ends, the year with its dates, the source and
# the assumptions, and no filed figure.
RECORD_KEYS = {"low", "high", "as_of", "year", "ends", "filed", "source", "assumptions"}
# Part 9 C: GOOGL's closes as the exchange printed them.
PART_9_C = {dt.date(2026, 9, 15): "344.98", dt.date(2026, 9, 16): "342.87"}


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


class PriceStandIn:
    """The price provider's one method the node's path calls, answering
    Part 9 C's rows for GOOGL and nothing for anyone else."""

    name = "stand-in prices"

    def __init__(self):
        self.calls = []

    def get_daily_prices(self, ticker, start, end):
        self.calls.append((ticker, start, end))
        return [ProviderPriceData(date=day, open=Decimal(close), high=Decimal(close),
                                  low=Decimal(close), close=Decimal(close), volume=1)
                for day, close in PART_9_C.items() if start <= day < end and ticker == "GOOGL"]


def _clear():
    session = get_session()
    try:
        for model in (FiledFact, FiledFetchMetadata, Filer):
            session.query(model).filter(model.cik.in_([ALPHABET, JPMORGAN])).delete(
                synchronize_session=False)
        session.query(TickerCik).delete()
        # The candidate's assets row is the node's to create; JPMorgan's is a
        # holding and stays.
        for asset in session.query(Asset).filter(Asset.ticker == "GOOGL").all():
            session.query(DailyPrice).filter(DailyPrice.asset_id == asset.id).delete()
            session.query(AssetFetchMetadata).filter(
                AssetFetchMetadata.asset_id == asset.id).delete()
            session.delete(asset)
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
    prices = PriceStandIn()
    monkeypatch.setattr(nodes, "price_provider", lambda: prices)
    stand_in.prices = prices
    _clear()
    yield stand_in
    _clear()


def _watchlist(monkeypatch, tmp_path, text):
    path = tmp_path / "watchlist.toml"
    path.write_text(text)
    monkeypatch.setattr(nodes, "WATCHLIST_PATH", str(path))


W1_WITHOUT_A_PAIR = '''
[[candidate]]
id = "W-1"
ticker = "GOOGL"
name = "Alphabet"
currency = "USD"
asset_class = "Equity"
sector = "Communication Services"
instrument_type = "share"
status = "active"
thesis = "A thesis."

[candidate.entry_condition]
kind = "valuation"
clause = "PHI-4.1"
'''


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
    assert (block["price"], block["price_stopped"]) == (None, None)
    assert (block["valuation"], block["valuation_stopped"]) == (None, None)
    assert provider.prices.calls == []
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
    """Alphabet files no combined D&A, and its FY2021 and FY2022 non-current
    debt only under a wider tag (Part 13 B, D36), so the check stops
    (PHI-1.2, D25) on the first clause in philosophy order whose metric a
    year lacks: PHI-2.1 at FY2021. Gross margin no longer stops it, since
    decision 48 reads cost of revenue, which Alphabet files. A stop is
    published, not raised: the answer says where the check stopped and
    reports no verdict."""
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


# --- case 4.2: the range and the price, beside the screen ----------------------------

async def test_the_range_on_the_fixture_is_part_11_c(provider):
    """The seam pytest's typed blocks do not see: the node assembles the
    block from stored rows and the assumptions from two documents, and the
    ends come out as Part 11 C computed them by hand. The screen still
    stops at PHI-2.1; the range does not depend on it."""
    out = await nodes.screening_agent_node(state_with(["GOOGL"]))
    assert out.get("errors") is None, out.get("errors")
    block = _block(out)
    assert set(block) == BLOCK_KEYS
    record = block["valuation"]
    assert set(record) == RECORD_KEYS
    assert (round(record["low"], 2), round(record["high"], 2)) == (129.39, 205.62)
    assert (record["year"], record["ends"], record["filed"]) == \
        ("FY2025", "2025-12-31", "2026-02-05")
    assert record["as_of"] == block["as_of"]
    assert record["source"] == "stand-in filings"
    assert record["assumptions"] == {
        "required_return": {"value": 0.09, "source": "PHI-4.1"},
        "terminal_growth": {"value": 0.03, "source": "PHI-4.1"},
        "horizon_years": {"value": 10, "source": "PHI-4.1"},
        "growth_low": {"value": 0.06, "source": "W-1"},
        "growth_high": {"value": 0.12, "source": "W-1"},
    }
    assert block["valuation_stopped"] is None
    assert block["stopped"]["clause"] == "PHI-2.1"


async def test_the_price_is_the_last_stored_close_on_a_row_the_node_creates(provider, monkeypatch):
    """Decision 57: the existing price path, on an assets row made from the
    ticker asked, EDGAR's name and the watchlist entry's currency, nothing
    else filled; the last stored close with its date and its source. The
    figure is Part 9 C's. The date the node runs at is pinned, so that the
    seven-day window it asks the provider for is the same on every day the
    test runs (KNOWN_GAPS, "A screening-node test is pinned to the
    calendar")."""
    monkeypatch.setattr(nodes, "utc_today", lambda: dt.date(2026, 9, 22))
    out = await nodes.screening_agent_node(state_with(["GOOGL"]))
    block = _block(out)
    assert block["price"] == {"ticker": "GOOGL", "value": 342.87, "as_of": "2026-09-16",
                              "source": "stand-in prices"}
    assert block["price_stopped"] is None
    [(ticker, start, end)] = provider.prices.calls
    assert ticker == "GOOGL" and start < dt.date(2026, 9, 16) <= end
    session = get_session()
    try:
        asset = session.query(Asset).filter(Asset.ticker == "GOOGL").one()
        assert (asset.name, asset.currency) == ("Alphabet Inc.", "USD")
        assert (asset.asset_class, asset.sector, asset.instrument_type) == (None, None, None)
        rows = session.query(DailyPrice).filter(DailyPrice.asset_id == asset.id).all()
        assert {r.date: (round(r.close, 2), r.source) for r in rows} == {
            dt.date(2026, 9, 15): (344.98, "stand-in prices"),
            dt.date(2026, 9, 16): (342.87, "stand-in prices"),
        }
    finally:
        session.close()


async def test_a_second_run_asks_the_price_provider_for_nothing_the_same_day(provider):
    await nodes.screening_agent_node(state_with(["GOOGL"]))
    provider.prices.calls.clear()
    block = _block(await nodes.screening_agent_node(state_with(["GOOGL"])))
    assert provider.prices.calls == []
    assert block["price"]["value"] == 342.87


async def test_a_candidate_stating_no_pair_stops_the_range_and_not_the_screen(
        provider, monkeypatch, tmp_path):
    """W-2's case (KNOWN_GAPS, "What the node needs before it can publish a
    range"): the stop names the pair, no range is defaulted, and the price
    and the screen are published as they are."""
    _watchlist(monkeypatch, tmp_path, W1_WITHOUT_A_PAIR)
    out = await nodes.screening_agent_node(state_with(["GOOGL"]))
    assert out.get("errors") is None, out.get("errors")
    block = _block(out)
    assert block["valuation"] is None
    assert "W-1 (GOOGL) states no growth_low and growth_high" in block["valuation_stopped"]
    assert block["price"]["value"] == 342.87
    assert block["stopped"]["clause"] == "PHI-2.1"


async def test_a_ticker_neither_held_nor_listed_has_no_range_and_no_price(
        provider, monkeypatch, tmp_path):
    _watchlist(monkeypatch, tmp_path, W1_WITHOUT_A_PAIR.replace('"GOOGL"', '"ADBE"'))
    out = await nodes.screening_agent_node(state_with(["GOOGL"]))
    assert out.get("errors") is None, out.get("errors")
    block = _block(out)
    assert block["valuation"] is None
    assert "GOOGL is not on the watchlist" in block["valuation_stopped"]
    assert block["price"] is None
    assert "neither held nor on the watchlist" in block["price_stopped"]
    assert provider.prices.calls == []
    session = get_session()
    try:
        assert session.query(Asset).filter(Asset.ticker == "GOOGL").count() == 0
    finally:
        session.close()
    assert block["stopped"]["clause"] == "PHI-2.1"


async def test_a_price_provider_that_fails_is_a_price_stop_and_the_range_stands(provider):
    def failing(ticker, start, end):
        raise RuntimeError("the vendor is down")
    provider.prices.get_daily_prices = failing
    out = await nodes.screening_agent_node(state_with(["GOOGL"]))
    assert out.get("errors") is None, out.get("errors")
    block = _block(out)
    assert block["price"] is None
    assert "the vendor is down" in block["price_stopped"]
    assert round(block["valuation"]["low"], 2) == 129.39


async def test_the_record_carries_no_filed_figure(provider):
    record = _block(await nodes.screening_agent_node(state_with(["GOOGL"])))["valuation"]
    for key in ("free_cash_flow", "net_debt", "shares_outstanding", "operating_cash_flow",
                "capex"):
        assert key not in record
    for value in record.values():
        assert not isinstance(value, Decimal)
