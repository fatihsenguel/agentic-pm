# FILE: src/portfolio_tool/tools/rebalance_tools.py
# PURPOSE: Deterministic math for portfolio rebalancing.
# PRINCIPLE: Pure functions. No LLM "guessing". Reproducible results.

@dataclass
class RebalanceConfig:
    """Settings for rebalancing logic."""
    drift_threshold_percent: float = 5.0  # e.g., if SPY is 45% vs 40% target -> Rebalance
    transaction_cost_bps: float = 10.0    # 0.10%
    min_trade_value: float = 100.0        # Avoid tiny trades
    tax_loss_harvesting: bool = True

@dataclass
class RebalanceResult:
    """
    Complete audit trail of the rebalancing decision.
    """
    should_rebalance: bool
    recommendation: str               # "full_rebalance", "no_action"
    current_weights: Dict[str, float]
    target_weights: Dict[str, float]
    drift_by_asset: Dict[str, float]  # {"SPY": +0.05}
    trades: List['Trade']             # The specific BUY/SELL orders
    total_transaction_cost: float
    break_even_drift: float           # Is the trade worth the cost?

def calculate_drift(current_weights: Dict[str, float], target_weights: Dict[str, float]) -> Dict[str, float]:
    """Pure math: Current - Target."""
    pass

def generate_trades(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
    portfolio_value: float,
    prices: Dict[str, float],
    config: RebalanceConfig
) -> List['Trade']:
    """
    Calculates exact number of shares to Buy/Sell.
    Logic:
      1. Calculate drift
      2. If drift > threshold:
         - Calculate trade value ($)
         - Calculate shares (Value / Price)
         - Calculate costs (Transaction + Tax)
    Returns: List of Trade objects (Action, Ticker, Shares)
    """
    pass

def analyze_rebalance(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
    portfolio_value: float,
    prices: Dict[str, float],
    config: Optional[RebalanceConfig] = None
) -> RebalanceResult:
    """
    The Main Entry Point.
    Orchestrates the entire analysis: Drift -> Decision -> Trades -> Costs -> Break-even.
    Returns a fully populated RebalanceResult.
    """
    pass

# --- AGENT TOOLS (Wrappers for LLM) ---

def analyze_rebalance_tool(
    current_weights: str, # JSON String
    target_weights: str,  # JSON String
    portfolio_value: float,
    prices: str           # JSON String
) -> Dict[str, Any]:
    """
    Agent-facing tool that wraps analyze_rebalance.
    Takes JSON strings (LLM friendly) and returns structured Dict.
    """
    pass