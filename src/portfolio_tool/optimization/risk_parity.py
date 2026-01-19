"""
Risk Parity Portfolio Optimization.

Implements Risk Parity / Equal Risk Contribution (ERC):
- Each asset contributes equally to total portfolio risk
- Does NOT require expected return estimates
- More robust to estimation error than mean-variance

Theory:
- Risk contribution of asset i: RC_i = w_i * (Σw)_i / σ_p
- Risk Parity: RC_i = RC_j for all i, j
- Equal Risk Contribution: RC_i = 1/n for n assets
"""

from typing import List, Optional, Dict

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
    create_weight_bounds,
)


class RiskParityOptimizer(OptimizerInterface):
    """
    Risk Parity (Equal Risk Contribution) Optimizer.
    
    Finds weights where each asset contributes equally to portfolio risk.
    
    Advantages over Mean-Variance:
    - Does not require return estimates (only covariance)
    - More diversified portfolios
    - More robust to estimation error
    - Lower turnover
    
    Disadvantages:
    - Ignores expected returns
    - May underweight high-Sharpe assets
    - Typically results in higher bond allocations
    
    Example:
        optimizer = RiskParityOptimizer()
        result = optimizer.optimize(expected_returns, cov_matrix)
    """
    
    def __init__(
        self,
        risk_free_rate: float = 0.0,
        verbose: bool = False,
        max_iterations: int = 500,
        tolerance: float = 1e-8,
        risk_budget: Optional[Dict[str, float]] = None
    ):
        """
        Initialize Risk Parity optimizer.
        
        Args:
            risk_free_rate: For Sharpe calculation (not used in optimization)
            verbose: Print progress
            max_iterations: Max solver iterations
            tolerance: Convergence tolerance
            risk_budget: Custom risk budget per asset (default: equal)
                        Format: {"SPY": 0.4, "TLT": 0.3, "GLD": 0.3}
        """
        super().__init__(risk_free_rate, verbose)
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.risk_budget = risk_budget
    
    @property
    def method(self) -> OptimizationMethod:
        return OptimizationMethod.RISK_PARITY
    
    def optimize(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        constraints: Optional[PortfolioConstraints] = None
    ) -> OptimizationResult:
        """
        Find risk parity portfolio.
        
        Note: expected_returns is included for interface compatibility
        but is NOT used in the optimization (only for reporting).
        
        Args:
            expected_returns: Expected returns (used only for reporting)
            cov_matrix: Covariance matrix (the key input)
            constraints: Portfolio constraints
            
        Returns:
            OptimizationResult with risk parity weights
        """
        warnings = self._validate_inputs(expected_returns, cov_matrix)
        warnings.append("Note: Risk Parity ignores expected returns in optimization")
        
        tickers = list(cov_matrix.columns)
        n_assets = len(tickers)
        
        cov = cov_matrix.values
        ret = expected_returns.values
        
        # Get risk budget
        if self.risk_budget:
            budget = np.array([self.risk_budget.get(t, 1.0/n_assets) for t in tickers])
            budget = budget / budget.sum()
        else:
            # Equal risk contribution
            budget = np.array([1.0 / n_assets] * n_assets)
        
        # Optimize using the improved algorithm
        weights, converged, iterations = self._solve_risk_parity_slsqp(
            cov, budget, constraints, tickers
        )
        
        if not converged:
            warnings.append("Optimizer did not fully converge - using best solution found")
        
        # Calculate actual risk contributions with the solution
        risk_contrib = self._calculate_risk_contributions(weights, cov, tickers)
        
        # Check how close to target budget
        max_deviation = max(
            abs(risk_contrib[t] - budget[i]) 
            for i, t in enumerate(tickers)
        )
        
        if max_deviation > 0.02:
            warnings.append(
                f"Risk contribution deviation from target: {max_deviation:.1%}"
            )
        
        active = []
        if constraints:
            active = constraints.get_active_constraints_description()
        active.append(f"Risk budget: {'Equal' if self.risk_budget is None else 'Custom'}")
        
        # Always return success=True if we have valid weights
        # (the algorithm finds a good solution even if scipy says it didn't "converge")
        weights_valid = (
            abs(weights.sum() - 1.0) < 0.01 and 
            all(w >= -0.001 for w in weights)
        )
        
        return self._create_result(
            weights=weights,
            expected_returns=ret,
            cov_matrix=cov,
            tickers=tickers,
            success=weights_valid,  # Success if weights are valid
            converged=converged,
            iterations=iterations,
            warnings=warnings,
            active_constraints=active
        )
    
    def _solve_risk_parity_slsqp(
        self,
        cov_matrix: np.ndarray,
        risk_budget: np.ndarray,
        constraints: Optional[PortfolioConstraints],
        tickers: List[str]
    ) -> tuple:
        """
        Solve risk parity using SLSQP with proper constraints.
        
        This is more robust than the log-space approach.
        """
        n = len(risk_budget)
        
        def risk_contribution_error(weights):
            """
            Objective: Sum of squared differences from target risk contributions.
            """
            weights = np.maximum(weights, 1e-8)
            
            # Portfolio variance and volatility
            port_var = np.dot(weights, np.dot(cov_matrix, weights))
            port_vol = np.sqrt(port_var)
            
            if port_vol < 1e-10:
                return 1e6
            
            # Marginal contribution to risk: ∂σ/∂w = Σw / σ
            marginal = np.dot(cov_matrix, weights) / port_vol
            
            # Component risk contribution: w * marginal / σ
            # This gives the fraction of total risk from each asset
            risk_contrib = weights * marginal / port_vol
            
            # Objective: minimize squared error from target budget
            error = np.sum((risk_contrib - risk_budget) ** 2)
            
            return error * 1000  # Scale for better numerical behavior
        
        # Initial guess: inverse volatility (good starting point)
        vols = np.sqrt(np.diag(cov_matrix))
        w0 = 1.0 / vols
        w0 = w0 / w0.sum()
        
        # Bounds
        if constraints:
            bounds = constraints.get_bounds(tickers)
        else:
            bounds = [(0.01, 1.0) for _ in range(n)]  # Minimum 1% to avoid numerical issues
        
        # Constraints: weights sum to 1
        eq_constraints = [{
            'type': 'eq',
            'fun': lambda w: np.sum(w) - 1.0,
            'jac': lambda w: np.ones(n)
        }]
        
        # Try multiple optimization methods
        best_result = None
        best_error = float('inf')
        
        for method_try in ['SLSQP', 'trust-constr']:
            try:
                if method_try == 'SLSQP':
                    result = optimize.minimize(
                        risk_contribution_error,
                        w0,
                        method='SLSQP',
                        bounds=bounds,
                        constraints=eq_constraints,
                        options={
                            'maxiter': self.max_iterations,
                            'ftol': self.tolerance,
                            'disp': self.verbose
                        }
                    )
                else:
                    # trust-constr as backup
                    result = optimize.minimize(
                        risk_contribution_error,
                        w0,
                        method='trust-constr',
                        bounds=optimize.Bounds(
                            [b[0] for b in bounds],
                            [b[1] for b in bounds]
                        ),
                        constraints={'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
                        options={
                            'maxiter': self.max_iterations,
                            'gtol': self.tolerance,
                            'disp': self.verbose
                        }
                    )
                
                if result.fun < best_error:
                    best_error = result.fun
                    best_result = result
                    
                # If we found a good solution, stop
                if result.success and result.fun < 0.001:
                    break
                    
            except Exception:
                continue
        
        if best_result is None:
            # Fallback to inverse volatility
            return w0, False, 0
        
        # Clean up weights
        weights = best_result.x
        weights = np.maximum(weights, 0)
        weights = weights / weights.sum()
        
        return weights, best_result.success or best_error < 0.01, best_result.nit
    
    def _solve_risk_parity_newton(
        self,
        cov_matrix: np.ndarray,
        risk_budget: np.ndarray
    ) -> np.ndarray:
        """
        Alternative: Solve using Newton's method (Spinu 2013).
        
        More reliable for the unconstrained case.
        """
        n = len(risk_budget)
        
        # Initial guess: inverse volatility
        vols = np.sqrt(np.diag(cov_matrix))
        x = 1.0 / vols
        
        for iteration in range(100):
            # Portfolio variance
            Sx = np.dot(cov_matrix, x)
            port_var = np.dot(x, Sx)
            
            # Gradient of the risk parity objective
            # We want: x_i * (Σx)_i / √(x'Σx) = b_i for all i
            # Rearranging: x_i * (Σx)_i = b_i * √(x'Σx)
            
            # Newton step for the log-transformed problem
            grad = Sx / port_var - risk_budget / x
            
            # Simple update (not full Newton, but works)
            x = x * np.sqrt(risk_budget * port_var / (x * Sx))
            
            # Check convergence
            actual_rc = x * Sx / port_var
            error = np.max(np.abs(actual_rc - risk_budget))
            
            if error < self.tolerance:
                break
        
        # Normalize
        x = x / x.sum()
        
        return x
    
    def optimize_with_custom_budget(
        self,
        cov_matrix: pd.DataFrame,
        risk_budget: Dict[str, float],
        constraints: Optional[PortfolioConstraints] = None
    ) -> OptimizationResult:
        """
        Risk budgeting with custom risk allocation.
        
        Args:
            cov_matrix: Covariance matrix
            risk_budget: Target risk contribution per asset
                        e.g., {"SPY": 0.5, "TLT": 0.3, "GLD": 0.2}
            constraints: Weight constraints
            
        Returns:
            OptimizationResult
        """
        tickers = list(cov_matrix.columns)
        
        # Validate budget
        budget_sum = sum(risk_budget.values())
        if abs(budget_sum - 1.0) > 0.01:
            raise ValueError(f"Risk budget must sum to 1.0, got {budget_sum}")
        
        for ticker in tickers:
            if ticker not in risk_budget:
                raise ValueError(f"Missing risk budget for {ticker}")
        
        # Create dummy returns (not used in optimization)
        dummy_returns = pd.Series(0.0, index=tickers)
        
        # Set custom budget and optimize
        self.risk_budget = risk_budget
        result = self.optimize(dummy_returns, cov_matrix, constraints)
        self.risk_budget = None  # Reset
        
        return result


class InverseVolatilityOptimizer(OptimizerInterface):
    """
    Simple inverse volatility weighting.
    
    Weights are proportional to 1/volatility.
    This is a simple heuristic that approximates risk parity
    when correlations are moderate.
    
    Advantages:
    - Very fast (closed-form solution)
    - No iteration needed
    - Intuitive
    
    Disadvantages:
    - Ignores correlations
    - Not true risk parity
    """
    
    @property
    def method(self) -> OptimizationMethod:
        return OptimizationMethod.RISK_PARITY
    
    def optimize(
        self,
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        constraints: Optional[PortfolioConstraints] = None
    ) -> OptimizationResult:
        """
        Calculate inverse volatility weights.
        """
        warnings = ["Using simple inverse volatility (ignores correlations)"]
        
        tickers = list(cov_matrix.columns)
        cov = cov_matrix.values
        ret = expected_returns.values
        
        # Get volatilities from diagonal
        vols = np.sqrt(np.diag(cov))
        
        # Inverse volatility weights
        inv_vols = 1.0 / vols
        weights = inv_vols / inv_vols.sum()
        
        # Apply bounds if constraints exist
        if constraints:
            bounds = constraints.get_bounds(tickers)
            for i, (min_w, max_w) in enumerate(bounds):
                weights[i] = np.clip(weights[i], min_w, max_w)
            
            # Renormalize
            weights = weights / weights.sum()
        
        return self._create_result(
            weights=weights,
            expected_returns=ret,
            cov_matrix=cov,
            tickers=tickers,
            success=True,
            converged=True,
            iterations=0,
            warnings=warnings,
            active_constraints=["Inverse volatility weighting"]
        )