"""
Base classes for Portfolio Optimization.

This module defines:
- OptimizerInterface: Abstract base for all optimizers
- OptimizationResult: Standardized result format
- OptimizationMethod: Enum of available methods
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


class OptimizationMethod(str, Enum):
    """Available optimization methods."""
    MEAN_VARIANCE = "mean_variance"
    MAX_SHARPE = "max_sharpe"
    MIN_VOLATILITY = "min_volatility"
    RISK_PARITY = "risk_parity"
    TARGET_VOLATILITY = "target_volatility"
    TARGET_RETURN = "target_return"


@dataclass
class OptimizationResult:
    """
    Result from portfolio optimization.
    
    Contains weights, metrics, and full audit trail.
    """
    # Status
    success: bool
    method: OptimizationMethod
    
    # Core outputs
    weights: Dict[str, float]  # {"SPY": 0.6, "TLT": 0.3, "GLD": 0.1}
    
    # Portfolio metrics
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    
    # Risk decomposition
    risk_contributions: Dict[str, float]  # Percentage of total risk
    marginal_risk: Optional[Dict[str, float]] = None
    
    # Optimization details
    converged: bool = True
    iterations: int = 0
    objective_value: Optional[float] = None
    
    # Constraints info
    constraints_satisfied: bool = True
    active_constraints: List[str] = field(default_factory=list)
    
    # Audit trail
    tickers: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Warnings and errors
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "method": self.method.value,
            "weights": {k: f"{v:.2%}" for k, v in self.weights.items()},
            "expected_return": f"{self.expected_return:.2%}",
            "expected_volatility": f"{self.expected_volatility:.2%}",
            "sharpe_ratio": f"{self.sharpe_ratio:.3f}",
            "risk_contributions": {k: f"{v:.1%}" for k, v in self.risk_contributions.items()},
            "converged": self.converged,
            "iterations": self.iterations,
            "constraints_satisfied": self.constraints_satisfied,
            "active_constraints": self.active_constraints,
            "timestamp": self.timestamp.isoformat(),
            "warnings": self.warnings,
        }
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Optimization Result ({self.method.value})",
            "=" * 50,
            f"Status: {'✓ Success' if self.success else '✗ Failed'}",
            "",
            "Optimal Weights:",
        ]
        
        for ticker, weight in sorted(self.weights.items(), key=lambda x: -x[1]):
            risk_contrib = self.risk_contributions.get(ticker, 0)
            lines.append(f"  {ticker}: {weight:6.1%}  (risk: {risk_contrib:5.1%})")
        
        lines.extend([
            "",
            "Portfolio Metrics:",
            f"  Expected Return:     {self.expected_return:7.2%}",
            f"  Expected Volatility: {self.expected_volatility:7.2%}",
            f"  Sharpe Ratio:        {self.sharpe_ratio:7.3f}",
        ])
        
        if self.active_constraints:
            lines.extend([
                "",
                "Active Constraints:",
            ])
            for c in self.active_constraints:
                lines.append(f"  • {c}")
        
        if self.warnings:
            lines.extend([
                "",
                "⚠️ Warnings:",
            ])
            for w in self.warnings:
                lines.append(f"  • {w}")
        
        return "\n".join(lines)


class OptimizerInterface(ABC):
    """
    Abstract interface for portfolio optimizers.
    
    All optimizers must implement:
    - optimize(): Main optimization method
    
    Optional methods:
    - efficient_frontier(): Generate frontier points
    """
    
    def __init__(
        self,
        risk_free_rate: float = 0.0,
        verbose: bool = False
    ):
        """
        Initialize optimizer.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe calculation
            verbose: Print optimization progress
        """
        self.risk_free_rate = risk_free_rate
        self.verbose = verbose
    
    @property
    @abstractmethod
    def method(self) -> OptimizationMethod:
        """Return the optimization method."""
        pass
    
    @abstractmethod
    def optimize(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        constraints: Optional['PortfolioConstraints'] = None
    ) -> OptimizationResult:
        """
        Optimize portfolio weights.
        
        Args:
            expected_returns: Expected returns per asset (annualized)
            cov_matrix: Covariance matrix (annualized)
            constraints: Portfolio constraints (optional)
            
        Returns:
            OptimizationResult with optimal weights and metrics
        """
        pass
    
    def _calculate_portfolio_return(
        self,
        weights: np.ndarray,
        expected_returns: np.ndarray
    ) -> float:
        """Calculate expected portfolio return."""
        return float(np.dot(weights, expected_returns))
    
    def _calculate_portfolio_volatility(
        self,
        weights: np.ndarray,
        cov_matrix: np.ndarray
    ) -> float:
        """Calculate portfolio volatility."""
        variance = np.dot(weights, np.dot(cov_matrix, weights))
        return float(np.sqrt(variance))
    
    def _calculate_sharpe_ratio(
        self,
        expected_return: float,
        volatility: float
    ) -> float:
        """Calculate Sharpe ratio."""
        if volatility == 0:
            return 0.0
        return (expected_return - self.risk_free_rate) / volatility
    
    def _calculate_risk_contributions(
        self,
        weights: np.ndarray,
        cov_matrix: np.ndarray,
        tickers: List[str]
    ) -> Dict[str, float]:
        """
        Calculate marginal and component risk contributions.
        
        Risk contribution of asset i = w_i * (Σw)_i / σ_p
        Sum of all risk contributions = 100%
        """
        portfolio_vol = self._calculate_portfolio_volatility(weights, cov_matrix)
        
        if portfolio_vol == 0:
            return {t: 0.0 for t in tickers}
        
        # Marginal contribution to risk
        marginal = np.dot(cov_matrix, weights) / portfolio_vol
        
        # Component contribution (percentage of total risk)
        component = weights * marginal / portfolio_vol
        
        return {tickers[i]: float(component[i]) for i in range(len(tickers))}
    
    def _validate_inputs(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame
    ) -> List[str]:
        """Validate optimization inputs."""
        warnings = []
        
        # Check dimensions match
        if len(expected_returns) != len(cov_matrix):
            raise ValueError(
                f"Dimension mismatch: returns has {len(expected_returns)} assets, "
                f"cov_matrix has {len(cov_matrix)}"
            )
        
        # Check tickers match
        if set(expected_returns.index) != set(cov_matrix.columns):
            raise ValueError("Tickers in returns and cov_matrix don't match")
        
        # Check for NaN
        if expected_returns.isna().any():
            warnings.append("Expected returns contain NaN values")
        
        if cov_matrix.isna().any().any():
            warnings.append("Covariance matrix contains NaN values")
        
        # Check positive definiteness
        try:
            np.linalg.cholesky(cov_matrix.values)
        except np.linalg.LinAlgError:
            warnings.append("Covariance matrix is not positive definite")
        
        # Check condition number
        cond = np.linalg.cond(cov_matrix.values)
        if cond > 100:
            warnings.append(f"High condition number ({cond:.0f}) - may cause numerical issues")
        
        return warnings
    
    def _create_result(
        self,
        weights: np.ndarray,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        tickers: List[str],
        success: bool = True,
        converged: bool = True,
        iterations: int = 0,
        warnings: List[str] = None,
        error_message: str = None,
        active_constraints: List[str] = None
    ) -> OptimizationResult:
        """Helper to create OptimizationResult."""
        
        weights_dict = {tickers[i]: float(weights[i]) for i in range(len(tickers))}
        
        if success:
            exp_ret = self._calculate_portfolio_return(weights, expected_returns)
            exp_vol = self._calculate_portfolio_volatility(weights, cov_matrix)
            sharpe = self._calculate_sharpe_ratio(exp_ret, exp_vol)
            risk_contrib = self._calculate_risk_contributions(weights, cov_matrix, tickers)
        else:
            exp_ret = 0.0
            exp_vol = 0.0
            sharpe = 0.0
            risk_contrib = {t: 0.0 for t in tickers}
        
        return OptimizationResult(
            success=success,
            method=self.method,
            weights=weights_dict,
            expected_return=exp_ret,
            expected_volatility=exp_vol,
            sharpe_ratio=sharpe,
            risk_contributions=risk_contrib,
            converged=converged,
            iterations=iterations,
            tickers=tickers,
            warnings=warnings or [],
            error_message=error_message,
            active_constraints=active_constraints or [],
        )


@dataclass
class EfficientFrontierPoint:
    """A single point on the efficient frontier."""
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    weights: Dict[str, float]


class EfficientFrontier:
    """
    Efficient Frontier representation.
    
    Contains multiple portfolio points from min-variance to max-return.
    """
    
    def __init__(self, points: List[EfficientFrontierPoint]):
        """Initialize with list of frontier points."""
        self.points = sorted(points, key=lambda p: p.expected_volatility)
    
    @property
    def returns(self) -> List[float]:
        """Get list of returns."""
        return [p.expected_return for p in self.points]
    
    @property
    def volatilities(self) -> List[float]:
        """Get list of volatilities."""
        return [p.expected_volatility for p in self.points]
    
    @property
    def sharpe_ratios(self) -> List[float]:
        """Get list of Sharpe ratios."""
        return [p.sharpe_ratio for p in self.points]
    
    def get_max_sharpe_portfolio(self) -> EfficientFrontierPoint:
        """Get portfolio with maximum Sharpe ratio."""
        return max(self.points, key=lambda p: p.sharpe_ratio)
    
    def get_min_volatility_portfolio(self) -> EfficientFrontierPoint:
        """Get minimum volatility portfolio."""
        return min(self.points, key=lambda p: p.expected_volatility)
    
    def get_portfolio_at_volatility(self, target_vol: float) -> Optional[EfficientFrontierPoint]:
        """Get portfolio closest to target volatility."""
        if not self.points:
            return None
        return min(self.points, key=lambda p: abs(p.expected_volatility - target_vol))
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to DataFrame for plotting."""
        return pd.DataFrame({
            "return": self.returns,
            "volatility": self.volatilities,
            "sharpe": self.sharpe_ratios,
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "num_points": len(self.points),
            "min_volatility": min(self.volatilities) if self.volatilities else None,
            "max_volatility": max(self.volatilities) if self.volatilities else None,
            "min_return": min(self.returns) if self.returns else None,
            "max_return": max(self.returns) if self.returns else None,
            "max_sharpe": max(self.sharpe_ratios) if self.sharpe_ratios else None,
        }
