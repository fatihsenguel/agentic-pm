"""
One tool run: its plan set from the terminal table rather than routed, its
validated inputs in the state, and the record the conversation layer logs
(KNOWN_GAPS, "The eleven tool contracts of Order 5", "The log's shape",
"What a turn's result carries - decision 77"): `tool`, `inputs`, `key`,
`block`, `text`, `as_of`, `blocks`, `agents`.

The graph is the one graph.py builds, less the router and the synthesizer:
the agents as graph.AGENT_NODES binds them, the gate on the edge after the
plan exactly as `_gate_or_synthesizer` puts it there, and the end where the
synthesizer was. Each tool renders its own block with the formatter that
renders it today.

The record carries the tool's block, and under `blocks` every summary
block the run published as BLOCKS names them, and nothing else from
`shared_data`: the prices, the covariance matrix and the window stop at
the tool's boundary (DIRECTION.md invariant 3). `agents` is each agent
that ran, in plan order, with the success it reported. A run with errors,
a run that publishes no block of its table, and a position without the
gate's check of the same ticker at the same weight (decision 62,
`require_gate`) raise instead of returning a record.
"""

from typing import Any, Dict, Mapping, Optional, Tuple

from langgraph.graph import END, StateGraph

from . import nodes
from .nodes import DataCalculationError
from .schemas import AGENTS, derive_plan
from .state import AgentState, create_initial_state

__all__ = ["BLOCKS", "BLOCK_KEY", "ToolRunError", "render", "run_tool"]


class ToolRunError(Exception):
    """Raised when a tool's run produced no answer that may be shown."""


# The `shared_data` key each tool's block is published under. The rebalance
# node publishes into none: its block is the agent's decision.
BLOCK_KEY: Dict[str, Optional[str]] = {
    "allocation": "allocation",
    "position_pnl": "position_pnl",
    "portfolio_volatility": "portfolio_volatility",
    "compliance_check": "compliance",
    "hypothetical_weight": "compliance",
    "policy_lookup": "compliance",
    "philosophy_screen": "screening",
    "thesis": "research",
    "position": "research",
    "rebalance": None,
    "ledger": "ledger",
}

# The summary blocks each tool's run publishes, the `shared_data` keys the
# record carries as `blocks`. The analysis agent publishes its three
# together or raises, so every run through it carries all three; the
# position's run adds the screen, the reading and the gate's check. The
# raw arrays beside them are not on the table (DIRECTION.md invariant 3).
# The rebalance run publishes none: its block is the agent's decision.
_PORTFOLIO = ("allocation", "position_pnl", "portfolio_volatility")
BLOCKS: Dict[str, Tuple[str, ...]] = {
    "allocation": _PORTFOLIO,
    "position_pnl": _PORTFOLIO,
    "portfolio_volatility": _PORTFOLIO,
    "compliance_check": _PORTFOLIO + ("compliance",),
    "hypothetical_weight": ("compliance",),
    "policy_lookup": ("compliance",),
    "philosophy_screen": ("screening",),
    "thesis": ("screening", "research"),
    "position": _PORTFOLIO + ("screening", "research", "gate"),
    "rebalance": (),
    "ledger": ("ledger",),
}

if set(BLOCKS) != set(BLOCK_KEY):
    raise RuntimeError(f"BLOCKS names {sorted(BLOCKS)} and BLOCK_KEY {sorted(BLOCK_KEY)}; "
                       "a tool is on both tables or on neither")
for _tool, _key in BLOCK_KEY.items():
    if _key is not None and _key not in BLOCKS[_tool]:
        raise RuntimeError(f"BLOCKS[{_tool!r}] leaves out the tool's own block {_key!r}")


def _tool_graph():
    """The graph without the router and the synthesizer, bound to the
    agents and the gate as they are bound when it is built. graph.py is
    read here and not at import, since its turn imports the layer that
    imports this module."""
    from . import graph as _graph

    tool_graph = StateGraph(AgentState)
    for name in AGENTS:
        tool_graph.add_node(name, _graph.AGENT_NODES[name])
    tool_graph.add_node(_graph.GATE, nodes.gate_node)
    routing = {name: name for name in AGENTS}
    routing[_graph.GATE] = _graph.GATE
    routing["synthesizer"] = END
    routing["end"] = END
    tool_graph.set_conditional_entry_point(_graph.route_next_step, routing)
    for name in AGENTS:
        tool_graph.add_conditional_edges(name, _graph.route_next_step, routing)
    tool_graph.add_edge(_graph.GATE, END)
    return tool_graph.compile()


def render(tool: str, state: Mapping[str, Any]) -> str:
    """The tool's block as its formatter renders it."""
    sub_results = state.get("sub_results") or {}
    shared = state.get("shared_data") or {}
    inputs = state.get("inputs") or {}
    if tool == "allocation":
        lines = nodes._format_allocation_response(sub_results)
    elif tool == "position_pnl":
        lines = nodes._format_pnl_response(sub_results, list(inputs.get("tickers") or []))
    elif tool == "portfolio_volatility":
        lines = nodes._format_portfolio_volatility_response(sub_results)
    elif tool in ("compliance_check", "hypothetical_weight", "policy_lookup"):
        lines = nodes._format_compliance_response({"parameters": {}}, sub_results)
    elif tool == "philosophy_screen":
        lines = nodes._format_research_response(sub_results)
    elif tool == "thesis":
        lines = nodes._format_thesis_response(sub_results)
    elif tool == "position":
        judgement = nodes.judgement_record(state)
        lines = nodes._format_position_response(judgement, nodes.require_gate(shared, judgement),
                                                shared.get("screening"))
    elif tool == "rebalance":
        lines = nodes._format_rebalance_response(sub_results)
    elif tool == "ledger":
        lines = nodes._format_ledger_response(sub_results)
    else:
        raise ToolRunError(f"No formatter renders {tool!r}.")
    return "\n".join(lines)


def _as_of(tool: str, block: Mapping[str, Any]) -> Optional[str]:
    """The block's as-of as a date string, None where it carries none: the
    worst case where the block reduces its dates to one, the earliest
    position's where each position carries its own."""
    if tool == "rebalance":
        return None
    if tool == "position_pnl":
        dates = [p["as_of"] for p in block.values() if isinstance(p, Mapping) and p.get("as_of")]
        return str(min(dates)) if dates else None
    if tool == "portfolio_volatility":
        return block.get("weights_as_of")
    as_of = block.get("as_of")
    if isinstance(as_of, Mapping):
        return as_of.get("worst_case")
    return as_of


async def run_tool(tool: str, inputs: Mapping[str, Any], portfolio_id: Optional[int],
                   request_id: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run one tool on inputs already validated against its model, and
    return its record and the run's final state."""
    state = create_initial_state("", request_id=request_id, portfolio_id=portfolio_id)
    state.update(tool=tool, inputs=dict(inputs), agents_to_run=derive_plan(tool))
    final = await _tool_graph().ainvoke(state)

    errors = final.get("errors") or []
    if errors:
        raise ToolRunError(f"{tool}: " + "; ".join(errors))

    key = BLOCK_KEY[tool]
    shared = final.get("shared_data") or {}
    sub_results = final.get("sub_results") or {}
    missing = [k for k in BLOCKS[tool] if k not in shared]
    if missing:
        raise ToolRunError(f"{tool}: the run published no "
                           f"{', '.join(repr(k) for k in missing)} block.")
    blocks = {k: shared[k] for k in BLOCKS[tool]}
    if key is None:
        result = sub_results.get("RebalanceAgent") or {}
        if "decision" not in result:
            raise ToolRunError(f"{tool}: the agent returned no decision.")
        block = {"decision": result["decision"]}
    else:
        block = blocks[key]

    try:
        if tool == "position":
            nodes.require_gate(shared, block)
        text = render(tool, final)
    except DataCalculationError as error:
        raise ToolRunError(f"{tool}: {error}") from error

    agents = {name: bool((result or {}).get("success")) for name, result in sub_results.items()}
    record = {"tool": tool, "inputs": dict(inputs), "key": key, "block": block,
              "text": text, "as_of": _as_of(tool, block), "blocks": blocks, "agents": agents}
    return record, final
