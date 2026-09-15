"""
Tools Module - Agent Interface Layer.

This module provides tools that agents can use to interact with the system.
Tools are the interface between AI agents and the business logic.

Available Tools:
    - rebalance_tools: Portfolio rebalancing (DETERMINISTIC - no LLM)
        - analyze_rebalance
        - calculate_drift
        - generate_trades
        - calculate_rebalance_costs

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

__all__ = [n for n in dir() if not n.startswith("_")]
