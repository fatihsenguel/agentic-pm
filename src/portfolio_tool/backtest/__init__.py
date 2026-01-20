"""
Backtest Module for Quant Portfolio Manager.

This module provides deterministic backtesting capabilities:
- Strategy definitions with TAA rules
- Backtest engine (NO LLM - 100% deterministic)
- Performance metrics and attribution
- Report generation

⚠️ CRITICAL DESIGN PRINCIPLE:
The BacktestEngine is 100% DETERMINISTIC.
Same inputs = Same outputs. Always.
NO LLM is used during the simulation loop.

The LLM's role:
1. BEFORE backtest: Translate user intent to Strategy rules
2. AFTER backtest: Interpret and explain results

The LLM NEVER:
- Makes trade decisions during simulation
- Evaluates market conditions during the loop
- Provides any input during the backtest run
"""

from .strategies import (
    Strategy,
    TAARule,
    RebalanceRule,
    RebalanceFrequency,
    create_buy_and_hold_strategy,
    create_sixty_forty_strategy,
    create_risk_parity_strategy,
)

from .engine import (
    BacktestEngine,
    Portfolio,
    BacktestResult,
    Trade,
)

from .metrics import (
    calculate_cagr,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_max_drawdown,
    calculate_calmar_ratio,
    calculate_var,
    calculate_drawdown_series,
    PerformanceMetrics,
)

from .reports import (
    BacktestReport,
    generate_performance_summary,
    generate_monthly_returns_table,
    compare_strategies,
)


__all__ = [
    # Strategies
    "Strategy",
    "TAARule",
    "RebalanceRule",
    "RebalanceFrequency",
    "create_buy_and_hold_strategy",
    "create_sixty_forty_strategy",
    "create_risk_parity_strategy",
    # Engine
    "BacktestEngine",
    "Portfolio",
    "BacktestResult",
    "Trade",
    # Metrics
    "calculate_cagr",
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_max_drawdown",
    "calculate_calmar_ratio",
    "calculate_var",
    "calculate_drawdown_series",
    "PerformanceMetrics",
    # Reports
    "BacktestReport",
    "generate_performance_summary",
    "generate_monthly_returns_table",
    "compare_strategies",
]
