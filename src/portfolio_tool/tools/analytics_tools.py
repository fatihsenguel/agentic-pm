# src/portfolio_tool/tools/analytics_tools.py
"""
Layer 5: Analytics Tools - LangChain wrappers for MetricsCalculator
===================================================================

These tools expose the MetricsCalculator to the agent.
They follow the same patterns as data_tools.py.

Design Principles:
- Tools are thin wrappers - logic lives in MetricsCalculator
- All tools return Dict (JSON-serializable)
- Hot Potato: Agent gets summaries, not raw data
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool

from portfolio_tool.analytics.metrics import MetricsCalculator


# =============================================================================
# SINGLETON CALCULATOR (consistent with data_tools pattern)
# =============================================================================

_calculator_instance: Optional[MetricsCalculator] = None


def _get_calculator() -> MetricsCalculator:
    """Get or create the singleton MetricsCalculator instance."""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = MetricsCalculator()
    return _calculator_instance


# =============================================================================
# ANALYTICS TOOLS
# =============================================================================

@tool
def calculate_returns(ticker: str, days: int = 365) -> Dict[str, Any]:
    """
    Calculate return metrics for a stock.
    
    Use this to analyze how well a stock has performed over a period.
    Returns total return and CAGR (Compound Annual Growth Rate).
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        days: Number of days to analyze (default: 365 for 1 year)
    
    Returns:
        Dict with total_return, cagr, and price info.
        
    Example:
        calculate_returns("AAPL", 365)
        → {"total_return": 0.15, "cagr": 0.12, "total_return_pct": "15.00%", ...}
    """
    try:
        calc = _get_calculator()
        return calc.calculate_returns(ticker, days)
    except Exception as e:
        return {"success": False, "ticker": ticker, "error": str(e)}


@tool
def calculate_volatility(ticker: str, days: int = 365) -> Dict[str, Any]:
    """
    Calculate volatility (risk metric) for a stock.
    
    Volatility measures how much the price fluctuates. Higher volatility = more risk.
    Returns annualized volatility as a percentage.
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days to analyze (default: 365)
    
    Returns:
        Dict with volatility percentage and interpretation.
        
    Example:
        calculate_volatility("TSLA", 365)
        → {"volatility": 0.45, "volatility_pct": "45.00%", "interpretation": "Very high volatility"}
    """
    try:
        calc = _get_calculator()
        return calc.calculate_volatility(ticker, days)
    except Exception as e:
        return {"success": False, "ticker": ticker, "error": str(e)}


@tool
def calculate_sharpe_ratio(ticker: str, days: int = 365, risk_free_rate: float = 0.05) -> Dict[str, Any]:
    """
    Calculate Sharpe Ratio (risk-adjusted return) for a stock.
    
    Sharpe Ratio = (Return - Risk Free Rate) / Volatility
    Higher is better. Above 1 is good, above 2 is very good.
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days to analyze (default: 365)
        risk_free_rate: Annual risk-free rate (default: 0.05 = 5%)
    
    Returns:
        Dict with sharpe_ratio and interpretation.
        
    Example:
        calculate_sharpe_ratio("AAPL", 365)
        → {"sharpe_ratio": 1.5, "interpretation": "Good risk-adjusted return"}
    """
    try:
        calc = _get_calculator()
        return calc.calculate_sharpe_ratio(ticker, days, risk_free_rate)
    except Exception as e:
        return {"success": False, "ticker": ticker, "error": str(e)}


@tool
def calculate_max_drawdown(ticker: str, days: int = 365) -> Dict[str, Any]:
    """
    Calculate Maximum Drawdown for a stock.
    
    Max Drawdown is the largest peak-to-trough decline. It shows the worst
    loss an investor would have experienced.
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days to analyze (default: 365)
    
    Returns:
        Dict with max_drawdown percentage and dates.
        
    Example:
        calculate_max_drawdown("META", 365)
        → {"max_drawdown_pct": "-25.00%", "peak_date": "2024-01-15", "trough_date": "2024-03-20"}
    """
    try:
        calc = _get_calculator()
        return calc.calculate_max_drawdown(ticker, days)
    except Exception as e:
        return {"success": False, "ticker": ticker, "error": str(e)}


@tool
def get_price_statistics(ticker: str, days: int = 30) -> Dict[str, Any]:
    """
    Get price statistics (min, max, average, median) for a stock.
    
    Useful for understanding the price range over a period.
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days to analyze (default: 30)
    
    Returns:
        Dict with current_price, min, max, mean, median prices.
        
    Example:
        get_price_statistics("NVDA", 30)
        → {"current_price": 450.00, "min_price": 420.00, "max_price": 480.00, ...}
    """
    try:
        calc = _get_calculator()
        return calc.get_price_statistics(ticker, days)
    except Exception as e:
        return {"success": False, "ticker": ticker, "error": str(e)}


@tool
def compare_stocks(tickers: str, days: int = 365) -> Dict[str, Any]:
    """
    Compare multiple stocks side by side.
    
    Compares returns, volatility, and Sharpe ratio for up to 10 stocks.
    
    Args:
        tickers: Comma-separated ticker symbols (e.g., "AAPL,MSFT,GOOGL")
        days: Number of days to analyze (default: 365)
    
    Returns:
        Dict with comparison table sorted by best return.
        
    Example:
        compare_stocks("AAPL,MSFT,GOOGL", 365)
        → {"comparison": [{"ticker": "AAPL", "total_return": "15%", ...}, ...]}
    """
    try:
        # Parse comma-separated tickers
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        
        if len(ticker_list) < 2:
            return {
                "success": False,
                "error": "Need at least 2 tickers. Format: 'AAPL,MSFT,GOOGL'"
            }
        
        calc = _get_calculator()
        return calc.compare_stocks(ticker_list, days)
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# TOOL COLLECTIONS
# =============================================================================

ALL_ANALYTICS_TOOLS = [
    calculate_returns,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    get_price_statistics,
    compare_stocks,
]

RISK_TOOLS = [
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
]

PERFORMANCE_TOOLS = [
    calculate_returns,
    get_price_statistics,
    compare_stocks,
]
