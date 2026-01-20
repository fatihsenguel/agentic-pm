"""
Rebalance Agent for Quant Portfolio Manager.

The Rebalance Agent is responsible for:
- Analyzing portfolio drift
- Determining if rebalancing is needed
- Generating trade lists
- Estimating transaction costs and tax impact

⚠️ CRITICAL DESIGN PRINCIPLE:
All calculations are performed by rebalance_tools.py (pure math).
This agent is ONLY an interface - it does NOT perform calculations.
The LLM's role is to:
1. Understand user requests
2. Extract parameters
3. Call the appropriate tools
4. Format and explain the results

This separation ensures:
- Compliance / Audit requirements
- Reproducibility (same inputs = same outputs)
- Regulatory approval
"""

from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentConfig, AgentRole, AgentState
from .protocols import PortfolioTask, PortfolioResult, TaskType


@dataclass
class RebalanceAgentConfig(AgentConfig):
    """Configuration for Rebalance Agent."""
    
    # Default thresholds
    default_drift_threshold: float = 5.0  # 5%
    default_transaction_cost_bps: float = 10.0  # 0.10%
    
    # Tax settings
    capital_gains_rate: float = 0.25  # 25%
    consider_tax_impact: bool = True


class RebalanceAgent(BaseAgent):
    """
    Rebalance Agent for portfolio rebalancing analysis.
    
    ⚠️ This agent uses rebalance_tools.py for ALL calculations.
    The agent itself does NOT perform any math.
    
    Capabilities:
    - analyze_rebalance: Full rebalancing analysis
    - calculate_drift: Portfolio drift calculation
    - generate_trades: Trade list generation
    - estimate_costs: Cost estimation
    """
    
    def __init__(self, config: Optional[RebalanceAgentConfig] = None):
        """Initialize Rebalance Agent."""
        if config is None:
            config = RebalanceAgentConfig(
                name="RebalanceAgent",
                role=AgentRole.DATA,  # Uses DATA role (could be separate REBALANCE role)
                temperature=0.0,  # Deterministic
            )
        super().__init__(config)
        self.config: RebalanceAgentConfig = config
    
    @property
    def capabilities(self) -> List[str]:
        """List of capabilities this agent provides."""
        return [
            "analyze_rebalance",
            "calculate_drift",
            "generate_trades",
            "estimate_costs",
            "check_rebalance_threshold",
        ]
    
    def get_tools(self) -> List[Callable]:
        """Get the list of tools available to this agent."""
        return [
            self.analyze_rebalance_tool,
            self.calculate_drift_tool,
            self.generate_trades_tool,
            self.quick_drift_check_tool,
        ]
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return """You are the Rebalance Agent for a Quant Portfolio Manager system.

Your role is to analyze portfolio drift and generate rebalancing recommendations.

⚠️ CRITICAL: You do NOT perform calculations yourself.
All calculations are done by deterministic tools (rebalance_tools.py).
Your job is to:
1. Understand user requests
2. Call the appropriate tools
3. Explain the results clearly

CAPABILITIES:
- Analyze portfolio drift (current vs target weights)
- Determine if rebalancing is needed
- Generate specific trade lists
- Estimate transaction costs and tax impact
- Calculate break-even thresholds

KEY CONCEPTS:
- Drift: Difference between current and target weights
- Threshold: Typically 5% - rebalance when max drift exceeds this
- Turnover: Total trades as % of portfolio value
- Break-even: Drift level at which rebalancing becomes cost-effective

OUTPUT FORMAT:
Always include:
1. Current vs Target weights comparison
2. Drift analysis (which assets are over/underweight)
3. Clear recommendation (rebalance YES/NO)
4. If YES: Specific trade list with costs
5. Cost-benefit analysis

SCOPE GUARDS:
- Do NOT recommend specific timing for trades
- Do NOT predict price movements
- Do NOT guarantee any outcomes
- Always note that actual execution prices may differ
"""
    
    async def process(self, state: AgentState) -> AgentState:
        """Process a rebalancing request."""
        task = state.current_task
        
        if task is None:
            state.add_message("assistant", "No task provided to Rebalance Agent")
            return state
        
        self.log(f"Processing rebalance task: {task.task_id}")
        
        # Get data from shared state
        shared = state.shared_data
        
        # Required: current and target weights
        current_weights = shared.get("current_weights")
        target_weights = shared.get("target_weights") or shared.get("optimal_weights")
        portfolio_value = shared.get("portfolio_value", 100000)
        prices = shared.get("current_prices", {})
        
        if not current_weights:
            state.add_message("assistant", "❌ Missing current portfolio weights. Please provide current_weights.")
            return state
        
        if not target_weights:
            state.add_message("assistant", "❌ Missing target weights. Run optimization first or provide target_weights.")
            return state
        
        # Perform analysis
        result = self.analyze_rebalance_tool(
            current_weights=current_weights,
            target_weights=target_weights,
            portfolio_value=portfolio_value,
            prices=prices
        )
        
        if not result.get("success"):
            state.add_message("assistant", f"❌ Rebalancing analysis failed: {result.get('error')}")
            return state
        
        # Store results in shared state
        state.shared_data["rebalance_result"] = result
        state.shared_data["should_rebalance"] = result["decision"]["should_rebalance"]
        state.shared_data["rebalance_trades"] = result.get("trades", [])
        
        # Create result
        portfolio_result = PortfolioResult(
            agent_name=self.name,
            task_id=task.task_id,
            success=True,
            result_type="rebalance_analysis",
            data=result,
            message=f"Rebalancing analysis complete. Recommendation: {result['decision']['recommendation']}",
            reasoning=f"Max drift: {result['drift_analysis']['max_drift']}, "
                      f"Threshold: {result['drift_analysis']['threshold']}",
        )
        
        state.add_sub_result(self.name, portfolio_result)
        state.add_message("assistant", result.get("summary", "Analysis complete"))
        
        return state
    
    # ==================== TOOL METHODS ====================
    
    def analyze_rebalance_tool(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        portfolio_value: float = 100000,
        prices: Optional[Dict[str, float]] = None,
        drift_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Perform complete rebalancing analysis.
        
        ⚠️ Delegates to rebalance_tools.py - NO calculations here.
        
        Args:
            current_weights: Current portfolio weights
            target_weights: Target/optimal weights
            portfolio_value: Total portfolio value
            prices: Current prices (optional, uses defaults if not provided)
            drift_threshold: Custom drift threshold (optional)
        
        Returns:
            Complete rebalancing analysis
        """
        # Import the pure math module
        from portfolio_tool.tools.rebalance_tools import (
            analyze_rebalance,
            RebalanceConfig
        )
        
        # Use default prices if not provided
        if prices is None or not prices:
            # Get from data manager if possible
            try:
                from portfolio_tool.data_manager import get_data_manager
                dm = get_data_manager()
                
                prices = {}
                for ticker in set(current_weights.keys()) | set(target_weights.keys()):
                    if ticker == "CASH":
                        prices[ticker] = 1.0
                        continue
                    
                    # Try to get latest price from DB
                    # This is a simplified approach - in production, get real prices
                    prices[ticker] = 100.0  # Default placeholder
                    
            except Exception:
                # Use placeholder prices
                prices = {t: 100.0 for t in set(current_weights.keys()) | set(target_weights.keys())}
                prices["CASH"] = 1.0
        
        # Configure
        config = RebalanceConfig(
            drift_threshold_percent=drift_threshold or self.config.default_drift_threshold,
            transaction_cost_bps=self.config.default_transaction_cost_bps,
            capital_gains_rate=self.config.capital_gains_rate,
        )
        
        # Delegate to pure math function
        try:
            result = analyze_rebalance(
                current_weights=current_weights,
                target_weights=target_weights,
                portfolio_value=portfolio_value,
                prices=prices,
                config=config,
            )
            
            return {
                "success": True,
                **result.to_dict(),
                "summary": result.to_summary(),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def calculate_drift_tool(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Calculate portfolio drift only.
        
        Quick check without full trade generation.
        
        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights
        
        Returns:
            Drift analysis
        """
        from portfolio_tool.tools.rebalance_tools import (
            calculate_drift,
            calculate_max_drift,
            should_rebalance
        )
        
        try:
            drift = calculate_drift(current_weights, target_weights)
            max_drift = calculate_max_drift(drift)
            should_reb, recommendation = should_rebalance(
                drift, 
                self.config.default_drift_threshold
            )
            
            return {
                "success": True,
                "drift_by_asset": drift,
                "drift_formatted": {k: f"{v:+.2%}" for k, v in drift.items()},
                "max_drift": max_drift,
                "max_drift_formatted": f"{max_drift:.2%}",
                "threshold": self.config.default_drift_threshold,
                "should_rebalance": should_reb,
                "recommendation": recommendation,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def generate_trades_tool(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        portfolio_value: float,
        prices: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Generate trade list to rebalance portfolio.
        
        Args:
            current_weights: Current weights
            target_weights: Target weights
            portfolio_value: Total portfolio value
            prices: Current prices per ticker
        
        Returns:
            Trade list with costs
        """
        from portfolio_tool.tools.rebalance_tools import (
            generate_trades,
            calculate_rebalance_costs,
            RebalanceConfig
        )
        
        try:
            config = RebalanceConfig(
                transaction_cost_bps=self.config.default_transaction_cost_bps,
            )
            
            trades = generate_trades(
                current_weights=current_weights,
                target_weights=target_weights,
                portfolio_value=portfolio_value,
                prices=prices,
                config=config,
            )
            
            tx_cost, tax_cost, total_cost = calculate_rebalance_costs(trades)
            
            return {
                "success": True,
                "num_trades": len(trades),
                "trades": [t.to_dict() for t in trades],
                "total_trade_value": sum(abs(t.trade_value) for t in trades),
                "transaction_costs": tx_cost,
                "estimated_taxes": tax_cost,
                "total_costs": total_cost,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def quick_drift_check_tool(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Quick one-line drift status check.
        
        Args:
            current_weights: Current weights
            target_weights: Target weights
        
        Returns:
            Simple status message
        """
        from portfolio_tool.tools.rebalance_tools import quick_drift_check
        
        try:
            message = quick_drift_check(
                current_weights=current_weights,
                target_weights=target_weights,
                threshold=self.config.default_drift_threshold
            )
            
            return {
                "success": True,
                "status": message,
                "needs_attention": "REBALANCE NEEDED" in message,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


# ==================== FACTORY FUNCTION ====================

def create_rebalance_agent(verbose: bool = False) -> RebalanceAgent:
    """
    Factory function to create configured Rebalance Agent.
    
    Args:
        verbose: Enable verbose logging
    
    Returns:
        Configured RebalanceAgent
    """
    config = RebalanceAgentConfig(
        name="RebalanceAgent",
        role=AgentRole.DATA,
        verbose=verbose,
        temperature=0.0,
    )
    return RebalanceAgent(config)
