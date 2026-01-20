"""
Tests for Phase 5.3: Backtest Agent

These tests cover:
- Strategy definitions and TAA Rules
- BacktestEngine (deterministic)
- Performance metrics
- Backtest Agent
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_prices() -> pd.DataFrame:
    """Generate sample price data for backtesting."""
    np.random.seed(42)
    dates = pd.date_range(start="2020-01-01", periods=500, freq="B")
    
    # Simulate correlated returns
    n = len(dates)
    
    spy_returns = np.random.normal(0.0004, 0.012, n)  # ~10% annual, 19% vol
    tlt_returns = np.random.normal(0.0001, 0.008, n)  # ~2.5% annual, 12% vol
    gld_returns = np.random.normal(0.0002, 0.010, n)  # ~5% annual, 16% vol
    
    prices = pd.DataFrame({
        "SPY": 100 * np.exp(np.cumsum(spy_returns)),
        "TLT": 100 * np.exp(np.cumsum(tlt_returns)),
        "GLD": 100 * np.exp(np.cumsum(gld_returns)),
    }, index=dates)
    
    return prices


@pytest.fixture
def sample_prices_with_vix() -> tuple:
    """Generate price data with VIX signal."""
    np.random.seed(42)
    dates = pd.date_range(start="2020-01-01", periods=500, freq="B")
    n = len(dates)
    
    # Prices
    spy_returns = np.random.normal(0.0004, 0.012, n)
    tlt_returns = np.random.normal(0.0001, 0.008, n)
    
    prices = pd.DataFrame({
        "SPY": 100 * np.exp(np.cumsum(spy_returns)),
        "TLT": 100 * np.exp(np.cumsum(tlt_returns)),
    }, index=dates)
    
    # VIX signal - starts low, spikes in the middle, returns to low
    vix = np.concatenate([
        np.random.uniform(15, 20, 200),   # Normal period
        np.random.uniform(28, 35, 100),   # High VIX period
        np.random.uniform(15, 22, 200),   # Back to normal
    ])
    
    signals = pd.DataFrame({"VIX": vix}, index=dates)
    
    return prices, signals


# ============================================================================
# TAA Rule Tests
# ============================================================================

class TestTAARule:
    """Tests for TAA Rule determinism."""
    
    def test_basic_rule_creation(self):
        """Test creating a TAA rule."""
        from portfolio_tool.backtest.strategies import TAARule
        
        rule = TAARule(
            name="VIX_Risk_Off",
            indicator="VIX",
            operator=">",
            threshold=25.0,
            target_weights={"SPY": 0.40, "TLT": 0.40, "CASH": 0.20}
        )
        
        assert rule.name == "VIX_Risk_Off"
        assert rule.threshold == 25.0
    
    def test_rule_evaluation_deterministic(self):
        """Test that rule evaluation is 100% deterministic."""
        from portfolio_tool.backtest.strategies import TAARule
        
        rule = TAARule(
            name="Test",
            indicator="VIX",
            operator=">",
            threshold=25.0,
            target_weights={"SPY": 0.5, "TLT": 0.5}
        )
        
        # Same input = same output, 100 times
        for _ in range(100):
            assert rule.evaluate(30.0) == True
            assert rule.evaluate(20.0) == False
            assert rule.evaluate(25.0) == False  # Not strictly greater
            assert rule.evaluate(25.001) == True
    
    def test_rule_operators(self):
        """Test all operators work correctly."""
        from portfolio_tool.backtest.strategies import TAARule
        
        base_args = {
            "name": "Test",
            "indicator": "X",
            "threshold": 10.0,
            "target_weights": {"A": 1.0}
        }
        
        # Greater than
        rule = TAARule(operator=">", **base_args)
        assert rule.evaluate(11) == True
        assert rule.evaluate(10) == False
        assert rule.evaluate(9) == False
        
        # Less than
        rule = TAARule(operator="<", **base_args)
        assert rule.evaluate(9) == True
        assert rule.evaluate(10) == False
        assert rule.evaluate(11) == False
        
        # Greater than or equal
        rule = TAARule(operator=">=", **base_args)
        assert rule.evaluate(11) == True
        assert rule.evaluate(10) == True
        assert rule.evaluate(9) == False
        
        # Less than or equal
        rule = TAARule(operator="<=", **base_args)
        assert rule.evaluate(9) == True
        assert rule.evaluate(10) == True
        assert rule.evaluate(11) == False
    
    def test_crosses_above(self):
        """Test crosses_above operator."""
        from portfolio_tool.backtest.strategies import TAARule
        
        rule = TAARule(
            name="Cross",
            indicator="X",
            operator="crosses_above",
            threshold=10.0,
            target_weights={"A": 1.0}
        )
        
        # Crosses from below to above
        assert rule.evaluate(11, previous_value=9) == True
        
        # Already above
        assert rule.evaluate(11, previous_value=11) == False
        
        # Crosses down
        assert rule.evaluate(9, previous_value=11) == False
        
        # No previous value
        assert rule.evaluate(11, previous_value=None) == False
    
    def test_rule_weights_validation(self):
        """Test that rule weights must sum to 1."""
        from portfolio_tool.backtest.strategies import TAARule
        
        with pytest.raises(ValueError):
            TAARule(
                name="Bad",
                indicator="X",
                operator=">",
                threshold=10,
                target_weights={"A": 0.5, "B": 0.3}  # Sums to 0.8
            )


# ============================================================================
# Strategy Tests
# ============================================================================

class TestStrategy:
    """Tests for Strategy class."""
    
    def test_strategy_creation(self):
        """Test creating a strategy."""
        from portfolio_tool.backtest.strategies import Strategy, RebalanceRule
        
        strategy = Strategy(
            name="60/40",
            initial_weights={"SPY": 0.60, "TLT": 0.40},
            rebalance_rule=RebalanceRule()
        )
        
        assert strategy.name == "60/40"
        assert strategy.initial_weights["SPY"] == 0.60
    
    def test_strategy_weights_validation(self):
        """Test that strategy weights must sum to 1."""
        from portfolio_tool.backtest.strategies import Strategy
        
        with pytest.raises(ValueError):
            Strategy(
                name="Bad",
                initial_weights={"SPY": 0.5, "TLT": 0.3}
            )
    
    def test_strategy_get_target_weights(self):
        """Test getting target weights with TAA rules."""
        from portfolio_tool.backtest.strategies import Strategy, TAARule
        
        rule = TAARule(
            name="VIX_High",
            indicator="VIX",
            operator=">",
            threshold=25.0,
            target_weights={"SPY": 0.30, "TLT": 0.70}
        )
        
        strategy = Strategy(
            name="Test",
            initial_weights={"SPY": 0.60, "TLT": 0.40},
            taa_rules=[rule]
        )
        
        # Normal VIX - return initial weights
        normal_data = pd.Series({"VIX": 18.0})
        weights, triggered = strategy.get_target_weights(normal_data)
        assert weights["SPY"] == 0.60
        assert triggered is None
        
        # High VIX - return TAA weights
        high_data = pd.Series({"VIX": 30.0})
        weights, triggered = strategy.get_target_weights(high_data)
        assert weights["SPY"] == 0.30
        assert triggered == "VIX_High"


# ============================================================================
# Rebalance Rule Tests
# ============================================================================

class TestRebalanceRule:
    """Tests for RebalanceRule."""
    
    def test_drift_threshold(self):
        """Test drift-based rebalancing."""
        from portfolio_tool.backtest.strategies import RebalanceRule, RebalanceFrequency
        
        rule = RebalanceRule(
            frequency=RebalanceFrequency.NEVER,  # Only drift-based
            drift_threshold=0.05
        )
        
        target = {"SPY": 0.60, "TLT": 0.40}
        
        # Small drift - no rebalance
        current = {"SPY": 0.62, "TLT": 0.38}
        should, reason = rule.should_rebalance(
            datetime.now(), None, current, target
        )
        assert should == False
        
        # Large drift - rebalance
        current = {"SPY": 0.70, "TLT": 0.30}
        should, reason = rule.should_rebalance(
            datetime.now(), None, current, target
        )
        assert should == True
        assert "drift" in reason.lower()
    
    def test_calendar_quarterly(self):
        """Test quarterly rebalancing."""
        from portfolio_tool.backtest.strategies import RebalanceRule, RebalanceFrequency
        
        rule = RebalanceRule(
            frequency=RebalanceFrequency.QUARTERLY,
            drift_threshold=1.0  # High threshold so only calendar triggers
        )
        
        target = {"SPY": 0.60, "TLT": 0.40}
        current = {"SPY": 0.60, "TLT": 0.40}
        
        # January 15 - should trigger (Q1)
        should, _ = rule.should_rebalance(
            datetime(2024, 1, 15), None, current, target
        )
        assert should == True
        
        # February 15 - should not trigger
        should, _ = rule.should_rebalance(
            datetime(2024, 2, 15), datetime(2024, 1, 15), current, target
        )
        assert should == False


# ============================================================================
# BacktestEngine Tests
# ============================================================================

class TestBacktestEngine:
    """Tests for BacktestEngine determinism."""
    
    def test_engine_deterministic(self, sample_prices):
        """Test that backtest results are 100% deterministic."""
        from portfolio_tool.backtest.engine import BacktestEngine
        from portfolio_tool.backtest.strategies import Strategy
        
        engine = BacktestEngine(transaction_cost=0.001)
        
        strategy = Strategy(
            name="Test",
            initial_weights={"SPY": 0.6, "TLT": 0.3, "GLD": 0.1}
        )
        
        # Run 5 times - all results must be identical
        results = []
        for _ in range(5):
            result = engine.run(strategy, sample_prices)
            results.append(result)
        
        # Compare all results
        for r in results[1:]:
            assert r.total_return == results[0].total_return
            assert r.volatility == results[0].volatility
            assert r.sharpe_ratio == results[0].sharpe_ratio
            assert r.max_drawdown == results[0].max_drawdown
    
    def test_engine_basic_metrics(self, sample_prices):
        """Test that engine calculates reasonable metrics."""
        from portfolio_tool.backtest.engine import BacktestEngine
        from portfolio_tool.backtest.strategies import Strategy
        
        engine = BacktestEngine()
        
        strategy = Strategy(
            name="60/40",
            initial_weights={"SPY": 0.6, "TLT": 0.4}
        )
        
        result = engine.run(strategy, sample_prices[["SPY", "TLT"]])
        
        # Basic sanity checks
        assert result.total_return != 0  # Should have some return
        assert result.volatility > 0  # Should have volatility
        assert -10 < result.sharpe_ratio < 10  # Reasonable Sharpe
        assert 0 < result.max_drawdown < 1  # Drawdown between 0-100%
        assert result.trading_days == len(sample_prices)
    
    def test_engine_with_taa(self, sample_prices_with_vix):
        """Test engine with TAA rules."""
        from portfolio_tool.backtest.engine import BacktestEngine
        from portfolio_tool.backtest.strategies import Strategy, TAARule
        
        prices, signals = sample_prices_with_vix
        
        rule = TAARule(
            name="VIX_Risk_Off",
            indicator="VIX",
            operator=">",
            threshold=25.0,
            target_weights={"SPY": 0.30, "TLT": 0.70}
        )
        
        strategy = Strategy(
            name="60/40 with TAA",
            initial_weights={"SPY": 0.60, "TLT": 0.40},
            taa_rules=[rule]
        )
        
        engine = BacktestEngine()
        result = engine.run(strategy, prices, signal_data=signals)
        
        # TAA rule should have triggered
        assert result.taa_triggers["VIX_Risk_Off"] > 0
        assert result.time_in_taa > 0
    
    def test_transaction_costs(self, sample_prices):
        """Test that transaction costs are applied."""
        from portfolio_tool.backtest.engine import BacktestEngine
        from portfolio_tool.backtest.strategies import Strategy, RebalanceRule, RebalanceFrequency
        
        strategy = Strategy(
            name="Test",
            initial_weights={"SPY": 0.5, "TLT": 0.5},
            rebalance_rule=RebalanceRule(frequency=RebalanceFrequency.MONTHLY)
        )
        
        # Run with different transaction costs
        engine_low = BacktestEngine(transaction_cost=0.0001)
        engine_high = BacktestEngine(transaction_cost=0.01)
        
        result_low = engine_low.run(strategy, sample_prices[["SPY", "TLT"]])
        result_high = engine_high.run(strategy, sample_prices[["SPY", "TLT"]])
        
        # Higher costs should result in lower returns
        assert result_low.total_return > result_high.total_return
        assert result_low.total_transaction_costs < result_high.total_transaction_costs


# ============================================================================
# Performance Metrics Tests
# ============================================================================

class TestMetrics:
    """Tests for performance metrics."""
    
    def test_cagr_calculation(self):
        """Test CAGR calculation."""
        from portfolio_tool.backtest.metrics import calculate_cagr
        
        # 2 years, doubled value = ~41.4% CAGR
        dates = pd.date_range("2020-01-01", periods=504, freq="B")  # ~2 years
        values = pd.Series(np.linspace(100, 200, 504), index=dates)
        
        cagr = calculate_cagr(values)
        assert 0.35 < cagr < 0.50  # Approximately 41%
    
    def test_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        from portfolio_tool.backtest.metrics import calculate_sharpe_ratio
        
        # Generate returns with known characteristics
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.01, 252))  # ~25% annual, 16% vol
        
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.0)
        
        # Should be positive for positive returns
        assert sharpe > 0
    
    def test_max_drawdown(self):
        """Test max drawdown calculation."""
        from portfolio_tool.backtest.metrics import calculate_max_drawdown
        
        # Simple case: 100 -> 80 -> 100 = 20% max drawdown
        values = pd.Series([100, 90, 80, 85, 100])
        
        max_dd = calculate_max_drawdown(values)
        assert abs(max_dd - 0.20) < 0.01
    
    def test_var_calculation(self):
        """Test VaR calculation."""
        from portfolio_tool.backtest.metrics import calculate_var
        
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.01, 1000))
        
        var_95 = calculate_var(returns, confidence_level=0.95)
        var_99 = calculate_var(returns, confidence_level=0.99)
        
        # VaR 99 should be larger than VaR 95
        assert var_99 > var_95
        assert var_95 > 0


# ============================================================================
# Backtest Agent Tests
# ============================================================================

class TestBacktestAgent:
    """Tests for Backtest Agent."""
    
    def test_agent_creation(self):
        """Test creating a Backtest Agent."""
        from agents.backtest_agent import create_backtest_agent
        
        agent = create_backtest_agent()
        
        assert agent.name == "BacktestAgent"
        assert "run_backtest" in agent.capabilities
    
    def test_agent_has_tools(self):
        """Test agent has required tools."""
        from agents.backtest_agent import create_backtest_agent
        
        agent = create_backtest_agent()
        tools = agent.get_tools()
        
        tool_names = [t.__name__ for t in tools]
        assert "run_backtest_tool" in tool_names
        assert "compare_strategies_tool" in tool_names
        assert "create_strategy_tool" in tool_names
    
    def test_create_strategy_tool(self):
        """Test strategy creation tool."""
        from agents.backtest_agent import create_backtest_agent
        import json
        
        agent = create_backtest_agent()
        
        result = agent.create_strategy_tool(
            name="Test Strategy",
            weights=json.dumps({"SPY": 0.6, "TLT": 0.4}),
            rebalance_frequency="quarterly"
        )
        
        assert result["success"]
        assert result["strategy"]["name"] == "Test Strategy"
    
    def test_create_strategy_invalid_weights(self):
        """Test strategy creation with invalid weights."""
        from agents.backtest_agent import create_backtest_agent
        import json
        
        agent = create_backtest_agent()
        
        result = agent.create_strategy_tool(
            name="Bad Strategy",
            weights=json.dumps({"SPY": 0.5, "TLT": 0.3})  # Sums to 0.8
        )
        
        assert not result["success"]
        assert "sum to 1" in result["error"].lower()


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for Phase 5.3."""
    
    def test_full_backtest_workflow(self, sample_prices):
        """Test complete backtest workflow."""
        from portfolio_tool.backtest.engine import BacktestEngine
        from portfolio_tool.backtest.strategies import (
            Strategy, TAARule, RebalanceRule, RebalanceFrequency
        )
        from portfolio_tool.backtest.reports import generate_performance_summary
        
        # 1. Create strategy
        strategy = Strategy(
            name="60/40 Portfolio",
            initial_weights={"SPY": 0.60, "TLT": 0.30, "GLD": 0.10},
            rebalance_rule=RebalanceRule(
                frequency=RebalanceFrequency.QUARTERLY,
                drift_threshold=0.05
            )
        )
        
        # 2. Run backtest
        engine = BacktestEngine(transaction_cost=0.001)
        result = engine.run(strategy, sample_prices)
        
        # 3. Validate results
        assert result.success if hasattr(result, 'success') else True
        assert result.total_return is not None
        assert result.sharpe_ratio is not None
        
        # 4. Generate report
        report = generate_performance_summary(result)
        assert "60/40" in report
        assert "Sharpe" in report
    
    def test_strategy_comparison(self, sample_prices):
        """Test comparing multiple strategies."""
        from portfolio_tool.backtest.engine import BacktestEngine
        from portfolio_tool.backtest.strategies import Strategy
        from portfolio_tool.backtest.reports import compare_strategies
        
        strategies = [
            Strategy(name="60/40", initial_weights={"SPY": 0.6, "TLT": 0.3, "GLD": 0.1}),
            Strategy(name="Equal Weight", initial_weights={"SPY": 0.333, "TLT": 0.333, "GLD": 0.334}),
            Strategy(name="All Equity", initial_weights={"SPY": 1.0}),
        ]
        
        engine = BacktestEngine()
        
        results = {}
        for strategy in strategies:
            assets = list(strategy.initial_weights.keys())
            result = engine.run(strategy, sample_prices[assets])
            results[strategy.name] = result
        
        # Compare
        comparison = compare_strategies(results)
        
        assert len(comparison) == 3
        assert "60/40" in comparison.index


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
