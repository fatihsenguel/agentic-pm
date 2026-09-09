# src/agents/graph.py
# Purpose: LangGraph state machine definition
# Principle: Dynamic routing based on Smart Router plan
# Phase: 6.2 - LangGraph State Machine
# Status: BANK-READY & FLEXIBLE

from typing import Dict, Any
from langgraph.graph import StateGraph, END

from .schemas import AGENTS
from .state import AgentState, create_initial_state, is_execution_complete, get_next_agent
from .nodes import (
    router_node,
    data_agent_node,
    macro_agent_node,
    optimization_agent_node,
    rebalance_agent_node,
    portfolio_analysis_agent_node,
    compliance_agent_node,
    backtest_agent_node,
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
    "MacroAgent": macro_agent_node,
    "OptimizationAgent": optimization_agent_node,
    "RebalanceAgent": rebalance_agent_node,
    "BacktestAgent": backtest_agent_node,
    "PortfolioAnalysisAgent": portfolio_analysis_agent_node,
    "ComplianceAgent": compliance_agent_node,
}

if set(AGENT_NODES) != set(AGENTS):
    raise RuntimeError(
        "agent roster and node bindings disagree: "
        f"schemas.AGENTS has {sorted(AGENTS)}, graph.AGENT_NODES has "
        f"{sorted(AGENT_NODES)}. An agent is added to both or to neither."
    )


# =============================================================================
# HELPER LOGIC (Internal)
# =============================================================================

def _get_next_agent_internal(state: AgentState) -> str | None:
    """
    Determines the next agent to run based on the plan and completion status.
    Self-contained logic to ensure robustness.
    """
    decision = state.get("router_decision", {})
    
    # 1. Get the plan (List of agent names)
    plan = decision.get("execution_order", [])
    
    # 2. Check who has finished
    completed_agents = state.get("sub_results", {}).keys()
    
    # 3. Find first agent in plan that hasn't finished
    for agent_name in plan:
        if agent_name not in completed_agents:
            return agent_name
            
    return None


def _is_execution_complete_internal(state: AgentState) -> bool:
    """Checks if all agents in the plan have run."""
    next_agent = _get_next_agent_internal(state)
    return next_agent is None

# =============================================================================
# ROUTING LOGIC (THE BRAIN)
# =============================================================================

def route_next_step(state: AgentState) -> str:
    """
    Universal Router: Decides the next step based on the execution plan.
    
    Why Dynamic? 
    It allows the Smart Router to create any valid sequence (e.g., Data->Backtest)
    without being forced into a rigid waterfall structure.

    Returns a key of the routing map built in build_graph: an agent name from
    schemas.AGENTS, "synthesizer" or "end". LangGraph raises on anything else.
    This used to be annotated as a Literal listing the agents by hand; with an
    explicit path_map LangGraph never reads the annotation, so it was a copy
    of the roster that checked nothing.
    """
    # 1. Early Exit (Clarification needed)
    if state.get("final_response") and not state.get("sub_results"):
        return "end"

    # 2. Check if we are done (Plan is empty)
    if is_execution_complete(state):
        return "synthesizer"
    
    # 3. Get next agent from the plan
    next_agent = get_next_agent(state)
    
    if not next_agent:
        return "synthesizer"
        
    # 4. Route to the agent
    # The return string must match the .add_node() name exactly
    return next_agent


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
    
    # Output Node
    graph.add_node("synthesizer", synthesizer_node)
    
    # 2. Set Entry Point
    graph.set_entry_point("Router")
    
    # 3. Define Edges
    
    # Map valid return values to nodes
    # This map is used by ALL nodes to determine where to go next
    routing_map = {name: name for name in AGENTS}
    routing_map["synthesizer"] = "synthesizer"
    routing_map["end"] = END
    
    # Router -> Next Agent
    graph.add_conditional_edges("Router", route_next_step, routing_map)
    
    # Agents -> Next Agent (Loop)
    # This allows any agent to transition to any other agent if the plan says so
    for node in AGENTS:
        graph.add_conditional_edges(node, route_next_step, routing_map)
    
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
    Run the full agent graph for a user message. `previous` is the final
    state of the turn before, when there is one: its messages and, if it
    asked back, the record of what it asked are carried into this turn.
    """
    # Create initial state with portfolio context
    state = create_initial_state(user_message, request_id, portfolio_id=portfolio_id,
                                 previous=previous)
    
    # Get compiled graph
    graph = get_graph()
    
    # One request span around the whole run, under the state's request id,
    # so every node - Router included - traces into the same request and the
    # stored trace shows the plan being executed, not only planned.
    from observability import get_tracer

    with get_tracer().trace_request(request_id=state["request_id"], user_input=user_message[:100]):
        final_state = await graph.ainvoke(state)
    
    return final_state


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