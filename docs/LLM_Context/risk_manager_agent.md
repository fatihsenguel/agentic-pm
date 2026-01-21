# FILE: src/agents/risk_manager_agent.py
# PURPOSE: Single point of entry. Orchestrates agents, validates inputs/outputs, enforces risk limits.

from .base_agent import SupervisorAgent
from .protocols import PortfolioTask, PortfolioResult, PortfolioConstraints, TaskType

@dataclass
class RiskManagerConfig:
    """Hard-coded safety limits."""
    default_max_weight: float = 0.40
    default_min_weight: float = 0.05
    default_max_volatility: float = 0.15
    
    # Safety Guardrails
    hard_max_volatility: float = 0.30      # Reject requests above this
    min_diversification_assets: int = 3    # Warn if fewer assets
    max_concentration_warning: float = 0.50

class RiskManagerAgent(SupervisorAgent):
    """
    1. Parse User Intent -> PortfolioTask
    2. Validate Constraints (Safety Check)
    3. Route to Sub-Agent (Data, Opt, Macro, Backtest)
    4. Validate Result (Quality Check)
    5. Add Risk Disclaimer
    """
    
    def get_system_prompt(self) -> str:
        return """
        You are the Risk Manager.
        1. UNDERSTAND request (universe, risk tolerance).
        2. VALIDATE constraints (max vol 5-30%).
        3. COORDINATE specialized agents.
        4. VALIDATE results (check concentration).
        5. SYNTHESIZE recommendation with DISCALIMERS.
        
        DO NOT make investment decisions.
        DO NOT guarantee returns.
        """

    async def process(self, state: AgentState) -> AgentState:
        """Main Execution Loop"""
        # 1. Parse Input
        user_msg = self._get_last_user_message(state)
        task = self._parse_mandate(user_msg) # Uses Regex/LLM to create PortfolioTask
        state.current_task = task
        
        # 2. Safety Check (Input)
        if errors := self._validate_constraints(task.constraints):
            state.warnings.extend(errors)

        # 3. Delegation (Routing)
        if task.task_type == TaskType.OPTIMIZE:
            # Pipeline: DataAgent -> OptimizationAgent
            await self.sub_agents["DataAgent"].process(state)
            await self.sub_agents["OptimizationAgent"].process(state)
            
        elif task.task_type == TaskType.BACKTEST:
            await self.sub_agents["BacktestAgent"].process(state)
            
        elif task.task_type == TaskType.ANALYZE_REGIME:
            await self.sub_agents["MacroAgent"].process(state)

        # 4. Safety Check (Output)
        final_result = self._synthesize_results(state)
        
        # 5. Format & Reply
        response = self._format_final_response(final_result)
        state.add_message("assistant", response)
        return state

    def _validate_result(self, result: PortfolioResult, task: PortfolioTask) -> List[str]:
        """Post-processing validation logic."""
        warnings = []
        # Check if volatility exceeds user request
        if result.expected_volatility > task.constraints.max_volatility:
            warnings.append(f"Volatility {result.expected_volatility} exceeds limit")
        
        # Check concentration (Herfindahl or simple max weight)
        if max(result.weights.values()) > self.config.max_concentration_warning:
            warnings.append("High concentration detected")
            
        return warnings

    # --- TOOLS (Exposed to LLM) ---
    def parse_user_mandate(self, msg: str) -> Dict: ...
    def validate_portfolio_constraints(self, **kwargs) -> Dict: ...
    def check_concentration_risk(self, weights: Dict) -> Dict: ...