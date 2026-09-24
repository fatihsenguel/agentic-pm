"""
The tool runner: one tool, its validated inputs, the graph run with the
tool's plan set rather than routed, and the record the conversation layer
logs (KNOWN_GAPS, "The eleven tool contracts of Order 5", "The log's
shape"): `tool`, `inputs`, `key`, `block`, `text`, `as_of`.

What is tested here is what the runner adds, over stand-in agents that
publish a known block: the plan run is the tool's, the tool and its inputs
reach every step, the record is read from the block the tool publishes and
from nothing else in `shared_data`, a run with errors raises instead of
returning a record, and a position raises without the gate's check of the
same ticker at the same weight. Which keys each block carries is pinned by
the node tests and not again here. The two tools that need no data,
`hypothetical_weight` and `policy_lookup`, also run end to end on the
suite's copy of the database, rendered by their formatter.
"""

import importlib

import pytest

from agents import graph, nodes
from agents.schemas import derive_plan
from agents.state import add_error, mark_agent_complete


@pytest.fixture
def runner():
    return importlib.import_module("agents.tool_runner")


AS_OF = "2026-09-21"
RAW = {"latest_prices": {"JPM": 300.0}, "covariance_matrix": {"JPM": {"JPM": 0.04}},
       "price_window": {"start": "2025-09-22", "end": AS_OF, "closes": 252}}
GOOGL_AT_6 = {"subject": {"ticker": "GOOGL"}, "weight": 0.06}

# What each stand-in agent publishes, as the real one publishes it: every
# block with the as-of where its node puts it.
PUBLISHED = {
    "DataAgent": RAW,
    "PortfolioAnalysisAgent": {
        "allocation": {"as_of": {"worst_case": AS_OF}},
        "position_pnl": {"JPM": {"as_of": AS_OF}, "AAPL": {"as_of": "2026-09-19"}},
        "portfolio_volatility": {"weights_as_of": AS_OF},
    },
    "ComplianceAgent": {"compliance": {"as_of": {"worst_case": AS_OF}}},
    "ScreeningAgent": {"screening": {"as_of": "2026-09-24"}},
    "LedgerAgent": {"ledger": {"as_of": "2026-09-24"}},
}

# tool, inputs, the key its block is published under, the block's as-of
TOOLS = [
    ("allocation", {}, "allocation", AS_OF),
    ("position_pnl", {"tickers": ["JPM"]}, "position_pnl", "2026-09-19"),
    ("portfolio_volatility", {"period": "1Y"}, "portfolio_volatility", AS_OF),
    ("compliance_check", {}, "compliance", AS_OF),
    ("hypothetical_weight", {"weight": 0.15, "instrument_type": "share"}, "compliance", AS_OF),
    ("policy_lookup", {"topic": "share price"}, "compliance", AS_OF),
    ("philosophy_screen", {"ticker": "JPM"}, "screening", "2026-09-24"),
    ("thesis", {"ticker": "GOOGL"}, "research", "2026-09-24"),
    ("position", {"ticker": "GOOGL"}, "research", "2026-09-24"),
    ("ledger", {}, "ledger", "2026-09-24"),
]


@pytest.fixture
def seen(monkeypatch):
    """Every stand-in step records its name and the tool and inputs it was
    run with; the gate stand-in checks the position it is shown."""
    calls = []

    def stand_in(name):
        async def node(state):
            calls.append((name, state.get("tool"), dict(state.get("inputs") or {})))
            out = mark_agent_complete(state, name, {"success": True})
            shared = {**(state.get("shared_data") or {}), **PUBLISHED.get(name, {})}
            if name == "ResearchAgent":
                shared["research"] = {"as_of": "2026-09-24", "asks": state["tool"], **GOOGL_AT_6}
            out["shared_data"] = shared
            return out
        return node

    async def gate(state):
        calls.append(("gate", state.get("tool"), dict(state.get("inputs") or {})))
        return {"shared_data": {**state["shared_data"], "gate": {"ticker": "GOOGL", "weight": 0.06}}}

    for name in graph.AGENT_NODES:
        monkeypatch.setitem(graph.AGENT_NODES, name, stand_in(name))
    monkeypatch.setattr(nodes, "gate_node", gate)
    return calls


@pytest.fixture
def rendered(runner, monkeypatch):
    monkeypatch.setattr(runner, "render", lambda tool, state: f"the {tool} answer")


@pytest.mark.parametrize("tool, inputs, key, as_of", TOOLS, ids=[t[0] for t in TOOLS])
async def test_a_tool_runs_its_plan_and_records_its_block(runner, seen, rendered,
                                                          tool, inputs, key, as_of):
    record, state = await runner.run_tool(tool, inputs, portfolio_id=3)
    steps = [name for name, _, _ in seen if name != "gate"]
    assert steps == derive_plan(tool)
    assert all((t, i) == (tool, inputs) for _, t, i in seen)
    assert record == {"tool": tool, "inputs": inputs, "key": key,
                      "block": state["shared_data"][key], "text": f"the {tool} answer",
                      "as_of": as_of}


async def test_only_a_position_passes_the_gate(runner, seen, rendered):
    await runner.run_tool("position", {"ticker": "GOOGL"}, portfolio_id=3)
    assert seen[-1][0] == "gate"
    seen.clear()
    await runner.run_tool("thesis", {"ticker": "GOOGL"}, portfolio_id=3)
    assert "gate" not in [name for name, _, _ in seen]


async def test_rebalance_records_the_agents_decision_under_no_key(runner, seen, rendered,
                                                                  monkeypatch):
    """The rebalance node publishes into no `shared_data` key; its block is
    the agent's decision, the trades left behind with the rest of its
    result."""
    decision = {"recommendation": "no_action", "max_drift": 0.01}

    async def rebalance(state):
        return mark_agent_complete(state, "RebalanceAgent",
                                   {"success": True, "decision": decision, "trades": [{"x": 1}]})

    monkeypatch.setitem(graph.AGENT_NODES, "RebalanceAgent", rebalance)
    record, _ = await runner.run_tool("rebalance", {}, portfolio_id=3)
    assert (record["key"], record["block"], record["as_of"]) == (None, {"decision": decision}, None)


async def test_the_raw_arrays_stay_behind(runner, seen, rendered):
    """Hot potato: the prices, the covariance matrix and the window move
    through `shared_data` inside the run and stop at the tool's boundary."""
    record, state = await runner.run_tool("allocation", {}, portfolio_id=3)
    assert set(RAW) <= set(state["shared_data"])
    assert set(record) == {"tool", "inputs", "key", "block", "text", "as_of"}
    for name in RAW:
        assert name not in repr(record), name


async def test_a_run_with_errors_raises_and_records_nothing(runner, seen, rendered, monkeypatch):
    async def failing(state):
        return {**mark_agent_complete(state, "ComplianceAgent", {"success": False}),
                **add_error(state, "ComplianceAgent: the policy file is missing")}

    monkeypatch.setitem(graph.AGENT_NODES, "ComplianceAgent", failing)
    with pytest.raises(runner.ToolRunError, match="the policy file is missing"):
        await runner.run_tool("compliance_check", {}, portfolio_id=3)


async def test_a_position_without_its_gate_check_raises(runner, seen, rendered, monkeypatch):
    async def silent_gate(state):
        return {"shared_data": state["shared_data"]}

    monkeypatch.setattr(nodes, "gate_node", silent_gate)
    with pytest.raises(runner.ToolRunError, match="gate"):
        await runner.run_tool("position", {"ticker": "GOOGL"}, portfolio_id=3)


async def test_a_run_that_publishes_no_block_raises(runner, seen, rendered, monkeypatch):
    async def publishing_nothing(state):
        return mark_agent_complete(state, "LedgerAgent", {"success": True})

    monkeypatch.setitem(graph.AGENT_NODES, "LedgerAgent", publishing_nothing)
    with pytest.raises(runner.ToolRunError, match="ledger"):
        await runner.run_tool("ledger", {}, portfolio_id=3)


# --- end to end, the two tools that need no data ---------------------------------

async def test_a_hypothetical_weight_end_to_end(runner):
    record, state = await runner.run_tool(
        "hypothetical_weight", {"weight": 0.15, "instrument_type": "share"}, portfolio_id=3)
    assert record["key"] == "compliance" and record["as_of"] is None
    assert {f["status"] for f in record["block"]["findings"]} == {"refused"}
    assert "IPS-4.1" in record["text"] and "IPS-4.2" in record["text"]
    assert list(state["sub_results"]) == ["ComplianceAgent"]


async def test_a_lookup_on_a_scope_topic_cites_the_scope_clause_end_to_end(runner):
    record, _ = await runner.run_tool("policy_lookup", {"topic": "share price"}, portfolio_id=3)
    assert record["block"]["topic"]["clauses"] == ["IPS-1.3"]
    assert "IPS-1.3" in record["text"]
