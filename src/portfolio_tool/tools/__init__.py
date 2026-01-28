# src/portfolio_tool/tools/__init__.py

"""
Tools Module - Agent Interface Layer.

This module provides tools that agents can use to interact with the system.
Tools are the interface between AI agents and the business logic.
"""

# Data Tools
from .data_tools import (
    # WRITE Tools (fetch from API)
    fetch_stock_prices,
    fetch_financial_statements,
    fetch_fundamentals,
    fetch_earnings_history,
    
    # READ Tools (query DB)
    list_tracked_assets,
    get_asset_info,
    get_latest_price,
    query_financial_data,
)

# Macro Tools
from .macro_tools import (
    fetch_macro_data,
    get_macro_snapshot,
    get_vix_analysis,
    get_yield_curve_analysis,
    get_market_regime,
    generate_taa_signal,
    fetch_fed_minutes,
    list_available_fed_minutes,
    get_macro_tools,
)

# Rebalance Tools (Pure Math - Deterministic)
from .rebalance_tools import (
    # Data classes
    RebalanceConfig,
    Position,
    Portfolio,
    Trade,
    RebalanceResult,
    
    # Core functions
    calculate_drift,
    calculate_max_drift,
    calculate_avg_drift,
    should_rebalance,
    generate_trades,
    calculate_rebalance_costs,
    calculate_break_even_drift,
    analyze_rebalance,
    
    # Agent-ready wrappers
    analyze_rebalance_tool,
    calculate_drift_tool,
    generate_trade_list_tool,
    quick_drift_check,
)

# Analytics Tools
from .analytics_tools import (
    calculate_returns,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    get_price_statistics,
    compare_stocks,
)

# Portfolio Tools (NEW)
from .portfolio_tools import (
    list_portfolios,
    get_portfolio_details,
    get_portfolio_holdings,
    get_portfolio_summary,
    create_portfolio,
    add_holding_to_portfolio,
    update_portfolio_holding,
    remove_holding_from_portfolio,
    delete_portfolio,
    check_portfolio_exists,
    find_portfolio_by_name,
)

__all__ = [
    # Data Tools
    "fetch_stock_prices",
    "fetch_financial_statements",
    "fetch_fundamentals",
    "fetch_earnings_history",
    "list_tracked_assets",
    "get_asset_info",
    "get_latest_price",
    "query_financial_data",
    
    # Macro Tools
    "fetch_macro_data",
    "get_macro_snapshot",
    "get_vix_analysis",
    "get_yield_curve_analysis",
    "get_market_regime",
    "generate_taa_signal",
    "fetch_fed_minutes",
    "list_available_fed_minutes",
    "get_macro_tools",
    
    # Rebalance Tools
    "RebalanceConfig",
    "Position",
    "Portfolio",
    "Trade",
    "RebalanceResult",
    "calculate_drift",
    "calculate_max_drift",
    "calculate_avg_drift",
    "should_rebalance",
    "generate_trades",
    "calculate_rebalance_costs",
    "calculate_break_even_drift",
    "analyze_rebalance",
    "analyze_rebalance_tool",
    "calculate_drift_tool",
    "generate_trade_list_tool",
    "quick_drift_check",
    
    # Analytics Tools
    "calculate_returns",
    "calculate_volatility",
    "calculate_sharpe_ratio",
    "calculate_max_drawdown",
    "get_price_statistics",
    "compare_stocks",

    # Portfolio Tools
    "list_portfolios",
    "get_portfolio_details",
    "get_portfolio_holdings",
    "get_portfolio_summary",
    "create_portfolio",
    "add_holding_to_portfolio",
    "update_portfolio_holding",
    "remove_holding_from_portfolio",
    "delete_portfolio",
    "check_portfolio_exists",
    "find_portfolio_by_name",
]