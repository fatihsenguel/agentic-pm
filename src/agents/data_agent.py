"""
Data Agent for Quant Portfolio Manager.

The Data Agent is responsible for:
- Fetching market data (prices, fundamentals)
- Calculating returns and covariance matrices
- Computing risk metrics
- Providing data for optimization and backtesting

ARCHITECTURE (Separation of Concerns):
- DataAgent = Interface/Orchestrator
- DataManager = Database operations (prices, fundamentals)
- quant/ module = Pure calculations (covariance, returns, risk metrics)

The Agent DELEGATES work to these components:
- DB operations → DataManager
- Calculations → quant/ module
- NEVER direct yfinance calls

Design Principles:
- Hot Potato Principle: Return processed summaries, not raw data
- All results include audit trails (dates, methods used)
- Graceful handling of missing data
- Database as the single source of truth
"""

from typing import Any, Callable, Dict, List, Optional
import json
from datetime import datetime, date, timedelta
from dataclasses import dataclass

import pandas as pd
import numpy as np

from .base_agent import BaseAgent, AgentConfig, AgentRole, AgentState
from .protocols import PortfolioTask, PortfolioResult, CovarianceResult

from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.tools.data_tools import (
    list_tracked_assets, 
    fetch_stock_prices, 
    fetch_fundamentals,
    get_asset_info
)
from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.agents.schemas import AgentResponse

from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.agents.config import config

class DataAgent(BaseAgent):
    """
    Data Agent for fetching and processing market data.
    
    Capabilities:
    - fetch_prices: Get historical prices for assets (via DataManager)
    - calculate_returns: Compute returns from prices
    - calculate_covariance: Estimate covariance matrix
    - get_risk_metrics: Compute risk metrics for assets/portfolios
    - get_risk_free_rate: Fetch current risk-free rate (from macro data)
    
    ARCHITECTURE:
    - Uses DataManager for all database operations
    - Uses quant/ module for all calculations
    - No direct yfinance calls
    """
    
    def __init__(self, agent_config: Optional[AgentConfig] = None):
        """Initialize Data Agent."""
        if agent_config is None:
            agent_config = AgentConfig(
                name="DataAgent",
                role=AgentRole.DATA,
                temperature=0.0,  # Deterministic
            )
        super().__init__(agent_config)
        
        # Lazy-loaded components
        self._data_manager = None
        
        # In-memory cache for processed data (not raw prices)
        # This caches DataFrames AFTER they're loaded from DB
        self._prices_df_cache: Dict[str, pd.DataFrame] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
    
    # ==================== LAZY-LOADED COMPONENTS ====================
    
    @property
    def data_manager(self):
        """Lazy-load DataManager for database operations."""
        if self._data_manager is None:
            from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.data_manager import get_data_manager
            self._data_manager = get_data_manager()
        return self._data_manager
    
    # ==================== AGENT INTERFACE ====================
    
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
            "list_assets",
            "update_database",
            "get_asset_details"
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
    
    # ==================== PROCESS METHOD ====================
    
    async def process(self, state: AgentState) -> AgentState:
        """
        Process a data request and return a strict AgentResponse.
        
        PATCHED: Phase 6.5 - Fixed to properly handle state dict
        """
        # 1. Get the router decision from state
        decision = state.get("router_decision", {})
        intent = decision.get("intent", "unknown")
        parameters = decision.get("parameters", {})
        
        self.log(f"Processing intent: {intent}")
        
        # 2. Execute Logic based on intent
        try:
            if intent == "data_management":
                # Admin operations (list, update, get_info)
                result_data = await self._handle_data_management(state)
            elif intent in ["data_fetch", "optimization", "rebalancing", "backtest"]:
                # Data fetching for analysis
                result_data = await self._handle_market_data(state)
            else:
                result_data = {
                    "success": False, 
                    "error": f"Unknown intent for DataAgent: {intent}"
                }
        except Exception as e:
            result_data = {
                "success": False, 
                "error": f"Critical Error in DataAgent: {str(e)}"
            }

        # 3. Create Strict AgentResponse
        response = AgentResponse(
            success=result_data.get("success", False),
            agent_name="DataAgent",
            data=result_data,
            error=result_data.get("error"),
            warnings=result_data.get("warnings", [])
        )

        # 4. Update State
        sub_results = state.get("sub_results") or {}
        sub_results["DataAgent"] = response.model_dump()
        
        if isinstance(state, dict):
            state["sub_results"] = sub_results
        else:
            state.sub_results = sub_results

        # 5. Log summary (removed broken state.add_message call)
        summary_msg = result_data.get("message") or result_data.get("reasoning") or "Data processed."
        self.log(f"Complete: {summary_msg}")
        
        return state
    
    async def _handle_fetch_data(self, task: PortfolioTask) -> PortfolioResult:
        """Handle a data fetch request."""
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
        
        # 4. Get risk-free rate (from macro data in DB)
        rf_result = self.get_risk_free_rate_tool()
        
        # ✅ STRICT: Fail if risk-free rate is unavailable (no hardcoded default)
        if not rf_result.get("success"):
             return self.create_result(
                task_id=task.task_id,
                success=False,
                error_message=f"Risk-free rate error: {rf_result.get('error')}"
            )
        
        risk_free_rate = rf_result.get("rate")
        
        # Build result
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
    
    # ==================== HELPER METHODS ====================
    
    def _get_prices_from_db(
        self, 
        tickers: List[str], 
        start_date: date, 
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """
        Get prices from database.
        
        Returns DataFrame with tickers as columns, dates as index.
        Returns None if no data found.
        """
        try:
            from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.database_setup import Asset, DailyPrice
            
            session = self.data_manager.session
            
            # Get all prices for these tickers in date range
            prices_data = {}
            
            for ticker in tickers:
                # Get asset
                asset = session.query(Asset).filter(Asset.ticker == ticker).first()
                if not asset:
                    continue
                
                # Get prices
                prices = session.query(DailyPrice).filter(
                    DailyPrice.asset_id == asset.id,
                    DailyPrice.date >= start_date,
                    DailyPrice.date <= end_date
                ).order_by(DailyPrice.date).all()
                
                if prices:
                    prices_data[ticker] = {
                        p.date: float(p.close) for p in prices
                    }
            
            if not prices_data:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(prices_data)
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            self.log(f"Error getting prices from DB: {e}")
            return None
    
    def _ensure_prices_in_db(
        self, 
        tickers: List[str], 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """
        Ensure prices are in database, fetching if needed.
        
        Returns status dict with success and any warnings.
        """
        warnings = []
        
        for ticker in tickers:
            try:
                # Get or create asset
                asset = self.data_manager._get_or_create_asset(
                    ticker=ticker,
                    name=ticker,
                    asset_class="equity"
                )
                
                # Update prices
                result = self.data_manager.update_prices_for_asset(
                    asset=asset,
                    start_date=start_date
                )
                
                if not result.success:
                    warnings.append(f"{ticker}: {result.error_message}")
                elif result.affected_count == 0:
                    warnings.append(f"{ticker}: No new data")
                    
            except Exception as e:
                warnings.append(f"{ticker}: {str(e)}")
        
        return {
            "success": len(warnings) < len(tickers),  # At least some succeeded
            "warnings": warnings if warnings else None
        }
    
    def _calculate_period_dates(self, period: str) -> tuple:
        """Convert period string to start/end dates."""
        end_date = date.today()
        days = config.data.period_days.get(period.upper(), 1825)  # Default 5Y
        start_date = end_date - timedelta(days=days)
        return start_date, end_date
    
    # ==================== TOOL METHODS ====================
    
    def fetch_prices_tool(
        self,
        tickers: str,
        period: str = "5Y",
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        Fetch historical prices for given tickers.
        
        Uses DataManager to fetch and persist prices to database.
        
        Args:
            tickers: Comma-separated ticker symbols (e.g., "SPY,TLT,GLD")
            period: Time period ("1Y", "3Y", "5Y", "10Y")
            interval: Data interval (only "1d" supported for DB)
            
        Returns:
            Dictionary with price data summary (NOT raw prices)
        """
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        start_date, end_date = self._calculate_period_dates(period)
        
        try:
            # Step 1: Ensure prices are in database
            if config.data.auto_fetch_if_missing:
                fetch_status = self._ensure_prices_in_db(ticker_list, start_date, end_date)
                if fetch_status.get("warnings"):
                    self.log(f"Fetch warnings: {fetch_status['warnings']}")
            
            # Step 2: Get prices from database
            prices = self._get_prices_from_db(ticker_list, start_date, end_date)
            
            if prices is None or prices.empty:
                return {
                    "success": False,
                    "error": f"No data found for tickers: {ticker_list}"
                }
            
            # Step 3: Cache the DataFrame for subsequent calculations
            cache_key = f"{','.join(sorted(ticker_list))}_{period}"
            self._prices_df_cache[cache_key] = prices
            self._cache_timestamps[cache_key] = datetime.now()
            
            # Create JSON for downstream tools (like BacktestAgent)
            price_data_json = prices.to_json(orient="index", date_format="iso")
            
            # Step 4: Build summary (Hot Potato - don't return raw data)
            summary = {
                "success": True,
                "tickers": ticker_list,
                "period": f"{prices.index[0].strftime('%Y-%m-%d')} to {prices.index[-1].strftime('%Y-%m-%d')}",
                "num_observations": len(prices),
                "data_source": "database",
                "data_points_per_ticker": {
                    ticker: int(prices[ticker].notna().sum())
                    for ticker in prices.columns
                },
                "latest_prices": {
                    ticker: round(float(prices[ticker].dropna().iloc[-1]), 2)
                    for ticker in prices.columns
                },
                "price_range": {
                    ticker: {
                        "min": round(float(prices[ticker].min()), 2),
                        "max": round(float(prices[ticker].max()), 2),
                    }
                    for ticker in prices.columns
                },
                "price_data": price_data_json 
            }
            
            # Check for data quality issues
            warnings = []
            for ticker in prices.columns:
                missing = prices[ticker].isna().sum()
                if missing > 0:
                    warnings.append(f"{ticker}: {missing} missing values")
            
            # Check for tickers not found
            missing_tickers = set(ticker_list) - set(prices.columns)
            if missing_tickers:
                warnings.append(f"No data for: {', '.join(missing_tickers)}")
            
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
        cache_key = f"{','.join(sorted(ticker_list))}_{period}"
        
        # Check cache first, fetch if needed
        if cache_key not in self._prices_df_cache:
            fetch_result = self.fetch_prices_tool(tickers, period)
            if not fetch_result.get("success"):
                return fetch_result
        
        prices = self._prices_df_cache[cache_key]
        
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
                annualized = mean_returns * config.data.trading_days_per_year
                result["annualized_returns"] = {
                    ticker: f"{annualized[ticker]:.2%}"
                    for ticker in returns.columns
                }
                # ✅ STRICT: Always return raw floats for calculation (Bank Standard)
                result["annualized_returns_raw"] = {
                    ticker: round(float(annualized[ticker]), 6)
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
        period: str = None,
        method: str = None
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

        period = period or config.data.default_period
        method = method or config.data.default_covariance_method

        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        cache_key = f"{','.join(sorted(ticker_list))}_{period}"
        
        # Check cache first
        if cache_key not in self._prices_df_cache:
            fetch_result = self.fetch_prices_tool(tickers, period)
            if not fetch_result.get("success"):
                return fetch_result
        
        prices = self._prices_df_cache[cache_key]
        
        try:
            # Try to use quant module
            from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.quant.covariance import CovarianceEstimator, CovarianceMethod
            
            returns = prices.pct_change().dropna()
            
            estimator = CovarianceEstimator(
                method=CovarianceMethod(method),
                annualize=True,
                min_observations=config.data.min_observations
            )
            
            result = estimator.estimate(returns)
            
            return result.to_dict()
            
        except ImportError:
            # Fallback if quant module not available
            returns = prices.pct_change().dropna()
            
            cov_matrix = returns.cov() * config.data.trading_days_per_year
            corr_matrix = returns.corr()
            
            vols = {
                ticker: float(np.sqrt(cov_matrix.loc[ticker, ticker]))
                for ticker in ticker_list if ticker in cov_matrix.columns
            }
            
            return {
                "success": True,
                "tickers": ticker_list,
                "method": method,
                "covariance_matrix": cov_matrix.to_dict(),
                "correlation_matrix": corr_matrix.to_dict(),
                "annualized_volatilities": {k: f"{v:.2%}" for k, v in vols.items()},
                # ✅ STRICT: Fallback MUST provide raw floats for math (Bank Standard)
                "annualized_volatilities_raw": vols,
                "num_observations": len(returns),
                "estimation_period": f"{returns.index[0].strftime('%Y-%m-%d')} to {returns.index[-1].strftime('%Y-%m-%d')}",
                "note": "Using fallback calculation (quant module not available)"
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
        cache_key = f"{','.join(sorted(ticker_list))}_{period}"
        
        if cache_key not in self._prices_df_cache:
            fetch_result = self.fetch_prices_tool(tickers, period)
            if not fetch_result.get("success"):
                return fetch_result
        
        prices = self._prices_df_cache[cache_key]
        returns = prices.pct_change().dropna()
        
        try:
            from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.quant.risk_metrics import RiskMetricsCalculator
            
            # Get risk-free rate from macro data
            rf_result = self.get_risk_free_rate_tool()
            risk_free_rate = rf_result.get("rate", 0.05)
            
            calc = RiskMetricsCalculator(risk_free_rate=risk_free_rate)
            
            if weights:
                # Portfolio metrics
                weight_dict = json.loads(weights)
                w = np.array([weight_dict.get(t, 0) for t in ticker_list])
                portfolio_returns = (returns * w).sum(axis=1)
                result = calc.calculate_all(portfolio_returns)
                return {
                    "success": True,
                    "type": "portfolio",
                    "weights": weight_dict,
                    "risk_free_rate": risk_free_rate,
                    **result.to_dict()
                }
            else:
                # Individual asset metrics
                results = {}
                for ticker in ticker_list:
                    if ticker in returns.columns:
                        asset_result = calc.calculate_all(returns[ticker])
                        results[ticker] = asset_result.to_dict()
                
                return {
                    "success": True,
                    "type": "individual",
                    "risk_free_rate": risk_free_rate,
                    "metrics": results
                }
                
        except ImportError:
            # Fallback
            vol = returns.std() * np.sqrt(config.data.trading_days_per_year)
            
            return {
                "success": True,
                "volatilities": {
                    ticker: f"{vol[ticker]:.2%}"
                    for ticker in ticker_list if ticker in vol.index
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
        Get current risk-free rate from macro data in database.
        
        Uses 10Y Treasury yield from MacroData table.
        FAIL SAFE: Fails if not in DB and no config default exists.
        
        Returns:
            Dictionary with risk-free rate or error.
        """
        try:
            # Try to get from macro data in database
            latest = self.data_manager.get_latest_macro_values()
            
            if latest.get("success"):
                indicators = latest.get("indicators", {})
                
                # Use 10Y Treasury
                if "TNX_10Y" in indicators:
                    rate = indicators["TNX_10Y"]["value"] / 100  # Convert from % to decimal
                    return {
                        "success": True,
                        "rate": float(rate),
                        "rate_formatted": f"{rate:.2%}",
                        "source": "database (10Y Treasury)",
                        "as_of": indicators["TNX_10Y"]["date"]
                    }
                
                # Fallback to 3M if 10Y not available
                if "IRX_3M" in indicators:
                    rate = indicators["IRX_3M"]["value"] / 100
                    return {
                        "success": True,
                        "rate": float(rate),
                        "rate_formatted": f"{rate:.2%}",
                        "source": "database (3M Treasury)",
                        "as_of": indicators["IRX_3M"]["date"]
                    }
            
            # ✅ STRICT: Check config for manual override/default
            # Never hardcode financial assumptions in code (Bank Standard)
            default_rate = getattr(config.data, 'default_risk_free_rate', None)
            
            if default_rate is not None:
                return {
                    "success": True,
                    "rate": float(default_rate),
                    "rate_formatted": f"{default_rate:.2%}",
                    "source": "config_fallback",
                    "note": "Macro data missing, using configured default"
                }

            # ✅ STRICT: Fail loudly if no data available
            return {
                "success": False,
                "error": "Risk-free rate unavailable in DB and no default configured.",
                "fix": "Run MacroAgent to fetch Treasury yields or set 'default_risk_free_rate' in config."
            }
            
        except Exception as e:
            # If unexpected error, still allow config fallback if safe
            return {
                 "success": False,
                 "error": f"Error fetching risk-free rate: {str(e)}"
            }
    
    def calculate_rolling_volatility_tool(
        self,
        ticker: str,
        window: int = 30,
        period: str = "1Y"
    ) -> Dict[str, Any]:
        """
        Calculate rolling volatility for regime detection.
        
        Uses data from database.
        
        Args:
            ticker: Single ticker symbol
            window: Rolling window in days
            period: Data period
            
        Returns:
            Dictionary with rolling volatility statistics
        """
        ticker = ticker.strip().upper()
        start_date, end_date = self._calculate_period_dates(period)
        
        try:
            # Get prices from database
            prices = self._get_prices_from_db([ticker], start_date, end_date)
            
            if prices is None or prices.empty or ticker not in prices.columns:
                # Try to fetch first
                if config.data.auto_fetch_if_missing:
                    self._ensure_prices_in_db([ticker], start_date, end_date)
                    prices = self._get_prices_from_db([ticker], start_date, end_date)
                
                if prices is None or prices.empty:
                    return {
                        "success": False,
                        "error": f"No data found for {ticker}"
                    }
            
            # Calculate returns and rolling vol
            returns = prices[ticker].pct_change().dropna()
            rolling_vol = returns.rolling(window=window).std() * np.sqrt(config.data.trading_days_per_year)
            rolling_vol = rolling_vol.dropna()
            
            if len(rolling_vol) == 0:
                return {
                    "success": False,
                    "error": f"Insufficient data for rolling calculation (need {window}+ observations)"
                }
            
            current_vol = rolling_vol.iloc[-1]
            avg_vol = rolling_vol.mean()
            percentile = (rolling_vol < current_vol).sum() / len(rolling_vol) * 100
            
            # Determine regime
            if current_vol > avg_vol * 1.2:
                vol_regime = "HIGH"
            elif current_vol < avg_vol * 0.8:
                vol_regime = "LOW"
            else:
                vol_regime = "NORMAL"
            
            return {
                "success": True,
                "ticker": ticker,
                "window": window,
                "data_source": "database",
                "current_volatility": f"{current_vol:.2%}",
                "current_volatility_raw": round(float(current_vol), 6),
                "average_volatility": f"{avg_vol:.2%}",
                "percentile_1y": f"{percentile:.0f}th",
                "vol_regime": vol_regime,
                "min_volatility": f"{rolling_vol.min():.2%}",
                "max_volatility": f"{rolling_vol.max():.2%}",
                "period": f"{rolling_vol.index[0].strftime('%Y-%m-%d')} to {rolling_vol.index[-1].strftime('%Y-%m-%d')}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


    async def _handle_data_management(self, state: AgentState) -> Dict[str, Any]:
        """
        Handle Admin/Data Management requests (List, Update, Info).
        Uses tools from src/portfolio_tool/tools/data_tools.py
        
        PATCHED: Phase 6.5 - Fixed to accept state dict instead of PortfolioTask
        
        Args:
            state: AgentState dict containing router_decision with parameters
            
        Returns:
            Dict with success, message, and data
        """
        # Extract parameters from state (not from PortfolioTask)
        decision = state.get("router_decision", {})
        parameters = decision.get("parameters", {})
        
        command = parameters.get("command", "list_assets")
        tickers = parameters.get("tickers", [])
        portfolio_id = parameters.get("portfolio_id") or state.get("portfolio_id")
        
        # If portfolio_id provided but no tickers, load from portfolio
        if portfolio_id and not tickers:
            try:
                from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.portfolio_manager import PortfolioManager
                pm = PortfolioManager()
                tickers = pm.get_portfolio_tickers(portfolio_id)
            except Exception as e:
                self.log(f"Could not load portfolio {portfolio_id}: {e}")
        
        self.log(f"Data Management: command={command}, tickers={tickers}")
        
        try:
            # =================================================================
            # COMMAND: list_assets
            # =================================================================
            if command == "list_assets":
                tool_result = list_tracked_assets.invoke({})
                
                if tool_result.get("success"):
                    assets = tool_result.get("assets", [])
                    return {
                        "success": True,
                        "message": f"Found {len(assets)} tracked assets in the database.",
                        "assets": assets,
                        "count": len(assets)
                    }
                else:
                    return {
                        "success": False,
                        "error": tool_result.get("error", "Failed to list assets")
                    }
            
            # =================================================================
            # COMMAND: get_info
            # =================================================================
            elif command == "get_info":
                if not tickers:
                    return {
                        "success": False,
                        "error": "No ticker specified for get_info command."
                    }
                
                ticker = tickers[0]
                tool_result = get_asset_info.invoke(ticker)
                
                if tool_result.get("success"):
                    return {
                        "success": True,
                        "message": f"Retrieved info for {ticker}.",
                        "asset_info": tool_result
                    }
                else:
                    return {
                        "success": False,
                        "error": tool_result.get("error", f"Failed to get info for {ticker}")
                    }
            
            # =================================================================
            # COMMAND: update_prices / fetch_prices
            # =================================================================
            elif command in ["update_prices", "fetch_prices"]:
                if not tickers:
                    return {
                        "success": False,
                        "error": "No tickers specified for price update."
                    }
                
                ticker_str = ",".join(tickers)
                tool_result = fetch_stock_prices.invoke({"ticker": ticker_str})
                
                if tool_result.get("success"):
                    return {
                        "success": True,
                        "message": f"Successfully updated prices for {len(tickers)} ticker(s): {ticker_str}",
                        "tickers_updated": tickers,
                        "details": tool_result
                    }
                else:
                    return {
                        "success": False,
                        "error": tool_result.get("error", f"Failed to update prices for {ticker_str}")
                    }
            
            # =================================================================
            # COMMAND: fetch_fundamentals
            # =================================================================
            elif command == "fetch_fundamentals":
                if not tickers:
                    return {
                        "success": False,
                        "error": "No ticker specified for fetch_fundamentals command."
                    }
                
                ticker = tickers[0]
                tool_result = fetch_fundamentals.invoke(ticker)
                
                if tool_result.get("success"):
                    return {
                        "success": True,
                        "message": f"Successfully fetched fundamentals for {ticker}.",
                        "fundamentals": tool_result
                    }
                else:
                    return {
                        "success": False,
                        "error": tool_result.get("error", f"Failed to fetch fundamentals for {ticker}")
                    }
            
            # =================================================================
            # UNKNOWN COMMAND
            # =================================================================
            else:
                return {
                    "success": False,
                    "error": f"Unknown data management command: {command}. "
                            f"Valid: list_assets, update_prices, get_info, fetch_fundamentals"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Data Management Error: {str(e)}"
            }

# ==================== FACTORY FUNCTION ====================

def create_data_agent(verbose: bool = False) -> DataAgent:
    """
    Factory function to create a configured Data Agent.
    
    Args:
        verbose: Enable verbose logging
        
    Returns:
        Configured DataAgent instance
    """
    agent_config = AgentConfig(
        name="DataAgent",
        role=AgentRole.DATA,
        verbose=verbose,
        temperature=0.0,
    )
    return DataAgent(agent_config)