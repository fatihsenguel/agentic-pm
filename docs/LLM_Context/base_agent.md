# FILE: src/agents/base_agent.py
# PURPOSE: Abstract template for all agents. Enforces consistency.

class AgentRole(Enum):
    SUPERVISOR = "supervisor"
    DATA = "data"
    OPTIMIZATION = "optimization"
    MACRO = "macro"
    BACKTEST = "backtest"

class BaseAgent(ABC):
    """
    Parent class for all agents.
    """
    def __init__(self, config: AgentConfig):
        self.config = config

    @abstractmethod
    def get_tools(self) -> List[Callable]:
        """must return list of @tool functions"""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """must return the system instruction"""
        pass

    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """
        Main entry point. Receives State -> Modifies State -> Returns State.
        """
        pass

    def create_result(self, success: bool, **kwargs) -> PortfolioResult:
        """Helper to create standardized results."""
        return PortfolioResult(agent_name=self.name, success=success, **kwargs)

class SupervisorAgent(BaseAgent):
    """
    Special agent that can delegate tasks to other agents.
    """
    def __init__(self, config, sub_agents: List[BaseAgent]):
        self.sub_agents = {a.name: a for a in sub_agents}
    
    def delegate(self, capability: str, state: AgentState) -> Optional[BaseAgent]:
        """Finds the right agent for the job."""
        pass