"""
Data Agent for Quant Portfolio Manager.

The Data Agent is responsible for:
- Fetching market data (prices, fundamentals)
- Calculating returns and covariance matrices
- Computing risk metrics
- Providing data for optimization and backtesting

It wraps the existing DataManager and adds quant-specific tools.

Design Principles:
- Hot Potato Principle: Return processed summaries, not raw data
- All results include audit trails (dates, methods used)
- Graceful handling of missing data
"""

from typing import Any, Callable, Dict, List, Optional
import json
from datetime import datetime, timedelta
from dataclasses import dataclass

import pandas as pd
import numpy as np

from .base_agent import BaseAgent, AgentConfig, AgentRole, AgentState
from .protocols import PortfolioTask, PortfolioResult, CovarianceResult


# Constants
TRADING_DAYS_PER_YEAR = 252


@dataclass
class DataAgentConfig(AgentConfig):
    """Configuration specific to the Data Agent."""
    
    # Data source settings
    default_period: str = "5Y"
    min_observations: int = 60
    
    # Caching
    cache_prices: bool = True
    cache_ttl_minutes: int = 60


class DataAgent(BaseAgent):
    """
    Data Agent for fetching and processing market data.
    
    Capabilities:
    - fetch_prices: Get historical prices for assets
    - calculate_returns: Compute returns from prices
    - calculate_covariance: Estimate covariance matrix
    - get_risk_metrics: Compute risk metrics for assets/portfolios
    - get_risk_free_rate: Fetch current risk-free rate
    """
    
    def __init__(self, config: Optional[DataAgentConfig] = None):
        """Initialize Data Agent."""
        if config is None:
            config = DataAgentConfig(
                name="DataAgent",
                role=AgentRole.DATA,
                temperature=0.0,  # Deterministic
            )
        super().__init__(config)
        
        # Cache for prices (in-memory for session)
        self._price_cache: Dict[str, pd.DataFrame] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
    
    @property
    def capabilities(self) -> List[str]:
        """List of capabilities this agent provides."""
        return [
            "fetch_prices",
            "calculate_returns",
            "calculate_covariance",
            "get_risk_metrics",
            "get_risk_free_rate",
            "get_correlation_matrix",
            "calculate_rolling_volatility",
        ]
    
    def get_tools(self) -> List[Callable]:
        """Get the list of tools available to this agent."""
        return [
            self.fetch_prices_tool,
            self.calculate_returns_tool,
            self.calculate_covariance_tool,
            self.get_risk_metrics_tool,
            self.get_risk_free_rate_tool,
            self.calculate_rolling_volatility_tool,
        ]
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return """You are the Data Agent for a Quant Portfolio Manager system.

Your role is to fetch and process market data for portfolio optimization and risk analysis.

CAPABILITIES:
- Fetch historical prices for any ticker
- Calculate returns (simple, log, excess)
- Estimate covariance matrices (sample, shrinkage, exponential)
- Compute risk metrics (volatility, VaR, Sharpe, etc.)
- Provide risk-free rate data

GUIDELINES:
1. Always validate ticker symbols before fetching
2. Check for sufficient data (minimum 60 observations recommended)
3. Handle missing data appropriately (report gaps, don't hide them)
4. Include audit trails in all responses (dates, methods, data quality)
5. Return PROCESSED summaries, not raw data (Hot Potato Principle)

SCOPE GUARDS:
- Do NOT make investment recommendations
- Do NOT interpret market conditions
- Do NOT make predictions about future prices
- Only provide DATA - leave interpretation to other agents

OUTPUT FORMAT:
Always include in your responses:
- Data period used
- Number of observations
- Any data quality warnings
- Method used for calculations
"""
    
    async def process(self, state: AgentState) -> AgentState:
        """
        Process a data request.
        
        This is called by LangGraph when delegated to by the supervisor.
        """
        task = state.current_task
        
        if task is None:
            state.add_message("assistant", "No task provided to Data Agent")
            return state
        
        self.log(f"Processing task: {task.task_type.value}")
        
        # Based on task type, execute appropriate tools
        if task.task_type.value == "fetch_data":
            result = await self._handle_fetch_data(task)
        elif task.task_type.value == "calculate_risk":
            result = await self._handle_calculate_risk(task)
        else:
            # For optimization tasks, prepare all required data
            result = await self._prepare_optimization_data(task)
        
        # Store result in state
        state.add_sub_result(self.name, result)
        state.add_message("assistant", result.to_summary())
        
        return state
    
    async def _handle_fetch_data(self, task: PortfolioTask) -> PortfolioResult:
        """Handle a data fetch request."""
        # Fetch prices for all assets in universe
        prices_result = self.fetch_prices_tool(
            tickers=",".join(task.universe),
            period=task.historical_period
        )
        
        if not prices_result.get("success"):
            return self.create_result(
                task_id=task.task_id,
                success=False,
                error_message=prices_result.get("error", "Failed to fetch prices")
            )
        
        return self.create_result(
            task_id=task.task_id,
            success=True,
            reasoning="Successfully fetched price data",
            data_period=prices_result.get("period"),
        )
    
    async def _handle_calculate_risk(self, task: PortfolioTask) -> PortfolioResult:
        """Handle a risk calculation request."""
        # Calculate risk metrics for the portfolio
        if task.current_weights:
            # Portfolio risk
            metrics = self.get_risk_metrics_tool(
                tickers=",".join(task.universe),
                weights=json.dumps(task.current_weights),
                period=task.historical_period
            )
        else:
            # Individual asset risk
            metrics = self.get_risk_metrics_tool(
                tickers=",".join(task.universe),
                period=task.historical_period
            )
        
        return self.create_result(
            task_id=task.task_id,
            success=metrics.get("success", False),
            expected_volatility=metrics.get("volatility"),
            reasoning="Risk metrics calculated",
        )
    
    async def _prepare_optimization_data(self, task: PortfolioTask) -> PortfolioResult:
        """Prepare all data needed for portfolio optimization."""
        warnings = []
        
        # 1. Fetch prices
        prices_result = self.fetch_prices_tool(
            tickers=",".join(task.universe),
            period=task.historical_period
        )
        
        if not prices_result.get("success"):
            return self.create_result(
                task_id=task.task_id,
                success=False,
                error_message=f"Failed to fetch prices: {prices_result.get('error')}"
            )
        
        # 2. Calculate covariance matrix
        cov_result = self.calculate_covariance_tool(
            tickers=",".join(task.universe),
            period=task.historical_period,
            method="shrinkage"  # Default to shrinkage for stability
        )
        
        if not cov_result.get("success"):
            return self.create_result(
                task_id=task.task_id,
                success=False,
                error_message=f"Failed to calculate covariance: {cov_result.get('error')}"
            )
        
        if cov_result.get("warnings"):
            warnings.extend(cov_result["warnings"])
        
        # 3. Calculate expected returns
        returns_result = self.calculate_returns_tool(
            tickers=",".join(task.universe),
            period=task.historical_period,
            annualize=True
        )
        
        # 4. Get risk-free rate
        rf_result = self.get_risk_free_rate_tool()
        risk_free_rate = rf_result.get("rate", 0.05)
        
        # Store data in shared state for other agents
        result = self.create_result(
            task_id=task.task_id,
            success=True,
            reasoning="Prepared optimization data: prices, covariance, returns",
            data_period=cov_result.get("estimation_period"),
            warnings=warnings
        )
        
        # Attach data for optimization agent
        result.metadata = {
            "covariance_matrix": cov_result.get("covariance_matrix"),
            "correlation_matrix": cov_result.get("correlation_matrix"),
            "expected_returns": returns_result.get("annualized_returns"),
            "volatilities": cov_result.get("annualized_volatilities"),
            "risk_free_rate": risk_free_rate,
            "num_observations": cov_result.get("num_observations"),
        }
        
        return result
    
    # ========== TOOLS ==========
    
    def fetch_prices_tool(
        self,
        tickers: str,
        period: str = "5Y",
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        Fetch historical prices for given tickers.
        
        Args:
            tickers: Comma-separated ticker symbols (e.g., "SPY,TLT,GLD")
            period: Time period ("1Y", "3Y", "5Y", "10Y", "max")
            interval: Data interval ("1d", "1wk", "1mo")
            
        Returns:
            Dictionary with price data summary (NOT raw prices)
        """
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        
        try:
            import yfinance as yf
            
            # Calculate start date from period
            end_date = datetime.now()
            period_map = {
                "1Y": 365,
                "2Y": 730,
                "3Y": 1095,
                "5Y": 1825,
                "10Y": 3650,
            }
            days = period_map.get(period.upper(), 1825)
            start_date = end_date - timedelta(days=days)
            
            # Fetch data
            data = yf.download(
                ticker_list,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                interval=interval,
                progress=False
            )
            
            if data.empty:
                return {
                    "success": False,
                    "error": f"No data found for tickers: {ticker_list}"
                }
            
            # Extract close prices
            if len(ticker_list) == 1:
                prices = data["Close"].to_frame(ticker_list[0])
            else:
                prices = data["Close"]
            
            # Cache prices
            cache_key = f"{','.join(sorted(ticker_list))}_{period}"
            self._price_cache[cache_key] = prices
            self._cache_timestamps[cache_key] = datetime.now()
            
            # Build summary (Hot Potato - don't return raw data)
            summary = {
                "success": True,
                "tickers": ticker_list,
                "period": f"{prices.index[0].strftime('%Y-%m-%d')} to {prices.index[-1].strftime('%Y-%m-%d')}",
                "num_observations": len(prices),
                "data_points_per_ticker": {
                    ticker: int(prices[ticker].notna().sum())
                    for ticker in prices.columns
                },
                "latest_prices": {
                    ticker: float(prices[ticker].dropna().iloc[-1])
                    for ticker in prices.columns
                },
                "price_range": {
                    ticker: {
                        "min": float(prices[ticker].min()),
                        "max": float(prices[ticker].max()),
                    }
                    for ticker in prices.columns
                }
            }
            
            # Check for data quality issues
            warnings = []
            for ticker in prices.columns:
                missing = prices[ticker].isna().sum()
                if missing > 0:
                    warnings.append(f"{ticker}: {missing} missing values")
            
            if warnings:
                summary["warnings"] = warnings
            
            return summary
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def calculate_returns_tool(
        self,
        tickers: str,
        period: str = "5Y",
        method: str = "simple",
        annualize: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate returns for given tickers.
        
        Args:
            tickers: Comma-separated ticker symbols
            period: Time period for data
            method: "simple" or "log" returns
            annualize: Whether to annualize the mean returns
            
        Returns:
            Dictionary with return statistics
        """
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        
        # Check cache first
        cache_key = f"{','.join(sorted(ticker_list))}_{period}"
        
        if cache_key not in self._price_cache:
            # Fetch prices first
            fetch_result = self.fetch_prices_tool(tickers, period)
            if not fetch_result.get("success"):
                return fetch_result
        
        prices = self._price_cache[cache_key]
        
        try:
            # Calculate returns
            if method == "simple":
                returns = prices.pct_change().dropna()
            else:  # log
                returns = np.log(prices / prices.shift(1)).dropna()
            
            # Calculate statistics
            result = {
                "success": True,
                "tickers": ticker_list,
                "method": method,
                "num_observations": len(returns),
                "period": f"{returns.index[0].strftime('%Y-%m-%d')} to {returns.index[-1].strftime('%Y-%m-%d')}",
            }
            
            # Per-ticker stats
            mean_returns = returns.mean()
            if annualize:
                annualized = mean_returns * TRADING_DAYS_PER_YEAR
                result["annualized_returns"] = {
                    ticker: f"{annualized[ticker]:.2%}"
                    for ticker in returns.columns
                }
            
            result["daily_return_stats"] = {
                ticker: {
                    "mean": f"{mean_returns[ticker]:.4%}",
                    "std": f"{returns[ticker].std():.4%}",
                    "min": f"{returns[ticker].min():.4%}",
                    "max": f"{returns[ticker].max():.4%}",
                }
                for ticker in returns.columns
            }
            
            # Total return over period
            total_returns = (1 + returns).prod() - 1
            result["total_returns"] = {
                ticker: f"{total_returns[ticker]:.2%}"
                for ticker in returns.columns
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def calculate_covariance_tool(
        self,
        tickers: str,
        period: str = "5Y",
        method: str = "shrinkage"
    ) -> Dict[str, Any]:
        """
        Calculate covariance matrix for portfolio optimization.
        
        Args:
            tickers: Comma-separated ticker symbols
            period: Time period for estimation
            method: "sample", "shrinkage", or "exponential"
            
        Returns:
            Dictionary with covariance matrix and quality metrics
        """
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        
        # Check cache
        cache_key = f"{','.join(sorted(ticker_list))}_{period}"
        
        if cache_key not in self._price_cache:
            fetch_result = self.fetch_prices_tool(tickers, period)
            if not fetch_result.get("success"):
                return fetch_result
        
        prices = self._price_cache[cache_key]
        
        try:
            # Import from quant module
            from portfolio_tool.quant.covariance import CovarianceEstimator, CovarianceMethod
            
            # Calculate returns
            returns = prices.pct_change().dropna()
            
            # Estimate covariance
            estimator = CovarianceEstimator(
                method=CovarianceMethod(method),
                annualize=True,
                min_observations=60
            )
            
            result = estimator.estimate(returns)
            
            return result.to_dict()
            
        except ImportError:
            # Fallback if quant module not available
            returns = prices.pct_change().dropna()
            
            # Simple sample covariance
            cov_matrix = returns.cov() * TRADING_DAYS_PER_YEAR
            corr_matrix = returns.corr()
            
            vols = {
                ticker: float(np.sqrt(cov_matrix.loc[ticker, ticker]))
                for ticker in ticker_list
            }
            
            return {
                "success": True,
                "tickers": ticker_list,
                "method": method,
                "covariance_matrix": cov_matrix.to_dict(),
                "correlation_matrix": corr_matrix.to_dict(),
                "annualized_volatilities": {k: f"{v:.2%}" for k, v in vols.items()},
                "num_observations": len(returns),
                "estimation_period": f"{returns.index[0].strftime('%Y-%m-%d')} to {returns.index[-1].strftime('%Y-%m-%d')}",
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_risk_metrics_tool(
        self,
        tickers: str,
        period: str = "5Y",
        weights: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive risk metrics.
        
        Args:
            tickers: Comma-separated ticker symbols
            period: Time period
            weights: JSON string of portfolio weights (optional)
            
        Returns:
            Dictionary with risk metrics
        """
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        
        # Check cache
        cache_key = f"{','.join(sorted(ticker_list))}_{period}"
        
        if cache_key not in self._price_cache:
            fetch_result = self.fetch_prices_tool(tickers, period)
            if not fetch_result.get("success"):
                return fetch_result
        
        prices = self._price_cache[cache_key]
        returns = prices.pct_change().dropna()
        
        try:
            from portfolio_tool.quant.risk_metrics import RiskMetricsCalculator
            
            calc = RiskMetricsCalculator(risk_free_rate=0.05)
            
            if weights:
                # Portfolio metrics
                weight_dict = json.loads(weights)
                w = np.array([weight_dict.get(t, 0) for t in ticker_list])
                portfolio_returns = (returns * w).sum(axis=1)
                result = calc.calculate_all(portfolio_returns)
                return {
                    "type": "portfolio",
                    "weights": weight_dict,
                    **result.to_dict()
                }
            else:
                # Individual asset metrics
                results = {}
                for ticker in ticker_list:
                    asset_result = calc.calculate_all(returns[ticker])
                    results[ticker] = asset_result.to_dict()
                
                return {
                    "success": True,
                    "type": "individual",
                    "metrics": results
                }
                
        except ImportError:
            # Fallback
            vol = returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
            
            return {
                "success": True,
                "volatilities": {
                    ticker: f"{vol[ticker]:.2%}"
                    for ticker in ticker_list
                },
                "note": "Limited metrics - quant module not available"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_risk_free_rate_tool(self) -> Dict[str, Any]:
        """
        Get current risk-free rate (10Y Treasury or proxy).
        
        Returns:
            Dictionary with risk-free rate
        """
        try:
            import yfinance as yf
            
            # Use 10Y Treasury yield as proxy
            tnx = yf.Ticker("^TNX")
            hist = tnx.history(period="5d")
            
            if hist.empty:
                return {
                    "success": True,
                    "rate": 0.05,  # Default 5%
                    "source": "default",
                    "note": "Using default rate - Treasury data unavailable"
                }
            
            # TNX is quoted in percentage points
            rate = hist["Close"].iloc[-1] / 100
            
            return {
                "success": True,
                "rate": float(rate),
                "rate_formatted": f"{rate:.2%}",
                "source": "10Y Treasury (^TNX)",
                "as_of": hist.index[-1].strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            return {
                "success": True,
                "rate": 0.05,
                "source": "default",
                "note": f"Using default rate - error: {str(e)}"
            }
    
    def calculate_rolling_volatility_tool(
        self,
        ticker: str,
        window: int = 30,
        period: str = "1Y"
    ) -> Dict[str, Any]:
        """
        Calculate rolling volatility for regime detection.
        
        Args:
            ticker: Single ticker symbol
            window: Rolling window in days
            period: Data period
            
        Returns:
            Dictionary with rolling volatility statistics
        """
        ticker = ticker.strip().upper()
        
        try:
            import yfinance as yf
            
            # Fetch data
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                return {
                    "success": False,
                    "error": f"No data found for {ticker}"
                }
            
            # Calculate returns and rolling vol
            returns = hist["Close"].pct_change().dropna()
            rolling_vol = returns.rolling(window=window).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
            rolling_vol = rolling_vol.dropna()
            
            current_vol = rolling_vol.iloc[-1]
            avg_vol = rolling_vol.mean()
            percentile = (rolling_vol < current_vol).sum() / len(rolling_vol) * 100
            
            return {
                "success": True,
                "ticker": ticker,
                "window": window,
                "current_volatility": f"{current_vol:.2%}",
                "average_volatility": f"{avg_vol:.2%}",
                "percentile_1y": f"{percentile:.0f}th",
                "vol_regime": "HIGH" if current_vol > avg_vol * 1.2 else "LOW" if current_vol < avg_vol * 0.8 else "NORMAL",
                "min_volatility": f"{rolling_vol.min():.2%}",
                "max_volatility": f"{rolling_vol.max():.2%}",
                "period": f"{rolling_vol.index[0].strftime('%Y-%m-%d')} to {rolling_vol.index[-1].strftime('%Y-%m-%d')}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Factory function for creating Data Agent
def create_data_agent(verbose: bool = False) -> DataAgent:
    """
    Factory function to create a configured Data Agent.
    
    Args:
        verbose: Enable verbose logging
        
    Returns:
        Configured DataAgent instance
    """
    config = DataAgentConfig(
        name="DataAgent",
        role=AgentRole.DATA,
        verbose=verbose,
        temperature=0.0,
    )
    return DataAgent(config)
