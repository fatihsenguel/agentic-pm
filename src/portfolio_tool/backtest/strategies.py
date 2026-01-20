"""
Strategy Definitions for Backtesting.

This module defines:
- Strategy: Complete strategy specification
- TAARule: Tactical Asset Allocation rules (DETERMINISTIC)
- RebalanceRule: When and how to rebalance

⚠️ CRITICAL: All rules are DETERMINISTIC.
No randomness, no LLM, no external calls during evaluation.
Same market data = Same decision. Always.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import operator
import re

import pandas as pd
import numpy as np


class RebalanceFrequency(str, Enum):
    """When to check for rebalancing."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    NEVER = "never"  # Buy and hold


@dataclass
class TAARule:
    """
    Tactical Asset Allocation Rule.
    
    ⚠️ MUST be 100% DETERMINISTIC.
    The evaluate() method uses only:
    - The current date
    - Market data values (prices, VIX, etc.)
    - Pre-defined thresholds
    
    NO LLM, NO randomness, NO external calls.
    
    Example:
        rule = TAARule(
            name="VIX_Risk_Off",
            indicator="VIX",
            operator=">",
            threshold=25.0,
            target_weights={"SPY": 0.40, "TLT": 0.40, "CASH": 0.20}
        )
        
        # Evaluation is deterministic
        if rule.evaluate(market_data):
            # Apply target_weights
    """
    
    name: str
    indicator: str  # Column name in market data (e.g., "VIX", "SPY_SMA200")
    operator: str   # ">", "<", ">=", "<=", "==", "crosses_above", "crosses_below"
    threshold: float
    target_weights: Dict[str, float]
    
    # Optional: Rule priority (higher = checked first)
    priority: int = 0
    
    # Optional: Condition description for reporting
    description: Optional[str] = None
    
    # Operators mapping
    _OPERATORS = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
    }
    
    def __post_init__(self):
        """Validate rule after creation."""
        if self.operator not in self._OPERATORS and self.operator not in ["crosses_above", "crosses_below"]:
            raise ValueError(f"Invalid operator: {self.operator}")
        
        # Validate weights sum to ~1
        weight_sum = sum(self.target_weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            raise ValueError(f"Target weights must sum to 1.0, got {weight_sum}")
        
        if self.description is None:
            self.description = f"{self.indicator} {self.operator} {self.threshold}"
    
    def evaluate(self, value: float, previous_value: Optional[float] = None) -> bool:
        """
        Evaluate if rule triggers.
        
        ⚠️ This method is DETERMINISTIC.
        Same inputs = Same output. Always.
        
        Args:
            value: Current value of the indicator
            previous_value: Previous value (needed for crosses_above/below)
            
        Returns:
            True if rule triggers, False otherwise
        """
        if self.operator in self._OPERATORS:
            return self._OPERATORS[self.operator](value, self.threshold)
        
        elif self.operator == "crosses_above":
            if previous_value is None:
                return False
            return previous_value <= self.threshold < value
        
        elif self.operator == "crosses_below":
            if previous_value is None:
                return False
            return previous_value >= self.threshold > value
        
        return False
    
    def evaluate_with_data(
        self, 
        current_data: pd.Series, 
        previous_data: Optional[pd.Series] = None
    ) -> bool:
        """
        Evaluate rule using market data series.
        
        Args:
            current_data: Current day's market data
            previous_data: Previous day's data (for cross conditions)
            
        Returns:
            True if rule triggers
        """
        if self.indicator not in current_data.index:
            return False  # Indicator not available
        
        current_value = current_data[self.indicator]
        
        if pd.isna(current_value):
            return False
        
        previous_value = None
        if previous_data is not None and self.indicator in previous_data.index:
            previous_value = previous_data[self.indicator]
        
        return self.evaluate(float(current_value), previous_value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "indicator": self.indicator,
            "operator": self.operator,
            "threshold": self.threshold,
            "target_weights": self.target_weights,
            "description": self.description,
        }


@dataclass
class RebalanceRule:
    """
    Rebalancing rule specification.
    
    Determines when portfolio should be rebalanced:
    - Calendar-based (monthly, quarterly)
    - Drift-based (when weights deviate too much)
    - Or combination of both
    """
    
    frequency: RebalanceFrequency = RebalanceFrequency.QUARTERLY
    drift_threshold: float = 0.05  # Rebalance if any weight drifts >5%
    
    # Calendar settings
    rebalance_day: int = 1  # Day of month/quarter to rebalance
    
    # Minimum days between rebalances
    min_days_between: int = 20
    
    def should_rebalance(
        self,
        current_date: datetime,
        last_rebalance_date: Optional[datetime],
        current_weights: Dict[str, float],
        target_weights: Dict[str, float]
    ) -> Tuple[bool, str]:
        """
        Check if rebalancing should occur.
        
        Returns:
            Tuple of (should_rebalance, reason)
        """
        # Check minimum days
        if last_rebalance_date is not None:
            days_since = (current_date - last_rebalance_date).days
            if days_since < self.min_days_between:
                return False, "Too soon since last rebalance"
        
        # Check calendar
        calendar_trigger = self._check_calendar(current_date, last_rebalance_date)
        
        # Check drift
        drift_trigger, max_drift = self._check_drift(current_weights, target_weights)
        
        if drift_trigger:
            return True, f"Drift threshold exceeded: {max_drift:.1%}"
        
        if calendar_trigger:
            return True, f"Calendar rebalance: {self.frequency.value}"
        
        return False, "No rebalance needed"
    
    def _check_calendar(
        self, 
        current_date: datetime,
        last_rebalance: Optional[datetime]
    ) -> bool:
        """Check if calendar trigger is met."""
        if self.frequency == RebalanceFrequency.NEVER:
            return False
        
        if self.frequency == RebalanceFrequency.DAILY:
            return True
        
        if self.frequency == RebalanceFrequency.WEEKLY:
            return current_date.weekday() == 0  # Monday
        
        if self.frequency == RebalanceFrequency.MONTHLY:
            if last_rebalance is None:
                return current_date.day >= self.rebalance_day
            return (current_date.month != last_rebalance.month and 
                    current_date.day >= self.rebalance_day)
        
        if self.frequency == RebalanceFrequency.QUARTERLY:
            quarter_months = [1, 4, 7, 10]
            if current_date.month not in quarter_months:
                return False
            if last_rebalance is None:
                return current_date.day >= self.rebalance_day
            # Different quarter
            current_q = (current_date.month - 1) // 3
            last_q = (last_rebalance.month - 1) // 3
            return current_q != last_q and current_date.day >= self.rebalance_day
        
        if self.frequency == RebalanceFrequency.ANNUALLY:
            if last_rebalance is None:
                return current_date.month == 1 and current_date.day >= self.rebalance_day
            return (current_date.year != last_rebalance.year and 
                    current_date.month == 1 and 
                    current_date.day >= self.rebalance_day)
        
        return False
    
    def _check_drift(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float]
    ) -> Tuple[bool, float]:
        """Check if drift threshold is exceeded."""
        max_drift = 0.0
        
        for asset in target_weights:
            current = current_weights.get(asset, 0.0)
            target = target_weights[asset]
            drift = abs(current - target)
            max_drift = max(max_drift, drift)
        
        return max_drift > self.drift_threshold, max_drift


@dataclass
class Strategy:
    """
    Complete strategy definition.
    
    A strategy consists of:
    - Name and description
    - Initial/target weights
    - Rebalancing rules
    - TAA rules (optional)
    
    Example:
        strategy = Strategy(
            name="60/40 with VIX TAA",
            initial_weights={"SPY": 0.60, "TLT": 0.40},
            rebalance_rule=RebalanceRule(
                frequency=RebalanceFrequency.QUARTERLY,
                drift_threshold=0.05
            ),
            taa_rules=[
                TAARule(
                    name="VIX_Risk_Off",
                    indicator="VIX",
                    operator=">",
                    threshold=25.0,
                    target_weights={"SPY": 0.40, "TLT": 0.40, "CASH": 0.20}
                )
            ]
        )
    """
    
    name: str
    initial_weights: Dict[str, float]
    
    # Rebalancing
    rebalance_rule: RebalanceRule = field(default_factory=RebalanceRule)
    
    # TAA Rules (evaluated in priority order)
    taa_rules: List[TAARule] = field(default_factory=list)
    
    # Description
    description: Optional[str] = None
    
    # Benchmark for comparison
    benchmark: Optional[str] = None  # e.g., "SPY"
    
    def __post_init__(self):
        """Validate strategy."""
        # Validate initial weights
        weight_sum = sum(self.initial_weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            raise ValueError(f"Initial weights must sum to 1.0, got {weight_sum}")
        
        # Sort TAA rules by priority (highest first)
        if self.taa_rules:
            self.taa_rules = sorted(self.taa_rules, key=lambda r: -r.priority)
    
    @property
    def assets(self) -> List[str]:
        """Get list of assets in the strategy."""
        assets = set(self.initial_weights.keys())
        for rule in self.taa_rules:
            assets.update(rule.target_weights.keys())
        return sorted(list(assets))
    
    def get_target_weights(
        self,
        current_data: pd.Series,
        previous_data: Optional[pd.Series] = None
    ) -> Tuple[Dict[str, float], Optional[str]]:
        """
        Get target weights based on current market conditions.
        
        Evaluates TAA rules in priority order.
        Returns initial weights if no rules trigger.
        
        Returns:
            Tuple of (target_weights, triggered_rule_name)
        """
        for rule in self.taa_rules:
            if rule.evaluate_with_data(current_data, previous_data):
                return rule.target_weights, rule.name
        
        return self.initial_weights, None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "initial_weights": self.initial_weights,
            "rebalance_frequency": self.rebalance_rule.frequency.value,
            "drift_threshold": self.rebalance_rule.drift_threshold,
            "taa_rules": [r.to_dict() for r in self.taa_rules],
            "benchmark": self.benchmark,
        }


# =============================================================================
# Pre-built Strategy Templates
# =============================================================================

def create_buy_and_hold_strategy(
    weights: Dict[str, float],
    name: str = "Buy and Hold"
) -> Strategy:
    """Create a simple buy-and-hold strategy."""
    return Strategy(
        name=name,
        initial_weights=weights,
        rebalance_rule=RebalanceRule(frequency=RebalanceFrequency.NEVER),
        taa_rules=[],
    )


def create_sixty_forty_strategy(
    equity_ticker: str = "SPY",
    bond_ticker: str = "TLT",
    rebalance_frequency: RebalanceFrequency = RebalanceFrequency.QUARTERLY
) -> Strategy:
    """Create classic 60/40 portfolio strategy."""
    return Strategy(
        name="60/40 Portfolio",
        description=f"Classic 60% {equity_ticker}, 40% {bond_ticker}",
        initial_weights={equity_ticker: 0.60, bond_ticker: 0.40},
        rebalance_rule=RebalanceRule(
            frequency=rebalance_frequency,
            drift_threshold=0.05
        ),
        benchmark=equity_ticker,
    )


def create_risk_parity_strategy(
    tickers: List[str],
    weights: Dict[str, float],
    rebalance_frequency: RebalanceFrequency = RebalanceFrequency.MONTHLY
) -> Strategy:
    """Create a risk parity strategy with given weights."""
    return Strategy(
        name="Risk Parity",
        description="Equal risk contribution portfolio",
        initial_weights=weights,
        rebalance_rule=RebalanceRule(
            frequency=rebalance_frequency,
            drift_threshold=0.03  # Tighter threshold for risk parity
        ),
    )


def create_tactical_strategy(
    base_weights: Dict[str, float],
    taa_rules: List[TAARule],
    name: str = "Tactical Strategy",
    rebalance_frequency: RebalanceFrequency = RebalanceFrequency.MONTHLY
) -> Strategy:
    """Create a tactical strategy with TAA rules."""
    return Strategy(
        name=name,
        initial_weights=base_weights,
        rebalance_rule=RebalanceRule(
            frequency=rebalance_frequency,
            drift_threshold=0.05
        ),
        taa_rules=taa_rules,
    )
