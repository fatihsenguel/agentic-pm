"""
Agent Communication Protocols for Quant Portfolio Manager.

This module defines the standardized data transfer objects (DTOs) used
for communication between agents in the multi-agent system.

Key Principles:
- Hot Potato Principle: Send processed summaries, not raw data
- Agent-Ready Responses: Include reasoning and audit trails
- Type Safety: Full typing for all fields
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

import uuid


class TaskType(str, Enum):
    """Types of portfolio tasks agents can perform."""
    OPTIMIZE = "optimize"
    BACKTEST = "backtest"
    ANALYZE_REGIME = "analyze_regime"
    REBALANCE = "rebalance"
    FETCH_DATA = "fetch_data"
    CALCULATE_RISK = "calculate_risk"
    MACRO_ANALYSIS = "macro_analysis"  # NEU für MacroAgent


class OptimizationMethod(str, Enum):
    """Available portfolio optimization methods."""
    MEAN_VARIANCE = "mean_variance"
    RISK_PARITY = "risk_parity"
    MIN_VARIANCE = "min_variance"
    MAX_SHARPE = "max_sharpe"
    BLACK_LITTERMAN = "black_litterman"


class RebalanceFrequency(str, Enum):
    """Rebalancing frequency options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class RegimeType(str, Enum):
    """
    Market regime classifications.
    
    Used by MacroAgent for TAA signal generation.
    """
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    NEUTRAL = "neutral"
    
    # NEU: Für MacroAgent Regime Detection
    CRISIS = "crisis"
    RECOVERY = "recovery"
    
    # Legacy (für Kompatibilität)
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


@dataclass
class PortfolioConstraints:
    """
    Portfolio constraints for optimization.
    
    All constraints are optional - only specified ones are enforced.
    """
    # Weight constraints
    min_weight: Optional[float] = 0.0  # Minimum weight per asset (e.g., 0.0)
    max_weight: Optional[float] = 1.0  # Maximum weight per asset (e.g., 0.4)
    
    # Risk constraints
    max_volatility: Optional[float] = None  # Maximum portfolio volatility (e.g., 0.12)
    max_drawdown: Optional[float] = None    # Maximum allowed drawdown
    
    # Asset-specific constraints
    asset_min_weights: Optional[Dict[str, float]] = None  # {"SPY": 0.1}
    asset_max_weights: Optional[Dict[str, float]] = None  # {"SPY": 0.5}
    
    # Group constraints (e.g., "equities" can't exceed 60%)
    group_constraints: Optional[Dict[str, Dict[str, float]]] = None
    
    # Long-only constraint
    long_only: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "min_weight": self.min_weight,
            "max_weight": self.max_weight,
            "max_volatility": self.max_volatility,
            "max_drawdown": self.max_drawdown,
            "asset_min_weights": self.asset_min_weights,
            "asset_max_weights": self.asset_max_weights,
            "group_constraints": self.group_constraints,
            "long_only": self.long_only,
        }


@dataclass
class TAARule:
    """
    Tactical Asset Allocation rule - purely deterministic.
    
    These rules are evaluated during backtesting WITHOUT any LLM involvement.
    The LLM's only role is to translate user intent into these structured rules.
    """
    name: str
    condition: str  # Human-readable: "VIX > 25"
    condition_type: str  # "threshold", "percentile", "crossover"
    indicator: str  # "VIX", "SMA_50", "YIELD_SPREAD"
    operator: str  # ">", "<", ">=", "<=", "=="
    threshold: float  # 25.0
    target_weights: Dict[str, float]  # {"SPY": 0.4, "TLT": 0.4, "CASH": 0.2}
    
    def evaluate(self, indicator_value: float) -> bool:
        """
        Evaluate if rule triggers based on indicator value.
        
        MUST be deterministic. No LLM involvement.
        """
        ops = {
            ">": lambda x, y: x > y,
            "<": lambda x, y: x < y,
            ">=": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y,
            "==": lambda x, y: abs(x - y) < 1e-9,
        }
        
        if self.operator not in ops:
            raise ValueError(f"Unknown operator: {self.operator}")
        
        return ops[self.operator](indicator_value, self.threshold)


@dataclass
class PortfolioTask:
    """
    Task specification for portfolio agents.
    
    This is the standardized input format that the Risk Manager Agent
    creates and passes to specialized agents.
    """
    # Task identification
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task_type: TaskType = TaskType.OPTIMIZE
    created_at: datetime = field(default_factory=datetime.now)
    
    # Investment Universe
    universe: List[str] = field(default_factory=list)  # ["SPY", "TLT", "GLD"]
    
    # Constraints
    constraints: PortfolioConstraints = field(default_factory=PortfolioConstraints)
    
    # Optimization parameters
    optimization_method: Optional[OptimizationMethod] = None
    risk_free_rate: Optional[float] = None  # If not provided, will be fetched
    
    # Current portfolio state (for rebalancing)
    current_weights: Optional[Dict[str, float]] = None
    current_value: Optional[float] = None
    
    # Historical analysis parameters
    historical_period: str = "5Y"  # "1Y", "3Y", "5Y", "10Y"
    start_date: Optional[str] = None  # Override for specific dates
    end_date: Optional[str] = None
    
    # TAA Rules (for backtesting)
    taa_rules: Optional[List[TAARule]] = None
    rebalance_frequency: Optional[RebalanceFrequency] = None
    rebalance_threshold: float = 0.05  # 5% drift triggers rebalance
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "created_at": self.created_at.isoformat(),
            "universe": self.universe,
            "constraints": self.constraints.to_dict(),
            "optimization_method": self.optimization_method.value if self.optimization_method else None,
            "risk_free_rate": self.risk_free_rate,
            "current_weights": self.current_weights,
            "current_value": self.current_value,
            "historical_period": self.historical_period,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "taa_rules": [vars(r) for r in self.taa_rules] if self.taa_rules else None,
            "rebalance_frequency": self.rebalance_frequency.value if self.rebalance_frequency else None,
            "rebalance_threshold": self.rebalance_threshold,
            "metadata": self.metadata,
        }


@dataclass
class BacktestMetrics:
    """Metrics from a backtest simulation."""
    total_return: float
    cagr: float  # Compound Annual Growth Rate
    volatility: float  # Annualized
    sharpe_ratio: float
    sortino_ratio: Optional[float] = None
    max_drawdown: float = 0.0
    calmar_ratio: Optional[float] = None  # CAGR / Max Drawdown
    win_rate: Optional[float] = None  # % of positive periods
    
    # Trade statistics
    num_trades: int = 0
    num_rebalances: int = 0
    turnover: Optional[float] = None  # Average annual turnover
    
    # TAA specific
    taa_triggers: int = 0
    avg_time_in_taa: Optional[float] = None  # Days
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_return": f"{self.total_return:.2%}",
            "cagr": f"{self.cagr:.2%}",
            "volatility": f"{self.volatility:.2%}",
            "sharpe_ratio": f"{self.sharpe_ratio:.2f}",
            "sortino_ratio": f"{self.sortino_ratio:.2f}" if self.sortino_ratio else None,
            "max_drawdown": f"{self.max_drawdown:.2%}",
            "calmar_ratio": f"{self.calmar_ratio:.2f}" if self.calmar_ratio else None,
            "win_rate": f"{self.win_rate:.1%}" if self.win_rate else None,
            "num_trades": self.num_trades,
            "num_rebalances": self.num_rebalances,
            "turnover": f"{self.turnover:.1%}" if self.turnover else None,
            "taa_triggers": self.taa_triggers,
        }


@dataclass
class RiskDecomposition:
    """Risk contribution breakdown by asset."""
    # Total portfolio volatility
    portfolio_volatility: float
    
    # Risk contributions per asset (should sum to 1.0)
    risk_contributions: Dict[str, float]
    
    # Marginal risk contributions
    marginal_contributions: Optional[Dict[str, float]] = None
    
    # Standalone volatility per asset
    asset_volatilities: Optional[Dict[str, float]] = None
    
    # Correlation matrix (for interpretation)
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None


@dataclass
class PortfolioContext:
    """
    The portfolio a request is about, resolved once from the database.

    Returned by `load_portfolio_context`. An object rather than a tuple so that
    adding a field later does not break every call site — `cash_balance` was
    added after `tickers` and `holdings` and forced exactly that churn.

    `holdings`, `cash_balance` and `base_currency` are None for ad-hoc queries
    that name tickers without a portfolio. None means "no portfolio, so
    unknown"; it does not mean zero, and it does not mean dollars. A
    portfolio holding no cash reports 0.0. `base_currency` is the
    portfolio's own currency (expected_values.md D15), the one every figure
    about it is reported in. `ips_path` is the policy file the portfolio is
    checked against (DIRECTION.md Order 2, item 4), from its row, None
    without a portfolio: no portfolio, no policy.
    """
    tickers: List[str]
    holdings: Optional[List[Dict[str, Any]]] = None
    cash_balance: Optional[float] = None
    base_currency: Optional[str] = None
    ips_path: Optional[str] = None
    portfolio_id: Optional[int] = None


@dataclass
class PortfolioResult:
    """
    Standardized result from portfolio agents.
    
    This follows the "Hot Potato Principle" - it contains processed
    summaries ready for LLM consumption, not raw data.
    """
    # Identification
    agent_name: str
    task_id: str
    success: bool
    error_message: Optional[str] = None
    
    # Core outputs
    weights: Dict[str, float] = field(default_factory=dict)  # {"SPY": 0.6, "TLT": 0.3}
    expected_return: Optional[float] = None
    expected_volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    
    # Risk decomposition
    risk_decomposition: Optional[RiskDecomposition] = None
    
    # Backtest specific (optional)
    backtest_metrics: Optional[BacktestMetrics] = None
    
    # Efficient frontier points (for visualization)
    efficient_frontier: Optional[List[Dict[str, float]]] = None
    
    # Audit trail - CRITICAL for transparency
    optimization_method: Optional[str] = None  # "mean_variance", "risk_parity"
    constraints_applied: List[str] = field(default_factory=list)
    data_period: Optional[str] = None  # "2021-01-01 to 2026-01-01"
    calculation_timestamp: datetime = field(default_factory=datetime.now)
    
    # For LLM interpretation
    reasoning: str = ""
    confidence: float = 1.0  # 0-1 scale
    warnings: List[str] = field(default_factory=list)
    
    # NEW: For macro analysis results
    result_type: Optional[str] = None  # "optimization", "macro_analysis", "backtest"
    data: Optional[Dict[str, Any]] = None  # Generic data container
    message: Optional[str] = None  # Human-readable summary
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization and LLM consumption."""
        result = {
            "agent_name": self.agent_name,
            "task_id": self.task_id,
            "success": self.success,
            "weights": {k: f"{v:.2%}" for k, v in self.weights.items()} if self.weights else {},
            "expected_return": f"{self.expected_return:.2%}" if self.expected_return else None,
            "expected_volatility": f"{self.expected_volatility:.2%}" if self.expected_volatility else None,
            "sharpe_ratio": f"{self.sharpe_ratio:.2f}" if self.sharpe_ratio else None,
            "optimization_method": self.optimization_method,
            "constraints_applied": self.constraints_applied,
            "data_period": self.data_period,
            "calculation_timestamp": self.calculation_timestamp.isoformat(),
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "warnings": self.warnings,
        }
        
        if self.error_message:
            result["error_message"] = self.error_message
        
        if self.risk_decomposition:
            result["risk_contributions"] = {
                k: f"{v:.1%}" 
                for k, v in self.risk_decomposition.risk_contributions.items()
            }
        
        if self.backtest_metrics:
            result["backtest_metrics"] = self.backtest_metrics.to_dict()
        
        if self.result_type:
            result["result_type"] = self.result_type
        
        if self.data:
            result["data"] = self.data
        
        if self.message:
            result["message"] = self.message
        
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result
    
    def to_summary(self) -> str:
        """Generate human-readable summary for LLM."""
        lines = [
            f"Portfolio Result (Task: {self.task_id})",
            f"Status: {'✓ Success' if self.success else '✗ Failed'}",
        ]
        
        if not self.success:
            lines.append(f"Error: {self.error_message}")
            return "\n".join(lines)
        
        # For macro analysis
        if self.result_type == "macro_analysis" and self.message:
            lines.append(f"\n{self.message}")
            return "\n".join(lines)
        
        # For optimization
        if self.weights:
            lines.append(f"\nOptimal Weights:")
            for asset, weight in sorted(self.weights.items(), key=lambda x: -x[1]):
                lines.append(f"  {asset}: {weight:.1%}")
        
        if self.expected_return:
            lines.append(f"\nExpected Return: {self.expected_return:.2%}")
        if self.expected_volatility:
            lines.append(f"Expected Volatility: {self.expected_volatility:.2%}")
        if self.sharpe_ratio:
            lines.append(f"Sharpe Ratio: {self.sharpe_ratio:.2f}")
        
        if self.risk_decomposition:
            lines.append(f"\nRisk Contributions:")
            for asset, contrib in self.risk_decomposition.risk_contributions.items():
                lines.append(f"  {asset}: {contrib:.1%} of total risk")
        
        if self.warnings:
            lines.append(f"\n⚠️ Warnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        
        if self.optimization_method:
            lines.append(f"\nMethod: {self.optimization_method}")
        if self.data_period:
            lines.append(f"Data Period: {self.data_period}")
        
        return "\n".join(lines)


@dataclass
class CovarianceResult:
    """Result from covariance matrix calculation."""
    success: bool
    tickers: List[str]
    
    # Matrices as nested dicts (for JSON serialization)
    covariance_matrix: Optional[Dict[str, Dict[str, float]]] = None
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    
    # Per-asset metrics
    annualized_volatilities: Optional[Dict[str, float]] = None
    
    # Estimation details
    method: str = "sample"  # "sample", "shrinkage", "exponential"
    estimation_period: Optional[str] = None
    num_observations: int = 0
    
    # Quality metrics
    condition_number: Optional[float] = None  # High = unstable
    
    # Warnings
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM consumption."""
        return {
            "success": self.success,
            "tickers": self.tickers,
            "covariance_matrix": self.covariance_matrix,
            "correlation_matrix": self.correlation_matrix,
            "annualized_volatilities": {
                k: f"{v:.2%}" for k, v in (self.annualized_volatilities or {}).items()
            },
            "method": self.method,
            "estimation_period": self.estimation_period,
            "num_observations": self.num_observations,
            "condition_number": f"{self.condition_number:.1f}" if self.condition_number else None,
            "warnings": self.warnings,
            "error_message": self.error_message,
        }


@dataclass
class RegimeSignal:
    """Signal from macro/regime analysis."""
    regime: RegimeType
    confidence: float  # 0-1
    
    # Contributing factors
    fed_sentiment: Optional[float] = None  # -1 (dovish) to +1 (hawkish)
    vix_level: Optional[float] = None
    vix_percentile: Optional[float] = None  # vs 1Y history
    yield_curve_spread: Optional[float] = None  # 10Y - 2Y
    
    # Recommendations
    recommended_action: str = ""  # "reduce_equity", "increase_bonds", etc.
    taa_adjustment: Optional[Dict[str, float]] = None  # Suggested weight changes
    
    # Audit trail
    analysis_date: datetime = field(default_factory=datetime.now)
    sources: List[str] = field(default_factory=list)  # ["fed_minutes", "vix", "yield_curve"]


@dataclass
class RebalanceAnalysis:
    """Result from rebalance analysis."""
    should_rebalance: bool
    
    # Current state
    current_weights: Dict[str, float]
    target_weights: Dict[str, float]
    drift_by_asset: Dict[str, float]  # {"SPY": +0.08, "TLT": -0.05}
    max_drift: float
    
    # Cost analysis
    portfolio_value: float
    rebalance_amount: float  # Total amount to trade
    estimated_transaction_cost: float
    estimated_tax_impact: Optional[float] = None
    
    # Recommendations
    recommendation: str = ""  # "full_rebalance", "partial_rebalance", "no_action"
    trades_required: Optional[Dict[str, float]] = None  # {"SPY": -20000, "TLT": +15000}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "should_rebalance": self.should_rebalance,
            "current_weights": {k: f"{v:.1%}" for k, v in self.current_weights.items()},
            "target_weights": {k: f"{v:.1%}" for k, v in self.target_weights.items()},
            "drift_by_asset": {k: f"{v:+.1%}" for k, v in self.drift_by_asset.items()},
            "max_drift": f"{self.max_drift:.1%}",
            "portfolio_value": f"€{self.portfolio_value:,.0f}",
            "rebalance_amount": f"€{self.rebalance_amount:,.0f}",
            "estimated_transaction_cost": f"€{self.estimated_transaction_cost:,.0f}",
            "estimated_tax_impact": f"€{self.estimated_tax_impact:,.0f}" if self.estimated_tax_impact else None,
            "recommendation": self.recommendation,
        }