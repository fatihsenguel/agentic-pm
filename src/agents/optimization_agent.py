"""
Optimization Agent for Quant Portfolio Manager.

The Optimization Agent is responsible for:
- Portfolio optimization (Mean-Variance)
- Constraint handling and validation

It uses the optimization module and provides tools for the multi-agent system.

Design Principles:
- All optimization is deterministic (no LLM in the math)
- Results include full audit trails
- Proper handling of infeasible constraints
- Clear comparison between methods
"""

from typing import Any, Callable, Dict, List, Optional
import json
from datetime import datetime
from dataclasses import dataclass

import numpy as np
import pandas as pd

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, AgentConfig, AgentRole, AgentState
from agents.protocols import (
    PortfolioTask,
    PortfolioResult,
    PortfolioConstraints as ProtocolConstraints,
    RiskDecomposition,
)
from config import config


class OptimizationAgent(BaseAgent):
    """
    Optimization Agent for portfolio optimization.
    
    Capabilities:
    - Mean-Variance (Markowitz) optimization
    """
    
    def __init__(self, agent_config: Optional[AgentConfig] = None):
        """Initialize Optimization Agent."""
        if agent_config is None:
            agent_config = AgentConfig(
                name="OptimizationAgent",
                role=AgentRole.OPTIMIZATION,
                temperature=0.0,
            )
        super().__init__(agent_config)
        
        # Lazy-load optimizers
        self._mv_optimizer = None
    
    @property
    def mv_optimizer(self):
        """Lazy-load Mean-Variance optimizer."""
        if self._mv_optimizer is None:
            from portfolio_tool.optimization.mean_variance import MeanVarianceOptimizer
            self._mv_optimizer = MeanVarianceOptimizer(
                risk_free_rate=config.optimization.risk_free_rate,
                max_iterations=config.optimization.max_iterations,
                tolerance=config.optimization.tolerance
            )
        return self._mv_optimizer
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "optimize_mean_variance",
            "optimize_max_sharpe",
        ]
    
    def get_tools(self) -> List[Callable]:
        return [
            self.optimize_portfolio_tool,
        ]
    
    def get_system_prompt(self) -> str:
        return """You are the Optimization Agent for a Quant Portfolio Manager system.

Your role is to optimize portfolio weights using mathematical optimization.

CAPABILITIES:
- Mean-Variance (Markowitz) Optimization: Maximize Sharpe ratio

AVAILABLE METHODS:
1. max_sharpe - Maximum Sharpe ratio (best risk-adjusted return)

GUIDELINES:
1. Always validate that constraints are feasible
2. Report when constraints are binding (active)
3. Include risk contributions in results
4. Warn about extreme weights or corner solutions
5. All optimization is DETERMINISTIC - same inputs = same outputs

SCOPE GUARDS:
- Do NOT make recommendations about which method is "best"
- Do NOT predict future returns
- Do NOT adjust returns estimates
- Only perform mathematical optimization

OUTPUT FORMAT:
Always include:
- Optimal weights for each asset
- Expected return, volatility, Sharpe ratio
- Risk contribution per asset
- Active constraints
- Any warnings about the solution
"""
    
    async def process(self, state: AgentState) -> AgentState:
        """Process optimization request."""
        task = state.current_task
        
        if task is None:
            state.add_message("assistant", "No task provided to Optimization Agent")
            return state
        
        self.log(f"Processing optimization task: {task.task_id}")
        
        # Get data from shared state (provided by Data Agent)
        shared = state.shared_data
        
        if "covariance_matrix" not in shared or "expected_returns" not in shared:
            state.add_message(
                "assistant", 
                "Missing data: Need covariance_matrix and expected_returns from Data Agent"
            )
            return state
        
        # Convert back to pandas
        cov_dict = shared["covariance_matrix"]
        ret_dict = shared["expected_returns"]
        
        tickers = list(cov_dict.keys())
        cov_matrix = pd.DataFrame(cov_dict)
        
        # Parse returns - handle both dict and string formats
        if isinstance(ret_dict, dict):
            expected_returns = pd.Series({
                k: float(v.strip('%')) / 100 if isinstance(v, str) else float(v)
                for k, v in ret_dict.items()
            })
        else:
            expected_returns = pd.Series(ret_dict)
        
        # Convert protocol constraints to optimization constraints
        from portfolio_tool.optimization.constraints import PortfolioConstraints
        
        opt_constraints = PortfolioConstraints(
            min_weight=task.constraints.min_weight or config.optimization.default_min_weight,
            max_weight=task.constraints.max_weight or config.optimization.default_max_weight,
            max_volatility=task.constraints.max_volatility,
            long_only=task.constraints.long_only,
        )
        
        
        # Run optimization
        opt_result = self.mv_optimizer.max_sharpe(
            expected_returns, cov_matrix, opt_constraints
        )
        
        # Convert to PortfolioResult
        result = self._convert_to_portfolio_result(opt_result, task.task_id)
        
        state.add_sub_result(self.name, result)
        state.add_message("assistant", result.to_summary())
        
        return state
    
    def _convert_to_portfolio_result(
        self, 
        opt_result, 
        task_id: str
    ) -> PortfolioResult:
        """Convert optimization result to PortfolioResult."""
        
        return PortfolioResult(
            agent_name=self.name,
            task_id=task_id,
            success=opt_result.success,
            weights=opt_result.weights,
            expected_return=opt_result.expected_return,
            expected_volatility=opt_result.expected_volatility,
            sharpe_ratio=opt_result.sharpe_ratio,
            risk_decomposition=RiskDecomposition(
                risk_contributions=opt_result.risk_contributions
            ),
            optimization_method=opt_result.method.value,
            constraints_applied=opt_result.active_constraints,
            reasoning=f"Optimization converged in {opt_result.iterations} iterations",
            warnings=opt_result.warnings,
        )
    
    # ========== TOOLS ==========
    
    def optimize_portfolio_tool(
        self,
        tickers: str,
        expected_returns: str,
        covariance_matrix: str,
        method: str = "max_sharpe",
        max_volatility: Optional[float] = None,
        min_weight: float = 0.0,
        max_weight: float = 0.40
    ) -> Dict[str, Any]:
        """
        Optimize portfolio weights.
        """
        try:
            # Parse inputs
            ticker_list = [t.strip() for t in tickers.split(",")]
            ret_dict = json.loads(expected_returns) if isinstance(expected_returns, str) else expected_returns
            cov_dict = json.loads(covariance_matrix) if isinstance(covariance_matrix, str) else covariance_matrix
            
            # Convert to pandas
            exp_ret = pd.Series(ret_dict)
            cov_mat = pd.DataFrame(cov_dict)
            
            # Ensure same order (Crucial for matrix math alignment)
            exp_ret = exp_ret[ticker_list]
            cov_mat = cov_mat.loc[ticker_list, ticker_list]
            
            # Create constraints
            from portfolio_tool.optimization.constraints import PortfolioConstraints
            
            constraints = PortfolioConstraints(
                min_weight=min_weight,
                max_weight=max_weight,
                max_volatility=max_volatility,
                long_only=True,
            )
            
            # Run optimization
            result = self.mv_optimizer.max_sharpe(exp_ret, cov_mat, constraints)
            
            # ✅ STRICT FIX: Convert Numpy types to Python Native types
            # nodes.py strictly checks isinstance(x, float). Numpy floats fail this.
            result_dict = result.to_dict()
            
            if "weights" in result_dict:
                cleaned_weights = {}
                for ticker, weight in result_dict["weights"].items():
                    try:
                        # Case 1: Already a float/int/numpy type
                        if isinstance(weight, (int, float)):
                            cleaned_weights[ticker] = float(weight)
                        
                        # Case 2: String with % (The error you saw: "40.00%")
                        elif isinstance(weight, str) and "%" in weight:
                            cleaned_weights[ticker] = float(weight.strip('%')) / 100.0
                        
                        # Case 3: Plain string number (e.g., "0.4")
                        else:
                            cleaned_weights[ticker] = float(weight)
                    except ValueError:
                        # Fallback: invalid format, keep as 0.0 to prevent crash
                        cleaned_weights[ticker] = 0.0
                
                result_dict["weights"] = cleaned_weights
            
            # (Optional) Clean metrics too if they are strings
            for metric in ['expected_return', 'expected_volatility', 'sharpe_ratio']:
                if metric in result_dict:
                    val = result_dict[metric]
                    try:
                        if isinstance(val, str) and "%" in val:
                            result_dict[metric] = float(val.strip('%')) / 100.0
                        else:
                            result_dict[metric] = float(val)
                    except ValueError:
                        pass

            return result_dict
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def create_optimization_agent(
    verbose: bool = False
) -> OptimizationAgent:
    """
    Factory function to create configured Optimization Agent.
    
    Args:
        risk_free_rate: Annual risk-free rate for Sharpe calculation
        verbose: Enable verbose logging
        
    Returns:
        Configured OptimizationAgent
    """
    agent_config = AgentConfig(
        name="OptimizationAgent",
        role=AgentRole.OPTIMIZATION,
        verbose=verbose,
    )
    return OptimizationAgent(agent_config)
