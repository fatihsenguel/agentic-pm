# src/portfolio_tool/analytics/__init__.py
"""
Analytics Engine (Layer 4)
==========================

This module contains the calculation logic for financial metrics.
It is separate from the tools (Layer 5) to maintain SoC.

Usage:
    from portfolio_tool.analytics import MetricsCalculator
    
    calc = MetricsCalculator()
    result = calc.calculate_returns("AAPL", days=365)
"""

from .metrics import MetricsCalculator

__all__ = ["MetricsCalculator"]
