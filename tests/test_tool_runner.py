"""
The tool runner: one tool, its validated inputs, the graph run with the
tool's plan set rather than routed, and the record the conversation layer
logs (KNOWN_GAPS, "The eleven tool contracts of Order 5", "The log's
shape", "What a turn's result carries - decision 77"): `tool`, `inputs`,
`key`, `block`, `text`, `blocks`, `agents`, `provenance`.

What is tested here is what the runner adds, over stand-in agents that
publish a known block: the plan run is the tool's, the tool and its inputs
reach every step, the record is read from the block the tool publishes and
from nothing else in `shared_data`, `blocks` carries every summary block
the run published and nothing raw, `agents` each agent that ran with its
success, `provenance` the block's as-of, the source it states or None,
and the tool's fixed caveats, a run with errors raises instead of
returning a record, a run missing a block of its table raises, and a
position raises without the gate's check of the same ticker at the same
weight. Which keys each block carries is pinned by
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
    "ScreeningAgent": {"screening": {"as_of": "2026-09-24", "source": "EDGAR"}},
    "LedgerAgent": {"ledger": {"as_of": "2026-09-24",
                               "figures": {"c-1": {"source": "EDGAR"},
                                           "c-2": {"source": "EDGAR"}}}},
}
READINGS = [{"form": "10-K", "source": "EDGAR"}, {"form": "10-K", "source": "EDGAR"}]

# tool, inputs, the key its block is published under, the block's as-of,
# and the source the block states: the screen's at its top level, a
# reading's or a candidate's figures' where the block carries those, none
# for the five blocks that state one nowhere.
TOOLS = [
    ("allocation", {}, "allocation", AS_OF, None),
    ("position_pnl", {"tickers": ["JPM"]}, "position_pnl", "2026-09-19", None),
    ("portfolio_volatility", {"period": "1Y"}, "portfolio_volatility", AS_OF, None),
    ("compliance_check", {}, "compliance", AS_OF, None),
    ("hypothetical_weight", {"weight": 0.15, "instrument_type": "share"}, "compliance", AS_OF,
     None),
    ("policy_lookup", {"topic": "share price"}, "compliance", AS_OF, None),
    ("philosophy_screen", {"ticker": "JPM"}, "screening", "2026-09-24", "EDGAR"),
    ("thesis", {"ticker": "GOOGL"}, "research", "2026-09-24", "EDGAR"),
    ("position", {"ticker": "GOOGL"}, "research", "2026-09-24", "EDGAR"),
    ("ledger", {}, "ledger", "2026-09-24", "EDGAR"),
]

# The tools whose method has a fixed caveat, each named by a word of it,
# and how many the tool's answer states. The sentences themselves are
# pinned to the formatters' text in test_caveats.py.
CAVEATED = {
    "allocation": (1, "look-through"),
    "position_pnl": (1, "Price return only"),
    "portfolio_volatility": (2, "average"),
    "compliance_check": (1, "no recommendation"),
    "hypothetical_weight": (1, "no recommendation"),
    "rebalance": (1, "trades"),
}

# The summary blocks each tool's run publishes, which its record carries
# as `blocks`: the analysis agent's three together, the position's three
# beside them, the rebalance none. The tool's own block is among them.
PORTFOLIO = {"allocation", "position_pnl", "portfolio_volatility"}
BLOCKS = {
    "allocation": PORTFOLIO,
    "position_pnl": PORTFOLIO,
    "portfolio_volatility": PORTFOLIO,
    "compliance_check": PORTFOLIO | {"compliance"},
    "hypothetical_weight": {"compliance"},
    "policy_lookup": {"compliance"},
    "philosophy_screen": {"screening"},
    "thesis": {"screening", "research"},
    "position": PORTFOLIO | {"screening", "research", "gate"},
    "rebalance": set(),
    "ledger": {"ledger"},
}


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
                shared["research"] = {"as_of": "2026-09-24", "asks": state["tool"],
                                      "readings": READINGS, **GOOGL_AT_6}
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


@pytest.mark.parametrize("tool, inputs, key, as_of, source", TOOLS, ids=[t[0] for t in TOOLS])
async def test_a_tool_runs_its_plan_and_records_its_block(runner, seen, rendered,
                                                          tool, inputs, key, as_of, source):
    record, state = await runner.run_tool(tool, inputs, portfolio_id=3)
    steps = [name for name, _, _ in seen if name != "gate"]
    assert steps == derive_plan(tool)
    assert all((t, i) == (tool, inputs) for _, t, i in seen)
    assert record == {"tool": tool, "inputs": inputs, "key": key,
                      "block": state["shared_data"][key], "text": f"the {tool} answer",
                      "blocks": {k: state["shared_data"][k] for k in BLOCKS[tool]},
                      "agents": {name: True for name in derive_plan(tool)},
                      "provenance": {"as_of": as_of, "source": source,
                                     "caveats": runner.CAVEATS[tool]}}
    assert record["blocks"][key] is record["block"]
    assert list(record["agents"]) == derive_plan(tool)


def test_the_caveats_are_fixed_per_tool_and_only_where_the_method_has_one(runner):
    """Six tools state what their method leaves out; the other five state
    nothing, and their tuple is empty rather than a sentence invented for
    the record. Every tuple is a tuple of strings, so the CLI prints it
    and a test asserts on it."""
    assert set(runner.CAVEATS) == set(runner.BLOCK_KEY)
    for tool, caveats in runner.CAVEATS.items():
        assert isinstance(caveats, tuple) and all(isinstance(c, str) for c in caveats), tool
        if tool in CAVEATED:
            count, word = CAVEATED[tool]
            assert len(caveats) == count, tool
            assert any(word in c for c in caveats), (tool, caveats)
        else:
            assert caveats == (), tool


async def test_readings_from_two_sources_are_both_recorded(runner, seen, rendered, monkeypatch):
    """A block whose readings state two sources records both, sorted and
    joined; a set of sources is not a default and not one of them."""
    async def research(state):
        out = mark_agent_complete(state, "ResearchAgent", {"success": True})
        out["shared_data"] = {**state["shared_data"], "research": {
            "as_of": "2026-09-24", "asks": "thesis",
            "readings": [{"source": "EDGAR"}, {"source": "a filing supplied by hand"}]}}
        return out

    monkeypatch.setitem(graph.AGENT_NODES, "ResearchAgent", research)
    record, _ = await runner.run_tool("thesis", {"ticker": "GOOGL"}, portfolio_id=3)
    assert record["provenance"]["source"] == "EDGAR, a filing supplied by hand"


async def test_a_ledger_with_no_figures_read_records_no_source(runner, seen, rendered,
                                                               monkeypatch):
    async def ledger(state):
        out = mark_agent_complete(state, "LedgerAgent", {"success": True})
        out["shared_data"] = {**state["shared_data"],
                              "ledger": {"as_of": "2026-09-24", "figures": {}}}
        return out

    monkeypatch.setitem(graph.AGENT_NODES, "LedgerAgent", ledger)
    record, _ = await runner.run_tool("ledger", {}, portfolio_id=3)
    assert record["provenance"] == {"as_of": "2026-09-24", "source": None, "caveats": ()}


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
    assert (record["key"], record["block"]) == (None, {"decision": decision})
    assert record["blocks"] == {}
    assert record["agents"] == {"DataAgent": True, "RebalanceAgent": True}
    assert record["provenance"] == {"as_of": None, "source": None,
                                    "caveats": runner.CAVEATS["rebalance"]}


async def test_an_agent_that_did_not_succeed_is_recorded_so(runner, seen, rendered, monkeypatch):
    """`agents` is each agent's success as it reported it, not the run's
    having raised: an agent that returned success False and no error
    leaves a record that says so."""
    async def unsure(state):
        return mark_agent_complete(state, "DataAgent", {"success": False})

    monkeypatch.setitem(graph.AGENT_NODES, "DataAgent", unsure)
    record, _ = await runner.run_tool("allocation", {}, portfolio_id=3)
    assert record["agents"] == {"DataAgent": False, "PortfolioAnalysisAgent": True}


async def test_a_run_missing_a_block_of_its_table_raises(runner, seen, rendered, monkeypatch):
    """A thesis run publishes screening and research; one that publishes
    its own block and not the other raises rather than recording a record
    with a hole in it."""
    async def screening_nothing(state):
        return mark_agent_complete(state, "ScreeningAgent", {"success": True})

    monkeypatch.setitem(graph.AGENT_NODES, "ScreeningAgent", screening_nothing)
    with pytest.raises(runner.ToolRunError, match="screening"):
        await runner.run_tool("thesis", {"ticker": "GOOGL"}, portfolio_id=3)


async def test_the_raw_arrays_stay_behind(runner, seen, rendered):
    """Hot potato: the prices, the covariance matrix and the window move
    through `shared_data` inside the run and stop at the tool's boundary."""
    record, state = await runner.run_tool("allocation", {}, portfolio_id=3)
    assert set(RAW) <= set(state["shared_data"])
    assert set(record) == {"tool", "inputs", "key", "block", "text", "blocks", "agents",
                           "provenance"}
    assert set(record["blocks"]).isdisjoint(RAW)
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
    assert record["key"] == "compliance"
    assert record["provenance"] == {"as_of": None, "source": None,
                                    "caveats": runner.CAVEATS["hypothetical_weight"]}
    assert {f["status"] for f in record["block"]["findings"]} == {"refused"}
    assert "IPS-4.1" in record["text"] and "IPS-4.2" in record["text"]
    assert list(state["sub_results"]) == ["ComplianceAgent"]


async def test_a_lookup_on_a_scope_topic_cites_the_scope_clause_end_to_end(runner):
    record, _ = await runner.run_tool("policy_lookup", {"topic": "share price"}, portfolio_id=3)
    assert record["block"]["topic"]["clauses"] == ["IPS-1.3"]
    assert "IPS-1.3" in record["text"]
