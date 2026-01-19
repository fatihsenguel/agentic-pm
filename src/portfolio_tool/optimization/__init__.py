"""
Portfolio Optimization Module.

This module provides portfolio optimization algorithms:
- Mean-Variance (Markowitz) Optimization
- Risk Parity / Equal Risk Contribution
- Minimum Volatility
- Maximum Sharpe Ratio
- Efficient Frontier Generation

Design Principles:
- All optimizers implement OptimizerInterface
- Results include audit trails (method, constraints, convergence)
- Proper handling of edge cases (singular matrices, infeasible constraints)
- No LLM involvement - pure mathematical optimization
"""

from .base import (
    OptimizerInterface,
    OptimizationResult,
    OptimizationMethod,
)

from .constraints import (
    PortfolioConstraints,
    BoundConstraint,
    create_scipy_constraints,
    create_weight_bounds,
)

from .mean_variance import (
    MeanVarianceOptimizer,
)

from .risk_parity import (
    RiskParityOptimizer,
)


__all__ = [
    # Base
    "OptimizerInterface",
    "OptimizationResult",
    "OptimizationMethod",
    # Constraints
    "PortfolioConstraints",
    "BoundConstraint",
    "create_scipy_constraints",
    "create_weight_bounds",
    # Optimizers
    "MeanVarianceOptimizer",
    "RiskParityOptimizer",
]
