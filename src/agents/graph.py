# src/agents/graph.py
# Purpose: LangGraph state machine definition
# Principle: Dynamic routing based on Smart Router plan
# Phase: 6.2 - LangGraph State Machine
# Status: BANK-READY & FLEXIBLE

from typing import Any, Dict, List, Tuple
from langgraph.graph import StateGraph, END

from langchain_core.messages import AIMessage, HumanMessage

from config import config as app_config

from .conversation import ConversationError, answer, conversation_model
from .extraction import extract, resolve
from .schemas import AGENTS
from .state import AgentState, create_initial_state, is_execution_complete, get_next_agent
from .tool_inputs import ToolContext
from .nodes import (
    router_node,
    data_agent_node,
    rebalance_agent_node,
    portfolio_analysis_agent_node,
    compliance_agent_node,
    screening_agent_node,
    ledger_agent_node,
    research_agent_node,
    gate_node,
    judgement_record,
    synthesizer_node,
)

import logging
logger = logging.getLogger(__name__)


# =============================================================================
# AGENT NODE BINDINGS
# =============================================================================

# Agent name -> the node coroutine that implements it. The roster itself is
# schemas.AGENTS; this is the one place a name is bound to code, and the two
# must agree exactly, so a roster entry with no node, or a node with no roster
# entry, fails here at import rather than on the first live route.
AGENT_NODES = {
    "DataAgent": data_agent_node,
    "RebalanceAgent": rebalance_agent_node,
    "PortfolioAnalysisAgent": portfolio_analysis_agent_node,
    "ComplianceAgent": compliance_agent_node,
    "ScreeningAgent": screening_agent_node,
    "LedgerAgent": ledger_agent_node,
    "ResearchAgent": research_agent_node,
}

# The gate is deliberately absent from both. It is a node and not an agent:
# the router cannot plan it, cannot route around it and cannot be asked for
# it, and it sits on the edge into the synthesizer instead (decision 62).
GATE = "gate"

if set(AGENT_NODES) != set(AGENTS):
    raise RuntimeError(
        "agent roster and node bindings disagree: "
        f"schemas.AGENTS has {sorted(AGENTS)}, graph.AGENT_NODES has "
        f"{sorted(AGENT_NODES)}. An agent is added to both or to neither."
    )


# =============================================================================
# ROUTING LOGIC (THE BRAIN)
# =============================================================================

def route_next_step(state: AgentState) -> str:
    """
    Universal Router: Decides the next step based on the execution plan.
    
    Why Dynamic? 
    It allows the Smart Router to create any valid sequence (e.g., Data->Analysis)
    without being forced into a rigid waterfall structure.

    Returns a key of the routing map built in build_graph: an agent name from
    schemas.AGENTS, "gate", "synthesizer" or "end". LangGraph raises on
    anything else. This used to be annotated as a Literal listing the agents
    by hand; with an explicit path_map LangGraph never reads the annotation,
    so it was a copy of the roster that checked nothing.

    **The gate sits on the edge into the synthesizer** (decision 62). Where
    the plan is finished and a judgement record is in shared_data, the run
    goes to the gate and the gate goes to the synthesizer. It is not a plan
    step, so no plan can leave it out and no router decision can skip it;
    an answer that implies a position cannot reach the synthesizer without
    passing it.
    """
    # 1. Early Exit (Clarification needed)
    if state.get("final_response") and not state.get("sub_results"):
        return "end"

    # 2. Check if we are done (Plan is empty)
    if is_execution_complete(state):
        return _gate_or_synthesizer(state)

    # 3. Get next agent from the plan
    next_agent = get_next_agent(state)

    if not next_agent:
        return _gate_or_synthesizer(state)

    # 4. Route to the agent
    # The return string must match the .add_node() name exactly
    return next_agent


def _gate_or_synthesizer(state: AgentState) -> str:
    """The one edge into the synthesizer, with the gate on it. A judgement
    record that has not been gated goes to the gate; everything else, and a
    judgement whose gate has already run, goes to the synthesizer. The gate
    has a plain edge to the synthesizer, so this is never asked twice about
    the same run and cannot loop."""
    if judgement_record(state) is not None and not (state.get("shared_data") or {}).get(GATE):
        return GATE
    return "synthesizer"


# =============================================================================
# GRAPH BUILDER
# =============================================================================

def build_graph() -> StateGraph:
    """
    Build the LangGraph state machine.
    """
    # Create graph with state type
    graph = StateGraph(AgentState)
    
    # 1. Add Nodes
    graph.add_node("Router", router_node)
    
    # Agent Nodes, one per roster entry, named as the roster names them so
    # that route_next_step's return value is the node name.
    for name in AGENTS:
        graph.add_node(name, AGENT_NODES[name])
    
    # The gate, on the edge into the synthesizer and not in the roster.
    graph.add_node(GATE, gate_node)

    # Output Node
    graph.add_node("synthesizer", synthesizer_node)
    
    # 2. Set Entry Point
    graph.set_entry_point("Router")
    
    # 3. Define Edges
    
    # Map valid return values to nodes
    # This map is used by ALL nodes to determine where to go next
    routing_map = {name: name for name in AGENTS}
    routing_map[GATE] = GATE
    routing_map["synthesizer"] = "synthesizer"
    routing_map["end"] = END
    
    # Router -> Next Agent
    graph.add_conditional_edges("Router", route_next_step, routing_map)
    
    # Agents -> Next Agent (Loop)
    # This allows any agent to transition to any other agent if the plan says so
    for node in AGENTS:
        graph.add_conditional_edges(node, route_next_step, routing_map)
    
    # Gate -> Synthesizer, a plain edge and not a conditional one: the gate
    # is passed once and what it found is the synthesizer's to print.
    graph.add_edge(GATE, "synthesizer")

    # Synthesizer -> END
    graph.add_edge("synthesizer", END)
    
    return graph


# =============================================================================
# COMPILED GRAPH & FACTORY
# =============================================================================

_compiled_graph = None

def create_agent_graph():
    """Create and compile the agent graph."""
    graph = build_graph()
    return graph.compile()

def get_graph():
    """Get or create the compiled graph singleton."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = create_agent_graph()
    return _compiled_graph

# =============================================================================
# CONVENIENCE FUNCTIONS (REQUIRED FOR TESTS)
# =============================================================================

async def run_agent_graph(user_message: str, request_id: str = None, portfolio_id: int = None,
                          previous: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    One turn of the conversation (Order 5, decision 45). `previous` is the
    final state of the turn before, when there is one: its messages and, if
    it asked back, the record of what it asked are carried into this turn.

    The reply is resolved against that record first, then the pre-pass
    reads the message: where extraction asks back, that is the turn's
    answer and no model is called. Otherwise the conversation layer answers
    with the tools, and the turn's state carries the tool-call log, the
    usage of every call and the last tool run's `shared_data` and
    `sub_results`.
    """
    state = create_initial_state(user_message, request_id, portfolio_id=portfolio_id,
                                 previous=previous)

    # One request span around the whole turn, under the state's request id,
    # so every tool run traces into the same request.
    from observability import get_tracer

    with get_tracer().trace_request(request_id=state["request_id"], user_input=user_message[:100]):
        return await _turn(state, user_message)


def _held_tickers(portfolio_id) -> List[str]:
    if not portfolio_id:
        return []
    from portfolio_tool.portfolio_manager import PortfolioManager
    return PortfolioManager().get_portfolio_tickers(portfolio_id)


def _watchlist_tickers() -> Tuple[str, ...]:
    from portfolio_tool.watchlist import load_watchlist
    from .nodes import WATCHLIST_PATH
    return tuple(c.ticker for c in load_watchlist(WATCHLIST_PATH).candidates.values())


def _history(messages) -> List[Dict[str, str]]:
    """The conversation's own earlier turns as the model is sent them: each
    question and each answer shown, as text."""
    roles = {HumanMessage: "user", AIMessage: "assistant"}
    return [{"role": roles[type(m)], "content": m.content} for m in messages if type(m) in roles]


async def _turn(state: Dict[str, Any], user_message: str) -> Dict[str, Any]:
    held = _held_tickers(state["portfolio_id"])
    periods = tuple(app_config.data.period_days.keys())
    history = _history(state["messages"][:-1])

    message = user_message
    resolved = resolve(user_message, state.get("pending"), held, periods)
    if resolved is not None:
        state["resolved"] = {"reply": user_message, "message": resolved}
        message = resolved

    extraction = extract(message, held, periods)
    if extraction.clarification:
        # An ask-back with no resolution rule leaves a record with no kind:
        # the turn asked back, and a reply to it resolves nothing.
        state["clarification"] = extraction.pending or {
            "kind": None, "token": None, "candidate": None, "message": message}
        state["final_response"] = extraction.clarification
        return state

    context = ToolContext(held=tuple(held), periods=periods, watchlist=_watchlist_tickers())
    try:
        turn = await answer(message, history=history, context=context,
                            portfolio_id=state["portfolio_id"], model=conversation_model(),
                            request_id=state["request_id"])
    except ConversationError as error:
        state["final_response"] = str(error)
        state["errors"] = [str(error)]
        state["model_calls"] = list(error.model_calls)
        return state

    state["final_response"] = turn["text"]
    state["tool_calls"] = turn["tool_calls"]
    state["model_calls"] = turn["model_calls"]
    ran = turn["state"] or {}
    state["shared_data"] = ran.get("shared_data") or {}
    state["sub_results"] = ran.get("sub_results") or {}
    return state


def run_agent_graph_sync(user_message: str, request_id: str = None, portfolio_id: int = None,
                         previous: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Synchronous version of run_agent_graph.
    """
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(run_agent_graph(user_message, request_id, portfolio_id, previous))


if __name__ == "__main__":
    # Test graph compilation
    print("Testing graph compilation...")
    graph = create_agent_graph()
    print("✓ Graph compiled successfully!")