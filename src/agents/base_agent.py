"""
Base Agent Abstract Class for Quant Portfolio Manager.

This module defines the base class that all specialized agents inherit from.
It provides common functionality for:
- Tool management
- State handling
- LLM interaction patterns
- Logging and audit trails

Design Principles:
- Separation of Concerns: Each agent has specific capabilities
- Hot Potato Principle: Agents return processed summaries, not raw data
- Testability: All agents can be tested with mock dependencies
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type

from .protocols import PortfolioTask, PortfolioResult


class AgentRole(str, Enum):
    """Roles available for agents in the multi-agent system."""
    SUPERVISOR = "supervisor"  # Risk Manager - coordinates other agents
    DATA = "data"              # Data Agent - fetches and processes market data
    OPTIMIZATION = "optimization"  # Optimization Agent - portfolio optimization
    MACRO = "macro"            # Macro/RAG Agent - macro analysis
    BACKTEST = "backtest"      # Backtest Agent - strategy simulation


@dataclass
class AgentConfig:
    """Configuration for an agent instance."""
    name: str
    role: AgentRole
    
    # LLM settings
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.0  # Deterministic for quant tasks
    max_tokens: int = 4096
    
    # Behavior settings
    verbose: bool = False
    log_tool_calls: bool = True
    
    # Rate limiting
    max_tool_calls_per_turn: int = 10
    
    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMessage:
    """Message in agent communication."""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # For tool messages
    tool_name: Optional[str] = None
    tool_call_id: Optional[str] = None


@dataclass
class AgentState:
    """
    State maintained by an agent during execution.
    
    This is passed between agent nodes in LangGraph.
    """
    # Message history
    messages: List[AgentMessage] = field(default_factory=list)
    
    # Current task
    current_task: Optional[PortfolioTask] = None
    
    # Accumulated results from sub-agents
    sub_results: Dict[str, PortfolioResult] = field(default_factory=dict)
    
    # Shared data (e.g., covariance matrix computed by Data Agent)
    shared_data: Dict[str, Any] = field(default_factory=dict)
    
    # Execution tracking
    tool_calls_this_turn: int = 0
    total_tool_calls: int = 0
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_message(self, role: str, content: str, **kwargs) -> None:
        """Add a message to the state."""
        self.messages.append(AgentMessage(role=role, content=content, **kwargs))
    
    def add_tool_result(self, tool_name: str, result: Any, tool_call_id: str) -> None:
        """Add a tool result to the state."""
        self.messages.append(AgentMessage(
            role="tool",
            content=str(result),
            tool_name=tool_name,
            tool_call_id=tool_call_id,
        ))
        self.tool_calls_this_turn += 1
        self.total_tool_calls += 1
    
    def add_sub_result(self, agent_name: str, result: PortfolioResult) -> None:
        """Add a result from a sub-agent."""
        self.sub_results[agent_name] = result
    
    def get_recent_messages(self, n: int = 10) -> List[AgentMessage]:
        """Get the n most recent messages."""
        return self.messages[-n:]
    
    def clear_turn(self) -> None:
        """Clear per-turn tracking (called at end of each turn)."""
        self.tool_calls_this_turn = 0


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Quant Portfolio Manager.
    
    Subclasses must implement:
    - capabilities: List of what the agent can do
    - get_tools(): Return list of tools available to this agent
    - get_system_prompt(): Return the agent's system prompt
    - process(): Main processing logic
    
    Example Usage:
        class DataAgent(BaseAgent):
            @property
            def capabilities(self) -> List[str]:
                return ["fetch_prices", "calculate_covariance", "calculate_returns"]
            
            def get_tools(self) -> List[Callable]:
                return [fetch_prices_tool, covariance_tool, returns_tool]
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the agent with configuration.
        
        Args:
            config: Agent configuration including name, role, and settings
        """
        self.config = config
        self._tools: Optional[List[Callable]] = None
        self._tool_map: Optional[Dict[str, Callable]] = None
    
    @property
    def name(self) -> str:
        """Agent's name."""
        return self.config.name
    
    @property
    def role(self) -> AgentRole:
        """Agent's role in the system."""
        return self.config.role
    
    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """
        List of capabilities this agent provides.
        
        Used by the supervisor to determine which agent to delegate to.
        
        Returns:
            List of capability strings, e.g., ["fetch_prices", "calculate_covariance"]
        """
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Callable]:
        """
        Get the list of tools available to this agent.
        
        Returns:
            List of tool functions (decorated with @tool)
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        
        The prompt should:
        - Define the agent's role and capabilities
        - Include scope guards (what NOT to do)
        - Provide formatting guidelines for responses
        
        Returns:
            System prompt string
        """
        pass
    
    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """
        Main processing logic for the agent.
        
        This is called by LangGraph when the agent receives a task.
        
        Args:
            state: Current agent state with messages and task
            
        Returns:
            Updated agent state
        """
        pass
    
    @property
    def tools(self) -> List[Callable]:
        """Lazily load and cache tools."""
        if self._tools is None:
            self._tools = self.get_tools()
        return self._tools
    
    @property
    def tool_map(self) -> Dict[str, Callable]:
        """Map of tool names to tool functions."""
        if self._tool_map is None:
            self._tool_map = {tool.__name__: tool for tool in self.tools}
        return self._tool_map
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a specific tool by name."""
        return self.tool_map.get(name)
    
    def can_handle(self, capability: str) -> bool:
        """Check if this agent can handle a specific capability."""
        return capability in self.capabilities
    
    def create_result(
        self,
        task_id: str,
        success: bool,
        weights: Optional[Dict[str, float]] = None,
        error_message: Optional[str] = None,
        **kwargs
    ) -> PortfolioResult:
        """
        Helper to create a standardized PortfolioResult.
        
        Args:
            task_id: ID of the task this result is for
            success: Whether the task succeeded
            weights: Portfolio weights (if applicable)
            error_message: Error message (if failed)
            **kwargs: Additional fields for PortfolioResult
            
        Returns:
            PortfolioResult instance
        """
        return PortfolioResult(
            agent_name=self.name,
            task_id=task_id,
            success=success,
            weights=weights or {},
            error_message=error_message,
            **kwargs
        )
    
    def log(self, message: str, level: str = "info") -> None:
        """
        Log a message if verbose mode is enabled.
        
        Args:
            message: Message to log
            level: Log level (info, warning, error)
        """
        if self.config.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            prefix = {
                "info": "ℹ️",
                "warning": "⚠️",
                "error": "❌",
                "success": "✅",
            }.get(level, "•")
            print(f"[{timestamp}] {prefix} [{self.name}] {message}")
    
    def validate_task(self, task: PortfolioTask) -> List[str]:
        """
        Validate a task before processing.
        
        Override in subclasses for specific validation.
        
        Args:
            task: Task to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not task.universe:
            errors.append("Task must specify a universe of assets")
        
        return errors
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', role={self.role.value})"


class SupervisorAgent(BaseAgent):
    """
    Base class for supervisor agents that coordinate other agents.
    
    The supervisor:
    - Receives tasks from users
    - Parses and validates constraints
    - Delegates to specialized agents
    - Synthesizes final results
    
    For the Quant PM, this is the Risk Manager Agent.
    """
    
    def __init__(self, config: AgentConfig, sub_agents: List[BaseAgent]):
        """
        Initialize supervisor with sub-agents.
        
        Args:
            config: Agent configuration
            sub_agents: List of agents this supervisor can delegate to
        """
        super().__init__(config)
        self.sub_agents = {agent.name: agent for agent in sub_agents}
        self._capability_map: Optional[Dict[str, str]] = None
    
    @property
    def capability_map(self) -> Dict[str, str]:
        """Map capabilities to agent names."""
        if self._capability_map is None:
            self._capability_map = {}
            for agent in self.sub_agents.values():
                for cap in agent.capabilities:
                    self._capability_map[cap] = agent.name
        return self._capability_map
    
    def get_agent_for_capability(self, capability: str) -> Optional[BaseAgent]:
        """Get the agent that can handle a specific capability."""
        agent_name = self.capability_map.get(capability)
        if agent_name:
            return self.sub_agents.get(agent_name)
        return None
    
    def delegate(self, capability: str, state: AgentState) -> Optional[BaseAgent]:
        """
        Delegate a capability to the appropriate sub-agent.
        
        Args:
            capability: The capability needed
            state: Current state to pass to sub-agent
            
        Returns:
            The sub-agent that can handle this, or None
        """
        agent = self.get_agent_for_capability(capability)
        if agent:
            self.log(f"Delegating '{capability}' to {agent.name}")
        else:
            self.log(f"No agent found for capability: {capability}", level="warning")
        return agent
    
    def synthesize_results(self, state: AgentState) -> PortfolioResult:
        """
        Synthesize results from all sub-agents into a final result.
        
        Override in subclasses for custom synthesis logic.
        
        Args:
            state: State containing sub-agent results
            
        Returns:
            Final synthesized PortfolioResult
        """
        # Default: return the first successful result
        for result in state.sub_results.values():
            if result.success:
                return result
        
        # If all failed, return error
        errors = [r.error_message for r in state.sub_results.values() if r.error_message]
        return self.create_result(
            task_id=state.current_task.task_id if state.current_task else "unknown",
            success=False,
            error_message="; ".join(errors) if errors else "All sub-agents failed"
        )


# Type alias for agent factory functions
AgentFactory = Callable[[AgentConfig], BaseAgent]


def register_agent(role: AgentRole) -> Callable[[Type[BaseAgent]], Type[BaseAgent]]:
    """
    Decorator to register an agent class for a specific role.
    
    Usage:
        @register_agent(AgentRole.DATA)
        class DataAgent(BaseAgent):
            ...
    """
    _agent_registry: Dict[AgentRole, Type[BaseAgent]] = {}
    
    def decorator(cls: Type[BaseAgent]) -> Type[BaseAgent]:
        _agent_registry[role] = cls
        return cls
    
    return decorator

# Alias for clearer naming when used alongside LangGraph's AgentState
MultiAgentState = AgentState