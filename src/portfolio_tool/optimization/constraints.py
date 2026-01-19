"""
Portfolio Constraints Module.

Handles constraint specification and conversion to scipy format.

Supported constraints:
- Weight bounds (min/max per asset)
- Total weight sum = 1
- Maximum volatility
- Minimum/target return
- Sector/group constraints (future)
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd


@dataclass
class BoundConstraint:
    """Constraint on a single asset's weight."""
    ticker: str
    min_weight: float = 0.0
    max_weight: float = 1.0
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to (min, max) tuple for scipy."""
        return (self.min_weight, self.max_weight)


@dataclass 
class PortfolioConstraints:
    """
    Complete constraint specification for portfolio optimization.
    
    Example:
        constraints = PortfolioConstraints(
            min_weight=0.05,      # At least 5% per asset
            max_weight=0.40,      # At most 40% per asset
            max_volatility=0.12,  # Portfolio vol <= 12%
        )
    """
    
    # Global weight constraints (applied to all assets)
    min_weight: float = 0.0   # Minimum weight per asset (0 = allow zero)
    max_weight: float = 1.0   # Maximum weight per asset (1 = no limit)
    
    # Per-asset overrides
    asset_bounds: Optional[Dict[str, Tuple[float, float]]] = None
    
    # Risk constraints
    max_volatility: Optional[float] = None   # Maximum portfolio volatility
    target_volatility: Optional[float] = None  # Target volatility (with tolerance)
    volatility_tolerance: float = 0.005  # Tolerance for target vol (0.5%)
    
    # Return constraints
    min_return: Optional[float] = None   # Minimum expected return
    target_return: Optional[float] = None  # Target return
    
    # Long-only constraint
    long_only: bool = True  # If False, allows shorting
    
    # Turnover constraints (for rebalancing)
    max_turnover: Optional[float] = None  # Max total turnover
    
    # Group/Sector constraints (keys are group names)
    group_constraints: Optional[Dict[str, Dict[str, Any]]] = None
    # Format: {"equities": {"assets": ["SPY", "QQQ"], "max_weight": 0.6}}
    
    def get_bounds(self, tickers: List[str]) -> List[Tuple[float, float]]:
        """
        Get weight bounds for each asset.
        
        Args:
            tickers: List of asset tickers in order
            
        Returns:
            List of (min, max) tuples for scipy
        """
        bounds = []
        
        for ticker in tickers:
            if self.asset_bounds and ticker in self.asset_bounds:
                # Use asset-specific bounds
                bounds.append(self.asset_bounds[ticker])
            else:
                # Use global bounds
                min_w = max(0.0, self.min_weight) if self.long_only else self.min_weight
                max_w = self.max_weight
                bounds.append((min_w, max_w))
        
        return bounds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "min_weight": self.min_weight,
            "max_weight": self.max_weight,
            "max_volatility": self.max_volatility,
            "target_volatility": self.target_volatility,
            "min_return": self.min_return,
            "target_return": self.target_return,
            "long_only": self.long_only,
            "asset_bounds": self.asset_bounds,
        }
    
    def get_active_constraints_description(self) -> List[str]:
        """Get human-readable list of active constraints."""
        active = []
        
        if self.min_weight > 0:
            active.append(f"Min weight per asset: {self.min_weight:.1%}")
        if self.max_weight < 1:
            active.append(f"Max weight per asset: {self.max_weight:.1%}")
        if self.max_volatility:
            active.append(f"Max portfolio volatility: {self.max_volatility:.1%}")
        if self.target_volatility:
            active.append(f"Target volatility: {self.target_volatility:.1%}")
        if self.min_return:
            active.append(f"Min return: {self.min_return:.1%}")
        if self.long_only:
            active.append("Long-only (no shorting)")
        if self.asset_bounds:
            for ticker, (min_w, max_w) in self.asset_bounds.items():
                active.append(f"{ticker}: [{min_w:.1%}, {max_w:.1%}]")
        
        return active


def create_weight_bounds(
    tickers: List[str],
    constraints: Optional[PortfolioConstraints] = None
) -> List[Tuple[float, float]]:
    """
    Create scipy-compatible bounds from constraints.
    
    Args:
        tickers: List of asset tickers
        constraints: Portfolio constraints
        
    Returns:
        List of (min, max) tuples
    """
    if constraints is None:
        # Default: long-only, full allocation allowed
        return [(0.0, 1.0) for _ in tickers]
    
    return constraints.get_bounds(tickers)


def create_scipy_constraints(
    tickers: List[str],
    cov_matrix: np.ndarray,
    expected_returns: np.ndarray,
    constraints: Optional[PortfolioConstraints] = None
) -> List[Dict[str, Any]]:
    """
    Create scipy.optimize constraint dictionaries.
    
    Args:
        tickers: List of asset tickers
        cov_matrix: Covariance matrix
        expected_returns: Expected returns array
        constraints: Portfolio constraints
        
    Returns:
        List of constraint dicts for scipy.optimize.minimize
    """
    scipy_constraints = []
    
    # Constraint 1: Weights sum to 1 (equality)
    scipy_constraints.append({
        'type': 'eq',
        'fun': lambda w: np.sum(w) - 1.0,
        'jac': lambda w: np.ones(len(w))
    })
    
    if constraints is None:
        return scipy_constraints
    
    # Constraint 2: Maximum volatility (inequality: vol <= max_vol)
    if constraints.max_volatility is not None:
        def vol_constraint(w, cov=cov_matrix, max_vol=constraints.max_volatility):
            port_vol = np.sqrt(np.dot(w, np.dot(cov, w)))
            return max_vol - port_vol  # >= 0 means vol <= max_vol
        
        scipy_constraints.append({
            'type': 'ineq',
            'fun': vol_constraint
        })
    
    # Constraint 3: Target volatility (equality with tolerance)
    if constraints.target_volatility is not None:
        target = constraints.target_volatility
        tol = constraints.volatility_tolerance
        
        # Implement as two inequalities: target - tol <= vol <= target + tol
        def vol_lower(w, cov=cov_matrix, target=target, tol=tol):
            port_vol = np.sqrt(np.dot(w, np.dot(cov, w)))
            return port_vol - (target - tol)  # vol >= target - tol
        
        def vol_upper(w, cov=cov_matrix, target=target, tol=tol):
            port_vol = np.sqrt(np.dot(w, np.dot(cov, w)))
            return (target + tol) - port_vol  # vol <= target + tol
        
        scipy_constraints.append({'type': 'ineq', 'fun': vol_lower})
        scipy_constraints.append({'type': 'ineq', 'fun': vol_upper})
    
    # Constraint 4: Minimum return (inequality)
    if constraints.min_return is not None:
        def return_constraint(w, ret=expected_returns, min_ret=constraints.min_return):
            port_return = np.dot(w, ret)
            return port_return - min_ret  # >= 0 means return >= min_return
        
        scipy_constraints.append({
            'type': 'ineq',
            'fun': return_constraint
        })
    
    # Constraint 5: Target return (equality)
    if constraints.target_return is not None:
        def target_return_constraint(w, ret=expected_returns, target=constraints.target_return):
            return np.dot(w, ret) - target
        
        scipy_constraints.append({
            'type': 'eq',
            'fun': target_return_constraint
        })
    
    # Constraint 6: Group constraints
    if constraints.group_constraints:
        for group_name, group_spec in constraints.group_constraints.items():
            assets = group_spec.get('assets', [])
            max_weight = group_spec.get('max_weight')
            min_weight = group_spec.get('min_weight')
            
            # Get indices of assets in this group
            indices = [tickers.index(a) for a in assets if a in tickers]
            
            if max_weight is not None and indices:
                def group_max(w, idx=indices, max_w=max_weight):
                    return max_w - sum(w[i] for i in idx)
                scipy_constraints.append({'type': 'ineq', 'fun': group_max})
            
            if min_weight is not None and indices:
                def group_min(w, idx=indices, min_w=min_weight):
                    return sum(w[i] for i in idx) - min_w
                scipy_constraints.append({'type': 'ineq', 'fun': group_min})
    
    return scipy_constraints


def check_constraints_satisfied(
    weights: np.ndarray,
    tickers: List[str],
    cov_matrix: np.ndarray,
    expected_returns: np.ndarray,
    constraints: Optional[PortfolioConstraints] = None,
    tolerance: float = 1e-6
) -> Tuple[bool, List[str]]:
    """
    Check if a weight vector satisfies all constraints.
    
    Args:
        weights: Portfolio weights
        tickers: Asset tickers
        cov_matrix: Covariance matrix
        expected_returns: Expected returns
        constraints: Portfolio constraints
        tolerance: Numerical tolerance
        
    Returns:
        Tuple of (all_satisfied, list of violated constraints)
    """
    violations = []
    
    # Check weights sum to 1
    weight_sum = np.sum(weights)
    if abs(weight_sum - 1.0) > tolerance:
        violations.append(f"Weights sum to {weight_sum:.4f}, not 1.0")
    
    if constraints is None:
        return len(violations) == 0, violations
    
    # Check bounds
    bounds = constraints.get_bounds(tickers)
    for i, (ticker, (min_w, max_w)) in enumerate(zip(tickers, bounds)):
        if weights[i] < min_w - tolerance:
            violations.append(f"{ticker} weight {weights[i]:.2%} < min {min_w:.2%}")
        if weights[i] > max_w + tolerance:
            violations.append(f"{ticker} weight {weights[i]:.2%} > max {max_w:.2%}")
    
    # Check volatility constraint
    port_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
    
    if constraints.max_volatility is not None:
        if port_vol > constraints.max_volatility + tolerance:
            violations.append(
                f"Volatility {port_vol:.2%} > max {constraints.max_volatility:.2%}"
            )
    
    if constraints.target_volatility is not None:
        tol = constraints.volatility_tolerance
        if abs(port_vol - constraints.target_volatility) > tol + tolerance:
            violations.append(
                f"Volatility {port_vol:.2%} not at target {constraints.target_volatility:.2%}"
            )
    
    # Check return constraint
    port_return = np.dot(weights, expected_returns)
    
    if constraints.min_return is not None:
        if port_return < constraints.min_return - tolerance:
            violations.append(
                f"Return {port_return:.2%} < min {constraints.min_return:.2%}"
            )
    
    return len(violations) == 0, violations
