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
"""

import pytest

from agents.nodes import portfolio_analysis_agent_node
from agents.state import create_initial_state

from test_allocation import CASH, HOLDINGS, PRICES


AS_OF = "2026-09-02"
FUNDS = {"SPY", "TLT", "GLD", "VNQ"}


def holdings():
    return [
        {**h, "purchase_date": "2024-01-15",
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
