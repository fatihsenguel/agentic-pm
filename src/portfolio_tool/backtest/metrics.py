"""
Performance Metrics for Backtesting.

Standalone functions for calculating performance metrics.
All functions are DETERMINISTIC - same inputs = same outputs.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

import pandas as pd
import numpy as np


TRADING_DAYS_PER_YEAR = 252


@dataclass
class PerformanceMetrics:
    """Container for all performance metrics."""
    
    # Return metrics
    total_return: float
    cagr: float
    
    # Risk metrics
    volatility: float
    max_drawdown: float
    var_95: float
    cvar_95: float
    
    # Risk-adjusted metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Distribution
    skewness: float
    kurtosis: float
    
    # Other
    win_rate: float
    best_day: float
    worst_day: float
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "total_return": f"{self.total_return:.2%}",
            "cagr": f"{self.cagr:.2%}",
            "volatility": f"{self.volatility:.2%}",
            "sharpe_ratio": f"{self.sharpe_ratio:.2f}",
            "sortino_ratio": f"{self.sortino_ratio:.2f}",
            "max_drawdown": f"{self.max_drawdown:.2%}",
            "calmar_ratio": f"{self.calmar_ratio:.2f}",
            "var_95": f"{self.var_95:.2%}",
            "cvar_95": f"{self.cvar_95:.2%}",
            "win_rate": f"{self.win_rate:.1%}",
            "best_day": f"{self.best_day:.2%}",
            "worst_day": f"{self.worst_day:.2%}",
        }


def calculate_returns(prices: pd.Series, method: str = "simple") -> pd.Series:
    """Calculate returns from price series."""
    if method == "simple":
        return prices.pct_change().dropna()
    elif method == "log":
        return np.log(prices / prices.shift(1)).dropna()
    else:
        raise ValueError(f"Unknown method: {method}")


def calculate_total_return(values: pd.Series) -> float:
    """Calculate total return over the period."""
    if len(values) < 2:
        return 0.0
    return (values.iloc[-1] / values.iloc[0]) - 1


def calculate_cagr(values: pd.Series, trading_days: Optional[int] = None) -> float:
    """
    Calculate Compound Annual Growth Rate.
    
    Args:
        values: Series of portfolio values
        trading_days: Number of trading days (default: len(values))
        
    Returns:
        CAGR as decimal (e.g., 0.08 for 8%)
    """
    if len(values) < 2:
        return 0.0
    
    if trading_days is None:
        trading_days = len(values)
    
    years = trading_days / TRADING_DAYS_PER_YEAR
    
    if years <= 0:
        return 0.0
    
    total_return = values.iloc[-1] / values.iloc[0]
    
    if total_return <= 0:
        return -1.0  # Complete loss
    
    return total_return ** (1 / years) - 1


def calculate_volatility(returns: pd.Series, annualize: bool = True) -> float:
    """
    Calculate volatility (standard deviation of returns).
    
    Args:
        returns: Series of returns
        annualize: If True, annualize the volatility
        
    Returns:
        Volatility as decimal
    """
    if len(returns) < 2:
        return 0.0
    
    vol = returns.std()
    
    if annualize:
        vol *= np.sqrt(TRADING_DAYS_PER_YEAR)
    
    return float(vol)


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    annualize: bool = True
) -> float:
    """
    Calculate Sharpe Ratio.
    
    Sharpe = (Mean Return - Risk Free Rate) / Volatility
    
    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate
        annualize: If True, annualize the ratio
        
    Returns:
        Sharpe ratio
    """
    if len(returns) < 2:
        return 0.0
    
    vol = returns.std()
    
    if vol == 0:
        return 0.0
    
    if annualize:
        excess_return = returns.mean() * TRADING_DAYS_PER_YEAR - risk_free_rate
        vol *= np.sqrt(TRADING_DAYS_PER_YEAR)
    else:
        excess_return = returns.mean() - risk_free_rate / TRADING_DAYS_PER_YEAR
    
    return float(excess_return / vol)


def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    target_return: float = 0.0
) -> float:
    """
    Calculate Sortino Ratio.
    
    Like Sharpe but uses downside deviation instead of total volatility.
    
    Sortino = (Mean Return - Target) / Downside Deviation
    
    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate
        target_return: Target return (default: 0)
        
    Returns:
        Sortino ratio
    """
    if len(returns) < 2:
        return 0.0
    
    # Downside returns
    downside = returns[returns < target_return]
    
    if len(downside) < 2:
        return float('inf') if returns.mean() > target_return else 0.0
    
    downside_std = downside.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    
    if downside_std == 0:
        return float('inf') if returns.mean() > target_return else 0.0
    
    annual_return = returns.mean() * TRADING_DAYS_PER_YEAR
    
    return float((annual_return - risk_free_rate) / downside_std)


def calculate_max_drawdown(values: pd.Series) -> float:
    """
    Calculate maximum drawdown.
    
    Max drawdown is the largest peak-to-trough decline.
    
    Args:
        values: Series of portfolio values
        
    Returns:
        Max drawdown as positive decimal (e.g., 0.20 for 20% drawdown)
    """
    if len(values) < 2:
        return 0.0
    
    # Running maximum
    running_max = values.cummax()
    
    # Drawdown at each point
    drawdown = (values - running_max) / running_max
    
    return float(abs(drawdown.min()))


def calculate_drawdown_series(values: pd.Series) -> pd.Series:
    """
    Calculate drawdown series.
    
    Returns series of drawdowns at each point (negative values).
    """
    running_max = values.cummax()
    return (values - running_max) / running_max


def calculate_calmar_ratio(values: pd.Series) -> float:
    """
    Calculate Calmar Ratio.
    
    Calmar = CAGR / Max Drawdown
    
    Args:
        values: Series of portfolio values
        
    Returns:
        Calmar ratio
    """
    cagr = calculate_cagr(values)
    max_dd = calculate_max_drawdown(values)
    
    if max_dd == 0:
        return float('inf') if cagr > 0 else 0.0
    
    return float(cagr / max_dd)


def calculate_var(
    returns: pd.Series,
    confidence_level: float = 0.95,
    method: str = "historical"
) -> float:
    """
    Calculate Value at Risk.
    
    Args:
        returns: Series of returns
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        method: "historical" or "parametric"
        
    Returns:
        VaR as positive decimal (potential loss)
    """
    if len(returns) < 2:
        return 0.0
    
    alpha = 1 - confidence_level
    
    if method == "historical":
        var = np.percentile(returns, alpha * 100)
    elif method == "parametric":
        from scipy import stats
        z = stats.norm.ppf(alpha)
        var = returns.mean() + z * returns.std()
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return float(abs(var))


def calculate_cvar(
    returns: pd.Series,
    confidence_level: float = 0.95
) -> float:
    """
    Calculate Conditional VaR (Expected Shortfall).
    
    CVaR is the expected loss given that loss exceeds VaR.
    
    Args:
        returns: Series of returns
        confidence_level: Confidence level
        
    Returns:
        CVaR as positive decimal
    """
    if len(returns) < 2:
        return 0.0
    
    var = calculate_var(returns, confidence_level)
    
    # Tail losses (below VaR threshold)
    tail_losses = returns[returns <= -var]
    
    if len(tail_losses) == 0:
        return var
    
    return float(abs(tail_losses.mean()))


def calculate_win_rate(returns: pd.Series) -> float:
    """Calculate percentage of positive return days."""
    if len(returns) == 0:
        return 0.0
    return float((returns > 0).sum() / len(returns))


def calculate_skewness(returns: pd.Series) -> float:
    """Calculate skewness of returns distribution."""
    if len(returns) < 3:
        return 0.0
    return float(returns.skew())


def calculate_kurtosis(returns: pd.Series) -> float:
    """Calculate excess kurtosis of returns distribution."""
    if len(returns) < 4:
        return 0.0
    return float(returns.kurtosis())


def calculate_beta(
    returns: pd.Series,
    benchmark_returns: pd.Series
) -> float:
    """
    Calculate beta relative to benchmark.
    
    Beta = Cov(r, r_b) / Var(r_b)
    """
    if len(returns) != len(benchmark_returns):
        # Align the series
        combined = pd.concat([returns, benchmark_returns], axis=1).dropna()
        if len(combined) < 2:
            return 1.0
        returns = combined.iloc[:, 0]
        benchmark_returns = combined.iloc[:, 1]
    
    if len(returns) < 2:
        return 1.0
    
    covariance = np.cov(returns, benchmark_returns)[0, 1]
    benchmark_variance = benchmark_returns.var()
    
    if benchmark_variance == 0:
        return 1.0
    
    return float(covariance / benchmark_variance)


def calculate_alpha(
    returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.0
) -> float:
    """
    Calculate Jensen's Alpha.
    
    Alpha = R_p - [R_f + Beta * (R_b - R_f)]
    """
    beta = calculate_beta(returns, benchmark_returns)
    
    port_return = returns.mean() * TRADING_DAYS_PER_YEAR
    bench_return = benchmark_returns.mean() * TRADING_DAYS_PER_YEAR
    
    expected_return = risk_free_rate + beta * (bench_return - risk_free_rate)
    
    return float(port_return - expected_return)


def calculate_information_ratio(
    returns: pd.Series,
    benchmark_returns: pd.Series
) -> float:
    """
    Calculate Information Ratio.
    
    IR = (R_p - R_b) / Tracking Error
    """
    if len(returns) != len(benchmark_returns):
        combined = pd.concat([returns, benchmark_returns], axis=1).dropna()
        if len(combined) < 2:
            return 0.0
        returns = combined.iloc[:, 0]
        benchmark_returns = combined.iloc[:, 1]
    
    excess = returns - benchmark_returns
    tracking_error = excess.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    
    if tracking_error == 0:
        return 0.0
    
    active_return = excess.mean() * TRADING_DAYS_PER_YEAR
    
    return float(active_return / tracking_error)


def calculate_all_metrics(
    values: pd.Series,
    risk_free_rate: float = 0.0
) -> PerformanceMetrics:
    """
    Calculate all performance metrics.
    
    Args:
        values: Series of portfolio values
        risk_free_rate: Annual risk-free rate
        
    Returns:
        PerformanceMetrics with all metrics
    """
    returns = values.pct_change().dropna()
    
    return PerformanceMetrics(
        total_return=calculate_total_return(values),
        cagr=calculate_cagr(values),
        volatility=calculate_volatility(returns),
        max_drawdown=calculate_max_drawdown(values),
        var_95=calculate_var(returns, 0.95),
        cvar_95=calculate_cvar(returns, 0.95),
        sharpe_ratio=calculate_sharpe_ratio(returns, risk_free_rate),
        sortino_ratio=calculate_sortino_ratio(returns, risk_free_rate),
        calmar_ratio=calculate_calmar_ratio(values),
        skewness=calculate_skewness(returns),
        kurtosis=calculate_kurtosis(returns),
        win_rate=calculate_win_rate(returns),
        best_day=float(returns.max()) if len(returns) > 0 else 0.0,
        worst_day=float(returns.min()) if len(returns) > 0 else 0.0,
    )
