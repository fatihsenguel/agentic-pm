"""
Mean-Variance (Markowitz) Portfolio Optimization.

Implements classic Markowitz optimization:
- Maximum Sharpe Ratio portfolio
- Minimum Volatility portfolio
- Target Return portfolio
- Target Volatility portfolio
- Efficient Frontier generation

Uses scipy.optimize for numerical optimization.
"""

from typing import List, Optional

import numpy as np
import pandas as pd
from scipy import optimize

from .base import (
    OptimizerInterface,
    OptimizationResult,
    OptimizationMethod,
    EfficientFrontier,
    EfficientFrontierPoint,
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
    
    Supports multiple optimization objectives:
    - max_sharpe: Maximize Sharpe ratio
    - min_volatility: Minimize portfolio volatility
    - target_return: Minimize volatility for target return
    - target_volatility: Maximize return for target volatility
    
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
            objective: "max_sharpe", "min_volatility", "target_return", "target_volatility"
            
        Returns:
            OptimizationResult
        """
        if objective == "max_sharpe":
            return self.max_sharpe(expected_returns, cov_matrix, constraints)
        elif objective == "min_volatility":
            return self.min_volatility(expected_returns, cov_matrix, constraints)
        elif objective == "target_return":
            return self.target_return(expected_returns, cov_matrix, constraints)
        elif objective == "target_volatility":
            return self.target_volatility(expected_returns, cov_matrix, constraints)
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
    
    def min_volatility(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        constraints: Optional[PortfolioConstraints] = None
    ) -> OptimizationResult:
        """
        Find minimum volatility portfolio.
        
        Minimizes: σ_p = sqrt(w' Σ w)
        """
        warnings = self._validate_inputs(expected_returns, cov_matrix)
        
        tickers = list(expected_returns.index)
        n_assets = len(tickers)
        
        ret = expected_returns.values
        cov = cov_matrix.values
        
        # Objective: Portfolio variance
        def portfolio_variance(weights):
            return np.dot(weights, np.dot(cov, weights))
        
        # Gradient for faster convergence
        def variance_gradient(weights):
            return 2 * np.dot(cov, weights)
        
        w0 = np.array([1.0 / n_assets] * n_assets)
        bounds = create_weight_bounds(tickers, constraints)
        scipy_constraints = create_scipy_constraints(tickers, cov, ret, constraints)
        
        result = optimize.minimize(
            portfolio_variance,
            w0,
            method='SLSQP',
            jac=variance_gradient,
            bounds=bounds,
            constraints=scipy_constraints,
            options={
                'maxiter': self.max_iterations,
                'ftol': self.tolerance,
                'disp': self.verbose
            }
        )
        
        if not result.success:
            warnings.append(f"Optimizer warning: {result.message}")
        
        weights = self._clean_weights(result.x)
        
        satisfied, violations = check_constraints_satisfied(
            weights, tickers, cov, ret, constraints
        )
        if not satisfied:
            warnings.extend(violations)
        
        active = constraints.get_active_constraints_description() if constraints else []
        
        opt_result = self._create_result(
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
        
        # Update method to MIN_VOLATILITY
        opt_result.method = OptimizationMethod.MIN_VOLATILITY
        
        return opt_result
    
    def target_return(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        constraints: Optional[PortfolioConstraints] = None
    ) -> OptimizationResult:
        """
        Find minimum volatility portfolio for a target return.
        
        Requires constraints.target_return to be set.
        """
        if constraints is None or constraints.target_return is None:
            raise ValueError("target_return constraint must be set")
        
        warnings = self._validate_inputs(expected_returns, cov_matrix)
        
        tickers = list(expected_returns.index)
        n_assets = len(tickers)
        
        ret = expected_returns.values
        cov = cov_matrix.values
        
        # Check if target is achievable
        if constraints.target_return > ret.max():
            warnings.append(
                f"Target return {constraints.target_return:.2%} exceeds max possible "
                f"{ret.max():.2%}"
            )
        
        def portfolio_variance(weights):
            return np.dot(weights, np.dot(cov, weights))
        
        w0 = np.array([1.0 / n_assets] * n_assets)
        bounds = create_weight_bounds(tickers, constraints)
        scipy_constraints = create_scipy_constraints(tickers, cov, ret, constraints)
        
        result = optimize.minimize(
            portfolio_variance,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=scipy_constraints,
            options={'maxiter': self.max_iterations, 'ftol': self.tolerance}
        )
        
        if not result.success:
            warnings.append(f"Optimizer warning: {result.message}")
        
        weights = self._clean_weights(result.x)
        active = constraints.get_active_constraints_description() if constraints else []
        
        opt_result = self._create_result(
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
        
        opt_result.method = OptimizationMethod.TARGET_RETURN
        
        return opt_result
    
    def target_volatility(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        constraints: Optional[PortfolioConstraints] = None
    ) -> OptimizationResult:
        """
        Find maximum return portfolio for a target volatility.
        
        Requires constraints.target_volatility or max_volatility to be set.
        """
        if constraints is None:
            raise ValueError("Constraints with target/max volatility must be set")
        
        if constraints.target_volatility is None and constraints.max_volatility is None:
            raise ValueError("Either target_volatility or max_volatility must be set")
        
        warnings = self._validate_inputs(expected_returns, cov_matrix)
        
        tickers = list(expected_returns.index)
        n_assets = len(tickers)
        
        ret = expected_returns.values
        cov = cov_matrix.values
        
        # Objective: Negative return (we minimize, so maximize return)
        def neg_return(weights):
            return -np.dot(weights, ret)
        
        w0 = np.array([1.0 / n_assets] * n_assets)
        bounds = create_weight_bounds(tickers, constraints)
        scipy_constraints = create_scipy_constraints(tickers, cov, ret, constraints)
        
        result = optimize.minimize(
            neg_return,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=scipy_constraints,
            options={'maxiter': self.max_iterations, 'ftol': self.tolerance}
        )
        
        if not result.success:
            warnings.append(f"Optimizer warning: {result.message}")
        
        weights = self._clean_weights(result.x)
        active = constraints.get_active_constraints_description() if constraints else []
        
        opt_result = self._create_result(
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
        
        opt_result.method = OptimizationMethod.TARGET_VOLATILITY
        
        return opt_result
    
    def efficient_frontier(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        constraints: Optional[PortfolioConstraints] = None,
        n_points: int = 50
    ) -> EfficientFrontier:
        """
        Generate the efficient frontier.
        
        Creates n_points portfolios from min-variance to max-return.
        
        Args:
            expected_returns: Expected returns per asset
            cov_matrix: Covariance matrix
            constraints: Portfolio constraints
            n_points: Number of points on the frontier
            
        Returns:
            EfficientFrontier with all points
        """
        tickers = list(expected_returns.index)
        ret = expected_returns.values
        cov = cov_matrix.values
        
        # Find min and max achievable returns
        min_vol_result = self.min_volatility(expected_returns, cov_matrix, constraints)
        
        # Max return is the highest returning single asset (respecting constraints)
        if constraints and constraints.max_weight < 1.0:
            # With max weight constraint, max return is more complex
            # Use max_sharpe as proxy for high-return portfolio
            max_ret_result = self.max_sharpe(expected_returns, cov_matrix, constraints)
            max_return = max_ret_result.expected_return * 1.1  # Slight buffer
        else:
            max_return = ret.max()
        
        min_return = min_vol_result.expected_return
        
        # Generate target returns
        target_returns = np.linspace(min_return, max_return, n_points)
        
        points = []
        
        for target in target_returns:
            # Create constraints with target return
            target_constraints = PortfolioConstraints(
                min_weight=constraints.min_weight if constraints else 0.0,
                max_weight=constraints.max_weight if constraints else 1.0,
                target_return=target,
                long_only=constraints.long_only if constraints else True,
                asset_bounds=constraints.asset_bounds if constraints else None,
            )
            
            try:
                result = self.target_return(
                    expected_returns, cov_matrix, target_constraints
                )
                
                if result.success:
                    points.append(EfficientFrontierPoint(
                        expected_return=result.expected_return,
                        expected_volatility=result.expected_volatility,
                        sharpe_ratio=result.sharpe_ratio,
                        weights=result.weights
                    ))
            except Exception:
                # Skip infeasible points
                continue
        
        return EfficientFrontier(points)
    
    def _clean_weights(self, weights: np.ndarray, threshold: float = 1e-4) -> np.ndarray:
        """Clean up very small weights to zero."""
        cleaned = weights.copy()
        cleaned[np.abs(cleaned) < threshold] = 0.0
        
        # Renormalize
        if cleaned.sum() > 0:
            cleaned = cleaned / cleaned.sum()
        
        return cleaned
