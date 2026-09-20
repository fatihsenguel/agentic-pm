"""
The gate in the graph: the node, the edge it sits on, and the guard that
stops an outcome printing without it (decision 62).

The pure check is `portfolio_tool.gate`, held to Part 17 in test_gate.py;
this file holds the seams. What it pins: that the node publishes the block
with the figures the pure module computed and the weight the watchlist
states; that a failure publishes no block at all rather than an empty one;
that the routing puts the gate on the edge into the synthesizer, that no
plan can leave it out, and that it cannot loop; and that the formatter
refuses an outcome whose gate block is missing or is for another position.

The allocation fixture is test_gate.py's, which is Part 17 B. The policy
path is monkeypatched: which file a portfolio is checked against is the
compliance node's seam and is held there, and reading it here would make
this a database test.

Nothing sets `asks` to "position" yet (case 4.3, decision 66), so the
judgement records here are built by hand, and the node runs on no question
the system answers today.
"""

import pytest

from agents import graph, nodes
from test_gate import CASH, HOLDINGS, NEW_MONEY, TOTAL, TOTAL_AFTER, _allocation


WEIGHT = 0.06  # what watchlist.toml states for W-1 (decisions 64 and 65)


@pytest.fixture
def shared():
    allocation = _allocation(HOLDINGS, CASH)
    allocation["base_currency"] = "USD"
    allocation["as_of"] = "2026-09-18"
    return {
        "allocation": allocation,
        "holdings": [{"ticker": t, "instrument_type": kind}
                     for t, _v, _c, kind, _s in HOLDINGS],
        "research": _judgement(),
    }


def _judgement(ticker="GOOGL", weight=WEIGHT):
    """A research block that answers a question implying a position."""
    return {"asks": "position", "subject": {"ticker": ticker, "name": "Alphabet"},
            "weight": weight, "as_of": "2026-09-18"}


def _state(shared, portfolio_id=3):
    return {"shared_data": shared, "portfolio_id": portfolio_id,
            "errors": [], "sub_results": {}, "agents_to_run": []}


@pytest.fixture(autouse=True)
def policy(monkeypatch):
    monkeypatch.setattr(nodes, "load_portfolio_policy_path", lambda state: "ips.toml")


# --- the node ----------------------------------------------------------------------

async def test_the_block_carries_the_candidate_the_weight_and_its_source(shared):
    out = await nodes.gate_node(_state(shared))
    block = out["shared_data"]["gate"]
    assert block["ticker"] == "GOOGL"
    assert block["weight"] == WEIGHT
    assert block["weight_source"] == "W-1"
    assert block["funding"] == "new money on top of the portfolio"
    assert (block["asset_class"], block["sector"], block["instrument_type"]) == (
        "Equity", "Communication Services", "share")
    assert (block["base_currency"], block["as_of"]) == ("USD", "2026-09-18")


async def test_the_block_carries_part_17s_arithmetic(shared):
    """The node computes nothing: these are the pure module's figures, and
    the pure module's are Part 17's."""
    out = await nodes.gate_node(_state(shared))
    block = out["shared_data"]["gate"]
    assert round(block["new_money"], 2) == NEW_MONEY[WEIGHT]
    assert round(block["total_after"], 2) == TOTAL_AFTER[WEIGHT]
    assert block["total_before"] == TOTAL


async def test_the_block_carries_the_findings_both_ways_round(shared):
    """Decision 68 needs the findings; Part 17 A needs the ones before the
    purchase beside them, or a reader cannot tell which way it moved."""
    out = await nodes.gate_node(_state(shared))
    block = out["shared_data"]["gate"]
    after = {(f["clause"], f["subject"]): f for f in block["findings"]}
    before = {(f["clause"], f["subject"]): f for f in block["findings_before"]}
    assert after[("IPS-3.1", "Equity")]["status"] == "breach"
    assert round(after[("IPS-3.1", "Equity")]["observed"] * 100, 4) == 71.4362
    assert before[("IPS-4.1", "MSFT")]["status"] == "breach"
    assert after[("IPS-4.1", "MSFT")]["status"] == "ok"
    assert after[("IPS-5.3", "Equity")]["status"] == "breach"
    assert block["first_limb_binds"] is True
    assert ["IPS-3.1", "Equity"] in block["unrestored"]
    assert block["permits"] is False


async def test_the_block_carries_the_policy_and_its_statements(shared):
    """The answer cites clauses by quoting them, and the statement clauses
    are named as not computed (Part 17 G, D60), so both travel with it."""
    out = await nodes.gate_node(_state(shared))
    block = out["shared_data"]["gate"]
    assert block["policy"]["IPS-3.1"]["type"] == "asset_class_band"
    assert "no more than 65%" in block["policy"]["IPS-3.1"]["text"]
    assert "IPS-2.1" in {s["clause"] for s in block["statements"]}


@pytest.mark.parametrize("missing", ["allocation", "holdings"])
async def test_without_the_portfolio_it_publishes_no_block(shared, missing):
    """The portfolio as it would be needs the portfolio as it is. No block
    means the guard stops the answer."""
    shared.pop(missing)
    out = await nodes.gate_node(_state(shared))
    assert "shared_data" not in out
    assert any(f"No {missing} in shared_data" in e for e in out["errors"])


async def test_without_a_base_currency_it_publishes_no_block(shared):
    shared["allocation"].pop("base_currency")
    out = await nodes.gate_node(_state(shared))
    assert "shared_data" not in out
    assert any("No base_currency" in e for e in out["errors"])


async def test_a_candidate_that_states_no_weight_publishes_no_block(shared):
    """W-2 states none. The gate does not choose one."""
    shared["research"] = _judgement(ticker="ADBE")
    out = await nodes.gate_node(_state(shared))
    assert "shared_data" not in out
    assert any("W-2 (ADBE) states no weight" in e for e in out["errors"])


async def test_a_ticker_not_on_the_watchlist_publishes_no_block(shared):
    shared["research"] = _judgement(ticker="AAPL")
    out = await nodes.gate_node(_state(shared))
    assert "shared_data" not in out
    assert any("AAPL is not on the watchlist" in e for e in out["errors"])


async def test_reached_without_a_judgement_record_it_publishes_no_block(shared):
    shared.pop("research")
    out = await nodes.gate_node(_state(shared))
    assert "shared_data" not in out
    assert any("no judgement record" in e for e in out["errors"])


async def test_a_thesis_question_is_not_a_judgement_record(shared):
    """`asks` is "thesis": a thesis question implies no position, so the
    gate is not keyed on it and would refuse if it were reached."""
    shared["research"]["asks"] = "thesis"
    assert nodes.judgement_record(_state(shared)) is None


# --- the edge into the synthesizer --------------------------------------------------

def test_the_gate_is_not_an_agent():
    """Not in the roster and not a plan step: the router cannot plan it,
    cannot be asked for it and cannot route around it (decision 62)."""
    from agents.schemas import AGENTS
    assert graph.GATE not in AGENTS
    assert graph.GATE not in graph.AGENT_NODES


def test_a_finished_plan_with_a_judgement_goes_to_the_gate(shared):
    assert graph.route_next_step(_state(shared)) == graph.GATE


def test_a_finished_plan_without_a_judgement_goes_to_the_synthesizer(shared):
    shared.pop("research")
    assert graph.route_next_step(_state(shared)) == "synthesizer"


def test_a_judgement_already_gated_goes_to_the_synthesizer(shared):
    """The gate has a plain edge to the synthesizer, so this is belt and
    braces; it also says the routing cannot loop on a gated judgement."""
    shared["gate"] = {"ticker": "GOOGL", "weight": WEIGHT}
    assert graph.route_next_step(_state(shared)) == "synthesizer"


def test_an_unfinished_plan_still_runs_its_agents_first(shared):
    """The gate is on the way out, not in the middle: while agents remain
    in `agents_to_run` the routing sends the run to them."""
    state = _state(shared)
    state["agents_to_run"] = ["ResearchAgent"]
    assert graph.route_next_step(state) == "ResearchAgent"


def test_the_compiled_graph_holds_the_gate_and_its_edge():
    compiled = graph.create_agent_graph()
    assert graph.GATE in compiled.get_graph().nodes


# --- the guard (decision 62) --------------------------------------------------------

def test_the_guard_returns_the_block_when_the_position_matches():
    block = {"ticker": "GOOGL", "weight": WEIGHT}
    assert nodes.require_gate({"gate": block}, _judgement()) is block


def test_no_outcome_without_a_gate_block():
    with pytest.raises(nodes.DataCalculationError, match="No gate block in shared_data"):
        nodes.require_gate({}, _judgement())


def test_no_outcome_when_the_gate_checked_another_ticker():
    shared = {"gate": {"ticker": "ADBE", "weight": WEIGHT}}
    with pytest.raises(nodes.DataCalculationError, match="not this position's check"):
        nodes.require_gate(shared, _judgement())


def test_no_outcome_when_the_gate_checked_another_weight():
    """The gate's verdict is a verdict at one weight: the candidate is
    clear of IPS-4.1 at 6% and breaches it at 15% (Part 17 E), so a block
    from another weight carries the wrong findings."""
    shared = {"gate": {"ticker": "GOOGL", "weight": 0.15}}
    with pytest.raises(nodes.DataCalculationError, match="not this position's check"):
        nodes.require_gate(shared, _judgement())


def test_no_outcome_when_the_judgement_states_no_weight():
    """Nothing to hold the check to. This is also what stops case 4.3's
    answer landing later without carrying the weight it was answered at."""
    shared = {"gate": {"ticker": "GOOGL", "weight": WEIGHT}}
    with pytest.raises(nodes.DataCalculationError, match="states no weight"):
        nodes.require_gate(shared, _judgement(weight=None))


async def test_the_synthesizer_refuses_a_position_answer_with_no_gate_block(shared):
    """End to end over the seam: a judgement record reaches the synthesizer
    with the gate having failed, and no answer about the position is
    printed."""
    shared.pop("allocation")
    state = _state(shared)
    state["router_decision"] = {"intent": "research", "parameters": {}}
    state["sub_results"] = {"ResearchAgent": {"success": True, "research": {}}}
    out = await nodes.synthesizer_node(state)
    assert "No gate block in shared_data" in str(out)


async def test_the_synthesizer_prints_a_thesis_answer_without_one(shared):
    """A thesis question implies no position, so the guard does not apply
    and the answer prints as it did before the gate existed."""
    shared["research"]["asks"] = "thesis"
    state = _state(shared)
    state["router_decision"] = {"intent": "research", "parameters": {}}
    state["sub_results"] = {"ResearchAgent": {"success": False, "error": "nothing to read"}}
    out = await nodes.synthesizer_node(state)
    assert "gate block" not in str(out)


