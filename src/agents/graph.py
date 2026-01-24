# src/agents/graph.py
# Purpose: LangGraph state machine definition
# Principle: Dynamic routing based on Smart Router plan
# Phase: 6.2 - LangGraph State Machine
# Status: BANK-READY & FLEXIBLE

from typing import Literal, Dict, Any, Tuple, AsyncGenerator
from langgraph.graph import StateGraph, END

from .state import AgentState, create_initial_state, is_execution_complete, get_next_agent
from .nodes import (
    router_node,
    data_agent_node,
    macro_agent_node,
    optimization_agent_node,
    rebalance_agent_node,
    backtest_agent_node,
    synthesizer_node,
)

import logging
logger = logging.getLogger(__name__)


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
    
    # Fallback: if execution_order is missing, try extracting from agents_needed
    if not plan:
        agents_needed = decision.get("agents_needed", [])
        plan = [
            a.get("agent") if isinstance(a, dict) else a 
            for a in agents_needed
        ]
    
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

def route_next_step(state: AgentState) -> Literal[
    "DataAgent", 
    "MacroAgent", 
    "OptimizationAgent", 
    "RebalanceAgent", 
    "BacktestAgent", 
    "synthesizer",
    "end"
]:
    """
    Universal Router: Decides the next step based on the execution plan.
    
    Why Dynamic? 
    It allows the Smart Router to create any valid sequence (e.g., Data->Backtest)
    without being forced into a rigid waterfall structure.
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
    
    # Agent Nodes (Names must match 'route_next_step' return values)
    graph.add_node("DataAgent", data_agent_node)
    graph.add_node("MacroAgent", macro_agent_node)
    graph.add_node("OptimizationAgent", optimization_agent_node)
    graph.add_node("RebalanceAgent", rebalance_agent_node)
    graph.add_node("BacktestAgent", backtest_agent_node)
    
    # Output Node
    graph.add_node("synthesizer", synthesizer_node)
    
    # 2. Set Entry Point
    graph.set_entry_point("Router")
    
    # 3. Define Edges
    
    # Map valid return values to nodes
    # This map is used by ALL nodes to determine where to go next
    routing_map = {
        "DataAgent": "DataAgent",
        "MacroAgent": "MacroAgent",
        "OptimizationAgent": "OptimizationAgent",
        "RebalanceAgent": "RebalanceAgent",
        "BacktestAgent": "BacktestAgent",
        "synthesizer": "synthesizer",
        "end": END
    }
    
    # Router -> Next Agent
    graph.add_conditional_edges("Router", route_next_step, routing_map)
    
    # Agents -> Next Agent (Loop)
    # This allows any agent to transition to any other agent if the plan says so
    agent_nodes = [
        "DataAgent", "MacroAgent", "OptimizationAgent", 
        "RebalanceAgent", "BacktestAgent"
    ]
    
    for node in agent_nodes:
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
# STREAMING SUPPORT
# =============================================================================

async def stream_agent_graph(user_input: str, portfolio_id: int = None) -> AsyncGenerator[Tuple[str, Dict[str, Any]], None]:
    """
    Runs the graph and yields events step-by-step.
    This enables the real-time "Thinking..." UI in the demo.
    """
    graph = get_graph()
    
    # Create valid initial state
    initial_state = create_initial_state(user_input, portfolio_id=portfolio_id)
    
    # Run graph with streaming
    async for event in graph.astream(initial_state):
        # event is a dict like {'Router': state_dict} or {'DataAgent': state_dict}
        for node_name, state in event.items():
            yield node_name, state

# =============================================================================
# CONVENIENCE FUNCTIONS (REQUIRED FOR TESTS)
# =============================================================================

async def run_agent_graph(user_message: str, request_id: str = None, portfolio_id: int = None) -> Dict[str, Any]:
    """
    Run the full agent graph for a user message.
    """
    # Create initial state with portfolio context
    state = create_initial_state(user_message, request_id, portfolio_id=portfolio_id)
    
    # Get compiled graph
    graph = get_graph()
    
    # Run the graph
    final_state = await graph.ainvoke(state)
    
    return final_state


def run_agent_graph_sync(user_message: str, request_id: str = None, portfolio_id: int = None) -> Dict[str, Any]:
    """
    Synchronous version of run_agent_graph.
    """
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(run_agent_graph(user_message, request_id, portfolio_id))


# =============================================================================
# GRAPH VISUALIZATION
# =============================================================================

def get_graph_mermaid() -> str:
    """Get Mermaid diagram 

[Image of State Machine Diagram]
"""
    return """
graph TD
    START((Start)) --> Router
    Router -->|clarification| END((End))
    
    Router -->|dynamic route| DataAgent
    Router -->|dynamic route| MacroAgent
    Router -->|dynamic route| OptimizationAgent
    Router -->|dynamic route| RebalanceAgent
    Router -->|dynamic route| BacktestAgent
    
    DataAgent -->|next step| RouterLogic
    MacroAgent -->|next step| RouterLogic
    OptimizationAgent -->|next step| RouterLogic
    RebalanceAgent -->|next step| RouterLogic
    BacktestAgent -->|next step| RouterLogic
    
    RouterLogic{Check Plan} -->|Next Agent| DataAgent
    RouterLogic -->|Next Agent| MacroAgent
    RouterLogic -->|...| OptimizationAgent
    RouterLogic -->|Done| Synthesizer
    
    Synthesizer --> END
"""

def print_graph():
    """Print the graph structure."""
    print("=" * 60)
    print("AGENT GRAPH STRUCTURE (Dynamic)")
    print("=" * 60)
    print(get_graph_mermaid())
    print("=" * 60)

if __name__ == "__main__":
    # Test graph compilation
    print("Testing graph compilation...")
    graph = create_agent_graph()
    print("✓ Graph compiled successfully!")
    print_graph()