# FILE: src/agents/state.py
# PURPOSE: Defines the "Global Memory" passed between nodes in the LangGraph.

from typing import TypedDict, Annotated, Sequence, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from dataclasses import dataclass, field
from .protocols import PortfolioTask, PortfolioResult

@dataclass
class AgentState:
    """
    The shared state object passed through the graph.
    """
    # 1. Chat History (User <-> AI)
    messages: List[BaseMessage] = field(default_factory=list)
    
    # 2. The Mandate (What are we doing?)
    current_task: Optional[PortfolioTask] = None
    
    # 3. The Results (What have we done?)
    sub_results: Dict[str, PortfolioResult] = field(default_factory=dict)
    
    # 4. Shared Data (e.g., Calculated Covariance Matrix)
    shared_data: Dict[str, Any] = field(default_factory=dict)
    
    # 5. Observability & Debugging
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    tool_calls_this_turn: int = 0
    
    def add_sub_result(self, agent_name: str, result: PortfolioResult):
        self.sub_results[agent_name] = result