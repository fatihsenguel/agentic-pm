"""
Mean-Variance (Markowitz) Portfolio Optimization.

Implements classic Markowitz optimization:
- Maximum Sharpe Ratio portfolio

Uses scipy.optimize for numerical optimization.
"""

from typing import Optional

import numpy as np
import pandas as pd
from scipy import optimize

from .base import (
    OptimizerInterface,
    OptimizationResult,
    OptimizationMethod,
)
from .constraints import (
    PortfolioConstraints,
    create_scipy_constraints,
    create_weight_bounds,
    check_constraints_satisfied,
)


class MeanVarianceOptimizer(OptimizerInterface):
    """
    Mean-Variance (Markowitz) Portfolio Optimizer.
    
    One objective: max_sharpe, the maximum Sharpe ratio portfolio.
    
    Example:
        optimizer = MeanVarianceOptimizer(risk_free_rate=0.05)
        result = optimizer.max_sharpe(expected_returns, cov_matrix, constraints)
    """
    
    def __init__(
        self,
        risk_free_rate: float = 0.0,
        verbose: bool = False,
        max_iterations: int = 1000,
        tolerance: float = 1e-10
    ):
        """
        Initialize Mean-Variance optimizer.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe calculation
            verbose: Print optimization progress
            max_iterations: Maximum iterations for optimizer
            tolerance: Convergence tolerance
        """
        super().__init__(risk_free_rate, verbose)
        self.max_iterations = max_iterations
        self.tolerance = tolerance
    
    @property
    def method(self) -> OptimizationMethod:
        return OptimizationMethod.MEAN_VARIANCE
    
    def optimize(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        constraints: Optional[PortfolioConstraints] = None,
        objective: str = "max_sharpe"
    ) -> OptimizationResult:
        """
        Run optimization with specified objective.
        
        Args:
            expected_returns: Expected returns per asset
            cov_matrix: Covariance matrix
            constraints: Portfolio constraints
            objective: "max_sharpe"
            
        Returns:
            OptimizationResult
        """
        if objective == "max_sharpe":
            return self.max_sharpe(expected_returns, cov_matrix, constraints)
        else:
            raise ValueError(f"Unknown objective: {objective}")
    
    def max_sharpe(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        constraints: Optional[PortfolioConstraints] = None
    ) -> OptimizationResult:
        """
        Find portfolio with maximum Sharpe ratio.
        
        Maximizes: (E[R] - Rf) / σ
        """
        # Validate inputs
        warnings = self._validate_inputs(expected_returns, cov_matrix)
        
        tickers = list(expected_returns.index)
        n_assets = len(tickers)
        
        # Convert to numpy
        ret = expected_returns.values
        cov = cov_matrix.values
        
        # Objective: Negative Sharpe ratio (we minimize)
        def neg_sharpe(weights):
            port_return = np.dot(weights, ret)
            port_vol = np.sqrt(np.dot(weights, np.dot(cov, weights)))
            if port_vol == 0:
                return 0
            return -(port_return - self.risk_free_rate) / port_vol
        
        # Initial guess: equal weights
        w0 = np.array([1.0 / n_assets] * n_assets)
        
        # Bounds
        bounds = create_weight_bounds(tickers, constraints)
        
        # Constraints
        scipy_constraints = create_scipy_constraints(
            tickers, cov, ret, constraints
        )
        
        # Optimize
        result = optimize.minimize(
            neg_sharpe,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=scipy_constraints,
            options={
                'maxiter': self.max_iterations,
                'ftol': self.tolerance,
                'disp': self.verbose
            }
        )
        
        # Check result
        if not result.success:
            warnings.append(f"Optimizer warning: {result.message}")
        
        # Clean up small weights
        weights = self._clean_weights(result.x)
        
        # Check constraints
        satisfied, violations = check_constraints_satisfied(
            weights, tickers, cov, ret, constraints
        )
        
        if not satisfied:
            warnings.extend(violations)
        
        # Get active constraints
        active = constraints.get_active_constraints_description() if constraints else []
        
        return self._create_result(
            weights=weights,
            expected_returns=ret,
            cov_matrix=cov,
            tickers=tickers,
            success=result.success,
            converged=result.success,
            iterations=result.nit,
            warnings=warnings,
            active_constraints=active
        )
    
    def _clean_weights(self, weights: np.ndarray, threshold: float = 1e-4) -> np.ndarray:
        """Clean up very small weights to zero."""
        cleaned = weights.copy()
        cleaned[np.abs(cleaned) < threshold] = 0.0
        
        # Renormalize
        if cleaned.sum() > 0:
            cleaned = cleaned / cleaned.sum()
        
        return cleaned
