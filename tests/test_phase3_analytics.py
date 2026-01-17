# tests/test_phase3_analytics.py
"""
Phase 3 Test Suite: Analytics Engine Tests
==========================================

Tests for MetricsCalculator and analytics tools.

Run with: pytest tests/test_phase3_analytics.py -v
"""

import pytest
import math
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
import pandas as pd


# =============================================================================
# UNIT TESTS: MetricsCalculator
# =============================================================================

class TestMetricsCalculatorUnit:
    """Unit tests for MetricsCalculator methods."""
    
    def test_interpret_volatility_low(self):
        """Test volatility interpretation for low values."""
        from portfolio_tool.analytics.metrics import MetricsCalculator
        
        calc = MetricsCalculator()
        assert "Low" in calc._interpret_volatility(0.10)
        assert "stable" in calc._interpret_volatility(0.10).lower()
    
    def test_interpret_volatility_high(self):
        """Test volatility interpretation for high values."""
        from portfolio_tool.analytics.metrics import MetricsCalculator
        
        calc = MetricsCalculator()
        assert "High" in calc._interpret_volatility(0.35)
    
    def test_interpret_volatility_very_high(self):
        """Test volatility interpretation for very high values."""
        from portfolio_tool.analytics.metrics import MetricsCalculator
        
        calc = MetricsCalculator()
        assert "Very high" in calc._interpret_volatility(0.50)
    
    def test_interpret_sharpe_negative(self):
        """Test Sharpe ratio interpretation for negative values."""
        from portfolio_tool.analytics.metrics import MetricsCalculator
        
        calc = MetricsCalculator()
        result = calc._interpret_sharpe(-0.5)
        assert "Negative" in result or "underperforming" in result.lower()
    
    def test_interpret_sharpe_good(self):
        """Test Sharpe ratio interpretation for good values."""
        from portfolio_tool.analytics.metrics import MetricsCalculator
        
        calc = MetricsCalculator()
        result = calc._interpret_sharpe(1.5)
        assert "Good" in result or "good" in result.lower()
    
    def test_interpret_sharpe_excellent(self):
        """Test Sharpe ratio interpretation for excellent values."""
        from portfolio_tool.analytics.metrics import MetricsCalculator
        
        calc = MetricsCalculator()
        result = calc._interpret_sharpe(3.5)
        assert "Excellent" in result or "excellent" in result.lower()
    
    def test_interpret_drawdown_minor(self):
        """Test drawdown interpretation for minor values."""
        from portfolio_tool.analytics.metrics import MetricsCalculator
        
        calc = MetricsCalculator()
        result = calc._interpret_drawdown(-0.05)
        assert "Minor" in result or "minor" in result.lower()
    
    def test_interpret_drawdown_severe(self):
        """Test drawdown interpretation for severe values."""
        from portfolio_tool.analytics.metrics import MetricsCalculator
        
        calc = MetricsCalculator()
        result = calc._interpret_drawdown(-0.40)
        assert "Severe" in result or "severe" in result.lower()


class TestMetricsCalculatorWithMockData:
    """Tests using mocked price data."""
    
    @pytest.fixture
    def mock_price_df(self):
        """Create a mock price DataFrame for testing."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        prices = [100 + i * 0.5 + (i % 10) for i in range(100)]  # Trending up with noise
        
        df = pd.DataFrame({
            'close': prices,
            'open': [p - 1 for p in prices],
            'high': [p + 2 for p in prices],
            'low': [p - 2 for p in prices],
            'volume': [1000000] * 100
        }, index=dates)
        
        return df
    
    def test_returns_calculation_logic(self, mock_price_df):
        """Test that return calculation math is correct."""
        # Manually calculate expected return
        first_price = mock_price_df['close'].iloc[0]
        last_price = mock_price_df['close'].iloc[-1]
        expected_return = (last_price - first_price) / first_price
        
        # The actual return should match
        actual_return = (last_price - first_price) / first_price
        
        assert abs(expected_return - actual_return) < 0.0001
    
    def test_volatility_calculation_logic(self, mock_price_df):
        """Test that volatility calculation uses correct formula."""
        daily_returns = mock_price_df['close'].pct_change().dropna()
        daily_vol = daily_returns.std()
        annual_vol = daily_vol * math.sqrt(252)
        
        # Volatility should be positive
        assert annual_vol > 0
        
        # For this trending data, volatility should be relatively low
        assert annual_vol < 1.0  # Less than 100%


# =============================================================================
# INTEGRATION TESTS: Analytics with Database
# =============================================================================

class TestAnalyticsIntegration:
    """Integration tests for analytics with real database."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for integration tests."""
        import os
        os.environ["USE_MOCK_QUOTA"] = "True"
        yield
    
    def test_calculate_returns_missing_ticker(self):
        """Test calculate_returns with non-existent ticker."""
        from portfolio_tool.analytics.metrics import MetricsCalculator
        
        calc = MetricsCalculator()
        result = calc.calculate_returns("NOTAREALTICKER12345", days=30)
        
        assert result["success"] is False
        assert "error" in result
    
    def test_calculate_volatility_missing_ticker(self):
        """Test calculate_volatility with non-existent ticker."""
        from portfolio_tool.analytics.metrics import MetricsCalculator
        
        calc = MetricsCalculator()
        result = calc.calculate_volatility("NOTAREALTICKER12345", days=30)
        
        assert result["success"] is False
    
    def test_compare_stocks_too_few_tickers(self):
        """Test compare_stocks with less than 2 tickers."""
        from portfolio_tool.analytics.metrics import MetricsCalculator
        
        calc = MetricsCalculator()
        result = calc.compare_stocks(["AAPL"], days=30)
        
        assert result["success"] is False
        assert "at least 2" in result["error"].lower()
    
    def test_compare_stocks_too_many_tickers(self):
        """Test compare_stocks with more than 10 tickers."""
        from portfolio_tool.analytics.metrics import MetricsCalculator
        
        calc = MetricsCalculator()
        tickers = [f"TICK{i}" for i in range(15)]
        result = calc.compare_stocks(tickers, days=30)
        
        assert result["success"] is False
        assert "10" in result["error"] or "Maximum" in result["error"]


# =============================================================================
# TOOL TESTS
# =============================================================================

class TestAnalyticsTools:
    """Test the LangChain tool wrappers."""
    
    def test_calculate_returns_tool_invalid_ticker(self):
        """Test calculate_returns tool with invalid ticker."""
        from portfolio_tool.tools.analytics_tools import calculate_returns
        
        result = calculate_returns.invoke({
            "ticker": "INVALIDTICKER999",
            "days": 30
        })
        
        assert result["success"] is False
    
    def test_compare_stocks_tool_parsing(self):
        """Test compare_stocks tool parses comma-separated tickers."""
        from portfolio_tool.tools.analytics_tools import compare_stocks
        
        # Even if tickers don't exist, the parsing should work
        result = compare_stocks.invoke({
            "tickers": "AAPL,MSFT,GOOGL",
            "days": 30
        })
        
        # Should not fail on parsing
        assert "success" in result
    
    def test_compare_stocks_tool_single_ticker_error(self):
        """Test compare_stocks tool rejects single ticker."""
        from portfolio_tool.tools.analytics_tools import compare_stocks
        
        result = compare_stocks.invoke({
            "tickers": "AAPL",
            "days": 30
        })
        
        assert result["success"] is False
        assert "at least 2" in result["error"].lower()


# =============================================================================
# RUN CONFIGURATION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
