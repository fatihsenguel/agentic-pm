# src/agents/finance_agent.py
# Purpose: Main finance agent using LangGraph
# Principle: Minimal, focused, cost-efficient

from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# Internal imports
from .config import get_llm, AGENT_SETTINGS
from .state import AgentState, trim_messages
from .prompts import FINANCE_AGENT_SYSTEM_PROMPT

# Tools - imported from portfolio_tool
from portfolio_tool.tools.data_tools import ALL_DATA_TOOLS


# =============================================================================
# NODE FUNCTIONS
# =============================================================================

def agent_node(state: AgentState) -> dict:
    """
    The 'thinking' node - LLM decides what to do.
    
    Flow:
    1. Trim history if too long (cost optimization!)
    2. Call LLM with tools bound
    3. Return response (either final answer or tool call)
    """
    # Cost optimization: trim old messages
    state = trim_messages(state, AGENT_SETTINGS.max_conversation_history)
    
    # Get configured LLM with tools
    llm = get_llm()
    llm_with_tools = llm.bind_tools(ALL_DATA_TOOLS, parallel_tool_calls=False)
    
    # Ensure system prompt is present
    messages = list(state["messages"])
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=FINANCE_AGENT_SYSTEM_PROMPT)] + messages
    
    # Call LLM
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """
    Router: Decide if we should call tools or end.
    
    Logic:
    - If last message has tool_calls → go to tools node
    - Otherwise → end and return response to user
    """
    last_message = state["messages"][-1]
    
    # Check if LLM wants to call tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    return "__end__"


# =============================================================================
# GRAPH BUILDER
# =============================================================================

def create_finance_agent():
    """
    Factory: Creates the finance agent graph.
    
    Graph Structure:
    ┌─────────┐     tool_calls     ┌─────────┐
    │  agent  │ ─────────────────► │  tools  │
    └─────────┘                    └─────────┘
         │                              │
         │ no tool_calls                │
         ▼                              │
      [END]  ◄──────────────────────────┘
    
    Returns:
        Compiled LangGraph agent
    """
    # Create tool node with all data tools
    tool_node = ToolNode(ALL_DATA_TOOLS)
    
    # Build graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "__end__": END,
        }
    )
    
    # Tools always go back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile and return
    return workflow.compile()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def chat(agent, user_message: str, conversation_history: list = None) -> str:
    """
    Simple chat interface for the agent.
    
    Args:
        agent: Compiled LangGraph agent
        user_message: User's input
        conversation_history: Optional previous messages
    
    Returns:
        Agent's response as string
    """
    # Build messages
    messages = conversation_history or []
    messages.append(HumanMessage(content=user_message))
    
    # Invoke agent
    result = agent.invoke({"messages": messages})
    
    # Extract final response
    final_message = result["messages"][-1]
    
    return final_message.content


def run_single_query(query: str) -> str:
    """
    One-shot query - no conversation history.
    Useful for scripts and testing.
    
    Args:
        query: The question or command
    
    Returns:
        Agent's response as string
    """
    agent = create_finance_agent()
    return chat(agent, query)


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    # Quick test
    print("Creating finance agent...")
    agent = create_finance_agent()
    
    print("\nTesting with: 'What assets are being tracked?'")
    response = chat(agent, "What assets are being tracked?")
    print(f"\nResponse: {response}")
