# FILE: src/agents/data_agent.py
# PURPOSE: Fetches market data & computes risk metrics.
# ARCHITECTURE: Uses DataManager for DB access, Quant module for math. No direct API calls.

class DataAgent(BaseAgent):
    """
    Capabilities:
    - Fetch Prices (writes to DB)
    - Calculate Covariance/Correlation (reads from DB -> Cache -> Math)
    - Calculate Returns & Volatility
    """
    def __init__(self, config):
        self._prices_df_cache = {} # In-memory cache to avoid DB spam

    async def process(self, state: AgentState) -> AgentState:
        """
        Handles TaskType.OPTIMIZE or TaskType.CALCULATE_RISK.
        1. Fetches prices for universe (e.g. "SPY,TLT").
        2. Calculates Covariance Matrix.
        3. Stores result in state.sub_results['DataAgent'].
        """
        pass

    # --- TOOLS ---
    def fetch_prices_tool(self, tickers: str, period: str = "5Y") -> Dict:
        """Ensures data exists in DB, returns summary stats (not raw rows)."""
        pass

    def calculate_covariance_tool(self, tickers: str, method: str = "shrinkage") -> Dict:
        """Computes Covariance Matrix from cached prices."""
        pass

    def get_risk_metrics_tool(self, tickers: str, weights: Optional[str]) -> Dict:
        """Calculates Volatility, Sharpe, VaR."""
        pass
