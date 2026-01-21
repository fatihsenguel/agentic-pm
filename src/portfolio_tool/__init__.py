"""
Portfolio Tool Module - Core Business Logic.

This module provides all the core functionality for portfolio management:

Data Layer:
    - DataManager: Database operations (CRUD)
    - YFinanceProvider: Market data provider
    - QuotaManager: API rate limiting

Analytics:
    - MetricsCalculator: Performance and risk metrics

Quantitative:
    - Covariance estimation (shrinkage methods)
    - Returns calculation
    - Risk metrics (VaR, CVaR, etc.)

Optimization:
    - Mean-variance optimization
    - Risk parity
    - Constraints handling

Backtesting:
    - Backtest engine
    - Strategy definitions
    - Performance reports

Tools (Agent Interface):
    - data_tools: Price fetching, covariance
    - macro_tools: VIX, yields, regime
    - rebalance_tools: Drift, trades
    - analytics_tools: Metrics

Design Principles:
    1. Separation of Concerns - Each module has ONE responsibility
    2. Hot Potato - Data is aggregated at each layer, LLMs never see raw data
    3. Idempotent Operations - All DB writes use ON CONFLICT UPDATE
    4. Provider Abstraction - Data sources are interchangeable
"""

# Database setup
from .database_setup import (
    get_engine,
    get_session,
    Base,
    DailyPrice,
    MacroData,
)

# Data Manager
from .data_manager import DataManager

# Provider models
from .provider_models import (
    PriceData,
    FinancialData,
)

__all__ = [
    # Database
    "get_engine",
    "get_session", 
    "Base",
    "DailyPrice",
    "MacroData",
    
    # Data Manager
    "DataManager",
    
    # Models
    "PriceData",
    "FinancialData",
]