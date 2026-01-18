"""
SNIPPET: analytics/metrics.py
PURPOSE: Financial calculations engine (returns, volatility, Sharpe, drawdown, comparisons)
PATTERN: Hot Potato - Returns aggregated metrics, NEVER raw data
"""

class MetricsCalculator:
    """
    Pure calculation logic (NOT a tool - tools call this).
    All methods: Load DB data → Calculate → Return summary dict
    """
    
    # ========== COMMON PATTERN FOR ALL METHODS ==========
    # 1. Load prices: df = _load_prices_df(ticker, days) → pandas DataFrame
    # 2. Calculate: metrics = df['close'].pct_change().std() * sqrt(252)
    # 3. Return: {"success": True, "ticker": ticker, "metric_value": X, "interpretation": "..."}
    
    def _load_prices_df(self, ticker: str, days: int) -> pd.DataFrame:
        """
        DB → pandas DataFrame.
        Returns: DataFrame with ['date', 'open', 'high', 'low', 'close', 'volume']
        Pattern: Query Asset → Filter DailyPrice → Convert to DataFrame
        """
        session = get_session()
        asset = session.query(Asset).filter_by(ticker=ticker).first()
        prices = session.query(DailyPrice).filter(
            DailyPrice.asset_id == asset.id,
            DailyPrice.date >= (date.today() - timedelta(days=days))
        ).order_by(DailyPrice.date).all()
        
        df = pd.DataFrame([{'date': p.date, 'close': float(p.close), ...} for p in prices])
        return df.set_index('date')
    
    # ========== PUBLIC CALCULATION METHODS ==========
    
    def calculate_returns(self, ticker: str, days: int = 365) -> dict:
        """
        Total return & CAGR.
        Returns: {
            "success": True,
            "ticker": "AAPL",
            "period_days": 364,
            "total_return": 0.1363,           # 13.63%
            "total_return_pct": "13.63%",
            "cagr": 0.1289,                   # Annualized
            "first_price": 182.50,
            "last_price": 207.39,
            "data_points": 251
        }
        """
        df = self._load_prices_df(ticker, days)
        total_return = (df['close'][-1] - df['close'][0]) / df['close'][0]
        cagr = (df['close'][-1] / df['close'][0]) ** (365/len(df)) - 1
        return {"success": True, "total_return": total_return, "cagr": cagr, ...}
    
    def calculate_volatility(self, ticker: str, days: int = 365) -> dict:
        """
        Annualized volatility (std dev of returns).
        Returns: {"volatility": 0.22, "volatility_pct": "22%", "interpretation": "Moderate"}
        """
        df = self._load_prices_df(ticker, days)
        daily_vol = df['close'].pct_change().std()
        annual_vol = daily_vol * math.sqrt(252)
        return {"success": True, "volatility": annual_vol, ...}
    
    def calculate_sharpe_ratio(self, ticker: str, days: int = 365, risk_free_rate: float = 0.04) -> dict:
        """
        Risk-adjusted return = (return - risk_free) / volatility.
        Returns: {"sharpe_ratio": 1.25, "interpretation": "Good risk-adjusted returns"}
        """
        returns = self.calculate_returns(ticker, days)
        vol = self.calculate_volatility(ticker, days)
        sharpe = (returns['cagr'] - risk_free_rate) / vol['volatility']
        return {"success": True, "sharpe_ratio": sharpe, ...}
    
    def calculate_max_drawdown(self, ticker: str, days: int = 365) -> dict:
        """
        Worst peak-to-trough decline.
        Returns: {"max_drawdown": -0.18, "max_drawdown_pct": "-18%", "peak_date": "2024-06-15"}
        """
        df = self._load_prices_df(ticker, days)
        cumulative = (1 + df['close'].pct_change()).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_dd = drawdown.min()
        return {"success": True, "max_drawdown": max_dd, ...}
    
    def get_price_statistics(self, ticker: str, days: int = 30) -> dict:
        """
        Basic stats: min, max, avg, median, std.
        Returns: {"min": 180.50, "max": 210.30, "avg": 195.20, ...}
        """
        df = self._load_prices_df(ticker, days)
        return {"min": df['close'].min(), "max": df['close'].max(), "avg": df['close'].mean(), ...}
    
    def compare_stocks(self, tickers: List[str], days: int = 365) -> dict:
        """
        Side-by-side comparison of multiple stocks.
        Returns: {
            "tickers": ["AAPL", "MSFT", "GOOGL"],
            "comparison": [
                {"ticker": "AAPL", "return": 0.15, "volatility": 0.22, "sharpe": 1.2},
                {"ticker": "MSFT", "return": 0.18, "volatility": 0.20, "sharpe": 1.4},
                ...
            ]
        }
        """
        results = [self.calculate_returns(t, days) | self.calculate_volatility(t, days) 
                   for t in tickers]
        return {"success": True, "comparison": results}

# KEY PATTERN: HOT POTATO
# - Agent never sees 10,000 price rows
# - Only sees: {"return": 0.15, "volatility": 0.22, "sharpe": 1.2}
# - Calculations happen in Python (fast), not in LLM context
