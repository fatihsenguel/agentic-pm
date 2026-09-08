"""
compliance_agent_node over a synthetic state: what it publishes, and that
it refuses to run without PortfolioAnalysisAgent's output.

No database, no LLM. The allocation and position P&L are the Part 7
fixture from test_compliance.py; the holdings summary carries the
instrument types the way build_holdings_summary publishes them.
"""

import pytest

from agents.nodes import compliance_agent_node
from agents.state import create_initial_state

from test_compliance import INSTRUMENT_TYPES, TOTAL, allocation, position_pnl


def holdings():
    return [{"ticker": t, "quantity": 1.0, "average_price": 1.0, "asset_class": "Equity",
             "sector": None, "instrument_type": kind, "purchase_date": None}
            for t, kind in INSTRUMENT_TYPES.items()]


def state_with(**shared):
    state = create_initial_state("Does my allocation violate any rule of my policy?")
    state["shared_data"] = shared
    state["agents_to_run"] = ["ComplianceAgent"]
    return state


async def test_publishes_the_compliance_block():
    out = await compliance_agent_node(
        state_with(allocation=allocation(), position_pnl=position_pnl(), holdings=holdings())
    )
    assert out.get("errors") is None
    block = out["shared_data"]["compliance"]
    assert set(block) == {"policy", "statements", "total_value", "as_of", "findings", "no_clause"}
    assert len(block["policy"]) == 17
    assert {c for c, e in block["policy"].items() if e["type"] == "statement"} == \
        {s["clause"] for s in block["statements"]}
    assert block["total_value"] == TOTAL
    assert block["as_of"] == allocation()["as_of"]
    assert block["no_clause"] is False
    statuses = [f["status"] for f in block["findings"]]
    assert statuses.count("breach") == 8 and statuses.count("exempt") == 4
    # The same block on the result, as every node publishes its result.
    assert out["sub_results"]["ComplianceAgent"]["compliance"] is block
    assert out["sub_results"]["ComplianceAgent"]["success"] is True
    assert out["agents_to_run"] == []


@pytest.mark.parametrize("missing", ["allocation", "position_pnl", "holdings"])
async def test_refuses_without_the_analysis_output(missing):
    shared = {"allocation": allocation(), "position_pnl": position_pnl(), "holdings": holdings()}
    del shared[missing]
    out = await compliance_agent_node(state_with(**shared))
    assert "compliance" not in (out.get("shared_data") or {})
    assert out["sub_results"]["ComplianceAgent"]["success"] is False
    [error] = out["errors"]
    assert f"No {missing} in shared_data" in error
    assert "PortfolioAnalysisAgent" in error


async def test_an_unknown_instrument_type_is_an_error_not_a_verdict():
    rows = holdings()
    rows[1]["instrument_type"] = None
    out = await compliance_agent_node(
        state_with(allocation=allocation(), position_pnl=position_pnl(), holdings=rows)
    )
    assert "compliance" not in (out.get("shared_data") or {})
    [error] = out["errors"]
    assert "Instrument type" in error
