"""
SNIPPET: agents/finance_agent.py
PURPOSE: Current single-agent implementation (LangGraph ReAct pattern)
PATTERN: ReAct Loop - Agent decides → Calls tools → Processes results → Decides again
"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from .state import AgentState, trim_messages
from .prompts import FINANCE_AGENT_SYSTEM_PROMPT
from portfolio_tool.tools.data_tools import ALL_DATA_TOOLS          # 8 tools
from portfolio_tool.tools.analytics_tools import ALL_ANALYTICS_TOOLS # 6 tools

ALL_TOOLS = ALL_DATA_TOOLS + ALL_ANALYTICS_TOOLS  # 14 total

# ========== NODE FUNCTIONS ==========

def agent_node(state: AgentState) -> dict:
    """
    LLM 'thinking' node - decides what to do next.
    
    Flow:
    1. Trim history (cost optimization)
    2. Ensure system prompt present
    3. Call LLM with tools bound
    4. Return: AIMessage (with optional tool_calls)
    """
    state = trim_messages(state, max_messages=10)
    
    llm = get_llm()  # From config.py
    llm_with_tools = llm.bind_tools(ALL_TOOLS, parallel_tool_calls=False)  # Sequential execution
    
    messages = [SystemMessage(FINANCE_AGENT_SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """
    Router: Tools needed? → "tools" | Done? → "__end__"
    """
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "__end__"

# ========== GRAPH CONSTRUCTION ==========

def create_finance_agent():
    """
    Factory: Builds LangGraph agent.
    
    Graph:
    ┌─────────┐   tool_calls   ┌─────────┐
    │  agent  │ ───────────────►│  tools  │
    └─────────┘                 └─────────┘
         │                           │
         │ no tool_calls             │
         ▼                           │
      [END]  ◄────────────────────────┘
    
    Flow:
    1. User query → agent_node (LLM decides)
    2. If tool_calls → tool_node (execute tools)
    3. Tool results → agent_node (LLM processes)
    4. Repeat until no tool_calls → END
    """
    tool_node = ToolNode(ALL_TOOLS)
    
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges("agent", should_continue, 
                                   {"tools": "tools", "__end__": END})
    workflow.add_edge("tools", "agent")  # Tools always loop back
    
    return workflow.compile()

# ========== CONVENIENCE API ==========

def chat(agent, user_message: str, conversation_history: list = None) -> str:
    """Simple chat interface. Returns agent's final response."""
    messages = (conversation_history or []) + [HumanMessage(user_message)]
    result = agent.invoke({"messages": messages})
    return result["messages"][-1].content

# ========== CURRENT LIMITATIONS (Phase 3) ==========
"""
WHAT WORKS:
✅ Sequential tool execution (1 tool at a time)
✅ Data fetching + analytics
✅ Conversation history management
✅ Cost optimization (message trimming)

WHAT DOESN'T WORK (needs Phase 4):
❌ Complex multi-step workflows (e.g., "Compare SAP with peers YOU choose")
   → Current agent doesn't autonomously select peers
❌ Document analysis (e.g., "Analyze this earnings call PDF")
   → No RAG capabilities
❌ Parallel execution of independent tasks
   → Sequential only
❌ Specialized reasoning
   → Single generalist agent, not specialized experts
"""

# ========== PHASE 4 TRANSITION PLAN ==========
"""
CURRENT (Phase 3):
User → Single Agent → 14 Tools → Data/Analytics

FUTURE (Phase 4):
User → Supervisor Agent → [Data Agent, Analyst Agent, RAG Agent] → Specialized Tools

Changes needed:
1. Create BaseAgent class (shared logic)
2. Create SupervisorAgent (routing + synthesis)
3. Create specialized agents (DataAgent, AnalystAgent, RAGAgent)
4. Define AgentTask, AgentResponse DTOs
5. Update AgentState to include agent coordination fields
6. Build multi-agent graph with parallel execution support
"""
