# src/portfolio_tool/analytics/metrics.py
"""
Layer 4: Analytics Engine - MetricsCalculator
==============================================

This is the "brain" that performs financial calculations.
It is NOT a tool - it's pure Python logic that tools can call.

Design Principles:
- Hot Potato: Returns aggregated results, not raw data
- SoC: Calculation logic separated from tool interface
- Testable: Pure functions with clear inputs/outputs

Usage:
    calc = MetricsCalculator()
    result = calc.calculate_returns("AAPL", days=365)
    # result = {"ticker": "AAPL", "total_return": 0.15, "cagr": 0.12, ...}
"""

import math
from datetime import date, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal

import pandas as pd
from sqlalchemy import func

from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.database_setup import get_session, DailyPrice, Asset


class MetricsCalculator:
    """
    Central class for all financial metric calculations.
    
    Each method:
    1. Loads data from DB into pandas DataFrame
    2. Performs calculations
    3. Returns a summary dict (Hot Potato principle)
    """
    
    # =============================================================================
    # INTERNAL HELPERS
    # =============================================================================
    
    def _get_session(self):
        """Get a fresh database session."""
        return get_session()
    
    def _get_asset(self, session, ticker: str) -> Optional[Asset]:
        """Find asset by ticker (case-insensitive)."""
        return session.query(Asset).filter(
            func.upper(Asset.ticker) == ticker.upper()
        ).first()
    
    def _load_prices_df(
        self, 
        ticker: str, 
        days: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[pd.DataFrame]:
        """
        Load price data from DB into a pandas DataFrame.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back (alternative to start_date)
            start_date: Start date for data range
            end_date: End date for data range (default: today)
            
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
            Sorted by date ascending. Returns None if no data found.
        """
        session = self._get_session()
        
        try:
            asset = self._get_asset(session, ticker)
            if not asset:
                return None
            
            # Build query
            query = session.query(DailyPrice).filter(DailyPrice.asset_id == asset.id)
            
            # Apply date filters
            if end_date is None:
                end_date = date.today()
            
            if days and not start_date:
                start_date = end_date - timedelta(days=days)
            
            if start_date:
                query = query.filter(DailyPrice.date >= start_date)
            if end_date:
                query = query.filter(DailyPrice.date <= end_date)
            
            # Execute and convert to DataFrame
            query = query.order_by(DailyPrice.date.asc())
            records = query.all()
            
            if not records:
                return None
            
            data = [{
                'date': r.date,
                'open': float(r.open) if r.open else None,
                'high': float(r.high) if r.high else None,
                'low': float(r.low) if r.low else None,
                'close': float(r.close) if r.close else None,
                'volume': r.volume
            } for r in records]
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
            
        finally:
            session.close()
    
    # =============================================================================
    # PUBLIC CALCULATION METHODS
    # =============================================================================
    
    def calculate_returns(
        self, 
        ticker: str, 
        days: int = 365,
        include_daily: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate return metrics for a stock.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to analyze (default: 365)
            include_daily: If True, include daily returns array (caution: large!)
            
        Returns:
            Dict with:
            - ticker: str
            - period_days: int
            - total_return: float (e.g., 0.15 for 15%)
            - cagr: float (Compound Annual Growth Rate)
            - first_price: float
            - last_price: float
            - first_date: str
            - last_date: str
        """
        df = self._load_prices_df(ticker, days=days)
        
        if df is None or len(df) < 2:
            return {
                "success": False,
                "ticker": ticker,
                "error": f"Insufficient data for {ticker}. Need at least 2 price records."
            }
        
        # Get first and last close prices
        first_price = df['close'].iloc[0]
        last_price = df['close'].iloc[-1]
        first_date = df.index[0]
        last_date = df.index[-1]
        
        # Total return
        total_return = (last_price - first_price) / first_price
        
        # CAGR (Compound Annual Growth Rate)
        actual_days = (last_date - first_date).days
        if actual_days > 0:
            years = actual_days / 365.25
            cagr = (last_price / first_price) ** (1 / years) - 1 if years > 0 else 0
        else:
            cagr = 0
        
        result = {
            "success": True,
            "ticker": ticker.upper(),
            "period_days": actual_days,
            "data_points": len(df),
            "total_return": round(total_return, 4),
            "total_return_pct": f"{total_return * 100:.2f}%",
            "cagr": round(cagr, 4),
            "cagr_pct": f"{cagr * 100:.2f}%",
            "first_price": round(first_price, 2),
            "last_price": round(last_price, 2),
            "first_date": first_date.strftime("%Y-%m-%d"),
            "last_date": last_date.strftime("%Y-%m-%d")
        }
        
        # Optional: include daily returns
        if include_daily:
            daily_returns = df['close'].pct_change().dropna()
            result["daily_returns"] = daily_returns.tolist()
        
        return result
    
    def calculate_volatility(
        self, 
        ticker: str, 
        days: int = 365,
        annualize: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate volatility (standard deviation of returns).
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to analyze
            annualize: If True, annualize the volatility (multiply by sqrt(252))
            
        Returns:
            Dict with:
            - ticker: str
            - volatility: float (annualized if annualize=True)
            - volatility_pct: str
            - daily_volatility: float
        """
        df = self._load_prices_df(ticker, days=days)
        
        if df is None or len(df) < 10:
            return {
                "success": False,
                "ticker": ticker,
                "error": f"Insufficient data for {ticker}. Need at least 10 price records."
            }
        
        # Calculate daily returns
        daily_returns = df['close'].pct_change().dropna()
        
        # Daily volatility (standard deviation)
        daily_vol = daily_returns.std()
        
        # Annualized volatility (252 trading days per year)
        annual_vol = daily_vol * math.sqrt(252) if annualize else daily_vol
        
        return {
            "success": True,
            "ticker": ticker.upper(),
            "period_days": days,
            "data_points": len(df),
            "volatility": round(annual_vol, 4),
            "volatility_pct": f"{annual_vol * 100:.2f}%",
            "daily_volatility": round(daily_vol, 6),
            "interpretation": self._interpret_volatility(annual_vol)
        }
    
    def _interpret_volatility(self, vol: float) -> str:
        """Provide human-readable interpretation of volatility."""
        if vol < 0.15:
            return "Low volatility (stable)"
        elif vol < 0.25:
            return "Moderate volatility"
        elif vol < 0.40:
            return "High volatility"
        else:
            return "Very high volatility (risky)"
    
    def calculate_sharpe_ratio(
        self, 
        ticker: str, 
        days: int = 365,
        risk_free_rate: float = 0.05
    ) -> Dict[str, Any]:
        """
        Calculate Sharpe Ratio (risk-adjusted return).
        
        Sharpe = (Return - Risk Free Rate) / Volatility
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to analyze
            risk_free_rate: Annual risk-free rate (default: 5%)
            
        Returns:
            Dict with sharpe_ratio and components
        """
        # Get returns
        returns_data = self.calculate_returns(ticker, days)
        if not returns_data.get("success"):
            return returns_data
        
        # Get volatility
        vol_data = self.calculate_volatility(ticker, days)
        if not vol_data.get("success"):
            return vol_data
        
        cagr = returns_data["cagr"]
        volatility = vol_data["volatility"]
        
        # Sharpe Ratio
        if volatility > 0:
            sharpe = (cagr - risk_free_rate) / volatility
        else:
            sharpe = 0
        
        return {
            "success": True,
            "ticker": ticker.upper(),
            "period_days": days,
            "sharpe_ratio": round(sharpe, 2),
            "return_cagr": returns_data["cagr"],
            "volatility": vol_data["volatility"],
            "risk_free_rate": risk_free_rate,
            "interpretation": self._interpret_sharpe(sharpe)
        }
    
    def _interpret_sharpe(self, sharpe: float) -> str:
        """Provide human-readable interpretation of Sharpe ratio."""
        if sharpe < 0:
            return "Negative (underperforming risk-free rate)"
        elif sharpe < 1:
            return "Below average risk-adjusted return"
        elif sharpe < 2:
            return "Good risk-adjusted return"
        elif sharpe < 3:
            return "Very good risk-adjusted return"
        else:
            return "Excellent risk-adjusted return"
    
    def calculate_max_drawdown(
        self, 
        ticker: str, 
        days: int = 365
    ) -> Dict[str, Any]:
        """
        Calculate Maximum Drawdown (largest peak-to-trough decline).
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to analyze
            
        Returns:
            Dict with max_drawdown and dates
        """
        df = self._load_prices_df(ticker, days=days)
        
        if df is None or len(df) < 2:
            return {
                "success": False,
                "ticker": ticker,
                "error": f"Insufficient data for {ticker}."
            }
        
        # Calculate running maximum
        rolling_max = df['close'].cummax()
        
        # Calculate drawdown
        drawdown = (df['close'] - rolling_max) / rolling_max
        
        # Find maximum drawdown
        max_dd = drawdown.min()
        max_dd_date = drawdown.idxmin()
        
        # Find the peak before the max drawdown
        peak_date = df.loc[:max_dd_date, 'close'].idxmax()
        peak_price = df.loc[peak_date, 'close']
        trough_price = df.loc[max_dd_date, 'close']
        
        return {
            "success": True,
            "ticker": ticker.upper(),
            "period_days": days,
            "max_drawdown": round(max_dd, 4),
            "max_drawdown_pct": f"{max_dd * 100:.2f}%",
            "peak_date": peak_date.strftime("%Y-%m-%d"),
            "peak_price": round(peak_price, 2),
            "trough_date": max_dd_date.strftime("%Y-%m-%d"),
            "trough_price": round(trough_price, 2),
            "interpretation": self._interpret_drawdown(max_dd)
        }
    
    def _interpret_drawdown(self, dd: float) -> str:
        """Provide human-readable interpretation of drawdown."""
        dd_abs = abs(dd)
        if dd_abs < 0.10:
            return "Minor drawdown (<10%)"
        elif dd_abs < 0.20:
            return "Moderate drawdown (10-20%)"
        elif dd_abs < 0.30:
            return "Significant drawdown (20-30%)"
        else:
            return "Severe drawdown (>30%)"
    
    def get_price_statistics(
        self, 
        ticker: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get basic price statistics.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days to analyze
            
        Returns:
            Dict with min, max, mean, median prices
        """
        df = self._load_prices_df(ticker, days=days)
        
        if df is None or len(df) == 0:
            return {
                "success": False,
                "ticker": ticker,
                "error": f"No data for {ticker}."
            }
        
        close_prices = df['close']
        
        return {
            "success": True,
            "ticker": ticker.upper(),
            "period_days": days,
            "data_points": len(df),
            "current_price": round(close_prices.iloc[-1], 2),
            "min_price": round(close_prices.min(), 2),
            "max_price": round(close_prices.max(), 2),
            "mean_price": round(close_prices.mean(), 2),
            "median_price": round(close_prices.median(), 2),
            "price_range": round(close_prices.max() - close_prices.min(), 2),
            "first_date": df.index[0].strftime("%Y-%m-%d"),
            "last_date": df.index[-1].strftime("%Y-%m-%d")
        }
    
    def compare_stocks(
        self, 
        tickers: List[str], 
        days: int = 365
    ) -> Dict[str, Any]:
        """
        Compare multiple stocks side by side.
        
        Args:
            tickers: List of ticker symbols
            days: Number of days to analyze
            
        Returns:
            Dict with comparison table
        """
        if not tickers or len(tickers) < 2:
            return {
                "success": False,
                "error": "Need at least 2 tickers to compare."
            }
        
        if len(tickers) > 10:
            return {
                "success": False,
                "error": "Maximum 10 tickers for comparison."
            }
        
        comparisons = []
        
        for ticker in tickers:
            returns = self.calculate_returns(ticker, days)
            vol = self.calculate_volatility(ticker, days)
            sharpe = self.calculate_sharpe_ratio(ticker, days)
            
            comparisons.append({
                "ticker": ticker.upper(),
                "total_return": returns.get("total_return_pct", "N/A"),
                "cagr": returns.get("cagr_pct", "N/A"),
                "volatility": vol.get("volatility_pct", "N/A"),
                "sharpe_ratio": sharpe.get("sharpe_ratio", "N/A"),
                "data_available": returns.get("success", False)
            })
        
        # Sort by total return (best first)
        comparisons.sort(
            key=lambda x: x.get("total_return", 0) if isinstance(x.get("total_return"), (int, float)) else -999,
            reverse=True
        )
        
        return {
            "success": True,
            "period_days": days,
            "comparison": comparisons,
            "best_return": comparisons[0]["ticker"] if comparisons else None,
            "lowest_volatility": min(comparisons, key=lambda x: float(x["volatility"].rstrip('%')) if x["volatility"] != "N/A" else 999)["ticker"]
        }
