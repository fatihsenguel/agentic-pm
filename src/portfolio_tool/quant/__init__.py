"""
Quant Module for Portfolio Analytics.

This module provides quantitative finance calculations for:
- Return calculations (simple, log, excess)
- Covariance estimation (sample)
- Volatility, per series and per portfolio

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
)

from .risk_metrics import (
    calculate_volatility,
    portfolio_volatility,
    portfolio_volatility_by_ticker,
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
    # Volatility
    "calculate_volatility",
    "portfolio_volatility",
    "portfolio_volatility_by_ticker",
]
