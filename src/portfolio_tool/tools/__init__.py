"""
Tools Module - Agent Interface Layer.

This module provides tools that agents can use to interact with the system.
Tools are the interface between AI agents and the business logic.

Available Tools:
    - data_tools: Market data operations
        - fetch_prices_tool
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
    fetch_prices_tool,
    calculate_covariance_tool,
    calculate_returns_tool,
    get_risk_free_rate_tool,
    get_latest_prices_tool,
)

# Macro Tools
from .macro_tools import (
    fetch_macro_data_tool,
    get_macro_snapshot_tool,
    assess_regime_tool,
    generate_taa_signal_tool,
)

# Rebalance Tools (Pure Math - Deterministic)
from .rebalance_tools import (
    # Main analysis function
    analyze_rebalance,
    
    # Individual functions
    calculate_drift,
    should_rebalance,
    generate_trades,
    calculate_rebalance_costs,
    calculate_break_even_drift,
    
    # Agent-ready wrappers
    analyze_rebalance_tool,
    calculate_drift_tool,
    generate_trade_list_tool,
    quick_drift_check,
    
    # Data classes
    RebalanceConfig,
    Position,
    Portfolio,
    Trade,
    RebalanceResult,
)

# Analytics Tools
from .analytics_tools import (
    calculate_portfolio_metrics,
    calculate_risk_metrics,
)

__all__ = [
    # Data Tools
    "fetch_prices_tool",
    "calculate_covariance_tool",
    "calculate_returns_tool",
    "get_risk_free_rate_tool",
    "get_latest_prices_tool",
    
    # Macro Tools
    "fetch_macro_data_tool",
    "get_macro_snapshot_tool",
    "assess_regime_tool",
    "generate_taa_signal_tool",
    
    # Rebalance Tools
    "analyze_rebalance",
    "calculate_drift",
    "should_rebalance",
    "generate_trades",
    "calculate_rebalance_costs",
    "calculate_break_even_drift",
    "analyze_rebalance_tool",
    "calculate_drift_tool",
    "generate_trade_list_tool",
    "quick_drift_check",
    "RebalanceConfig",
    "Position",
    "Portfolio",
    "Trade",
    "RebalanceResult",
    
    # Analytics Tools
    "calculate_portfolio_metrics",
    "calculate_risk_metrics",
]