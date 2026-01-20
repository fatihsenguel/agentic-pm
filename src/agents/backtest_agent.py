"""
Backtest Agent for Quant Portfolio Manager.

The Backtest Agent orchestrates backtesting:
1. Translates user intent into Strategy objects (LLM helps here)
2. Runs the DETERMINISTIC BacktestEngine (NO LLM during simulation)
3. Interprets and explains results (LLM helps here)

⚠️ CRITICAL DESIGN:
The LLM's role is LIMITED to:
- BEFORE: Understanding user's strategy description → Strategy object
- AFTER: Explaining results in natural language

The LLM NEVER participates in the actual backtest simulation.
The BacktestEngine is 100% deterministic.
"""

from typing import Any, Callable, Dict, List, Optional
import json
from datetime import datetime
from dataclasses import dataclass

import pandas as pd
import numpy as np

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, AgentConfig, AgentRole, AgentState
from agents.protocols import (
    PortfolioTask,
    PortfolioResult,
    BacktestMetrics,
    TAARule as ProtocolTAARule,
)


@dataclass
class BacktestAgentConfig(AgentConfig):
    """Configuration for Backtest Agent."""
    
    # Default backtest settings
    default_initial_capital: float = 100_000
    default_transaction_cost: float = 0.001  # 10 bps
    
    # Risk-free rate for Sharpe calculation
    risk_free_rate: float = 0.05


class BacktestAgent(BaseAgent):
    """
    Backtest Agent for running portfolio simulations.
    
    Workflow:
    1. Receive strategy specification from user/supervisor
    2. Build Strategy object from specification
    3. Run BacktestEngine (DETERMINISTIC - no LLM)
    4. Return results with interpretation
    
    The agent does NOT make any decisions during the backtest.
    All trading rules are defined BEFORE the simulation runs.
    """
    
    def __init__(self, config: Optional[BacktestAgentConfig] = None):
        """Initialize Backtest Agent."""
        if config is None:
            config = BacktestAgentConfig(
                name="BacktestAgent",
                role=AgentRole.BACKTEST,
                temperature=0.0,
            )
        super().__init__(config)
        self.config: BacktestAgentConfig = config
        
        # Lazy-load engine
        self._engine = None
    
    @property
    def engine(self):
        """Lazy-load BacktestEngine."""
        if self._engine is None:
            from portfolio_tool.backtest.engine import BacktestEngine
            self._engine = BacktestEngine(
                transaction_cost=self.config.default_transaction_cost,
                risk_free_rate=self.config.risk_free_rate
            )
        return self._engine
    
    @property
    def capabilities(self) -> List[str]:
        return [
            "run_backtest",
            "compare_strategies",
            "analyze_drawdowns",
            "generate_report",
        ]
    
    def get_tools(self) -> List[Callable]:
        return [
            self.run_backtest_tool,
            self.compare_strategies_tool,
            self.create_strategy_tool,
        ]
    
    def get_system_prompt(self) -> str:
        return """You are the Backtest Agent for a Quant Portfolio Manager system.

Your role is to run backtests on portfolio strategies.

⚠️ CRITICAL LIMITATION:
The BacktestEngine is 100% DETERMINISTIC.
You translate user intent into Strategy rules BEFORE the backtest.
You NEVER make decisions during the simulation.
Same inputs = Same outputs. Always.

CAPABILITIES:
- Run backtest on a strategy with historical data
- Compare multiple strategies
- Analyze drawdowns and risk metrics
- Generate performance reports

WORKFLOW:
1. Receive strategy specification
2. Build Strategy object with:
   - Initial weights
   - Rebalancing rules (frequency, drift threshold)
   - TAA rules (indicator, operator, threshold, target weights)
3. Run BacktestEngine (you don't control this - it's deterministic)
4. Return and interpret results

TAA RULES FORMAT:
Rules are defined as: "If [INDICATOR] [OPERATOR] [THRESHOLD] then [TARGET_WEIGHTS]"
Example: "If VIX > 25 then reduce equities to 40%, increase bonds to 40%, hold 20% cash"

AVAILABLE OPERATORS:
- ">" : Greater than
- "<" : Less than
- ">=" : Greater than or equal
- "<=" : Less than or equal
- "crosses_above" : Value crosses above threshold
- "crosses_below" : Value crosses below threshold

OUTPUT:
Always include in results:
- Total Return, CAGR, Volatility
- Sharpe Ratio, Sortino Ratio
- Max Drawdown, Calmar Ratio
- Number of trades, transaction costs
- TAA rule trigger counts (if applicable)

SCOPE GUARDS:
- Do NOT make predictions about future performance
- Do NOT guarantee that past performance will repeat
- Always include risk disclaimers
"""
    
    async def process(self, state: AgentState) -> AgentState:
        """Process backtest request."""
        task = state.current_task
        
        if task is None:
            state.add_message("assistant", "No task provided to Backtest Agent")
            return state
        
        self.log(f"Processing backtest task: {task.task_id}")
        
        # Get data from shared state
        shared = state.shared_data
        
        if "price_data" not in shared:
            state.add_message(
                "assistant",
                "Missing price data for backtest. Need historical prices from Data Agent."
            )
            return state
        
        # Build strategy from task
        strategy = self._build_strategy_from_task(task)
        
        # Get price data
        price_data = shared["price_data"]
        if isinstance(price_data, dict):
            price_data = pd.DataFrame(price_data)
        
        # Get signal data if available
        signal_data = shared.get("signal_data")
        if signal_data and isinstance(signal_data, dict):
            signal_data = pd.DataFrame(signal_data)
        
        # Run backtest
        result = self.engine.run(
            strategy=strategy,
            price_data=price_data,
            initial_capital=self.config.default_initial_capital,
            signal_data=signal_data
        )
        
        # Convert to PortfolioResult
        portfolio_result = self._convert_to_portfolio_result(result, task.task_id)
        
        state.add_sub_result(self.name, portfolio_result)
        state.add_message("assistant", result.to_summary())
        
        return state
    
    def _build_strategy_from_task(self, task: PortfolioTask):
        """Build Strategy object from PortfolioTask."""
        from portfolio_tool.backtest.strategies import (
            Strategy, TAARule, RebalanceRule, RebalanceFrequency
        )
        
        # Convert rebalance frequency
        freq_map = {
            "daily": RebalanceFrequency.DAILY,
            "weekly": RebalanceFrequency.WEEKLY,
            "monthly": RebalanceFrequency.MONTHLY,
            "quarterly": RebalanceFrequency.QUARTERLY,
            "annually": RebalanceFrequency.ANNUALLY,
            "never": RebalanceFrequency.NEVER,
        }
        
        rebal_freq = RebalanceFrequency.QUARTERLY
        if task.rebalance_frequency:
            rebal_freq = freq_map.get(
                task.rebalance_frequency.value.lower(),
                RebalanceFrequency.QUARTERLY
            )
        
        # Build TAA rules
        taa_rules = []
        if task.taa_rules:
            for rule in task.taa_rules:
                taa_rules.append(TAARule(
                    name=rule.name,
                    indicator=rule.indicator,
                    operator=rule.operator,
                    threshold=rule.threshold,
                    target_weights=rule.target_weights,
                ))
        
        # Build strategy
        initial_weights = task.current_weights or {
            asset: 1.0 / len(task.universe)
            for asset in task.universe
        }
        
        return Strategy(
            name=f"Strategy_{task.task_id[:8]}",
            initial_weights=initial_weights,
            rebalance_rule=RebalanceRule(
                frequency=rebal_freq,
                drift_threshold=task.constraints.max_drift or 0.05
            ),
            taa_rules=taa_rules,
        )
    
    def _convert_to_portfolio_result(self, result, task_id: str) -> PortfolioResult:
        """Convert BacktestResult to PortfolioResult."""
        return PortfolioResult(
            agent_name=self.name,
            task_id=task_id,
            success=True,
            backtest_metrics=BacktestMetrics(
                total_return=result.total_return,
                cagr=result.cagr,
                volatility=result.volatility,
                sharpe_ratio=result.sharpe_ratio,
                sortino_ratio=result.sortino_ratio,
                max_drawdown=result.max_drawdown,
                calmar_ratio=result.calmar_ratio,
                win_rate=result.win_rate,
                num_trades=result.total_trades,
                start_date=result.start_date,
                end_date=result.end_date,
            ),
            reasoning=f"Backtest completed: {result.trading_days} trading days",
        )
    
    # ========== TOOLS ==========
    
    def run_backtest_tool(
        self,
        tickers: str,
        weights: str,
        price_data: str,
        rebalance_frequency: str = "quarterly",
        drift_threshold: float = 0.05,
        taa_rules: Optional[str] = None,
        initial_capital: float = 100_000,
        signal_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a backtest on a portfolio strategy.
        
        Args:
            tickers: Comma-separated ticker symbols
            weights: JSON dict of initial weights {"SPY": 0.6, "TLT": 0.4}
            price_data: JSON dict of price data (or DataFrame as JSON)
            rebalance_frequency: "daily", "weekly", "monthly", "quarterly", "annually", "never"
            drift_threshold: Rebalance if any weight drifts more than this
            taa_rules: JSON list of TAA rules (optional)
            initial_capital: Starting capital
            signal_data: JSON dict of signal data for TAA (optional)
            
        Returns:
            Backtest results
        """
        try:
            from portfolio_tool.backtest.strategies import (
                Strategy, TAARule, RebalanceRule, RebalanceFrequency
            )
            from portfolio_tool.backtest.engine import BacktestEngine
            
            # Parse inputs
            ticker_list = [t.strip() for t in tickers.split(",")]
            weights_dict = json.loads(weights) if isinstance(weights, str) else weights
            
            # Parse price data
            if isinstance(price_data, str):
                price_df = pd.DataFrame(json.loads(price_data))
            else:
                price_df = pd.DataFrame(price_data)
            
            # Ensure datetime index
            if not isinstance(price_df.index, pd.DatetimeIndex):
                price_df.index = pd.to_datetime(price_df.index)
            
            # Parse signal data if provided
            signal_df = None
            if signal_data:
                if isinstance(signal_data, str):
                    signal_df = pd.DataFrame(json.loads(signal_data))
                else:
                    signal_df = pd.DataFrame(signal_data)
                if not isinstance(signal_df.index, pd.DatetimeIndex):
                    signal_df.index = pd.to_datetime(signal_df.index)
            
            # Parse rebalance frequency
            freq_map = {
                "daily": RebalanceFrequency.DAILY,
                "weekly": RebalanceFrequency.WEEKLY,
                "monthly": RebalanceFrequency.MONTHLY,
                "quarterly": RebalanceFrequency.QUARTERLY,
                "annually": RebalanceFrequency.ANNUALLY,
                "never": RebalanceFrequency.NEVER,
            }
            rebal_freq = freq_map.get(rebalance_frequency.lower(), RebalanceFrequency.QUARTERLY)
            
            # Parse TAA rules
            strategy_taa_rules = []
            if taa_rules:
                rules_list = json.loads(taa_rules) if isinstance(taa_rules, str) else taa_rules
                for rule in rules_list:
                    strategy_taa_rules.append(TAARule(
                        name=rule["name"],
                        indicator=rule["indicator"],
                        operator=rule["operator"],
                        threshold=rule["threshold"],
                        target_weights=rule["target_weights"],
                    ))
            
            # Build strategy
            strategy = Strategy(
                name="Backtest Strategy",
                initial_weights=weights_dict,
                rebalance_rule=RebalanceRule(
                    frequency=rebal_freq,
                    drift_threshold=drift_threshold
                ),
                taa_rules=strategy_taa_rules,
            )
            
            # Run backtest
            engine = BacktestEngine(
                transaction_cost=self.config.default_transaction_cost,
                risk_free_rate=self.config.risk_free_rate
            )
            
            result = engine.run(
                strategy=strategy,
                price_data=price_df,
                initial_capital=initial_capital,
                signal_data=signal_df
            )
            
            return {
                "success": True,
                **result.to_dict(),
                "summary": result.to_summary()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def compare_strategies_tool(
        self,
        strategies: str,
        price_data: str,
        initial_capital: float = 100_000,
        signal_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple strategies.
        
        Args:
            strategies: JSON list of strategy specifications
            price_data: JSON dict of price data
            initial_capital: Starting capital
            signal_data: JSON dict of signal data (optional)
            
        Returns:
            Comparison results
        """
        try:
            from portfolio_tool.backtest.strategies import (
                Strategy, TAARule, RebalanceRule, RebalanceFrequency
            )
            from portfolio_tool.backtest.reports import compare_strategies, format_comparison_table
            
            # Parse inputs
            strategies_list = json.loads(strategies) if isinstance(strategies, str) else strategies
            
            if isinstance(price_data, str):
                price_df = pd.DataFrame(json.loads(price_data))
            else:
                price_df = pd.DataFrame(price_data)
            
            if not isinstance(price_df.index, pd.DatetimeIndex):
                price_df.index = pd.to_datetime(price_df.index)
            
            signal_df = None
            if signal_data:
                if isinstance(signal_data, str):
                    signal_df = pd.DataFrame(json.loads(signal_data))
                else:
                    signal_df = pd.DataFrame(signal_data)
            
            # Build strategy objects
            built_strategies = []
            for spec in strategies_list:
                freq_map = {
                    "daily": RebalanceFrequency.DAILY,
                    "weekly": RebalanceFrequency.WEEKLY,
                    "monthly": RebalanceFrequency.MONTHLY,
                    "quarterly": RebalanceFrequency.QUARTERLY,
                    "annually": RebalanceFrequency.ANNUALLY,
                    "never": RebalanceFrequency.NEVER,
                }
                
                rebal_freq = freq_map.get(
                    spec.get("rebalance_frequency", "quarterly").lower(),
                    RebalanceFrequency.QUARTERLY
                )
                
                taa_rules = []
                for rule in spec.get("taa_rules", []):
                    taa_rules.append(TAARule(
                        name=rule["name"],
                        indicator=rule["indicator"],
                        operator=rule["operator"],
                        threshold=rule["threshold"],
                        target_weights=rule["target_weights"],
                    ))
                
                built_strategies.append(Strategy(
                    name=spec["name"],
                    initial_weights=spec["weights"],
                    rebalance_rule=RebalanceRule(
                        frequency=rebal_freq,
                        drift_threshold=spec.get("drift_threshold", 0.05)
                    ),
                    taa_rules=taa_rules,
                ))
            
            # Run backtests
            results = self.engine.compare_strategies(
                built_strategies,
                price_df,
                initial_capital,
                signal_df
            )
            
            # Generate comparison
            comparison_table = format_comparison_table(results)
            
            return {
                "success": True,
                "strategies_compared": len(results),
                "results": {name: r.to_dict() for name, r in results.items()},
                "comparison": comparison_table
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_strategy_tool(
        self,
        name: str,
        weights: str,
        rebalance_frequency: str = "quarterly",
        drift_threshold: float = 0.05,
        taa_rules: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a strategy specification (for validation).
        
        This tool helps validate strategy parameters before running a backtest.
        
        Args:
            name: Strategy name
            weights: JSON dict of weights
            rebalance_frequency: Rebalancing frequency
            drift_threshold: Drift threshold for rebalancing
            taa_rules: JSON list of TAA rules
            
        Returns:
            Validated strategy specification
        """
        try:
            weights_dict = json.loads(weights) if isinstance(weights, str) else weights
            
            # Validate weights sum to 1
            weight_sum = sum(weights_dict.values())
            if abs(weight_sum - 1.0) > 0.01:
                return {
                    "success": False,
                    "error": f"Weights must sum to 1.0, got {weight_sum}"
                }
            
            # Parse and validate TAA rules
            validated_rules = []
            if taa_rules:
                rules_list = json.loads(taa_rules) if isinstance(taa_rules, str) else taa_rules
                for rule in rules_list:
                    required = ["name", "indicator", "operator", "threshold", "target_weights"]
                    missing = [k for k in required if k not in rule]
                    if missing:
                        return {
                            "success": False,
                            "error": f"TAA rule missing fields: {missing}"
                        }
                    
                    rule_weight_sum = sum(rule["target_weights"].values())
                    if abs(rule_weight_sum - 1.0) > 0.01:
                        return {
                            "success": False,
                            "error": f"TAA rule '{rule['name']}' weights must sum to 1.0"
                        }
                    
                    validated_rules.append(rule)
            
            return {
                "success": True,
                "strategy": {
                    "name": name,
                    "weights": weights_dict,
                    "rebalance_frequency": rebalance_frequency,
                    "drift_threshold": drift_threshold,
                    "taa_rules": validated_rules,
                    "num_assets": len(weights_dict),
                    "num_taa_rules": len(validated_rules),
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def create_backtest_agent(
    transaction_cost: float = 0.001,
    risk_free_rate: float = 0.05,
    verbose: bool = False
) -> BacktestAgent:
    """
    Factory function to create configured Backtest Agent.
    
    Args:
        transaction_cost: Transaction cost per trade (default: 10 bps)
        risk_free_rate: Annual risk-free rate for Sharpe calculation
        verbose: Enable verbose logging
        
    Returns:
        Configured BacktestAgent
    """
    config = BacktestAgentConfig(
        name="BacktestAgent",
        role=AgentRole.BACKTEST,
        verbose=verbose,
        default_transaction_cost=transaction_cost,
        risk_free_rate=risk_free_rate,
    )
    return BacktestAgent(config)
