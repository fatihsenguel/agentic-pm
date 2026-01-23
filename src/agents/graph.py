# src/agents/graph.py
# Purpose: LangGraph state machine definition
# Principle: Clean graph structure with conditional routing based on Smart Router
# Phase: 6.2 - LangGraph State Machine

from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, END

from .state import AgentState, create_initial_state, is_execution_complete, get_next_agent, has_errors
from .nodes import (
    router_node,
    agent_dispatcher_node,
    data_agent_node,
    macro_agent_node,
    optimization_agent_node,
    rebalance_agent_node,
    backtest_agent_node,
    synthesizer_node,
)


# =============================================================================
# CONDITIONAL EDGE FUNCTIONS
# =============================================================================

def should_continue_or_end(state: AgentState) -> Literal["dispatcher", "synthesizer", "end"]:
    """
    Decide whether to continue execution or end.
    
    Routes to:
    - "dispatcher": More agents to run
    - "synthesizer": All agents done, synthesize response
    - "end": Final response already set (clarification)
    """
    # If we already have a final response (e.g., clarification), end
    if state.get("final_response"):
        return "end"
    
    # If there are more agents to run, continue
    if not is_execution_complete(state):
        return "dispatcher"
    
    # All agents done, synthesize
    return "synthesizer"


def route_to_agent(state: AgentState) -> Literal[
    "data_agent", 
    "macro_agent", 
    "optimization_agent", 
    "rebalance_agent", 
    "backtest_agent",
    "synthesizer"
]:
    """
    Route to the appropriate agent based on current_agent.
    """
    current = state.get("current_agent")
    
    agent_map = {
        "DataAgent": "data_agent",
        "MacroAgent": "macro_agent",
        "OptimizationAgent": "optimization_agent",
        "RebalanceAgent": "rebalance_agent",
        "BacktestAgent": "backtest_agent",
    }
    
    if current and current in agent_map:
        return agent_map[current]
    
    # No more agents, go to synthesizer
    return "synthesizer"


def after_agent(state: AgentState) -> Literal["dispatcher", "synthesizer"]:
    """
    After an agent completes, check if more agents need to run.
    """
    if is_execution_complete(state):
        return "synthesizer"
    return "dispatcher"


# =============================================================================
# GRAPH BUILDER
# =============================================================================

def build_graph() -> StateGraph:
    """
    Build the LangGraph state machine.
    
    Graph Structure:
    
        START
          │
          ▼
       [router]  ─────────────────────────────┐
          │                                    │ (clarification)
          ▼                                    │
       [dispatcher] ◄─────────────────────┐    │
          │                               │    │
          ├──► [data_agent] ─────────────►│    │
          ├──► [macro_agent] ────────────►│    │
          ├──► [optimization_agent] ─────►│    │
          ├──► [rebalance_agent] ────────►│    │
          └──► [backtest_agent] ─────────►│    │
                                          │    │
                                          ▼    │
                                    [synthesizer]
                                          │    │
                                          ▼    ▼
                                         END
    """
    # Create graph with state type
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("dispatcher", agent_dispatcher_node)
    graph.add_node("data_agent", data_agent_node)
    graph.add_node("macro_agent", macro_agent_node)
    graph.add_node("optimization_agent", optimization_agent_node)
    graph.add_node("rebalance_agent", rebalance_agent_node)
    graph.add_node("backtest_agent", backtest_agent_node)
    graph.add_node("synthesizer", synthesizer_node)
    
    # Set entry point
    graph.set_entry_point("router")
    
    # Router -> dispatcher or end (if clarification)
    graph.add_conditional_edges(
        "router",
        should_continue_or_end,
        {
            "dispatcher": "dispatcher",
            "synthesizer": "synthesizer",
            "end": END,
        }
    )
    
    # Dispatcher -> appropriate agent
    graph.add_conditional_edges(
        "dispatcher",
        route_to_agent,
        {
            "data_agent": "data_agent",
            "macro_agent": "macro_agent",
            "optimization_agent": "optimization_agent",
            "rebalance_agent": "rebalance_agent",
            "backtest_agent": "backtest_agent",
            "synthesizer": "synthesizer",
        }
    )
    
    # Each agent -> back to dispatcher or synthesizer
    for agent_node in ["data_agent", "macro_agent", "optimization_agent", 
                       "rebalance_agent", "backtest_agent"]:
        graph.add_conditional_edges(
            agent_node,
            after_agent,
            {
                "dispatcher": "dispatcher",
                "synthesizer": "synthesizer",
            }
        )
    
    # Synthesizer -> END
    graph.add_edge("synthesizer", END)
    
    return graph


# =============================================================================
# COMPILED GRAPH
# =============================================================================

def create_agent_graph():
    """
    Create and compile the agent graph.
    
    Returns:
        Compiled LangGraph that can be invoked with state
    """
    graph = build_graph()
    return graph.compile()


# Global compiled graph (lazy initialization)
_compiled_graph = None


def get_graph():
    """Get or create the compiled graph singleton."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = create_agent_graph()
    return _compiled_graph


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def run_agent_graph(user_message: str, request_id: str = None) -> Dict[str, Any]:
    """
    Run the full agent graph for a user message.
    
    This is the main entry point for processing user requests.
    
    Args:
        user_message: The user's input message
        request_id: Optional request ID for tracing
    
    Returns:
        Final state with results
    """
    # Create initial state
    state = create_initial_state(user_message, request_id)
    
    # Get compiled graph
    graph = get_graph()
    
    # Run the graph
    final_state = await graph.ainvoke(state)
    
    return final_state


def run_agent_graph_sync(user_message: str, request_id: str = None) -> Dict[str, Any]:
    """
    Synchronous version of run_agent_graph.
    """
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(run_agent_graph(user_message, request_id))


# =============================================================================
# STREAMING SUPPORT
# =============================================================================

async def stream_agent_graph(user_message: str, request_id: str = None):
    """
    Stream the agent graph execution, yielding state after each node.
    
    This is useful for showing progress in a UI.
    
    Args:
        user_message: The user's input message
        request_id: Optional request ID for tracing
    
    Yields:
        Tuple of (node_name, state) after each node execution
    """
    state = create_initial_state(user_message, request_id)
    graph = get_graph()
    
    async for event in graph.astream(state):
        # event is a dict with node_name -> output
        for node_name, node_output in event.items():
            yield node_name, node_output


# =============================================================================
# GRAPH VISUALIZATION (for debugging)
# =============================================================================

def get_graph_mermaid() -> str:
    """
    Get Mermaid diagram representation of the graph.
    
    Returns:
        Mermaid diagram string
    """
    return """
graph TD
    START((Start)) --> router[Router]
    router -->|clarification| END1((End))
    router -->|has agents| dispatcher[Dispatcher]
    
    dispatcher -->|DataAgent| data_agent[Data Agent]
    dispatcher -->|MacroAgent| macro_agent[Macro Agent]
    dispatcher -->|OptimizationAgent| opt_agent[Optimization Agent]
    dispatcher -->|RebalanceAgent| rebal_agent[Rebalance Agent]
    dispatcher -->|BacktestAgent| backtest_agent[Backtest Agent]
    
    data_agent -->|more agents| dispatcher
    macro_agent -->|more agents| dispatcher
    opt_agent -->|more agents| dispatcher
    rebal_agent -->|more agents| dispatcher
    backtest_agent -->|more agents| dispatcher
    
    data_agent -->|done| synthesizer[Synthesizer]
    macro_agent -->|done| synthesizer
    opt_agent -->|done| synthesizer
    rebal_agent -->|done| synthesizer
    backtest_agent -->|done| synthesizer
    
    dispatcher -->|no agents| synthesizer
    synthesizer --> END2((End))
"""


def print_graph():
    """Print the graph structure for debugging."""
    print("=" * 60)
    print("AGENT GRAPH STRUCTURE")
    print("=" * 60)
    print(get_graph_mermaid())
    print("=" * 60)
