"""
portfolio_analysis_agent_node over a synthetic state: what it publishes.

No database, no LLM, no provider. The holdings and closes are
test_allocation's, which are expected_values.md Part 1 at the 2026-09-02
closes, so the published allocation is checked against Parts 2, 3 and 7
after it has passed through the node - the block the checker and the
formatters read, not the dataclass. Until this file existed nothing in
pytest reached the node's allocation call, and a broken signature passed
the suite green.

The covariance matrix is a diagonal stand-in: the node needs one to run,
and portfolio volatility has its own reference in
tests/test_portfolio_volatility.py.

A second state is expected_values.md Part 8 C: one AAPL position in a euro
portfolio, the 09-02 close and a stated 0.8500 spot on the same date, so
the node's own valuation through the rate is checked against 27,621.60 EUR
and +50.08%, both dates published (D16), and its refusal without the rate
is checked to publish nothing (D17). Portfolio 3 carries base USD and an
empty table, and none of its figures move.
"""

import pytest

from agents.nodes import portfolio_analysis_agent_node
from agents.state import create_initial_state

from test_allocation import CASH, HOLDINGS, PRICES


AS_OF = "2026-09-02"
FUNDS = {"SPY", "TLT", "GLD", "VNQ"}


def holdings():
    return [
        {**h, "purchase_date": "2024-01-15", "currency": "USD",
         "instrument_type": "fund" if h["ticker"] in FUNDS else "share"}
        for h in HOLDINGS
    ]


def state():
    s = create_initial_state("What share of my portfolio is technology?", portfolio_id=3)
    s["shared_data"] = {
        "holdings": holdings(),
        "latest_prices": dict(PRICES),
        "as_of_dates": {t: AS_OF for t in PRICES},
        "cash_balance": CASH,
        "covariance_matrix": {t: {u: (0.04 if t == u else 0.0) for u in PRICES} for t in PRICES},
        "price_window": {"start": "2025-09-03", "end": AS_OF, "closes": 252},
        "covariance_method": "sample",
        "base_currency": "USD",
        "fx_rates": {},
    }
    s["agents_to_run"] = ["PortfolioAnalysisAgent"]
    s["router_decision"] = {"intent": "data_fetch", "parameters": {}}
    return s


# expected_values.md Part 8 C: the position after the one euro row, the
# 09-02 close in dollars, and a stated spot rate on the same date.
EURO_HOLDING = {
    "ticker": "AAPL", "quantity": 100.0, "average_price": 184.05, "cost_basis": 18405.0,
    "asset_class": "Equity", "sector": "Technology", "instrument_type": "share",
    "purchase_date": "2024-02-20", "currency": "USD",
}
EURO_SPOT = {"USD": {AS_OF: 0.8500}}


def euro_state(fx_rates):
    s = create_initial_state("How is my AAPL position doing?", portfolio_id=7)
    s["shared_data"] = {
        "holdings": [dict(EURO_HOLDING)],
        "latest_prices": {"AAPL": 324.96},
        "as_of_dates": {"AAPL": AS_OF},
        "cash_balance": 0.0,
        "covariance_matrix": {"AAPL": {"AAPL": 0.04}},
        "price_window": {"start": "2025-09-03", "end": AS_OF, "closes": 252},
        "covariance_method": "sample",
        "base_currency": "EUR",
        "fx_rates": fx_rates,
    }
    s["agents_to_run"] = ["PortfolioAnalysisAgent"]
    s["router_decision"] = {"intent": "data_fetch", "parameters": {}}
    return s


def _by_label(block):
    return {line["label"]: line for line in block["lines"]}


@pytest.fixture(scope="module")
async def published():
    out = await portfolio_analysis_agent_node(state())
    assert out.get("errors") is None, out.get("errors")
    return out["shared_data"]["allocation"]


async def test_sector_lines_carry_the_ips_4_3_share_of_total(published):
    """Part 7, IPS-4.3 column, as published: the figure the checker reads."""
    lines = _by_label(published["by_sector"])
    assert lines["Technology"]["pct_of_total"] == pytest.approx(0.2796, abs=0.00005)
    assert lines["Healthcare"]["pct_of_total"] == pytest.approx(0.1006, abs=0.00005)
    assert lines["Financials"]["pct_of_total"] == pytest.approx(0.0868, abs=0.00005)
    assert lines["Utilities"]["pct_of_total"] == pytest.approx(0.0405, abs=0.00005)
    assert lines["(no sector)"]["pct_of_total"] == pytest.approx(0.4547, abs=0.00005)


async def test_sector_block_carries_the_d2_total(published):
    """The same total as the asset-class block, so a reader given only the
    sector block can name the denominator without dividing for it."""
    by_sector, by_class = published["by_sector"], published["by_asset_class"]
    assert by_sector["total_value"] == pytest.approx(410200.50, abs=0.01)
    assert by_sector["total_value"] == by_class["total_value"]
    assert by_sector["sectored_value"] == pytest.approx(208197.50, abs=0.01)
    assert by_sector["invested_value"] == pytest.approx(394700.50, abs=0.01)


async def test_asset_class_lines_carry_the_share_of_total_under_the_same_name(published):
    lines = _by_label(published["by_asset_class"])
    assert lines["Equity"]["pct_of_total"] == pytest.approx(0.6941, abs=0.00005)
    assert lines["Cash"]["pct_of_total"] == pytest.approx(0.0378, abs=0.00005)
    for line in lines.values():
        assert line["pct_of_sectored"] is None


async def test_position_view_is_published_largest_first(published):
    """Part 7, IPS-4.1 column, as published: one line per holding, largest
    first, share of total - the block the checker and the formatter read."""
    by_position = published["by_position"]
    assert [l["label"] for l in by_position["lines"]] == [
        "SPY", "AAPL", "MSFT", "JNJ", "TLT", "GLD", "JPM", "VNQ", "NEE"]
    lines = _by_label(by_position)
    assert lines["SPY"]["pct_of_total"] == pytest.approx(0.1865, abs=0.00005)
    assert lines["MSFT"]["pct_of_total"] == pytest.approx(0.1211, abs=0.00005)
    assert lines["NEE"]["pct_of_total"] == pytest.approx(0.0405, abs=0.00005)
    assert lines["SPY"]["tickers"] == ["SPY"]
    assert "Cash" not in lines


async def test_position_block_carries_the_same_denominators(published):
    by_position, by_class = published["by_position"], published["by_asset_class"]
    assert by_position["total_value"] == by_class["total_value"]
    assert by_position["invested_value"] == by_class["invested_value"]
    assert by_position["cash_balance"] == by_class["cash_balance"]
    assert by_position["total_value"] == pytest.approx(410200.50, abs=0.01)


async def test_part_3_columns_are_unchanged(published):
    """Adding a third figure moved neither of the first two."""
    lines = _by_label(published["by_sector"])
    assert lines["Technology"]["pct_of_sectored"] == pytest.approx(0.5508, abs=0.00005)
    assert lines["Technology"]["pct_of_invested"] == pytest.approx(0.2905, abs=0.00005)
    assert lines["(no sector)"]["pct_of_sectored"] is None


@pytest.mark.parametrize("view", ["by_asset_class", "by_sector", "by_position"])
async def test_blocks_carry_no_denominator_label(published, view):
    """Every share names its own denominator (pct_of_total, pct_of_sectored,
    pct_of_invested) and the block carries the amounts; a prose label in the
    block was the formatter's words living in the computation."""
    assert "denominator" not in published[view]


# ---------------------------------------------------------------------------
# Part 8 C through the node: valued in the base currency, both dates stated
# ---------------------------------------------------------------------------

CENT = 0.005


async def test_portfolio_3_is_valued_with_no_rate(published):
    """Base USD, every holding USD, an empty table: no figure moves and no
    position carries a rate or a rate date."""
    out = await portfolio_analysis_agent_node(state())
    pnl = out["shared_data"]["position_pnl"]
    assert set(pnl) == set(PRICES)
    for p in pnl.values():
        assert p["rate"] is None and p["rate_as_of"] is None
        assert p["currency"] == "USD"
    assert out["shared_data"]["position_pnl"]["AAPL"]["market_value"] == pytest.approx(64992.00, abs=CENT)


async def test_euro_position_is_valued_through_the_rate():
    out = await portfolio_analysis_agent_node(euro_state(EURO_SPOT))
    assert out.get("errors") is None, out.get("errors")
    p = out["shared_data"]["position_pnl"]["AAPL"]
    assert p["market_value"] == pytest.approx(27_621.60, abs=CENT)
    assert p["pnl_abs"] == pytest.approx(9_216.60, abs=CENT)
    assert p["pnl_pct"] == pytest.approx(0.500766, abs=0.0000005)
    assert p["cost_basis"] == pytest.approx(18_405.00, abs=CENT)
    assert p["price"] == 324.96
    assert p["average_price"] == pytest.approx(184.05, abs=CENT)


async def test_euro_position_publishes_both_dates_and_both_currencies():
    """D16: the price's as-of date and the rate's, D18: the currency of the
    quote and the base every other figure is in."""
    out = await portfolio_analysis_agent_node(euro_state(EURO_SPOT))
    p = out["shared_data"]["position_pnl"]["AAPL"]
    assert p["as_of"] == AS_OF
    assert p["rate"] == pytest.approx(0.8500, abs=1e-9)
    assert p["rate_as_of"] == AS_OF
    assert p["currency"] == "USD"
    result = out["sub_results"]["PortfolioAnalysisAgent"]
    assert result["base_currency"] == "EUR"
    assert out["shared_data"]["allocation"]["base_currency"] == "EUR"


async def test_euro_allocation_values_through_the_same_rate():
    out = await portfolio_analysis_agent_node(euro_state(EURO_SPOT))
    by_position = out["shared_data"]["allocation"]["by_position"]
    [line] = by_position["lines"]
    assert line["market_value"] == pytest.approx(27_621.60, abs=CENT)
    assert by_position["total_value"] == pytest.approx(27_621.60, abs=CENT)
    assert line["pct_of_total"] == pytest.approx(1.0, abs=1e-9)


async def test_euro_position_without_a_rate_is_refused_and_nothing_is_published():
    """Part 8 C, D17: no rate for 2026-09-02 means no market value, not a
    value at yesterday's rate and not a value at 1. The error names the
    currency and the date; no allocation, P&L or volatility is published."""
    out = await portfolio_analysis_agent_node(euro_state({"USD": {"2026-09-01": 0.86}}))
    [error] = out["errors"]
    assert "USD" in error and AS_OF in error
    shared = out.get("shared_data") or {}
    assert "allocation" not in shared
    assert "position_pnl" not in shared
    assert "portfolio_volatility" not in shared
    assert out["sub_results"]["PortfolioAnalysisAgent"]["success"] is False


@pytest.mark.parametrize("key", ["base_currency", "fx_rates"])
async def test_missing_currency_input_raises(key):
    """The base currency and the rate table are DataAgent's to publish; an
    absent key is not an empty table and not a dollar portfolio."""
    s = euro_state(EURO_SPOT)
    del s["shared_data"][key]
    out = await portfolio_analysis_agent_node(s)
    [error] = out["errors"]
    assert key in error
    assert "allocation" not in (out.get("shared_data") or {})
