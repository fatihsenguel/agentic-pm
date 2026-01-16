# src/agents/state.py
# Purpose: Define the agent's state structure
# Principle: Minimal state - only what's needed for the graph to function

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Minimal state for the finance agent.
    
    Design Decision: We keep state minimal to reduce token usage.
    The 'messages' field uses add_messages reducer which handles:
    - Appending new messages
    - Deduplication by message ID
    
    Future extensions (Phase 3+):
    - current_portfolio: Dict[str, Any]
    - analysis_cache: Dict[str, Any]  
    - user_preferences: Dict[str, Any]
    """
    
    # Core: Conversation history (managed by LangGraph)
    messages: Annotated[Sequence[BaseMessage], add_messages]


# =============================================================================
# STATE UTILITIES (for context window management)
# =============================================================================

def trim_messages(state: AgentState, max_messages: int) -> AgentState:
    """
    Trim conversation history to prevent context overflow.
    Keeps system message (if present) + last N messages.
    
    Args:
        state: Current agent state
        max_messages: Maximum messages to keep
    
    Returns:
        State with trimmed messages
    """
    messages = list(state["messages"])
    
    if len(messages) <= max_messages:
        return state
    
    # Check if first message is system message
    from langchain_core.messages import SystemMessage
    
    if messages and isinstance(messages[0], SystemMessage):
        # Keep system + last (max_messages - 1)
        trimmed = [messages[0]] + messages[-(max_messages - 1):]
    else:
        # Keep last max_messages
        trimmed = messages[-max_messages:]
    
    return {"messages": trimmed}
