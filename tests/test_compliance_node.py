"""
compliance_agent_node over a synthetic state: what it publishes, and that
it refuses to run without PortfolioAnalysisAgent's output.

No database, no LLM. The allocation is the Part 7 fixture from
test_compliance.py; the holdings summary carries the instrument types the
way build_holdings_summary publishes them.
"""

import pytest

from agents.nodes import compliance_agent_node
from agents.state import create_initial_state

from test_compliance import INSTRUMENT_TYPES, TOTAL, allocation


def holdings():
    return [{"ticker": t, "quantity": 1.0, "average_price": 1.0, "asset_class": "Equity",
             "sector": None, "instrument_type": kind, "purchase_date": None}
            for t, kind in INSTRUMENT_TYPES.items()]


def state_with(_params=None, **shared):
    state = create_initial_state("Does my allocation violate any rule of my policy?")
    state["shared_data"] = shared
    state["agents_to_run"] = ["ComplianceAgent"]
    state["router_decision"] = {"intent": "compliance", "parameters": _params or {}}
    return state


BLOCK_KEYS = {"policy", "statements", "total_value", "as_of", "findings", "no_clause", "topic"}


async def test_publishes_the_compliance_block():
    out = await compliance_agent_node(
        state_with(allocation=allocation(), holdings=holdings())
    )
    assert out.get("errors") is None
    block = out["shared_data"]["compliance"]
    assert set(block) == BLOCK_KEYS
    assert len(block["policy"]) == 17
    assert {c for c, e in block["policy"].items() if e["type"] == "statement"} == \
        {s["clause"] for s in block["statements"]}
    assert block["total_value"] == TOTAL
    assert block["as_of"] == allocation()["as_of"]
    assert block["no_clause"] is False
    assert block["topic"] is None
    statuses = [f["status"] for f in block["findings"]]
    assert statuses.count("breach") == 8 and statuses.count("exempt") == 4
    # The same block on the result, as every node publishes its result.
    assert out["sub_results"]["ComplianceAgent"]["compliance"] is block
    assert out["sub_results"]["ComplianceAgent"]["success"] is True
    assert out["agents_to_run"] == []


@pytest.mark.parametrize("missing", ["allocation", "holdings"])
async def test_refuses_without_the_analysis_output(missing):
    shared = {"allocation": allocation(), "holdings": holdings()}
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
        state_with(allocation=allocation(), holdings=rows)
    )
    assert "compliance" not in (out.get("shared_data") or {})
    [error] = out["errors"]
    assert "Instrument type" in error


# --- the two modes that measure no portfolio ---------------------------------

async def test_hypothetical_weight_refuses_without_a_portfolio():
    out = await compliance_agent_node(state_with({"hypothetical_weight": 0.15}))
    assert out.get("errors") is None
    block = out["shared_data"]["compliance"]
    assert set(block) == BLOCK_KEYS
    assert block["total_value"] is None and block["as_of"] is None
    assert block["no_clause"] is False and block["topic"] is None
    assert {f["clause"]: f["status"] for f in block["findings"]} == {
        "IPS-4.1": "refused", "IPS-4.2": "refused"}
    assert all(f["distance_value"] is None for f in block["findings"])


async def test_topic_the_policy_is_silent_on_sets_no_clause():
    out = await compliance_agent_node(state_with({"policy_topic": "currency risk"}))
    assert out.get("errors") is None
    block = out["shared_data"]["compliance"]
    assert block["findings"] == []
    assert block["no_clause"] is True
    assert block["topic"] == {"asked": "currency risk", "clauses": []}
    assert block["total_value"] is None and block["as_of"] is None
    assert len(block["policy"]) == 17   # nothing, said over a visibly full policy


async def test_topic_the_policy_has_names_its_clauses():
    out = await compliance_agent_node(state_with({"policy_topic": " Concentration "}))
    block = out["shared_data"]["compliance"]
    assert block["no_clause"] is False
    assert block["topic"] == {"asked": "concentration", "clauses": ["IPS-4.1", "IPS-4.2", "IPS-4.3"]}
    assert block["findings"] == []


async def test_a_lookup_or_hypothetical_needs_no_analysis_output():
    out = await compliance_agent_node(state_with({"policy_topic": "cash"}))
    assert out.get("errors") is None
    out = await compliance_agent_node(state_with({"hypothetical_weight": 0.05}))
    assert out.get("errors") is None
    assert {f["status"] for f in out["shared_data"]["compliance"]["findings"]} == {"ok"}


async def test_both_modes_is_an_error():
    out = await compliance_agent_node(
        state_with({"hypothetical_weight": 0.15, "policy_topic": "cash"}))
    [error] = out["errors"]
    assert "Both" in error
