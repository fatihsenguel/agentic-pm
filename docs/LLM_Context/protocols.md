# FILE: src/agents/protocols.py
# PURPOSE: Defines standard DTOs for Agent communication. Enforces "Hot Potato Principle" (Agents trade summaries, not raw data).

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

# --- ENUMS (Vocabulary) ---
class TaskType(Enum):
    OPTIMIZE = "optimize"
    BACKTEST = "backtest"
    ANALYZE_REGIME = "analyze_regime" # Macro analysis
    REBALANCE = "rebalance"

class OptimizationMethod(Enum):
    MEAN_VARIANCE = "mean_variance"
    RISK_PARITY = "risk_parity"
    MIN_VARIANCE = "min_variance"
    MAX_SHARPE = "max_sharpe"
    BLACK_LITTERMAN = "black_litterman"

class RegimeType(Enum):
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    NEUTRAL = "neutral"
    CRISIS = "crisis"
    RECOVERY = "recovery"

# --- INPUT STRUCTURES (RiskManager -> Agents) ---

@dataclass
class PortfolioConstraints:
    """Rules for optimization. All optional."""
    min_weight: float = 0.0
    max_weight: float = 1.0
    max_volatility: Optional[float] = None # e.g., 0.12 for 12%
    max_drawdown: Optional[float] = None
    asset_min_weights: Optional[Dict[str, float]] = None # {"SPY": 0.1}
    asset_max_weights: Optional[Dict[str, float]] = None
    long_only: bool = True

@dataclass
class TAARule:
    """
    Deterministic rules for Tactical Asset Allocation.
    LLM generates these; System executes them.
    Example: IF "VIX" > 25.0 THEN {"SPY": 0.4, "TLT": 0.6}
    """
    name: str
    condition: str      # Human readable
    indicator: str      # "VIX", "SMA_50"
    operator: str       # ">", "<"
    threshold: float
    target_weights: Dict[str, float]

@dataclass
class PortfolioTask:
    """
    Standard request object passed to Agents.
    """
    task_id: str
    task_type: TaskType
    universe: List[str]          # ["SPY", "TLT", "GLD"]
    constraints: PortfolioConstraints
    optimization_method: Optional[OptimizationMethod]
    
    # Context
    current_weights: Optional[Dict[str, float]] # For rebalancing
    historical_period: str = "5Y"
    
    # Logic
    taa_rules: Optional[List[TAARule]] # For backtesting rules

# --- OUTPUT STRUCTURES (Agents -> RiskManager) ---

@dataclass
class PortfolioResult:
    """
    Standard response. Contains SUMMARIES, not raw data lines.
    """
    success: bool
    agent_name: str
    
    # Quantitative Output
    weights: Dict[str, float]           # Optimal allocation
    expected_return: Optional[float]
    expected_volatility: Optional[float]
    sharpe_ratio: Optional[float]
    
    # Audit Trail (Critical for hallucinations prevention)
    optimization_method: str
    constraints_applied: List[str]
    
    # Qualitative Output (For LLM to explain to user)
    reasoning: str
    warnings: List[str]
    
    # Polymorphic Data (Specific agent results go here)
    backtest_metrics: Optional['BacktestMetrics']
    risk_decomposition: Optional['RiskDecomposition']
    data: Optional[Dict[str, Any]]      # Generic bucket

@dataclass
class RegimeSignal:
    """Output from MacroAgent."""
    regime: RegimeType
    confidence: float
    recommended_action: str
    taa_adjustment: Optional[Dict[str, float]]

@dataclass
class RebalanceAnalysis:
    """Output from RebalanceAgent."""
    should_rebalance: bool
    current_weights: Dict[str, float]
    target_weights: Dict[str, float]
    drift_by_asset: Dict[str, float]
    rebalance_amount: float
    estimated_transaction_cost: float
    trades_required: Dict[str, float]   # {"SPY": -200, "TLT": +100}