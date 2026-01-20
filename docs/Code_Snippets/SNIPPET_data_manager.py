"""
Data Agent for Quant Portfolio Manager.
Responsibility: Fetch market data, calculate returns/covariance/risk metrics.
Principles: Hot Potato (return processed summaries), Audit Trails included.
Dependencies: yfinance, pandas, numpy, portfolio_tool.quant
"""
from typing import Any, Callable, Dict, List, Optional
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd
import numpy as np
# [Standard imports omitted...]

TRADING_DAYS_PER_YEAR = 252

@dataclass
class DataAgentConfig(AgentConfig):
    default_period: str = "5Y"
    min_observations: int = 60
    cache_prices: bool = True
    cache_ttl_minutes: int = 60

class DataAgent(BaseAgent):
    """
    Fetches and processes market data.
    Capabilities: prices, returns, covariance, risk_metrics, risk_free_rate.
    """
    
    def __init__(self, config: Optional[DataAgentConfig] = None):
        super().__init__(config)
        self._price_cache: Dict[str, pd.DataFrame] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

    async def process(self, state: AgentState) -> AgentState:
        """
        Delegator based on task.task_type.
        1. 'fetch_data' -> _handle_fetch_data
        2. 'calculate_risk' -> _handle_calculate_risk
        3. 'optimize' -> _prepare_optimization_data
        Stores result in state.sub_results and returns summary message.
        """
        task = state.current_task
        if task.task_type.value == "fetch_data":
            result = await self._handle_fetch_data(task)
        elif task.task_type.value == "calculate_risk":
            result = await self._handle_calculate_risk(task)
        else:
            result = await self._prepare_optimization_data(task)
        
        state.add_sub_result(self.name, result)
        state.add_message("assistant", result.to_summary())
        return state

    async def _handle_fetch_data(self, task: PortfolioTask) -> PortfolioResult:
        """Executes fetch_prices_tool."""
        prices_result = self.fetch_prices_tool(
            tickers=",".join(task.universe),
            period=task.historical_period
        )
        # Returns PortfolioResult with success status and data period
        return self.create_result(task_id=task.task_id, success=prices_result.get("success"), ...)

    async def _handle_calculate_risk(self, task: PortfolioTask) -> PortfolioResult:
        """Executes get_risk_metrics_tool (portfolio or individual)."""
        if task.current_weights:
            metrics = self.get_risk_metrics_tool(
                tickers=",".join(task.universe),
                weights=json.dumps(task.current_weights),
                period=task.historical_period
            )
        else:
            metrics = self.get_risk_metrics_tool(
                tickers=",".join(task.universe),
                period=task.historical_period
            )
        return self.create_result(task_id=task.task_id, success=metrics.get("success"), ...)

    async def _prepare_optimization_data(self, task: PortfolioTask) -> PortfolioResult:
        """
        Orchestrates full data prep for optimization:
        1. fetch_prices_tool
        2. calculate_covariance_tool (shrinkage)
        3. calculate_returns_tool (annualized)
        4. get_risk_free_rate_tool
        
        Returns: PortfolioResult with metadata containing:
            covariance_matrix, correlation_matrix, expected_returns, 
            volatilities, risk_free_rate, num_observations.
        """
        # [Implementation details omitted for brevity, logic follows steps above]
        pass

    # ========== TOOLS (Signatures & Logic Preserved) ==========

    def fetch_prices_tool(self, tickers: str, period: str = "5Y", interval: str = "1d") -> Dict[str, Any]:
        """
        Fetches prices via yfinance.
        Returns: {
            "success": bool,
            "tickers": List[str],
            "period": str,
            "num_observations": int,
            "latest_prices": Dict[str, float],
            "price_range": Dict[str, {min, max}],
            "warnings": List[str] (if missing data)
        }
        """
        # Logic: Calculates start_date, calls yf.download, caches result, formats summary.
        pass

    def calculate_returns_tool(self, tickers: str, period: str = "5Y", method: str = "simple", annualize: bool = True) -> Dict[str, Any]:
        """
        Computes returns from cached prices.
        Returns: {
            "success": bool,
            "annualized_returns": Dict[str, str] (formatted %),
            "daily_return_stats": Dict[str, {mean, std, min, max}],
            "total_returns": Dict[str, str]
        }
        """
        # Logic: Checks cache, computes pct_change or log, aggregates stats.
        pass

    def calculate_covariance_tool(self, tickers: str, period: str = "5Y", method: str = "shrinkage") -> Dict[str, Any]:
        """
        Estimates covariance matrix using specified method (sample, shrinkage, exponential).
        Returns: {
            "covariance_matrix": Dict[str, Dict[str, float]],
            "correlation_matrix": Dict[str, Dict[str, float]],
            "annualized_volatilities": Dict[str, str],
            "estimation_period": str
        }
        """
        # Logic: Uses portfolio_tool.quant.CovarianceEstimator if available, else standard pandas cov().
        pass

    def get_risk_metrics_tool(self, tickers: str, period: str = "5Y", weights: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculates advanced risk metrics (VaR, Sharpe, etc.).
        Returns: {
            "type": "portfolio" | "individual",
            "metrics": Dict (Sharpe, Sortino, MaxDrawdown, VaR, CVaR),
            "weights": Dict (if portfolio)
        }
        """
        # Logic: Uses portfolio_tool.quant.RiskMetricsCalculator.
        pass

    def get_risk_free_rate_tool(self) -> Dict[str, Any]:
        """
        Fetches 10Y Treasury yield (^TNX).
        Returns: {
            "success": bool,
            "rate": float (e.g. 0.045),
            "source": str ("10Y Treasury" or "default")
        }
        """
        # Logic: yf.Ticker("^TNX"), falls back to 0.05 (5%) on error.
        pass

    def calculate_rolling_volatility_tool(self, ticker: str, window: int = 30, period: str = "1Y") -> Dict[str, Any]:
        """
        Calculates rolling vol for regime detection.
        Returns: {
            "current_volatility": str,
            "average_volatility": str,
            "vol_regime": "HIGH" (>1.2*avg) | "LOW" (<0.8*avg) | "NORMAL",
            "percentile_1y": str
        }
        """
        # Logic: yf.history -> pct_change -> rolling(window).std() -> compare current vs avg.
        pass