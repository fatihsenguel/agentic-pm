"""
Volatility for portfolio analytics.

Three functions: the standard deviation of a return series, and the
portfolio volatility sqrt(w' Σ w) that expected_values.md D7 names this
module the canonical home of, over arrays and over the dicts shared_data
carries. Pure and deterministic; nothing here reads a database or a model.
"""

from typing import Dict, Union

import numpy as np
import pandas as pd


TRADING_DAYS_PER_YEAR = 252


def calculate_volatility(
    returns: Union[pd.Series, pd.DataFrame],
    annualize: bool = True,
    periods_per_year: int = TRADING_DAYS_PER_YEAR
) -> Union[float, pd.Series]:
    """
    Calculate volatility (standard deviation) of returns.
    
    Args:
        returns: Return series or DataFrame
        annualize: Whether to annualize (default True)
        periods_per_year: Periods per year for annualization
        
    Returns:
        Volatility (annualized if specified)
    """
    vol = returns.std()
    
    if annualize:
        vol = vol * np.sqrt(periods_per_year)
    
    return vol


def portfolio_volatility(
    weights: np.ndarray,
    cov_matrix: np.ndarray,
) -> float:
    """
    Portfolio volatility: sqrt(w' Σ w).

    The canonical implementation (expected_values.md D7). Anything that needs
    this number calls here; nothing restates the formula.

    Pure arithmetic. The result carries whatever scale the covariance matrix
    carries: an annualised Σ gives annualised volatility, a daily Σ gives
    daily. The caller states which it passed - this function cannot tell and
    does not pretend to.

    Raises rather than normalising when the weights do not sum to one. A
    weight vector that sums to 0.9 is a portfolio with 10% of something
    missing, and rescaling it silently would report the volatility of a
    portfolio nobody holds.

    Args:
        weights: 1-D array of portfolio weights, same order as cov_matrix.
        cov_matrix: 2-D covariance matrix.

    Returns:
        Volatility as a float, same scale as cov_matrix.
    """
    w = np.asarray(weights, dtype=float)
    cov = np.asarray(cov_matrix, dtype=float)

    if w.ndim != 1:
        raise ValueError(f"weights must be 1-D, got shape {w.shape}")
    if cov.shape != (w.size, w.size):
        raise ValueError(
            f"cov_matrix shape {cov.shape} does not match {w.size} weights"
        )
    # 1e-6, not tighter: optimiser output satisfies its sum-to-one constraint
    # only to solver tolerance, and this is called on that output. Anything
    # further off than that is a missing holding, not rounding.
    if abs(w.sum() - 1.0) > 1e-6:
        raise ValueError(
            f"weights sum to {w.sum():.10f}, not 1. Not rescaling: a partial "
            "weight vector is a different portfolio."
        )

    variance = float(w @ cov @ w)
    if variance < 0:
        raise ValueError(
            f"w'Σw is {variance}; the covariance matrix is not positive "
            "semi-definite."
        )
    return float(np.sqrt(variance))


def portfolio_volatility_by_ticker(
    weights: Dict[str, float],
    cov_matrix: Dict[str, Dict[str, float]],
) -> float:
    """
    `portfolio_volatility` over dicts keyed by ticker, as shared_data carries
    them. Aligns the two by ticker and raises on any mismatch: a weight with no
    covariance row, or a covariance row with no weight, is a holding the
    matrix does not describe, and dropping it would shrink the portfolio.
    """
    tickers = sorted(weights)
    missing = [t for t in tickers if t not in cov_matrix]
    if missing:
        raise ValueError(f"No covariance row for: {', '.join(missing)}")
    extra = sorted(set(cov_matrix) - set(tickers))
    if extra:
        raise ValueError(
            f"Covariance rows with no weight: {', '.join(extra)}. Pass a "
            "weight for every ticker in the matrix, zero if unheld."
        )
    for t in tickers:
        row_missing = [u for u in tickers if u not in cov_matrix[t]]
        if row_missing:
            raise ValueError(f"Covariance row {t} lacks: {', '.join(row_missing)}")

    w = np.array([weights[t] for t in tickers], dtype=float)
    cov = np.array([[cov_matrix[t][u] for u in tickers] for t in tickers], dtype=float)
    return portfolio_volatility(w, cov)
