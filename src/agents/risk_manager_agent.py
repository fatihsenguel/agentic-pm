"""
Risk Manager Agent (Supervisor) for Quant Portfolio Manager.

The Risk Manager is the supervisor agent that:
- Receives user requests and parses investment mandates
- Validates constraints and risk limits
- Coordinates specialized agents (Data, Optimization, Macro, Backtest)
- Synthesizes final recommendations with risk context
- Ensures all outputs meet compliance requirements

Design Principles:
- Single point of contact for users
- Validates all outputs before returning
- Maintains audit trail for compliance
- Does NOT make investment decisions - only coordinates and validates
"""

from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .base_agent import BaseAgent, SupervisorAgent, AgentConfig, AgentRole, AgentState
from .protocols import (
    PortfolioTask, 
    PortfolioResult, 
    PortfolioConstraints,
    TaskType,
    OptimizationMethod,
    TAARule,
    RebalanceFrequency,
)


@dataclass
class RiskManagerConfig(AgentConfig):
    """Configuration for Risk Manager Agent."""
    
    # Default constraints if user doesn't specify
    default_max_weight: float = 0.40  # 40% max per asset
    default_min_weight: float = 0.05  # 5% min per asset  
    default_max_volatility: float = 0.15  # 15% max portfolio vol
    
    # Validation thresholds
    max_concentration_warning: float = 0.50  # Warn if any asset > 50%
    min_diversification_assets: int = 3  # Warn if fewer assets
    
    # Risk limits
    hard_max_volatility: float = 0.30  # Reject if > 30%
    hard_max_drawdown: float = 0.40  # Reject if historical DD > 40%


class RiskManagerAgent(SupervisorAgent):
    """
    Risk Manager Agent - Supervisor for the Multi-Agent System.
    
    This agent:
    1. Parses user requests into structured PortfolioTasks
    2. Validates constraints are reasonable and complete
    3. Delegates to specialized agents
    4. Validates results meet risk requirements
    5. Synthesizes final response with risk context
    
    It does NOT:
    - Make investment decisions
    - Choose specific assets
    - Time the market
    """
    
    def __init__(
        self, 
        config: Optional[RiskManagerConfig] = None,
        sub_agents: Optional[List[BaseAgent]] = None
    ):
        """Initialize Risk Manager."""
        if config is None:
            config = RiskManagerConfig(
                name="RiskManager",
                role=AgentRole.SUPERVISOR,
                temperature=0.1,  # Slight variation for natural responses
            )
        
        super().__init__(config, sub_agents or [])
        self.config: RiskManagerConfig = config
    
    @property
    def capabilities(self) -> List[str]:
        """Risk Manager coordinates all capabilities."""
        return [
            "parse_mandate",
            "validate_constraints", 
            "coordinate_optimization",
            "coordinate_backtest",
            "validate_results",
            "generate_recommendation",
        ]
    
    def get_tools(self) -> List[Callable]:
        """Tools for the Risk Manager."""
        return [
            self.parse_user_mandate,
            self.validate_portfolio_constraints,
            self.check_concentration_risk,
            self.validate_optimization_result,
            self.generate_risk_summary,
        ]
    
    def get_system_prompt(self) -> str:
        """System prompt for Risk Manager."""
        return """You are the Risk Manager Agent for a Quant Portfolio Manager system.

Your role is to:
1. UNDERSTAND user investment requests and extract:
   - Investment universe (which assets)
   - Risk constraints (max volatility, max drawdown, etc.)
   - Optimization preferences (method, time horizon)
   
2. VALIDATE that constraints are reasonable:
   - Maximum volatility between 5% and 30%
   - Diversification across at least 3 assets
   - Weights sum to 100%
   
3. COORDINATE specialized agents:
   - Data Agent: Fetch prices, calculate covariance
   - Optimization Agent: Run Markowitz, Risk Parity
   - Backtest Agent: Simulate strategies
   - Macro Agent: Analyze market regime
   
4. VALIDATE results:
   - Check constraints are satisfied
   - Flag concentration risks
   - Ensure data quality is sufficient
   
5. SYNTHESIZE final recommendation:
   - Present results clearly
   - Include risk context
   - Add appropriate caveats

SCOPE GUARDS:
- Do NOT recommend specific investment actions
- Do NOT predict market movements
- Do NOT guarantee any returns
- Always include risk disclaimers

CONSTRAINTS YOU ENFORCE:
- Default max weight per asset: 40%
- Default min weight per asset: 5%
- Default max portfolio volatility: 15%
- Minimum 3 assets for diversification
- Warn if any position > 50%

OUTPUT FORMAT:
Always structure responses with:
1. Summary of user request
2. Constraints applied
3. Results from optimization
4. Risk assessment
5. Caveats and disclaimers
"""
    
    async def process(self, state: AgentState) -> AgentState:
        """
        Main processing loop for Risk Manager.
        
        Orchestrates the multi-agent workflow.
        """
        # Extract user request from messages
        user_message = self._get_last_user_message(state)
        
        if not user_message:
            state.add_message("assistant", "No user request found.")
            return state
        
        self.log(f"Processing user request: {user_message[:100]}...")
        
        # Step 1: Parse the mandate
        task = self._parse_mandate(user_message, state)
        state.current_task = task
        
        if not task:
            state.add_message(
                "assistant", 
                "I couldn't understand your investment request. Please specify:\n"
                "- Which assets to include (e.g., SPY, TLT, GLD)\n"
                "- Your risk tolerance (e.g., max 12% volatility)\n"
                "- What you want to do (optimize, backtest, rebalance)"
            )
            return state
        
        # Step 2: Validate constraints
        validation_errors = self._validate_constraints(task.constraints)
        if validation_errors:
            state.add_message(
                "assistant",
                f"⚠️ Constraint Issues:\n" + "\n".join(f"- {e}" for e in validation_errors)
            )
            # Continue with warnings, don't fail
            state.warnings.extend(validation_errors)
        
        # Step 3: Delegate to appropriate agents based on task type
        if task.task_type == TaskType.OPTIMIZE:
            await self._handle_optimization(state)
        elif task.task_type == TaskType.BACKTEST:
            await self._handle_backtest(state)
        elif task.task_type == TaskType.REBALANCE:
            await self._handle_rebalance(state)
        elif task.task_type == TaskType.ANALYZE_REGIME:
            await self._handle_regime_analysis(state)
        else:
            state.add_message("assistant", f"Unknown task type: {task.task_type}")
        
        # Step 4: Synthesize and validate final result
        final_result = self._synthesize_results(state)
        
        # Step 5: Add risk context and caveats
        response = self._format_final_response(final_result, state)
        state.add_message("assistant", response)
        
        return state
    
    def _get_last_user_message(self, state: AgentState) -> Optional[str]:
        """Extract the last user message from state."""
        for msg in reversed(state.messages):
            if msg.role == "user":
                return msg.content
        return None
    
    def _parse_mandate(self, user_message: str, state: AgentState) -> Optional[PortfolioTask]:
        """
        Parse user message into a structured PortfolioTask.
        
        This is where we translate natural language to structured parameters.
        """
        # In a full implementation, this would use LLM to parse
        # For now, we'll implement basic parsing
        
        message_lower = user_message.lower()
        
        # Detect task type
        task_type = TaskType.OPTIMIZE  # Default
        if "backtest" in message_lower:
            task_type = TaskType.BACKTEST
        elif "rebalance" in message_lower or "drift" in message_lower:
            task_type = TaskType.REBALANCE
        elif "regime" in message_lower or "macro" in message_lower or "fed" in message_lower:
            task_type = TaskType.ANALYZE_REGIME
        
        # Extract universe (look for ticker patterns)
        import re
        ticker_pattern = r'\b([A-Z]{2,5})\b'
        potential_tickers = re.findall(ticker_pattern, user_message)
        
        # Filter to likely tickers (exclude common words)
        exclude_words = {'THE', 'AND', 'FOR', 'WITH', 'MAX', 'MIN', 'USD', 'EUR', 'GBP'}
        universe = [t for t in potential_tickers if t not in exclude_words]
        
        # If no tickers found, check for common asset classes
        if not universe:
            if "equity" in message_lower or "stock" in message_lower:
                universe.append("SPY")
            if "bond" in message_lower:
                universe.append("TLT")
            if "gold" in message_lower:
                universe.append("GLD")
            if "reit" in message_lower:
                universe.append("VNQ")
        
        # Extract constraints
        constraints = PortfolioConstraints()
        
        # Look for volatility constraint
        vol_match = re.search(r'(?:max|maximum)?\s*(?:vol|volatility)\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*%?', message_lower)
        if vol_match:
            vol = float(vol_match.group(1))
            if vol > 1:  # Assume percentage if > 1
                vol = vol / 100
            constraints.max_volatility = vol
        else:
            constraints.max_volatility = self.config.default_max_volatility
        
        # Look for weight constraints
        max_weight_match = re.search(r'max(?:imum)?\s*weight\s*(?:of|:)?\s*(\d+(?:\.\d+)?)\s*%?', message_lower)
        if max_weight_match:
            mw = float(max_weight_match.group(1))
            if mw > 1:
                mw = mw / 100
            constraints.max_weight = mw
        else:
            constraints.max_weight = self.config.default_max_weight
        
        constraints.min_weight = self.config.default_min_weight
        
        # Detect optimization method preference
        opt_method = None
        if "risk parity" in message_lower:
            opt_method = OptimizationMethod.RISK_PARITY
        elif "markowitz" in message_lower or "mean-variance" in message_lower or "mean variance" in message_lower:
            opt_method = OptimizationMethod.MEAN_VARIANCE
        elif "min var" in message_lower or "minimum variance" in message_lower:
            opt_method = OptimizationMethod.MIN_VARIANCE
        elif "sharpe" in message_lower:
            opt_method = OptimizationMethod.MAX_SHARPE
        
        # Extract time period
        period = "5Y"  # Default
        if "10 year" in message_lower or "10y" in message_lower:
            period = "10Y"
        elif "3 year" in message_lower or "3y" in message_lower:
            period = "3Y"
        elif "1 year" in message_lower or "1y" in message_lower:
            period = "1Y"
        
        # Create task
        return PortfolioTask(
            task_type=task_type,
            universe=universe if universe else ["SPY", "TLT", "GLD"],  # Default universe
            constraints=constraints,
            optimization_method=opt_method,
            historical_period=period,
            metadata={"original_request": user_message}
        )
    
    def _validate_constraints(self, constraints: PortfolioConstraints) -> List[str]:
        """Validate constraints are reasonable."""
        errors = []
        
        if constraints.max_volatility:
            if constraints.max_volatility < 0.05:
                errors.append(f"Max volatility {constraints.max_volatility:.1%} is very low - may not find feasible solution")
            if constraints.max_volatility > self.config.hard_max_volatility:
                errors.append(f"Max volatility {constraints.max_volatility:.1%} exceeds hard limit of {self.config.hard_max_volatility:.1%}")
        
        if constraints.max_weight and constraints.max_weight < 0.1:
            errors.append(f"Max weight {constraints.max_weight:.1%} is very restrictive")
        
        if constraints.min_weight and constraints.min_weight > 0.2:
            errors.append(f"Min weight {constraints.min_weight:.1%} may be too high for diversification")
        
        return errors
    
    async def _handle_optimization(self, state: AgentState) -> None:
        """Handle portfolio optimization task."""
        task = state.current_task
        self.log(f"Starting optimization for {task.universe}")
        
        # 1. Get data from Data Agent
        data_agent = self.sub_agents.get("DataAgent")
        if data_agent:
            state = await data_agent.process(state)
        else:
            self.log("DataAgent not available - using direct data fetch", "warning")
        
        # 2. Run optimization via Optimization Agent
        opt_agent = self.sub_agents.get("OptimizationAgent")
        if opt_agent:
            state = await opt_agent.process(state)
        else:
            self.log("OptimizationAgent not available", "warning")
            # Store placeholder result
            state.add_sub_result("OptimizationAgent", PortfolioResult(
                agent_name="OptimizationAgent",
                task_id=task.task_id,
                success=False,
                error_message="Optimization Agent not configured"
            ))
    
    async def _handle_backtest(self, state: AgentState) -> None:
        """Handle backtest task."""
        task = state.current_task
        self.log(f"Starting backtest for {task.universe}")
        
        # Backtest Agent handles the simulation
        backtest_agent = self.sub_agents.get("BacktestAgent")
        if backtest_agent:
            state = await backtest_agent.process(state)
        else:
            self.log("BacktestAgent not available", "warning")
    
    async def _handle_rebalance(self, state: AgentState) -> None:
        """Handle rebalance analysis task."""
        task = state.current_task
        self.log(f"Analyzing rebalance for {task.universe}")
        
        # This would delegate to a rebalance analysis function
        # For now, placeholder
        state.add_sub_result("Rebalance", PortfolioResult(
            agent_name="RiskManager",
            task_id=task.task_id,
            success=True,
            reasoning="Rebalance analysis placeholder",
        ))
    
    async def _handle_regime_analysis(self, state: AgentState) -> None:
        """Handle macro regime analysis task."""
        task = state.current_task
        self.log(f"Analyzing market regime")
        
        # Macro Agent handles regime detection
        macro_agent = self.sub_agents.get("MacroAgent")
        if macro_agent:
            state = await macro_agent.process(state)
        else:
            self.log("MacroAgent not available", "warning")
    
    def _synthesize_results(self, state: AgentState) -> PortfolioResult:
        """Synthesize results from all sub-agents."""
        task = state.current_task
        
        # Collect all successful results
        successful_results = [
            r for r in state.sub_results.values() if r.success
        ]
        
        if not successful_results:
            # All failed
            errors = [r.error_message for r in state.sub_results.values() if r.error_message]
            return PortfolioResult(
                agent_name=self.name,
                task_id=task.task_id if task else "unknown",
                success=False,
                error_message="; ".join(errors) if errors else "No results available"
            )
        
        # Get the primary result (usually from Optimization or Backtest agent)
        primary = successful_results[0]
        
        # Validate the result
        validation = self._validate_result(primary, task)
        
        # Merge warnings
        all_warnings = list(state.warnings)
        all_warnings.extend(primary.warnings)
        all_warnings.extend(validation)
        
        return PortfolioResult(
            agent_name=self.name,
            task_id=task.task_id if task else primary.task_id,
            success=True,
            weights=primary.weights,
            expected_return=primary.expected_return,
            expected_volatility=primary.expected_volatility,
            sharpe_ratio=primary.sharpe_ratio,
            risk_decomposition=primary.risk_decomposition,
            backtest_metrics=primary.backtest_metrics,
            optimization_method=primary.optimization_method,
            constraints_applied=primary.constraints_applied,
            data_period=primary.data_period,
            reasoning=primary.reasoning,
            warnings=all_warnings,
        )
    
    def _validate_result(self, result: PortfolioResult, task: Optional[PortfolioTask]) -> List[str]:
        """Validate optimization result meets constraints."""
        warnings = []
        
        if not result.weights:
            return warnings
        
        # Check concentration
        max_weight = max(result.weights.values()) if result.weights else 0
        if max_weight > self.config.max_concentration_warning:
            warnings.append(f"⚠️ High concentration: {max_weight:.1%} in single asset")
        
        # Check diversification
        n_assets = len([w for w in result.weights.values() if w > 0.01])
        if n_assets < self.config.min_diversification_assets:
            warnings.append(f"⚠️ Limited diversification: only {n_assets} meaningful positions")
        
        # Check volatility constraint
        if task and task.constraints.max_volatility and result.expected_volatility:
            if result.expected_volatility > task.constraints.max_volatility:
                warnings.append(
                    f"⚠️ Volatility {result.expected_volatility:.1%} exceeds target {task.constraints.max_volatility:.1%}"
                )
        
        # Check weights sum to 1
        weight_sum = sum(result.weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            warnings.append(f"⚠️ Weights sum to {weight_sum:.1%}, not 100%")
        
        return warnings
    
    def _format_final_response(self, result: PortfolioResult, state: AgentState) -> str:
        """Format the final response for the user."""
        task = state.current_task
        
        lines = []
        
        # Header
        lines.append("📊 PORTFOLIO ANALYSIS RESULT")
        lines.append("=" * 50)
        
        if not result.success:
            lines.append(f"\n❌ Analysis Failed: {result.error_message}")
            return "\n".join(lines)
        
        # Task Summary
        if task:
            lines.append(f"\n📋 Request Summary:")
            lines.append(f"   • Universe: {', '.join(task.universe)}")
            lines.append(f"   • Task: {task.task_type.value}")
            if task.constraints.max_volatility:
                lines.append(f"   • Max Volatility: {task.constraints.max_volatility:.1%}")
            lines.append(f"   • Data Period: {task.historical_period}")
        
        # Results
        if result.weights:
            lines.append(f"\n💼 Optimal Allocation:")
            for asset, weight in sorted(result.weights.items(), key=lambda x: -x[1]):
                lines.append(f"   • {asset}: {weight:.1%}")
        
        # Metrics
        lines.append(f"\n📈 Portfolio Metrics:")
        if result.expected_return:
            lines.append(f"   • Expected Return: {result.expected_return:.2%}")
        if result.expected_volatility:
            lines.append(f"   • Expected Volatility: {result.expected_volatility:.2%}")
        if result.sharpe_ratio:
            lines.append(f"   • Sharpe Ratio: {result.sharpe_ratio:.2f}")
        
        # Risk contributions
        if result.risk_decomposition:
            lines.append(f"\n⚖️ Risk Contributions:")
            for asset, contrib in result.risk_decomposition.risk_contributions.items():
                lines.append(f"   • {asset}: {contrib:.1%} of total risk")
        
        # Backtest metrics if available
        if result.backtest_metrics:
            bm = result.backtest_metrics
            lines.append(f"\n📉 Backtest Results:")
            lines.append(f"   • Total Return: {bm.total_return:.2%}")
            lines.append(f"   • CAGR: {bm.cagr:.2%}")
            lines.append(f"   • Max Drawdown: {bm.max_drawdown:.2%}")
            lines.append(f"   • Sharpe Ratio: {bm.sharpe_ratio:.2f}")
        
        # Warnings
        if result.warnings:
            lines.append(f"\n⚠️ Warnings:")
            for warning in result.warnings:
                lines.append(f"   {warning}")
        
        # Audit trail
        lines.append(f"\n📅 Audit Trail:")
        if result.optimization_method:
            lines.append(f"   • Method: {result.optimization_method}")
        if result.data_period:
            lines.append(f"   • Data: {result.data_period}")
        lines.append(f"   • Calculated: {result.calculation_timestamp.strftime('%Y-%m-%d %H:%M')}")
        
        # Disclaimer
        lines.append(f"\n" + "=" * 50)
        lines.append("⚠️ DISCLAIMER: This is not financial advice. Past performance")
        lines.append("   does not guarantee future results. Consult a qualified")
        lines.append("   financial advisor before making investment decisions.")
        
        return "\n".join(lines)
    
    # ========== TOOLS ==========
    
    def parse_user_mandate(self, user_message: str) -> Dict[str, Any]:
        """
        Parse user investment mandate into structured format.
        
        Args:
            user_message: Raw user request
            
        Returns:
            Parsed mandate as dictionary
        """
        task = self._parse_mandate(user_message, AgentState())
        if task:
            return task.to_dict()
        return {"error": "Could not parse mandate"}
    
    def validate_portfolio_constraints(
        self,
        max_volatility: Optional[float] = None,
        max_weight: Optional[float] = None,
        min_weight: Optional[float] = None,
        num_assets: int = 0
    ) -> Dict[str, Any]:
        """
        Validate portfolio constraints.
        
        Returns validation result with any warnings.
        """
        constraints = PortfolioConstraints(
            max_volatility=max_volatility,
            max_weight=max_weight,
            min_weight=min_weight,
        )
        
        errors = self._validate_constraints(constraints)
        
        if num_assets < self.config.min_diversification_assets:
            errors.append(f"Only {num_assets} assets - recommend at least {self.config.min_diversification_assets}")
        
        return {
            "valid": len(errors) == 0,
            "warnings": errors,
            "constraints_used": constraints.to_dict()
        }
    
    def check_concentration_risk(self, weights: Dict[str, float]) -> Dict[str, Any]:
        """
        Check portfolio for concentration risk.
        
        Args:
            weights: Portfolio weights
            
        Returns:
            Concentration analysis
        """
        if not weights:
            return {"error": "No weights provided"}
        
        max_weight = max(weights.values())
        min_weight = min(weights.values())
        n_positions = len([w for w in weights.values() if w > 0.01])
        
        # Herfindahl index (sum of squared weights)
        hhi = sum(w ** 2 for w in weights.values())
        
        return {
            "max_weight": f"{max_weight:.1%}",
            "min_weight": f"{min_weight:.1%}",
            "num_positions": n_positions,
            "herfindahl_index": f"{hhi:.3f}",
            "concentration_level": "HIGH" if hhi > 0.25 else "MODERATE" if hhi > 0.15 else "LOW",
            "warnings": [
                f"High concentration in single asset ({max_weight:.1%})"
            ] if max_weight > self.config.max_concentration_warning else []
        }
    
    def validate_optimization_result(
        self,
        weights: Dict[str, float],
        expected_volatility: float,
        max_volatility_constraint: float
    ) -> Dict[str, Any]:
        """
        Validate optimization result meets constraints.
        
        Args:
            weights: Optimized weights
            expected_volatility: Portfolio volatility
            max_volatility_constraint: Maximum allowed volatility
            
        Returns:
            Validation result
        """
        issues = []
        
        # Check weights sum
        weight_sum = sum(weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            issues.append(f"Weights sum to {weight_sum:.1%}")
        
        # Check volatility
        if expected_volatility > max_volatility_constraint:
            issues.append(f"Volatility {expected_volatility:.1%} > limit {max_volatility_constraint:.1%}")
        
        # Check concentration
        concentration = self.check_concentration_risk(weights)
        issues.extend(concentration.get("warnings", []))
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "weight_sum": f"{weight_sum:.1%}",
            "volatility_check": "PASS" if expected_volatility <= max_volatility_constraint else "FAIL"
        }
    
    def generate_risk_summary(
        self,
        weights: Dict[str, float],
        volatility: float,
        sharpe: float,
        max_drawdown: Optional[float] = None
    ) -> str:
        """
        Generate a human-readable risk summary.
        
        Args:
            weights: Portfolio weights
            volatility: Expected volatility
            sharpe: Sharpe ratio
            max_drawdown: Historical max drawdown (optional)
            
        Returns:
            Formatted risk summary
        """
        lines = [
            "Risk Summary:",
            f"- Expected Volatility: {volatility:.1%}",
            f"- Sharpe Ratio: {sharpe:.2f}",
        ]
        
        if max_drawdown:
            lines.append(f"- Historical Max Drawdown: {max_drawdown:.1%}")
        
        # Risk level assessment
        if volatility < 0.08:
            risk_level = "LOW"
        elif volatility < 0.15:
            risk_level = "MODERATE"
        else:
            risk_level = "HIGH"
        
        lines.append(f"- Risk Level: {risk_level}")
        
        # Concentration
        concentration = self.check_concentration_risk(weights)
        lines.append(f"- Concentration: {concentration['concentration_level']}")
        
        return "\n".join(lines)


# Factory function
def create_risk_manager(
    sub_agents: Optional[List[BaseAgent]] = None,
    verbose: bool = False
) -> RiskManagerAgent:
    """
    Create a configured Risk Manager Agent.
    
    Args:
        sub_agents: List of specialized agents to coordinate
        verbose: Enable verbose logging
        
    Returns:
        Configured RiskManagerAgent
    """
    config = RiskManagerConfig(
        name="RiskManager",
        role=AgentRole.SUPERVISOR,
        verbose=verbose,
    )
    return RiskManagerAgent(config, sub_agents)
