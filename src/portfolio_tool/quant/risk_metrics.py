"""
Risk Metrics Calculator for Portfolio Analytics.

This module provides comprehensive risk metrics including:
- Volatility (standard deviation)
- Value at Risk (VaR)
- Conditional VaR / Expected Shortfall
- Maximum Drawdown
- Sharpe Ratio
- Sortino Ratio
- Calmar Ratio

Design Principles:
- All functions are pure and deterministic
- Support both single assets and portfolios
- Include confidence levels and time horizons
- Return audit-friendly results with methodology
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats


# Constants
TRADING_DAYS_PER_YEAR = 252
WEEKS_PER_YEAR = 52
MONTHS_PER_YEAR = 12


@dataclass
class RiskMetricsResult:
    """Comprehensive risk metrics result."""
    success: bool
    
    # Core metrics
    volatility: Optional[float] = None  # Annualized
    var_95: Optional[float] = None      # 95% VaR (1-day)
    var_99: Optional[float] = None      # 99% VaR (1-day)
    cvar_95: Optional[float] = None     # 95% CVaR (Expected Shortfall)
    max_drawdown: Optional[float] = None
    
    # Risk-adjusted returns
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    
    # Distribution characteristics
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None
    
    # Downside metrics
    downside_deviation: Optional[float] = None
    
    # Metadata
    annualized_return: Optional[float] = None
    risk_free_rate: float = 0.0
    period: str = ""
    num_observations: int = 0
    
    # Warnings
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        result = {
            "success": self.success,
            "period": self.period,
            "num_observations": self.num_observations,
        }
        
        if self.volatility is not None:
            result["volatility"] = f"{self.volatility:.2%}"
        if self.var_95 is not None:
            result["var_95"] = f"{self.var_95:.2%}"
        if self.var_99 is not None:
            result["var_99"] = f"{self.var_99:.2%}"
        if self.cvar_95 is not None:
            result["cvar_95"] = f"{self.cvar_95:.2%}"
        if self.max_drawdown is not None:
            result["max_drawdown"] = f"{self.max_drawdown:.2%}"
        if self.sharpe_ratio is not None:
            result["sharpe_ratio"] = f"{self.sharpe_ratio:.2f}"
        if self.sortino_ratio is not None:
            result["sortino_ratio"] = f"{self.sortino_ratio:.2f}"
        if self.calmar_ratio is not None:
            result["calmar_ratio"] = f"{self.calmar_ratio:.2f}"
        if self.skewness is not None:
            result["skewness"] = f"{self.skewness:.2f}"
        if self.kurtosis is not None:
            result["kurtosis"] = f"{self.kurtosis:.2f}"
        if self.annualized_return is not None:
            result["annualized_return"] = f"{self.annualized_return:.2%}"
        
        if self.warnings:
            result["warnings"] = self.warnings
        if self.error_message:
            result["error_message"] = self.error_message
        
        return result


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


def calculate_var(
    returns: Union[pd.Series, np.ndarray],
    confidence_level: float = 0.95,
    method: str = "historical"
) -> float:
    """
    Calculate Value at Risk (VaR).
    
    VaR represents the maximum loss expected at a given confidence level
    over a given time horizon.
    
    Args:
        returns: Return series (already for the desired time horizon)
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        method: "historical" for historical simulation, "parametric" for normal assumption
        
    Returns:
        VaR as a positive percentage (e.g., 0.05 means 5% loss)
    """
    if isinstance(returns, pd.Series):
        returns = returns.dropna().values
    
    if len(returns) < 10:
        return np.nan
    
    if method == "historical":
        # Historical simulation - use percentile
        var = -np.percentile(returns, (1 - confidence_level) * 100)
    
    elif method == "parametric":
        # Assume normal distribution
        mu = np.mean(returns)
        sigma = np.std(returns)
        z = stats.norm.ppf(1 - confidence_level)
        var = -(mu + z * sigma)
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return float(var)


def calculate_cvar(
    returns: Union[pd.Series, np.ndarray],
    confidence_level: float = 0.95,
    method: str = "historical"
) -> float:
    """
    Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.
    
    CVaR is the expected loss given that the loss exceeds VaR.
    It captures tail risk better than VaR.
    
    Args:
        returns: Return series
        confidence_level: Confidence level (e.g., 0.95)
        method: "historical" or "parametric"
        
    Returns:
        CVaR as a positive percentage
    """
    if isinstance(returns, pd.Series):
        returns = returns.dropna().values
    
    if len(returns) < 10:
        return np.nan
    
    if method == "historical":
        # Expected value of losses beyond VaR
        cutoff = np.percentile(returns, (1 - confidence_level) * 100)
        cvar = -np.mean(returns[returns <= cutoff])
    
    elif method == "parametric":
        # Parametric CVaR assuming normal distribution
        mu = np.mean(returns)
        sigma = np.std(returns)
        alpha = 1 - confidence_level
        z = stats.norm.ppf(alpha)
        cvar = -(mu - sigma * stats.norm.pdf(z) / alpha)
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return float(cvar)


def calculate_max_drawdown(
    returns: Union[pd.Series, pd.DataFrame]
) -> Union[float, pd.Series]:
    """
    Calculate maximum drawdown from returns.
    
    Maximum drawdown is the largest peak-to-trough decline.
    
    Args:
        returns: Return series or DataFrame
        
    Returns:
        Maximum drawdown as a positive percentage
    """
    # Calculate cumulative wealth
    cumulative = (1 + returns).cumprod()
    
    # Running maximum
    running_max = cumulative.cummax()
    
    # Drawdown series
    drawdown = (cumulative - running_max) / running_max
    
    # Maximum drawdown (most negative value, returned as positive)
    return -drawdown.min()


def calculate_drawdown_series(
    returns: pd.Series
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate the full drawdown series and underwater curve.
    
    Args:
        returns: Return series
        
    Returns:
        Tuple of (drawdown_series, cumulative_returns)
    """
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    
    return drawdown, cumulative


def calculate_sharpe_ratio(
    returns: Union[pd.Series, np.ndarray],
    risk_free_rate: float = 0.0,
    periods_per_year: int = TRADING_DAYS_PER_YEAR
) -> float:
    """
    Calculate the Sharpe Ratio.
    
    Sharpe Ratio = (Return - Risk-Free Rate) / Volatility
    
    Args:
        returns: Return series
        risk_free_rate: Annual risk-free rate
        periods_per_year: For annualization
        
    Returns:
        Sharpe Ratio
    """
    if isinstance(returns, pd.Series):
        returns = returns.dropna().values
    
    if len(returns) < 2:
        return np.nan
    
    # Annualized return
    mean_return = np.mean(returns) * periods_per_year
    
    # Annualized volatility
    vol = np.std(returns) * np.sqrt(periods_per_year)
    
    if vol == 0:
        return np.nan
    
    return float((mean_return - risk_free_rate) / vol)


def calculate_sortino_ratio(
    returns: Union[pd.Series, np.ndarray],
    risk_free_rate: float = 0.0,
    target_return: float = 0.0,
    periods_per_year: int = TRADING_DAYS_PER_YEAR
) -> float:
    """
    Calculate the Sortino Ratio.
    
    Like Sharpe, but only considers downside volatility.
    Better for asymmetric return distributions.
    
    Sortino Ratio = (Return - Target) / Downside Deviation
    
    Args:
        returns: Return series
        risk_free_rate: Annual risk-free rate
        target_return: Target return (typically 0 or risk-free rate per period)
        periods_per_year: For annualization
        
    Returns:
        Sortino Ratio
    """
    if isinstance(returns, pd.Series):
        returns = returns.dropna().values
    
    if len(returns) < 2:
        return np.nan
    
    # Annualized return
    mean_return = np.mean(returns) * periods_per_year
    
    # Downside deviation (only negative returns vs target)
    target_per_period = target_return / periods_per_year
    downside_returns = returns[returns < target_per_period] - target_per_period
    
    if len(downside_returns) == 0:
        return np.inf if mean_return > risk_free_rate else 0
    
    downside_std = np.sqrt(np.mean(downside_returns ** 2)) * np.sqrt(periods_per_year)
    
    if downside_std == 0:
        return np.nan
    
    return float((mean_return - risk_free_rate) / downside_std)


def calculate_calmar_ratio(
    returns: Union[pd.Series, np.ndarray],
    periods_per_year: int = TRADING_DAYS_PER_YEAR
) -> float:
    """
    Calculate the Calmar Ratio.
    
    Calmar Ratio = Annualized Return / Maximum Drawdown
    
    Args:
        returns: Return series
        periods_per_year: For annualization
        
    Returns:
        Calmar Ratio
    """
    if isinstance(returns, np.ndarray):
        returns = pd.Series(returns)
    
    if len(returns) < 2:
        return np.nan
    
    # Annualized return (geometric)
    total_return = (1 + returns).prod()
    n_periods = len(returns)
    annual_return = total_return ** (periods_per_year / n_periods) - 1
    
    # Maximum drawdown
    max_dd = calculate_max_drawdown(returns)
    
    if max_dd == 0:
        return np.inf if annual_return > 0 else 0
    
    return float(annual_return / max_dd)


def calculate_downside_deviation(
    returns: Union[pd.Series, np.ndarray],
    target: float = 0.0,
    periods_per_year: int = TRADING_DAYS_PER_YEAR
) -> float:
    """
    Calculate downside deviation (semi-deviation).
    
    Only considers returns below the target.
    
    Args:
        returns: Return series
        target: Target return per period
        periods_per_year: For annualization
        
    Returns:
        Annualized downside deviation
    """
    if isinstance(returns, pd.Series):
        returns = returns.dropna().values
    
    downside = returns[returns < target]
    
    if len(downside) == 0:
        return 0.0
    
    downside_var = np.mean((downside - target) ** 2)
    downside_std = np.sqrt(downside_var) * np.sqrt(periods_per_year)
    
    return float(downside_std)


def calculate_skewness(returns: Union[pd.Series, np.ndarray]) -> float:
    """
    Calculate skewness of returns.
    
    - Negative skew: More extreme negative returns (left tail)
    - Positive skew: More extreme positive returns (right tail)
    - Zero: Symmetric distribution
    
    Args:
        returns: Return series
        
    Returns:
        Skewness
    """
    if isinstance(returns, pd.Series):
        returns = returns.dropna().values
    
    return float(stats.skew(returns))


def calculate_kurtosis(returns: Union[pd.Series, np.ndarray]) -> float:
    """
    Calculate excess kurtosis of returns.
    
    - Positive: Fat tails (more extreme events than normal)
    - Negative: Thin tails
    - Zero: Normal distribution
    
    Args:
        returns: Return series
        
    Returns:
        Excess kurtosis
    """
    if isinstance(returns, pd.Series):
        returns = returns.dropna().values
    
    return float(stats.kurtosis(returns))


class RiskMetricsCalculator:
    """
    Unified calculator for comprehensive risk metrics.
    
    Usage:
        calc = RiskMetricsCalculator(risk_free_rate=0.05)
        result = calc.calculate_all(returns)
    """
    
    def __init__(
        self,
        risk_free_rate: float = 0.0,
        periods_per_year: int = TRADING_DAYS_PER_YEAR,
        var_confidence: float = 0.95
    ):
        """
        Initialize risk calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate
            periods_per_year: Trading periods per year
            var_confidence: Confidence level for VaR/CVaR
        """
        self.risk_free_rate = risk_free_rate
        self.periods_per_year = periods_per_year
        self.var_confidence = var_confidence
    
    def calculate_all(
        self, 
        returns: Union[pd.Series, np.ndarray],
        include_distribution: bool = True
    ) -> RiskMetricsResult:
        """
        Calculate all risk metrics for a return series.
        
        Args:
            returns: Return series
            include_distribution: Include skewness/kurtosis
            
        Returns:
            RiskMetricsResult with all metrics
        """
        warnings = []
        
        if isinstance(returns, np.ndarray):
            returns = pd.Series(returns)
        
        returns = returns.dropna()
        n_obs = len(returns)
        
        if n_obs < 20:
            warnings.append(f"Limited data: {n_obs} observations (recommend 60+)")
        
        if n_obs < 2:
            return RiskMetricsResult(
                success=False,
                error_message="Insufficient data (need at least 2 observations)",
                num_observations=n_obs
            )
        
        # Calculate all metrics
        try:
            vol = calculate_volatility(returns, True, self.periods_per_year)
            var_95 = calculate_var(returns, 0.95, "historical")
            var_99 = calculate_var(returns, 0.99, "historical")
            cvar = calculate_cvar(returns, 0.95, "historical")
            max_dd = calculate_max_drawdown(returns)
            sharpe = calculate_sharpe_ratio(returns, self.risk_free_rate, self.periods_per_year)
            sortino = calculate_sortino_ratio(returns, self.risk_free_rate, 0, self.periods_per_year)
            calmar = calculate_calmar_ratio(returns, self.periods_per_year)
            downside = calculate_downside_deviation(returns, 0, self.periods_per_year)
            
            # Annualized return
            total_return = (1 + returns).prod()
            annual_return = total_return ** (self.periods_per_year / n_obs) - 1
            
            # Distribution metrics
            skew = None
            kurt = None
            if include_distribution:
                skew = calculate_skewness(returns)
                kurt = calculate_kurtosis(returns)
                
                if skew < -1:
                    warnings.append(f"Negative skewness ({skew:.2f}) - tail risk to the left")
                if kurt > 3:
                    warnings.append(f"High kurtosis ({kurt:.2f}) - fat tails present")
            
            # Build period string
            if hasattr(returns.index, '__getitem__') and len(returns.index) > 0:
                if hasattr(returns.index[0], 'strftime'):
                    start = returns.index[0].strftime('%Y-%m-%d')
                    end = returns.index[-1].strftime('%Y-%m-%d')
                    period = f"{start} to {end}"
                else:
                    period = f"{n_obs} observations"
            else:
                period = f"{n_obs} observations"
            
            return RiskMetricsResult(
                success=True,
                volatility=float(vol),
                var_95=float(var_95) if not np.isnan(var_95) else None,
                var_99=float(var_99) if not np.isnan(var_99) else None,
                cvar_95=float(cvar) if not np.isnan(cvar) else None,
                max_drawdown=float(max_dd),
                sharpe_ratio=float(sharpe) if not np.isnan(sharpe) else None,
                sortino_ratio=float(sortino) if not np.isnan(sortino) and not np.isinf(sortino) else None,
                calmar_ratio=float(calmar) if not np.isnan(calmar) and not np.isinf(calmar) else None,
                downside_deviation=float(downside),
                skewness=skew,
                kurtosis=kurt,
                annualized_return=float(annual_return),
                risk_free_rate=self.risk_free_rate,
                period=period,
                num_observations=n_obs,
                warnings=warnings
            )
            
        except Exception as e:
            return RiskMetricsResult(
                success=False,
                error_message=str(e),
                num_observations=n_obs,
                warnings=warnings
            )
    
    def calculate_portfolio_risk(
        self,
        weights: Dict[str, float],
        cov_matrix: pd.DataFrame
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate portfolio volatility and risk contributions.
        
        Args:
            weights: Portfolio weights by asset
            cov_matrix: Covariance matrix
            
        Returns:
            Tuple of (portfolio_volatility, risk_contributions)
        """
        # Ensure weights are in same order as covariance matrix
        tickers = list(cov_matrix.columns)
        w = np.array([weights.get(t, 0) for t in tickers])
        
        # Portfolio variance
        cov = cov_matrix.values
        port_var = w @ cov @ w
        port_vol = np.sqrt(port_var)
        
        # Marginal risk contribution
        marginal = cov @ w
        
        # Component risk contribution
        component = w * marginal / port_vol
        
        # Percentage contribution
        risk_contrib = {
            tickers[i]: float(component[i] / port_vol)
            for i in range(len(tickers))
        }
        
        return float(port_vol), risk_contrib
