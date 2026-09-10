"""
DataAgent carries the currencies and the rates into shared_data (D15-D17).

Three things, each the analysis node's input and nothing it can derive:

  - the portfolio's currency reaches the context (`base_currency`), from
    the portfolio row, so every figure can be reported in it (D15)
  - `fetch_fx_rates_tool` fetches each foreign currency's rates beside the
    prices, over the price fetch's window, and returns only the rates on
    the dates asked for - the held tickers' as-of dates - so a year of
    rates stays in the database (hot potato). A date with no row is absent
    from the result, never invented; the node's lookup is what raises (D17)
  - data_agent_node publishes `base_currency` and `fx_rates`, an empty
    table for a single-currency portfolio, and every holding's currency

Runs against the copy conftest.py makes of data/portfolio.db, so the tool
tests pass only once migrations 0f3f60d44ce0 and ee845dad889a have been
applied. The fetch itself is replaced by a recorder: it has its own test
(test_fx_fetch.py) and no rate here is a market rate. The one live node
run fetches nothing from the provider: SPY's series is in the copy.
"""

import datetime

import pytest

from agents.data_agent import create_data_agent
from agents.nodes import data_agent_node, load_portfolio_context
from agents.state import create_initial_state
from portfolio_tool.database_setup import FxRate, get_session
from portfolio_tool.portfolio_manager import PortfolioManager


AS_OF = "2026-09-02"
DAY_BEFORE = "2026-09-01"


# --- the context ----------------------------------------------------------

def test_context_carries_the_portfolios_currency():
    """D15: the base currency is the portfolio's, read from its row."""
    pm = PortfolioManager()
    portfolio_id = pm.create_portfolio("Euro Context Test", currency="EUR", ips_path="ips.toml")
    pm.record_transaction(portfolio_id, "SPY", datetime.date(2024, 1, 15), "buy",
                          100, 450.0, 0.0, 41_400.0)
    try:
        ctx = load_portfolio_context(create_initial_state("Test", portfolio_id=portfolio_id))
        assert ctx.base_currency == "EUR"
        assert ctx.holdings[0]["currency"] == "USD"
    finally:
        pm.delete_portfolio(portfolio_id)


def test_context_without_a_portfolio_has_no_base_currency():
    state = create_initial_state("Analyze SPY and TLT")
    state["router_decision"] = {"intent": "data_fetch",
                                "parameters": {"tickers": ["SPY", "TLT"]}}
    assert load_portfolio_context(state).base_currency is None


# --- the tool -------------------------------------------------------------

def _clear(session):
    session.query(FxRate).filter(FxRate.base == "EUR", FxRate.quote == "USD").delete()
    session.commit()


@pytest.fixture
def agent():
    """A DataAgent whose rate fetch records instead of fetching, over a
    table seeded with two stated rates."""
    a = create_data_agent(verbose=False)
    session = a.data_manager.session
    _clear(session)
    session.add_all([
        FxRate(base="EUR", quote="USD", date=datetime.date(2026, 9, 1), rate=0.8600, source="test"),
        FxRate(base="EUR", quote="USD", date=datetime.date(2026, 9, 2), rate=0.8500, source="test"),
    ])
    session.commit()

    calls = []

    def recorder(base, quote, start_date=None, force_update=False):
        calls.append((base, quote, start_date))
        from portfolio_tool.models.responses import UpdateResult
        return UpdateResult(success=True, operation="update_fx_rates", affected_count=0,
                            entities=[f"{base}/{quote}"], entity_type="fx_pair",
                            metadata={"status": "cached"})

    a.data_manager.update_fx_rates = recorder
    a.recorded = calls
    yield a
    _clear(session)


def test_tool_returns_only_the_rates_on_the_dates_asked_for(agent):
    result = agent.fetch_fx_rates_tool("EUR", {"USD": [AS_OF]}, period=None)
    assert result["success"], result.get("error")
    assert result["base_currency"] == "EUR"
    assert result["rates"] == {"USD": {AS_OF: pytest.approx(0.8500, abs=1e-9)}}


def test_tool_fetches_each_foreign_currency_over_the_price_window(agent):
    agent.fetch_fx_rates_tool("EUR", {"USD": [AS_OF]}, period="1Y")
    [(base, quote, start)] = agent.recorded
    assert (base, quote) == ("EUR", "USD")
    expected_start, _, _ = agent._calculate_period_dates("1Y")
    assert start == expected_start


def test_tool_does_not_invent_a_rate_for_a_date_with_no_row(agent):
    """The day before is in the table and must not stand in; the missing
    date is absent, and the node's lookup is what refuses (D17)."""
    result = agent.fetch_fx_rates_tool("EUR", {"USD": ["2026-09-03"]}, period=None)
    assert result["success"]
    assert result["rates"] == {"USD": {}}


def test_tool_with_nothing_foreign_fetches_nothing(agent):
    result = agent.fetch_fx_rates_tool("USD", {}, period=None)
    assert result["success"]
    assert result["rates"] == {}
    assert agent.recorded == []


# --- the node -------------------------------------------------------------

async def test_node_publishes_base_currency_and_an_empty_table_for_a_dollar_portfolio():
    """Portfolio 3's shape: base USD, every holding USD. The node publishes
    the base, an empty table and each holding's currency, and makes no
    rate fetch. SPY's series is in the database copy, so no provider call."""
    pm = PortfolioManager()
    portfolio_id = pm.create_portfolio("Dollar Node Test", currency="USD", ips_path="ips.toml")
    pm.record_transaction(portfolio_id, "SPY", datetime.date(2024, 1, 15), "buy",
                          100, 450.0, 0.0, 45_000.0)
    try:
        out = await data_agent_node(create_initial_state("Test", portfolio_id=portfolio_id))
        assert out["sub_results"]["DataAgent"]["success"], out.get("errors")
        shared = out["shared_data"]
        assert shared["base_currency"] == "USD"
        assert shared["fx_rates"] == {}
        assert [h["currency"] for h in shared["holdings"]] == ["USD"]
    finally:
        pm.delete_portfolio(portfolio_id)
