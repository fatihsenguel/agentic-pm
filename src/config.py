# src/config.py

"""
Central configuration for the Quant Portfolio Manager.

SINGLE SOURCE OF TRUTH for all configuration values.

Usage:
    from config import config
    
    period = config.data.default_period
    vix_threshold = config.macro.vix_elevated
"""

from dataclasses import dataclass, field
from typing import Dict, Literal
import os

# Type definitions
CovarMethod = Literal["sample", "shrinkage", "exponential"]


@dataclass
class DataConfig:
    """Configuration for data fetching and processing."""
    
    # Data fetching
    default_period: str = "3Y"
    min_observations: int = 60
    auto_fetch_if_missing: bool = True
    
    # Covariance estimation
    default_covariance_method: CovarMethod = "sample"
    shrinkage_max_intensity: float = 0.5
    
    # Constants
    trading_days_per_year: int = 252
    
    # Period mappings
    period_days: Dict[str, int] = field(default_factory=lambda: {
        "1Y": 365,
        "2Y": 730,
        "3Y": 1095,
        "5Y": 1825,
        "10Y": 3650,
    })
    
    # Risk-free rate
    default_risk_free_rate: float = 0.05


@dataclass
class MacroConfig:
    """Configuration for macro analysis."""
    
    # VIX thresholds
    vix_low: float = 15.0
    vix_elevated: float = 25.0
    vix_high: float = 35.0          # (was vix_crisis in your file)
    vix_crisis: float = 40.0         # ← ADDED (extreme crisis level)
    
    # Yield curve thresholds (in basis points)
    yield_curve_flat: float = 10.0
    yield_curve_inverted: float = 0.0
    
    # Fed policy thresholds (for rate changes)
    hawkish_threshold: float = 0.25  # ← ADDED (25 bps rate hike)
    dovish_threshold: float = -0.25  # ← ADDED (25 bps rate cut)
    
    # Tactical Asset Allocation (TAA) adjustments
    max_equity_adjust: float = 0.20  # ← ADDED (max ±20% equity adjustment)
    
    # Default lookback periods
    default_vix_days: int = 30
    default_yield_days: int = 90
    default_history_days: int = 90   # ← ADDED
    
    # Data fetching
    auto_fetch_if_missing: bool = True  # ← ADDED
    
    # Update frequency (in hours)
    update_frequency_hours: int = 6


@dataclass
class OptimizationConfig:
    """Configuration for portfolio optimization."""
    
    # Optimization method
    default_method: str = "max_sharpe"  # ← ADDED! (max_sharpe, min_volatility, efficient_frontier)
    
    # Risk-free rate (for Sharpe ratio calculations)
    risk_free_rate: float = 0.05  # ← ADDED! 5%
    
    # Constraints
    default_max_volatility: float = 0.15  # 15%
    default_max_weight: float = 0.40  # 40%
    default_min_weight: float = 0.0   # ← RENAMED from min_weight for consistency
    min_weight: float = 0.0           # ← Keep for backward compatibility
    long_only: bool = True
    
    # Solver settings
    max_iterations: int = 1000
    tolerance: float = 1e-10  # ← CHANGED from 1e-6 to match your setting
    
    # Risk preferences
    default_risk_aversion: float = 1.0
    target_sharpe_ratio: float = 1.0


@dataclass
class RebalanceConfig:
    """Configuration for portfolio rebalancing."""
    
    # Thresholds
    default_drift_threshold: float = 5.0  # 5%
    max_drift_threshold: float = 10.0  # 10%
    
    # Transaction costs
    default_transaction_cost_bps: float = 10.0  # 0.10%
    
    # Tax settings
    capital_gains_rate: float = 0.25  # 25%
    consider_tax_impact: bool = True
    
    # Rebalancing frequency
    min_days_between_rebalances: int = 30


@dataclass
class BacktestConfig:
    default_period: str = "5Y"
    default_rebalance_frequency: str = "monthly"
    default_initial_capital: float = 100_000  # ← ADD
    transaction_cost_bps: float = 10.0
    default_transaction_cost: float = 0.001  # ← ADD
    slippage_bps: float = 5.0
    calculate_rolling_sharpe: bool = True
    rolling_window_days: int = 252
    risk_free_rate: float = 0.05  # ← ADD
    default_benchmark: str = "SPY"


@dataclass
class RiskManagerConfig:
    var_confidence_level: float = 0.95
    var_time_horizon_days: int = 1
    default_stress_scenarios: int = 5
    max_drawdown_threshold: float = 0.20
    alert_on_high_volatility: bool = True
    volatility_threshold_multiplier: float = 2.0
    default_max_volatility: float = 0.15  # ← ADD
    hard_max_volatility: float = 0.25  # ← ADD
    default_max_weight: float = 0.40  # ← ADD
    default_min_weight: float = 0.0  # ← ADD
    max_concentration: float = 0.30
    max_concentration_warning: float = 0.25  # ← ADD
    min_diversification_score: float = 0.5
    min_diversification_assets: int = 5  # ← ADD


@dataclass
class APIConfig:
    """Configuration for external APIs."""
    
    yfinance_rate_limit: int = 60  # Calls per minute
    yfinance_daily_quota: int = 2000
    timeout_seconds: int = 30


@dataclass
class FeatureFlags:
    """Feature flags for optional functionality."""
    
    # Observability
    tracing_enabled: bool = field(default_factory=lambda: os.getenv("ENABLE_TRACING", "false").lower() == "true")
    observability_enabled: bool = field(default_factory=lambda: os.getenv("ENABLE_OBSERVABILITY", "false").lower() == "true")
    
    # Features
    enable_ml_predictions: bool = False
    enable_sentiment_analysis: bool = False
    enable_alternative_data: bool = False


@dataclass
class AppConfig:
    """Main application configuration."""
    
    data: DataConfig = field(default_factory=DataConfig)
    macro: MacroConfig = field(default_factory=MacroConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    rebalance: RebalanceConfig = field(default_factory=RebalanceConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    risk: RiskManagerConfig = field(default_factory=RiskManagerConfig)
    api: APIConfig = field(default_factory=APIConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    
    # Application-wide settings
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


# Singleton instance
config = AppConfig()


# Helper function for testing
def override_config(**kwargs):
    """
    Override config values for testing.
    
    Usage:
        override_config(
            data__default_period="1Y",
            macro__vix_elevated=30.0
        )
    """
    for key, value in kwargs.items():
        parts = key.split("__")
        obj = config
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)