"""
Rebalancing Tools for Quant Portfolio Manager.

This module provides PURE MATHEMATICAL tools for portfolio rebalancing.

⚠️ CRITICAL: NO LLM INVOLVEMENT IN ANY CALCULATION
All functions are deterministic. Same inputs = Same outputs. Always.
This is essential for:
- Compliance / Audit requirements
- Reproducibility
- Regulatory approval

The tools calculate:
- Portfolio drift (current vs target weights)
- Required trades to rebalance
- Transaction costs estimation
- Tax impact estimation (simplified)
- Rebalancing recommendations

Design Principles:
- Pure functions (no side effects)
- All calculations are transparent and auditable
- Results include full breakdown for compliance
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, ROUND_HALF_UP
import math


# ==================== CONFIGURATION ====================

@dataclass
class RebalanceConfig:
    """
    Configuration for rebalancing calculations.
    
    All thresholds are configurable for different client needs.
    """
    # Drift thresholds
    drift_threshold_percent: float = 5.0  # Trigger rebalance if any asset drifts > 5%
    min_drift_for_partial: float = 2.0    # Minimum drift to include in partial rebalance
    
    # Transaction costs (in basis points)
    transaction_cost_bps: float = 10.0    # 0.10% per trade (round trip)
    min_transaction_cost: float = 5.0     # Minimum €5 per trade
    
    # Tax settings (simplified)
    capital_gains_rate: float = 0.25      # 25% capital gains tax
    tax_loss_harvesting: bool = True      # Consider tax loss harvesting
    
    # Trade constraints
    min_trade_value: float = 100.0        # Don't trade less than €100
    round_to_shares: bool = False         # Round to whole shares (if prices provided)
    
    # Currency
    currency_symbol: str = "€"


# Default configuration
DEFAULT_CONFIG = RebalanceConfig()


# ==================== DATA CLASSES ====================

@dataclass
class Position:
    """Single position in a portfolio."""
    ticker: str
    shares: float
    current_price: float
    cost_basis: Optional[float] = None  # Average cost per share
    
    @property
    def market_value(self) -> float:
        """Current market value of position."""
        return self.shares * self.current_price
    
    @property
    def unrealized_gain(self) -> Optional[float]:
        """Unrealized gain/loss if cost basis known."""
        if self.cost_basis is None:
            return None
        return (self.current_price - self.cost_basis) * self.shares
    
    @property
    def unrealized_gain_percent(self) -> Optional[float]:
        """Unrealized gain/loss as percentage."""
        if self.cost_basis is None or self.cost_basis == 0:
            return None
        return (self.current_price - self.cost_basis) / self.cost_basis


@dataclass
class Portfolio:
    """Current portfolio state."""
    positions: Dict[str, Position]  # ticker -> Position
    cash: float = 0.0
    
    @property
    def total_value(self) -> float:
        """Total portfolio value including cash."""
        return sum(p.market_value for p in self.positions.values()) + self.cash
    
    @property
    def weights(self) -> Dict[str, float]:
        """Current weights by ticker."""
        total = self.total_value
        if total == 0:
            return {}
        
        weights = {
            ticker: pos.market_value / total 
            for ticker, pos in self.positions.items()
        }
        
        # Add cash weight if significant
        if self.cash > 0:
            weights["CASH"] = self.cash / total
        
        return weights


@dataclass
class Trade:
    """Single trade to execute."""
    ticker: str
    action: str  # "BUY" or "SELL"
    shares: float
    estimated_price: float
    trade_value: float
    
    # Cost estimates
    transaction_cost: float = 0.0
    estimated_tax: float = 0.0  # Only for sells with gains
    
    # Metadata
    reason: str = ""  # "rebalance", "tax_loss_harvest", etc.
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ticker": self.ticker,
            "action": self.action,
            "shares": round(self.shares, 4),
            "estimated_price": round(self.estimated_price, 2),
            "trade_value": round(self.trade_value, 2),
            "transaction_cost": round(self.transaction_cost, 2),
            "estimated_tax": round(self.estimated_tax, 2),
            "reason": self.reason,
        }


@dataclass
class RebalanceResult:
    """
    Complete result of rebalancing analysis.
    
    This is the main output - fully auditable and transparent.
    """
    # Decision
    should_rebalance: bool
    recommendation: str  # "full_rebalance", "partial_rebalance", "no_action", "tax_loss_harvest"
    
    # Portfolio state
    portfolio_value: float
    current_weights: Dict[str, float]
    target_weights: Dict[str, float]
    
    # Drift analysis
    drift_by_asset: Dict[str, float]  # Signed drift (+ = overweight, - = underweight)
    max_drift: float
    avg_drift: float
    
    # Trade list
    trades: List[Trade]
    total_trade_value: float  # Sum of absolute trade values
    turnover: float  # As percentage of portfolio
    
    # Cost analysis
    total_transaction_cost: float
    total_estimated_tax: float
    net_cost: float  # Total cost of rebalancing
    cost_as_percent: float  # Cost as % of portfolio
    
    # Break-even analysis
    break_even_drift: float  # Drift at which rebalancing becomes worthwhile
    
    # Metadata
    config_used: RebalanceConfig
    calculation_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        cfg = self.config_used
        return {
            "decision": {
                "should_rebalance": self.should_rebalance,
                "recommendation": self.recommendation,
            },
            "portfolio": {
                "total_value": f"{cfg.currency_symbol}{self.portfolio_value:,.2f}",
                "current_weights": {k: f"{v:.2%}" for k, v in self.current_weights.items()},
                "target_weights": {k: f"{v:.2%}" for k, v in self.target_weights.items()},
            },
            "drift_analysis": {
                "drift_by_asset": {k: f"{v:+.2%}" for k, v in self.drift_by_asset.items()},
                "max_drift": f"{self.max_drift:.2%}",
                "avg_drift": f"{self.avg_drift:.2%}",
                "threshold": f"{cfg.drift_threshold_percent:.1f}%",
            },
            "trades": [t.to_dict() for t in self.trades],
            "trade_summary": {
                "num_trades": len(self.trades),
                "total_trade_value": f"{cfg.currency_symbol}{self.total_trade_value:,.2f}",
                "turnover": f"{self.turnover:.2%}",
            },
            "costs": {
                "transaction_costs": f"{cfg.currency_symbol}{self.total_transaction_cost:,.2f}",
                "estimated_taxes": f"{cfg.currency_symbol}{self.total_estimated_tax:,.2f}",
                "total_cost": f"{cfg.currency_symbol}{self.net_cost:,.2f}",
                "cost_percent": f"{self.cost_as_percent:.3%}",
            },
            "break_even": {
                "break_even_drift": f"{self.break_even_drift:.2%}",
                "note": "Rebalancing is cost-effective when drift exceeds this threshold"
            },
            "audit": {
                "calculation_timestamp": self.calculation_timestamp.isoformat(),
                "config": {
                    "drift_threshold": f"{cfg.drift_threshold_percent}%",
                    "transaction_cost_bps": cfg.transaction_cost_bps,
                    "capital_gains_rate": f"{cfg.capital_gains_rate:.0%}",
                }
            }
        }
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        cfg = self.config_used
        lines = [
            "=" * 60,
            "REBALANCING ANALYSIS",
            "=" * 60,
            "",
            f"📊 PORTFOLIO VALUE: {cfg.currency_symbol}{self.portfolio_value:,.2f}",
            "",
            "📈 DRIFT ANALYSIS:",
        ]
        
        for ticker, drift in sorted(self.drift_by_asset.items(), key=lambda x: abs(x[1]), reverse=True):
            status = "⬆️ OVER" if drift > 0 else "⬇️ UNDER" if drift < 0 else "✓"
            lines.append(f"   {ticker}: {drift:+.2%} ({status})")
        
        lines.extend([
            "",
            f"   Max Drift: {self.max_drift:.2%} (Threshold: {cfg.drift_threshold_percent}%)",
            "",
            f"🎯 RECOMMENDATION: {self.recommendation.upper()}",
            f"   Should Rebalance: {'YES ✓' if self.should_rebalance else 'NO ✗'}",
        ])
        
        if self.trades:
            lines.extend([
                "",
                "📋 TRADE LIST:",
            ])
            for trade in self.trades:
                lines.append(
                    f"   {trade.action} {trade.shares:.2f} {trade.ticker} "
                    f"@ {cfg.currency_symbol}{trade.estimated_price:.2f} "
                    f"= {cfg.currency_symbol}{abs(trade.trade_value):,.2f}"
                )
        
        lines.extend([
            "",
            "💰 COST ANALYSIS:",
            f"   Transaction Costs: {cfg.currency_symbol}{self.total_transaction_cost:,.2f}",
            f"   Estimated Taxes:   {cfg.currency_symbol}{self.total_estimated_tax:,.2f}",
            f"   Total Cost:        {cfg.currency_symbol}{self.net_cost:,.2f} ({self.cost_as_percent:.3%})",
            "",
            f"📐 BREAK-EVEN: Drift > {self.break_even_drift:.2%} makes rebalancing worthwhile",
            "",
            "=" * 60,
        ])
        
        return "\n".join(lines)


# ==================== CORE CALCULATION FUNCTIONS ====================

def calculate_drift(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate drift between current and target weights.
    
    PURE MATH - No LLM involvement.
    
    Args:
        current_weights: Current portfolio weights (must sum to ~1.0)
        target_weights: Target portfolio weights (must sum to ~1.0)
    
    Returns:
        Dict of drift per asset (positive = overweight, negative = underweight)
    
    Example:
        current = {"SPY": 0.65, "TLT": 0.25, "GLD": 0.10}
        target  = {"SPY": 0.60, "TLT": 0.30, "GLD": 0.10}
        drift   = {"SPY": +0.05, "TLT": -0.05, "GLD": 0.00}
    """
    # Get all tickers
    all_tickers = set(current_weights.keys()) | set(target_weights.keys())
    
    drift = {}
    for ticker in all_tickers:
        current = current_weights.get(ticker, 0.0)
        target = target_weights.get(ticker, 0.0)
        drift[ticker] = current - target
    
    return drift


def calculate_max_drift(drift: Dict[str, float]) -> float:
    """
    Calculate maximum absolute drift.
    
    Args:
        drift: Drift by asset from calculate_drift()
    
    Returns:
        Maximum absolute drift value
    """
    if not drift:
        return 0.0
    return max(abs(d) for d in drift.values())


def calculate_avg_drift(drift: Dict[str, float]) -> float:
    """
    Calculate average absolute drift.
    
    Args:
        drift: Drift by asset from calculate_drift()
    
    Returns:
        Average absolute drift
    """
    if not drift:
        return 0.0
    return sum(abs(d) for d in drift.values()) / len(drift)


def should_rebalance(
    drift: Dict[str, float],
    threshold_percent: float = 5.0
) -> Tuple[bool, str]:
    """
    Determine if portfolio should be rebalanced.
    
    PURE MATH - No LLM involvement.
    
    Args:
        drift: Drift by asset
        threshold_percent: Trigger threshold (e.g., 5.0 = 5%)
    
    Returns:
        Tuple of (should_rebalance, recommendation)
    """
    max_drift = calculate_max_drift(drift)
    threshold = threshold_percent / 100.0
    
    if max_drift >= threshold:
        # Check how many assets need rebalancing
        assets_over_threshold = sum(1 for d in drift.values() if abs(d) >= threshold)
        
        if assets_over_threshold >= len(drift) / 2:
            return True, "full_rebalance"
        else:
            return True, "partial_rebalance"
    
    # Check if close to threshold (warning zone)
    if max_drift >= threshold * 0.8:
        return False, "monitor_closely"
    
    return False, "no_action"


def generate_trades(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
    portfolio_value: float,
    prices: Dict[str, float],
    config: RebalanceConfig = DEFAULT_CONFIG,
    cost_basis: Optional[Dict[str, float]] = None,
) -> List[Trade]:
    """
    Generate list of trades needed to rebalance.
    
    PURE MATH - No LLM involvement.
    
    Args:
        current_weights: Current portfolio weights
        target_weights: Target portfolio weights
        portfolio_value: Total portfolio value
        prices: Current prices per ticker
        config: Rebalancing configuration
        cost_basis: Optional cost basis per ticker for tax calculation
    
    Returns:
        List of Trade objects
    """
    trades = []
    drift = calculate_drift(current_weights, target_weights)
    
    for ticker, ticker_drift in drift.items():
        # Skip if drift is too small
        if abs(ticker_drift) < config.min_drift_for_partial / 100.0:
            continue
        
        # Calculate trade value
        trade_value = ticker_drift * portfolio_value  # Positive = sell, Negative = buy
        
        # Skip if trade value is below minimum
        if abs(trade_value) < config.min_trade_value:
            continue
        
        # Get price
        price = prices.get(ticker, 0)
        if price <= 0:
            continue
        
        # Calculate shares
        shares = abs(trade_value) / price
        
        # Round to whole shares if configured
        if config.round_to_shares:
            shares = math.floor(shares) if trade_value > 0 else math.ceil(shares)
            trade_value = shares * price
        
        # Determine action
        action = "SELL" if trade_value > 0 else "BUY"
        
        # Calculate transaction cost
        transaction_cost = max(
            abs(trade_value) * (config.transaction_cost_bps / 10000.0),
            config.min_transaction_cost
        )
        
        # Calculate tax impact (only for sells with gains)
        estimated_tax = 0.0
        if action == "SELL" and cost_basis and ticker in cost_basis:
            basis = cost_basis[ticker]
            if price > basis:
                gain_per_share = price - basis
                total_gain = gain_per_share * shares
                estimated_tax = total_gain * config.capital_gains_rate
        
        trades.append(Trade(
            ticker=ticker,
            action=action,
            shares=shares,
            estimated_price=price,
            trade_value=abs(trade_value) if action == "BUY" else -abs(trade_value),
            transaction_cost=transaction_cost,
            estimated_tax=estimated_tax,
            reason="rebalance"
        ))
    
    # Sort by absolute trade value (largest first)
    trades.sort(key=lambda t: abs(t.trade_value), reverse=True)
    
    return trades


def calculate_rebalance_costs(trades: List[Trade]) -> Tuple[float, float, float]:
    """
    Calculate total rebalancing costs.
    
    Args:
        trades: List of trades
    
    Returns:
        Tuple of (transaction_costs, tax_costs, total_costs)
    """
    transaction_costs = sum(t.transaction_cost for t in trades)
    tax_costs = sum(t.estimated_tax for t in trades)
    total_costs = transaction_costs + tax_costs
    
    return transaction_costs, tax_costs, total_costs


def calculate_break_even_drift(
    portfolio_value: float,
    transaction_cost_bps: float = 10.0,
    expected_tracking_error_reduction: float = 0.5
) -> float:
    """
    Calculate break-even drift threshold.
    
    The idea: Rebalancing is worthwhile when the expected benefit
    (reduced tracking error) exceeds the cost.
    
    Simplified model:
    - Cost = transaction costs
    - Benefit = drift reduction * expected return improvement
    
    Args:
        portfolio_value: Total portfolio value
        transaction_cost_bps: Transaction cost in basis points
        expected_tracking_error_reduction: Expected improvement factor
    
    Returns:
        Break-even drift as decimal (e.g., 0.03 = 3%)
    """
    # Simplified: break-even when cost ~ expected tracking error
    # This is a heuristic - real calculation would need more inputs
    cost_percent = transaction_cost_bps / 10000.0
    
    # Rule of thumb: break-even drift ≈ 2x transaction cost
    return cost_percent * 2 / expected_tracking_error_reduction


# ==================== MAIN ANALYSIS FUNCTION ====================

def analyze_rebalance(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
    portfolio_value: float,
    prices: Dict[str, float],
    config: Optional[RebalanceConfig] = None,
    cost_basis: Optional[Dict[str, float]] = None,
) -> RebalanceResult:
    """
    Complete rebalancing analysis.
    
    ⚠️ PURE MATH - No LLM involvement. Fully deterministic.
    
    This is the main entry point for rebalancing analysis.
    
    Args:
        current_weights: Current portfolio weights
        target_weights: Target/optimal weights
        portfolio_value: Total portfolio value
        prices: Current prices per ticker
        config: Optional configuration (uses defaults if not provided)
        cost_basis: Optional cost basis for tax calculation
    
    Returns:
        RebalanceResult with complete analysis
    
    Example:
        result = analyze_rebalance(
            current_weights={"SPY": 0.65, "TLT": 0.25, "GLD": 0.10},
            target_weights={"SPY": 0.60, "TLT": 0.30, "GLD": 0.10},
            portfolio_value=100000,
            prices={"SPY": 450, "TLT": 95, "GLD": 180}
        )
        
        print(result.to_summary())
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    # Step 1: Calculate drift
    drift = calculate_drift(current_weights, target_weights)
    max_drift = calculate_max_drift(drift)
    avg_drift = calculate_avg_drift(drift)
    
    # Step 2: Determine if rebalancing is needed
    should_reb, recommendation = should_rebalance(drift, config.drift_threshold_percent)
    
    # Step 3: Generate trades
    trades = generate_trades(
        current_weights=current_weights,
        target_weights=target_weights,
        portfolio_value=portfolio_value,
        prices=prices,
        config=config,
        cost_basis=cost_basis
    )
    
    # Step 4: Calculate costs
    transaction_costs, tax_costs, total_costs = calculate_rebalance_costs(trades)
    
    # Step 5: Calculate trade summary
    total_trade_value = sum(abs(t.trade_value) for t in trades)
    turnover = total_trade_value / portfolio_value if portfolio_value > 0 else 0
    cost_percent = total_costs / portfolio_value if portfolio_value > 0 else 0
    
    # Step 6: Calculate break-even
    break_even = calculate_break_even_drift(portfolio_value, config.transaction_cost_bps)
    
    # Step 7: Refine recommendation based on costs
    if should_reb and cost_percent > 0.01:  # >1% cost
        recommendation = "partial_rebalance"  # Suggest partial to reduce costs
    
    if max_drift < break_even and should_reb:
        # Drift is below break-even - rebalancing may not be cost-effective
        should_reb = False
        recommendation = "below_break_even"
    
    return RebalanceResult(
        should_rebalance=should_reb,
        recommendation=recommendation,
        portfolio_value=portfolio_value,
        current_weights=current_weights,
        target_weights=target_weights,
        drift_by_asset=drift,
        max_drift=max_drift,
        avg_drift=avg_drift,
        trades=trades,
        total_trade_value=total_trade_value,
        turnover=turnover,
        total_transaction_cost=transaction_costs,
        total_estimated_tax=tax_costs,
        net_cost=total_costs,
        cost_as_percent=cost_percent,
        break_even_drift=break_even,
        config_used=config,
    )


# ==================== AGENT-READY TOOL WRAPPERS ====================

def analyze_rebalance_tool(
    current_weights: str,  # JSON string: '{"SPY": 0.65, "TLT": 0.25}'
    target_weights: str,   # JSON string
    portfolio_value: float,
    prices: str,           # JSON string
    drift_threshold: float = 5.0,
    transaction_cost_bps: float = 10.0,
) -> Dict[str, Any]:
    """
    Agent-ready wrapper for rebalancing analysis.
    
    Accepts JSON strings for compatibility with LLM tool calls.
    
    Args:
        current_weights: Current weights as JSON string
        target_weights: Target weights as JSON string
        portfolio_value: Total portfolio value
        prices: Current prices as JSON string
        drift_threshold: Rebalance trigger threshold (%)
        transaction_cost_bps: Transaction cost in basis points
    
    Returns:
        Complete analysis as dictionary
    """
    import json
    
    try:
        current = json.loads(current_weights) if isinstance(current_weights, str) else current_weights
        target = json.loads(target_weights) if isinstance(target_weights, str) else target_weights
        price_dict = json.loads(prices) if isinstance(prices, str) else prices
        
        config = RebalanceConfig(
            drift_threshold_percent=drift_threshold,
            transaction_cost_bps=transaction_cost_bps,
        )
        
        result = analyze_rebalance(
            current_weights=current,
            target_weights=target,
            portfolio_value=portfolio_value,
            prices=price_dict,
            config=config,
        )
        
        return {
            "success": True,
            **result.to_dict(),
            "summary": result.to_summary(),
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def calculate_drift_tool(
    current_weights: str,
    target_weights: str,
) -> Dict[str, Any]:
    """
    Agent-ready tool to calculate portfolio drift.
    
    Args:
        current_weights: Current weights as JSON
        target_weights: Target weights as JSON
    
    Returns:
        Drift analysis
    """
    import json
    
    try:
        current = json.loads(current_weights) if isinstance(current_weights, str) else current_weights
        target = json.loads(target_weights) if isinstance(target_weights, str) else target_weights
        
        drift = calculate_drift(current, target)
        max_drift = calculate_max_drift(drift)
        should_reb, rec = should_rebalance(drift)
        
        return {
            "success": True,
            "drift_by_asset": {k: f"{v:+.2%}" for k, v in drift.items()},
            "max_drift": f"{max_drift:.2%}",
            "should_rebalance": should_reb,
            "recommendation": rec,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def generate_trade_list_tool(
    current_weights: str,
    target_weights: str,
    portfolio_value: float,
    prices: str,
) -> Dict[str, Any]:
    """
    Agent-ready tool to generate trade list.
    
    Args:
        current_weights: Current weights as JSON
        target_weights: Target weights as JSON
        portfolio_value: Portfolio value
        prices: Current prices as JSON
    
    Returns:
        Trade list
    """
    import json
    
    try:
        current = json.loads(current_weights) if isinstance(current_weights, str) else current_weights
        target = json.loads(target_weights) if isinstance(target_weights, str) else target_weights
        price_dict = json.loads(prices) if isinstance(prices, str) else prices
        
        trades = generate_trades(
            current_weights=current,
            target_weights=target,
            portfolio_value=portfolio_value,
            prices=price_dict,
        )
        
        return {
            "success": True,
            "num_trades": len(trades),
            "trades": [t.to_dict() for t in trades],
            "total_value": sum(abs(t.trade_value) for t in trades),
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# ==================== CONVENIENCE FUNCTIONS ====================

def quick_drift_check(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
    threshold: float = 5.0
) -> str:
    """
    Quick one-line drift check.
    
    Returns human-readable status.
    """
    drift = calculate_drift(current_weights, target_weights)
    max_drift = calculate_max_drift(drift)
    should_reb, rec = should_rebalance(drift, threshold)
    
    if should_reb:
        return f"⚠️ REBALANCE NEEDED: Max drift {max_drift:.1%} exceeds {threshold}% threshold"
    else:
        return f"✓ Portfolio OK: Max drift {max_drift:.1%} within {threshold}% threshold"
