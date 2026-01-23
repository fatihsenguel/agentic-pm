# src/agents/state.py
# Purpose: Define the agent's state structure for LangGraph
# Principle: Minimal state - only what's needed for the graph to function
# Updated: Phase 6.2 - Full multi-agent state management

from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph.message import add_messages
from datetime import datetime
from dataclasses import dataclass, field


# =============================================================================
# CORE AGENT STATE (LangGraph Compatible)
# =============================================================================

class AgentState(TypedDict):
    """
    Global state passed through LangGraph.
    
    Design Decisions:
    - 'messages' uses add_messages reducer for chat history
    - 'router_decision' contains the Smart Router's output
    - 'sub_results' stores results from each worker agent
    - 'shared_data' for passing computed data between agents (Hot Potato!)
    
    Hot Potato Principle:
    - shared_data contains SUMMARIES, not raw DataFrames
    - Each agent reads what it needs, writes its summary
    """
    
    # Core: Conversation history (managed by LangGraph reducer)
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Router decision (from Smart Router - Phase 6.1)
    router_decision: Optional[Dict[str, Any]]
    
    # Current execution context
    current_agent: Optional[str]
    execution_step: int
    agents_to_run: List[str]  # Remaining agents in execution order
    
    # Results from sub-agents
    sub_results: Dict[str, Dict[str, Any]]
    
    # Shared computed data (Hot Potato - pass summaries, not raw data!)
    # Example keys: "covariance_matrix", "macro_regime", "latest_prices"
    shared_data: Dict[str, Any]
    
    # Request tracking
    request_id: str
    started_at: str
    
    # Error tracking
    errors: List[str]
    warnings: List[str]
    
    # Final response (set by synthesizer)
    final_response: Optional[str]
    
    # Human-in-the-loop (Phase 6.11)
    requires_approval: bool
    approval_status: Optional[str]  # "pending", "approved", "rejected"


# =============================================================================
# STATE FACTORY
# =============================================================================

def create_initial_state(
    user_message: str,
    request_id: Optional[str] = None,
) -> AgentState:
    """
    Create a fresh initial state for a new request.
    
    Args:
        user_message: The user's input message
        request_id: Unique identifier for this request (for tracing)
    
    Returns:
        Initialized AgentState
    """
    from uuid import uuid4
    
    return AgentState(
        messages=[HumanMessage(content=user_message)],
        router_decision=None,
        current_agent=None,
        execution_step=0,
        agents_to_run=[],
        sub_results={},
        shared_data={},
        request_id=request_id or str(uuid4())[:8],
        started_at=datetime.now().isoformat(),
        errors=[],
        warnings=[],
        final_response=None,
        requires_approval=False,
        approval_status=None,
    )


# =============================================================================
# STATE UPDATE HELPERS
# =============================================================================

def set_router_decision(state: AgentState, decision: Dict[str, Any]) -> Dict[str, Any]:
    """Set the router decision and initialize execution order."""
    agents_to_run = decision.get("execution_order", [])
    return {
        "router_decision": decision,
        "agents_to_run": agents_to_run,
    }


def mark_agent_complete(state: AgentState, agent_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """Mark an agent as complete and store its result."""
    # Update sub_results
    new_results = {**state.get("sub_results", {}), agent_name: result}
    
    # Remove from agents_to_run
    remaining = [a for a in state.get("agents_to_run", []) if a != agent_name]
    
    return {
        "sub_results": new_results,
        "agents_to_run": remaining,
        "execution_step": state.get("execution_step", 0) + 1,
    }


def add_shared_data(state: AgentState, key: str, value: Any) -> Dict[str, Any]:
    """
    Add shared data for other agents to use.
    
    IMPORTANT: Value should be a SUMMARY, not raw data!
    """
    new_shared = {**state.get("shared_data", {}), key: value}
    return {"shared_data": new_shared}


def add_error(state: AgentState, error: str) -> Dict[str, Any]:
    """Add an error to the state."""
    errors = list(state.get("errors", []))
    errors.append(error)
    return {"errors": errors}


def add_warning(state: AgentState, warning: str) -> Dict[str, Any]:
    """Add a warning to the state."""
    warnings = list(state.get("warnings", []))
    warnings.append(warning)
    return {"warnings": warnings}


def set_final_response(state: AgentState, response: str) -> Dict[str, Any]:
    """Set the final response to send to user."""
    return {
        "final_response": response,
        "messages": [AIMessage(content=response)],
    }


def request_approval(state: AgentState, reason: str = "") -> Dict[str, Any]:
    """Request human approval before proceeding."""
    return {
        "requires_approval": True,
        "approval_status": "pending",
    }


# =============================================================================
# STATE INSPECTION HELPERS
# =============================================================================

def get_next_agent(state: AgentState) -> Optional[str]:
    """Get the next agent to execute."""
    agents_to_run = state.get("agents_to_run", [])
    return agents_to_run[0] if agents_to_run else None


def is_execution_complete(state: AgentState) -> bool:
    """Check if all agents have completed."""
    return len(state.get("agents_to_run", [])) == 0


def has_errors(state: AgentState) -> bool:
    """Check if there are any errors."""
    return len(state.get("errors", [])) > 0


def get_agent_result(state: AgentState, agent_name: str) -> Optional[Dict[str, Any]]:
    """Get the result from a specific agent."""
    return state.get("sub_results", {}).get(agent_name)


def get_shared_data(state: AgentState, key: str, default: Any = None) -> Any:
    """Get shared data by key."""
    return state.get("shared_data", {}).get(key, default)


def get_user_message(state: AgentState) -> str:
    """Get the original user message."""
    messages = state.get("messages", [])
    for msg in messages:
        if isinstance(msg, HumanMessage):
            return msg.content
    return ""


def get_execution_summary(state: AgentState) -> Dict[str, Any]:
    """Get a summary of the current execution state."""
    return {
        "request_id": state.get("request_id"),
        "started_at": state.get("started_at"),
        "current_agent": state.get("current_agent"),
        "execution_step": state.get("execution_step", 0),
        "agents_completed": list(state.get("sub_results", {}).keys()),
        "agents_remaining": state.get("agents_to_run", []),
        "shared_data_keys": list(state.get("shared_data", {}).keys()),
        "num_errors": len(state.get("errors", [])),
        "num_warnings": len(state.get("warnings", [])),
        "has_final_response": state.get("final_response") is not None,
    }


# =============================================================================
# MESSAGE UTILITIES
# =============================================================================

def trim_messages(state: AgentState, max_messages: int) -> Dict[str, Any]:
    """
    Trim conversation history to prevent context overflow.
    Keeps system message (if present) + last N messages.
    """
    messages = list(state.get("messages", []))
    
    if len(messages) <= max_messages:
        return {}  # No change needed
    
    if messages and isinstance(messages[0], SystemMessage):
        # Keep system + last (max_messages - 1)
        trimmed = [messages[0]] + messages[-(max_messages - 1):]
    else:
        # Keep last max_messages
        trimmed = messages[-max_messages:]
    
    return {"messages": trimmed}
