"""
Quant Module for Portfolio Analytics.

This module provides quantitative finance calculations for:
- Return calculations (simple, log, excess)
- Covariance estimation (sample, shrinkage, exponential)
- Risk metrics (VaR, CVaR, volatility, drawdown)

Design Principles:
- All functions are pure and deterministic
- Functions return processed summaries, not raw data (Hot Potato Principle)
- Results include metadata for audit trails
- Edge cases (NaN, missing data) are handled gracefully
"""

from .returns import (
    calculate_returns,
    calculate_log_returns,
    calculate_excess_returns,
    annualize_returns,
    calculate_cumulative_returns,
)

from .covariance import (
    CovarianceEstimator,
    calculate_sample_covariance,
    calculate_shrinkage_covariance,
    calculate_exponential_covariance,
)

from .risk_metrics import (
    calculate_volatility,
    calculate_var,
    calculate_cvar,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    RiskMetricsCalculator,
)

__all__ = [
    # Returns
    "calculate_returns",
    "calculate_log_returns",
    "calculate_excess_returns",
    "annualize_returns",
    "calculate_cumulative_returns",
    # Covariance
    "CovarianceEstimator",
    "calculate_sample_covariance",
    "calculate_shrinkage_covariance",
    "calculate_exponential_covariance",
    # Risk Metrics
    "calculate_volatility",
    "calculate_var",
    "calculate_cvar",
    "calculate_max_drawdown",
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "RiskMetricsCalculator",
]
