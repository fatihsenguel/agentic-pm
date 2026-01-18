"""
SNIPPET: tools/analytics_tools.py
PURPOSE: LangChain tool wrappers for MetricsCalculator (Layer 5 → Layer 4)
PATTERN: Singleton + Thin wrappers (logic in MetricsCalculator, not tools)
"""

from langchain_core.tools import tool
from portfolio_tool.analytics.metrics import MetricsCalculator

# ========== SINGLETON PATTERN ==========
_calculator_instance: Optional[MetricsCalculator] = None

def _get_calculator() -> MetricsCalculator:
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = MetricsCalculator()
    return _calculator_instance

# ========== ANALYTICS TOOLS (All return Dict[str, Any]) ==========

@tool
def calculate_returns(ticker: str, days: int = 365) -> Dict[str, Any]:
    """
    Total return & CAGR calculation.
    Returns: {"success": True, "total_return": 0.15, "cagr": 0.12, 
              "first_price": 182.50, "last_price": 207.39, "data_points": 251}
    """
    return _get_calculator().calculate_returns(ticker, days)

@tool
def calculate_volatility(ticker: str, days: int = 365) -> Dict[str, Any]:
    """
    Annualized volatility (std dev of returns).
    Returns: {"success": True, "volatility": 0.22, "volatility_pct": "22%", 
              "interpretation": "Moderate volatility"}
    """
    return _get_calculator().calculate_volatility(ticker, days)

@tool
def calculate_sharpe_ratio(ticker: str, days: int = 365, risk_free_rate: float = 0.05) -> Dict[str, Any]:
    """
    Risk-adjusted return: (Return - RiskFree) / Volatility.
    Returns: {"success": True, "sharpe_ratio": 1.5, 
              "interpretation": "Good risk-adjusted return"}
    """
    return _get_calculator().calculate_sharpe_ratio(ticker, days, risk_free_rate)

@tool
def calculate_max_drawdown(ticker: str, days: int = 365) -> Dict[str, Any]:
    """
    Worst peak-to-trough decline.
    Returns: {"success": True, "max_drawdown": -0.18, "max_drawdown_pct": "-18%",
              "peak_date": "2024-06-15", "trough_date": "2024-08-10"}
    """
    return _get_calculator().calculate_max_drawdown(ticker, days)

@tool
def get_price_statistics(ticker: str, days: int = 30) -> Dict[str, Any]:
    """
    Basic stats: min, max, avg, median, std.
    Returns: {"success": True, "min": 180.50, "max": 210.30, 
              "avg": 195.20, "median": 194.80}
    """
    return _get_calculator().get_price_statistics(ticker, days)

@tool
def compare_stocks(tickers: str, days: int = 365) -> Dict[str, Any]:
    """
    Side-by-side comparison of multiple stocks.
    Args: tickers as comma-separated string: "AAPL,MSFT,GOOGL"
    Returns: {"success": True, "comparison": [
                {"ticker": "AAPL", "return": 0.15, "volatility": 0.22, "sharpe": 1.2},
                {"ticker": "MSFT", "return": 0.18, "volatility": 0.20, "sharpe": 1.4}
              ]}
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    return _get_calculator().compare_stocks(ticker_list, days)

# ========== TOOL COLLECTIONS ==========
ALL_ANALYTICS_TOOLS = [
    calculate_returns,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    get_price_statistics,
    compare_stocks,
]

# ========== KEY PATTERNS ==========
"""
1. SINGLETON: One calculator for all tools (efficiency)
2. THIN WRAPPERS: Tools just call MetricsCalculator methods
3. HOT POTATO: Return aggregated metrics, never raw price arrays
4. CONSISTENT RETURNS: All return Dict with "success" flag
5. INTERPRETATION: Include human-readable explanations (e.g., "High volatility")
"""
