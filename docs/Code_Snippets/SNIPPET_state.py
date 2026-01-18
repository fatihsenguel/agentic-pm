"""
SNIPPET: agents/state.py
PURPOSE: LangGraph state definition (minimal for cost efficiency)
"""

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    Current state (Phase 3 - Single Agent):
    - messages: Conversation history (auto-managed by LangGraph add_messages reducer)
    
    Future state (Phase 4 - Multi-Agent):
    - current_task: AgentTask (what supervisor delegated)
    - agent_responses: Dict[str, AgentResponse] (responses from specialized agents)
    - shared_context: Dict (data shared between agents)
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]

def trim_messages(state: AgentState, max_messages: int) -> AgentState:
    """
    Cost optimization: Keep system prompt + last N messages.
    Example: max_messages=10 → [SystemMessage, ...last 9 messages]
    """
    messages = list(state["messages"])
    if len(messages) <= max_messages:
        return state
    
    # Preserve system message if present
    if isinstance(messages[0], SystemMessage):
        return {"messages": [messages[0]] + messages[-(max_messages - 1):]}
    return {"messages": messages[-max_messages:]}
