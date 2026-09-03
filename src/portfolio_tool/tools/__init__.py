"""
Tools Module - Agent Interface Layer.

This module provides tools that agents can use to interact with the system.
Tools are the interface between AI agents and the business logic.

Available Tools:
    - data_tools: Market data operations
        - calculate_covariance_tool
        - calculate_returns_tool
        - get_risk_free_rate_tool
        
    - macro_tools: Macro environment analysis
        - fetch_macro_data_tool
        - get_macro_snapshot_tool
        - assess_regime_tool
        - generate_taa_signal_tool
        
    - rebalance_tools: Portfolio rebalancing (DETERMINISTIC - no LLM)
        - analyze_rebalance
        - calculate_drift
        - generate_trades
        - calculate_rebalance_costs
        
    - analytics_tools: Performance metrics
        - calculate_performance_metrics
        - calculate_risk_metrics

Design Principle - Agent-Ready Responses:
    All tools return structured dictionaries:
    {
        "success": bool,
        "data": {...},
        "metadata": {...},
        "error": Optional[str]
    }

Design Principle - Hot Potato:
    Tools aggregate data before returning. Agents receive summaries,
    not raw data arrays.
"""

# Data Tools
from .data_tools import (
    ALL_DATA_TOOLS,
    FETCH_TOOLS,
    READ_TOOLS,
    fetch_stock_prices,
    fetch_financial_statements,
    fetch_fundamentals,
    fetch_earnings_history,
    get_asset_info,
    list_tracked_assets,
    get_latest_price,
    query_financial_data,
)

# Macro Tools
from .macro_tools import (
    get_macro_tools,
    fetch_macro_data,
    get_macro_snapshot,
    get_market_regime,
    get_vix_analysis,
    get_yield_curve_analysis
)

# Rebalance Tools (Pure Math - Deterministic)
from .rebalance_tools import (
    analyze_rebalance,
    calculate_drift,
    should_rebalance,
    generate_trades,
    calculate_rebalance_costs,
    calculate_break_even_drift,
    analyze_rebalance_tool,
    calculate_drift_tool,
    generate_trade_list_tool,
    quick_drift_check,
    RebalanceConfig,
    Position,
    Portfolio,
    Trade,
    RebalanceResult,
)

# Analytics Tools
from .analytics_tools import (
    ALL_ANALYTICS_TOOLS,
    RISK_TOOLS,
    PERFORMANCE_TOOLS,
    calculate_returns,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    get_price_statistics,
)

__all__ = [n for n in dir() if not n.startswith("_")]
