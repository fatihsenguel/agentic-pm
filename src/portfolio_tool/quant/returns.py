"""
Return Calculations for Portfolio Analytics.

This module provides functions for calculating various types of returns:
- Simple returns (percentage change)
- Log returns (continuously compounded)
- Excess returns (over risk-free rate)
- Cumulative returns
- Annualized returns

All functions follow these principles:
- Pure functions with no side effects
- Proper handling of NaN and missing values
- Comprehensive type hints
- Return metadata for audit trails
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import numpy as np


# Constants
TRADING_DAYS_PER_YEAR = 252
MONTHS_PER_YEAR = 12


@dataclass
class ReturnsResult:
    """Result from return calculations."""
    success: bool
    returns: Optional[pd.Series] = None
    returns_df: Optional[pd.DataFrame] = None  # For multi-asset
    
    # Statistics
    mean_return: Optional[float] = None
    total_return: Optional[float] = None
    annualized_return: Optional[float] = None
    
    # Metadata
    method: str = "simple"  # "simple", "log", "excess"
    period: str = ""  # "daily", "weekly", "monthly"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    num_observations: int = 0
    
    # Warnings
    warnings: List[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        result = {
            "success": self.success,
            "method": self.method,
            "period": self.period,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "num_observations": self.num_observations,
        }
        
        if self.mean_return is not None:
            result["mean_return"] = f"{self.mean_return:.4%}"
        if self.total_return is not None:
            result["total_return"] = f"{self.total_return:.4%}"
        if self.annualized_return is not None:
            result["annualized_return"] = f"{self.annualized_return:.4%}"
        
        if self.warnings:
            result["warnings"] = self.warnings
        if self.error_message:
            result["error_message"] = self.error_message
        
        return result


def calculate_returns(
    prices: Union[pd.Series, pd.DataFrame],
    method: str = "simple"
) -> Union[pd.Series, pd.DataFrame]:
    """
    Calculate returns from price series.
    
    Args:
        prices: Price series or DataFrame with prices as columns
        method: "simple" for percentage change, "log" for log returns
        
    Returns:
        Returns series or DataFrame
    """
    if method == "simple":
        return prices.pct_change().dropna()
    elif method == "log":
        return np.log(prices / prices.shift(1)).dropna()
    else:
        raise ValueError(f"Unknown method: {method}. Use 'simple' or 'log'.")


def calculate_log_returns(
    prices: Union[pd.Series, pd.DataFrame]
) -> Union[pd.Series, pd.DataFrame]:
    """
    Calculate log (continuously compounded) returns.
    
    Log returns have the property that multi-period returns
    are simply the sum of single-period log returns.
    
    Args:
        prices: Price series or DataFrame
        
    Returns:
        Log returns
    """
    return np.log(prices / prices.shift(1)).dropna()


def calculate_excess_returns(
    returns: Union[pd.Series, pd.DataFrame],
    risk_free_rate: float,
    periods_per_year: int = TRADING_DAYS_PER_YEAR
) -> Union[pd.Series, pd.DataFrame]:
    """
    Calculate excess returns over the risk-free rate.
    
    Args:
        returns: Return series or DataFrame (already calculated)
        risk_free_rate: Annual risk-free rate (e.g., 0.05 for 5%)
        periods_per_year: Number of periods per year (252 for daily)
        
    Returns:
        Excess returns
    """
    # Convert annual rate to per-period rate
    rf_per_period = risk_free_rate / periods_per_year
    
    return returns - rf_per_period


def annualize_returns(
    returns: Union[pd.Series, pd.DataFrame],
    periods_per_year: int = TRADING_DAYS_PER_YEAR
) -> Union[float, pd.Series]:
    """
    Annualize returns.
    
    For arithmetic returns: multiply by periods_per_year
    This function uses the geometric mean for more accurate compounding.
    
    Args:
        returns: Periodic returns
        periods_per_year: Number of periods per year
        
    Returns:
        Annualized return(s)
    """
    # Geometric mean approach
    compound_return = (1 + returns).prod()
    n_periods = len(returns)
    
    if n_periods == 0:
        return 0.0 if isinstance(returns, pd.Series) else pd.Series()
    
    # Annualize
    annualized = compound_return ** (periods_per_year / n_periods) - 1
    
    return annualized


def calculate_cumulative_returns(
    returns: Union[pd.Series, pd.DataFrame]
) -> Union[pd.Series, pd.DataFrame]:
    """
    Calculate cumulative returns (wealth index).
    
    Starting from 1.0, shows growth of $1 invested.
    
    Args:
        returns: Return series or DataFrame
        
    Returns:
        Cumulative returns (starting at 1.0)
    """
    return (1 + returns).cumprod()


def calculate_total_return(
    returns: Union[pd.Series, pd.DataFrame]
) -> Union[float, pd.Series]:
    """
    Calculate total return over the entire period.
    
    Args:
        returns: Return series or DataFrame
        
    Returns:
        Total return
    """
    return (1 + returns).prod() - 1


def calculate_returns_statistics(
    prices: pd.DataFrame,
    risk_free_rate: float = 0.0,
    periods_per_year: int = TRADING_DAYS_PER_YEAR
) -> Dict[str, Dict[str, float]]:
    """
    Calculate comprehensive return statistics for multiple assets.
    
    Args:
        prices: DataFrame with asset prices
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of periods per year
        
    Returns:
        Dictionary with statistics per asset
    """
    returns = calculate_returns(prices, method="simple")
    
    stats = {}
    for column in returns.columns:
        asset_returns = returns[column].dropna()
        
        if len(asset_returns) < 2:
            stats[column] = {"error": "Insufficient data"}
            continue
        
        total_ret = calculate_total_return(asset_returns)
        annual_ret = annualize_returns(asset_returns, periods_per_year)
        
        stats[column] = {
            "mean_daily_return": float(asset_returns.mean()),
            "total_return": float(total_ret),
            "annualized_return": float(annual_ret),
            "num_observations": len(asset_returns),
            "start_date": str(asset_returns.index[0].date()) if hasattr(asset_returns.index[0], 'date') else str(asset_returns.index[0]),
            "end_date": str(asset_returns.index[-1].date()) if hasattr(asset_returns.index[-1], 'date') else str(asset_returns.index[-1]),
        }
    
    return stats


def get_returns_for_optimization(
    prices: pd.DataFrame,
    method: str = "log",
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
    min_observations: int = 60
) -> Tuple[pd.Series, pd.DataFrame, List[str]]:
    """
    Prepare returns data for portfolio optimization.
    
    This function:
    1. Calculates returns using specified method
    2. Handles missing data appropriately
    3. Calculates expected (mean) returns for each asset
    4. Validates data quality
    
    Args:
        prices: DataFrame with asset prices
        method: Return calculation method ("simple" or "log")
        periods_per_year: For annualization
        min_observations: Minimum required observations
        
    Returns:
        Tuple of (expected_returns, returns_df, warnings)
    """
    warnings = []
    
    # Calculate returns
    returns = calculate_returns(prices, method=method)
    
    # Check for sufficient data
    for col in returns.columns:
        valid_count = returns[col].notna().sum()
        if valid_count < min_observations:
            warnings.append(
                f"{col}: Only {valid_count} observations (min: {min_observations})"
            )
    
    # Drop rows with any NaN (common period only)
    returns_clean = returns.dropna()
    
    if len(returns_clean) < min_observations:
        warnings.append(
            f"Only {len(returns_clean)} common observations across all assets"
        )
    
    # Calculate annualized expected returns
    mean_returns = returns_clean.mean()
    expected_returns = mean_returns * periods_per_year
    
    return expected_returns, returns_clean, warnings


def resample_returns(
    returns: pd.DataFrame,
    freq: str = "M"
) -> pd.DataFrame:
    """
    Resample returns to a different frequency.
    
    Args:
        returns: Daily returns DataFrame
        freq: Target frequency ("W" for weekly, "M" for monthly, "Q" for quarterly)
        
    Returns:
        Resampled returns
    """
    # For returns, we need to compound
    return (1 + returns).resample(freq).prod() - 1


def rolling_returns(
    prices: pd.DataFrame,
    window: int,
    periods_per_year: int = TRADING_DAYS_PER_YEAR
) -> pd.DataFrame:
    """
    Calculate rolling annualized returns.
    
    Args:
        prices: Price DataFrame
        window: Rolling window size in periods
        periods_per_year: For annualization
        
    Returns:
        Rolling annualized returns
    """
    returns = calculate_returns(prices, method="simple")
    
    # Rolling total return
    rolling_total = (1 + returns).rolling(window=window).apply(
        lambda x: x.prod(), raw=True
    ) - 1
    
    # Annualize
    annualization_factor = periods_per_year / window
    rolling_annualized = (1 + rolling_total) ** annualization_factor - 1
    
    return rolling_annualized
