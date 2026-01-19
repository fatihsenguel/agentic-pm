"""
Tests for Phase 5.1: Foundation + Data Agent

These tests cover:
- Protocol DTOs (PortfolioTask, PortfolioResult)
- Quant module (returns, covariance, risk_metrics)
- Data Agent functionality
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict

# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_prices() -> pd.DataFrame:
    """Generate sample price data for testing."""
    np.random.seed(42)  # Reproducible
    dates = pd.date_range(start="2020-01-01", periods=500, freq="B")
    
    # Simulate correlated returns
    n = len(dates)
    
    # Generate correlated random returns
    cov_matrix = np.array([
        [0.04, 0.02, 0.01],  # SPY-like
        [0.02, 0.02, 0.005], # TLT-like  
        [0.01, 0.005, 0.03]  # GLD-like
    ])
    
    mean_returns = np.array([0.0003, 0.0001, 0.0002])  # Daily
    
    returns = np.random.multivariate_normal(mean_returns, cov_matrix / 252, n)
    
    # Convert to prices
    prices = pd.DataFrame(
        100 * np.exp(np.cumsum(returns, axis=0)),
        index=dates,
        columns=["SPY", "TLT", "GLD"]
    )
    
    return prices


@pytest.fixture
def sample_returns(sample_prices) -> pd.DataFrame:
    """Calculate returns from sample prices."""
    return sample_prices.pct_change().dropna()


@pytest.fixture
def sample_weights() -> Dict[str, float]:
    """Sample portfolio weights."""
    return {"SPY": 0.6, "TLT": 0.3, "GLD": 0.1}


# ============================================================================
# Protocol Tests
# ============================================================================

class TestProtocols:
    """Tests for agent communication protocols."""
    
    def test_portfolio_task_creation(self):
        """Test creating a PortfolioTask."""
        from agents.protocols import PortfolioTask, TaskType, PortfolioConstraints
        
        constraints = PortfolioConstraints(
            max_volatility=0.12,
            max_weight=0.4,
            min_weight=0.05
        )
        
        task = PortfolioTask(
            task_type=TaskType.OPTIMIZE,
            universe=["SPY", "TLT", "GLD"],
            constraints=constraints,
            historical_period="5Y"
        )
        
        assert task.task_type == TaskType.OPTIMIZE
        assert len(task.universe) == 3
        assert task.constraints.max_volatility == 0.12
        assert task.task_id is not None  # Auto-generated
    
    def test_portfolio_task_to_dict(self):
        """Test PortfolioTask serialization."""
        from agents.protocols import PortfolioTask, TaskType
        
        task = PortfolioTask(
            task_type=TaskType.BACKTEST,
            universe=["SPY", "TLT"],
        )
        
        d = task.to_dict()
        assert d["task_type"] == "backtest"
        assert "SPY" in d["universe"]
    
    def test_portfolio_result_creation(self):
        """Test creating a PortfolioResult."""
        from agents.protocols import PortfolioResult
        
        result = PortfolioResult(
            agent_name="TestAgent",
            task_id="test123",
            success=True,
            weights={"SPY": 0.6, "TLT": 0.4},
            expected_return=0.08,
            expected_volatility=0.12,
            sharpe_ratio=0.67
        )
        
        assert result.success
        assert result.weights["SPY"] == 0.6
        assert result.sharpe_ratio == 0.67
    
    def test_portfolio_result_to_summary(self):
        """Test PortfolioResult summary generation."""
        from agents.protocols import PortfolioResult
        
        result = PortfolioResult(
            agent_name="TestAgent",
            task_id="test123",
            success=True,
            weights={"SPY": 0.6, "TLT": 0.4},
            expected_return=0.08,
            expected_volatility=0.12,
        )
        
        summary = result.to_summary()
        assert "SPY" in summary
        assert "60.0%" in summary
        assert "Success" in summary
    
    def test_taa_rule_evaluation(self):
        """Test TAA rule evaluation is deterministic."""
        from agents.protocols import TAARule
        
        rule = TAARule(
            name="VIX_Risk_Off",
            condition="VIX > 25",
            condition_type="threshold",
            indicator="VIX",
            operator=">",
            threshold=25.0,
            target_weights={"SPY": 0.4, "TLT": 0.4, "CASH": 0.2}
        )
        
        # Test evaluation
        assert rule.evaluate(30.0) == True  # VIX = 30 > 25
        assert rule.evaluate(20.0) == False  # VIX = 20 < 25
        assert rule.evaluate(25.0) == False  # VIX = 25 is not > 25
        
        # Test determinism - same input = same output
        for _ in range(100):
            assert rule.evaluate(26.0) == True


# ============================================================================
# Returns Module Tests
# ============================================================================

class TestReturns:
    """Tests for returns calculations."""
    
    def test_calculate_simple_returns(self, sample_prices):
        """Test simple returns calculation."""
        from portfolio_tool.quant.returns import calculate_returns
        
        returns = calculate_returns(sample_prices, method="simple")
        
        assert len(returns) == len(sample_prices) - 1
        assert list(returns.columns) == list(sample_prices.columns)
        assert not returns.isna().any().any()
    
    def test_calculate_log_returns(self, sample_prices):
        """Test log returns calculation."""
        from portfolio_tool.quant.returns import calculate_log_returns
        
        log_returns = calculate_log_returns(sample_prices)
        
        # Log returns should be close to simple returns for small values
        simple_returns = sample_prices.pct_change().dropna()
        
        # They should be highly correlated
        for col in log_returns.columns:
            corr = log_returns[col].corr(simple_returns[col])
            assert corr > 0.99
    
    def test_annualize_returns(self, sample_returns):
        """Test return annualization."""
        from portfolio_tool.quant.returns import annualize_returns
        
        annual = annualize_returns(sample_returns)
        
        # Annualized return should be reasonable
        for ticker in annual.index:
            assert -0.5 < annual[ticker] < 0.5  # Between -50% and +50%
    
    def test_cumulative_returns(self, sample_returns):
        """Test cumulative returns calculation."""
        from portfolio_tool.quant.returns import calculate_cumulative_returns
        
        cumulative = calculate_cumulative_returns(sample_returns)
        
        # First value should be around 1 (after first return)
        # Final value should match total return
        total_return = (1 + sample_returns).prod()
        
        for col in cumulative.columns:
            assert abs(cumulative[col].iloc[-1] - total_return[col]) < 0.0001


# ============================================================================
# Covariance Module Tests
# ============================================================================

class TestCovariance:
    """Tests for covariance estimation."""
    
    def test_sample_covariance(self, sample_returns):
        """Test sample covariance calculation."""
        from portfolio_tool.quant.covariance import calculate_sample_covariance
        
        result = calculate_sample_covariance(sample_returns)
        
        assert result.success
        assert result.covariance_matrix is not None
        assert result.correlation_matrix is not None
        assert len(result.tickers) == 3
    
    def test_shrinkage_covariance(self, sample_returns):
        """Test Ledoit-Wolf shrinkage covariance."""
        from portfolio_tool.quant.covariance import calculate_shrinkage_covariance
        
        result = calculate_shrinkage_covariance(sample_returns)
        
        assert result.success
        assert result.shrinkage_intensity is not None
        assert 0 <= result.shrinkage_intensity <= 1
    
    def test_covariance_is_positive_definite(self, sample_returns):
        """Test that covariance matrix is positive definite."""
        from portfolio_tool.quant.covariance import CovarianceEstimator, CovarianceMethod
        
        for method in [CovarianceMethod.SAMPLE, CovarianceMethod.SHRINKAGE]:
            estimator = CovarianceEstimator(method=method)
            result = estimator.estimate(sample_returns)
            
            assert result.success
            assert result.is_positive_definite
    
    def test_correlation_bounds(self, sample_returns):
        """Test correlation values are between -1 and 1."""
        from portfolio_tool.quant.covariance import calculate_sample_covariance
        
        result = calculate_sample_covariance(sample_returns)
        
        assert result.success
        corr = result.correlation_matrix
        
        # All correlations should be in [-1, 1]
        assert (corr.values >= -1.0001).all()
        assert (corr.values <= 1.0001).all()
        
        # Diagonal should be 1
        for i in range(len(corr)):
            assert abs(corr.iloc[i, i] - 1.0) < 0.0001
    
    def test_condition_number_warning(self):
        """Test that high condition numbers generate warnings."""
        from portfolio_tool.quant.covariance import CovarianceEstimator
        
        # Create nearly singular returns (highly correlated)
        np.random.seed(123)
        n = 100
        base_returns = np.random.normal(0, 0.01, n)
        
        returns = pd.DataFrame({
            "A": base_returns,
            "B": base_returns + np.random.normal(0, 0.0001, n),  # Almost identical
            "C": base_returns + np.random.normal(0, 0.0001, n),
        })
        
        estimator = CovarianceEstimator(min_observations=10)
        result = estimator.estimate(returns)
        
        assert result.success
        # Should have warning about high correlation or condition number
        assert len(result.warnings) > 0


# ============================================================================
# Risk Metrics Tests
# ============================================================================

class TestRiskMetrics:
    """Tests for risk metrics calculations."""
    
    def test_volatility_calculation(self, sample_returns):
        """Test volatility calculation."""
        from portfolio_tool.quant.risk_metrics import calculate_volatility
        
        vol = calculate_volatility(sample_returns, annualize=True)
        
        # Annualized vol should be reasonable (5% to 50%)
        for ticker in vol.index:
            assert 0.05 < vol[ticker] < 0.50
    
    def test_var_calculation(self, sample_returns):
        """Test VaR calculation."""
        from portfolio_tool.quant.risk_metrics import calculate_var
        
        var_95 = calculate_var(sample_returns["SPY"], confidence_level=0.95)
        var_99 = calculate_var(sample_returns["SPY"], confidence_level=0.99)
        
        # VaR should be positive (it's a loss amount)
        assert var_95 > 0
        assert var_99 > 0
        
        # 99% VaR should be larger than 95% VaR
        assert var_99 > var_95
    
    def test_cvar_exceeds_var(self, sample_returns):
        """Test that CVaR >= VaR."""
        from portfolio_tool.quant.risk_metrics import calculate_var, calculate_cvar
        
        var_95 = calculate_var(sample_returns["SPY"], 0.95)
        cvar_95 = calculate_cvar(sample_returns["SPY"], 0.95)
        
        # CVaR should be >= VaR (expected loss given exceeding VaR)
        assert cvar_95 >= var_95
    
    def test_max_drawdown(self, sample_returns):
        """Test max drawdown calculation."""
        from portfolio_tool.quant.risk_metrics import calculate_max_drawdown
        
        max_dd = calculate_max_drawdown(sample_returns["SPY"])
        
        # Max drawdown should be positive (it's a loss)
        assert max_dd > 0
        # Max drawdown should be less than 100%
        assert max_dd < 1.0
    
    def test_sharpe_ratio(self, sample_returns):
        """Test Sharpe ratio calculation."""
        from portfolio_tool.quant.risk_metrics import calculate_sharpe_ratio
        
        sharpe = calculate_sharpe_ratio(sample_returns["SPY"], risk_free_rate=0.02)
        
        # Sharpe should be a reasonable number
        assert -5 < sharpe < 5
    
    def test_risk_metrics_calculator(self, sample_returns):
        """Test comprehensive risk metrics calculator."""
        from portfolio_tool.quant.risk_metrics import RiskMetricsCalculator
        
        calc = RiskMetricsCalculator(risk_free_rate=0.05)
        result = calc.calculate_all(sample_returns["SPY"])
        
        assert result.success
        assert result.volatility is not None
        assert result.sharpe_ratio is not None
        assert result.max_drawdown is not None
        assert result.var_95 is not None
    
    def test_portfolio_risk(self, sample_returns, sample_weights):
        """Test portfolio risk calculation."""
        from portfolio_tool.quant.risk_metrics import RiskMetricsCalculator
        from portfolio_tool.quant.covariance import calculate_sample_covariance
        
        # Get covariance matrix
        cov_result = calculate_sample_covariance(sample_returns)
        assert cov_result.success
        
        calc = RiskMetricsCalculator()
        port_vol, risk_contrib = calc.calculate_portfolio_risk(
            sample_weights, 
            cov_result.covariance_matrix
        )
        
        # Portfolio vol should be positive
        assert port_vol > 0
        
        # Risk contributions should sum to 1
        total_contrib = sum(risk_contrib.values())
        assert abs(total_contrib - 1.0) < 0.01


# ============================================================================
# Data Agent Tests
# ============================================================================

class TestDataAgent:
    """Tests for Data Agent."""
    
    def test_agent_creation(self):
        """Test creating a Data Agent."""
        from agents.data_agent import create_data_agent
        
        agent = create_data_agent(verbose=False)
        
        assert agent.name == "DataAgent"
        assert "fetch_prices" in agent.capabilities
        assert "calculate_covariance" in agent.capabilities
    
    def test_agent_has_tools(self):
        """Test that Data Agent has required tools."""
        from agents.data_agent import create_data_agent
        
        agent = create_data_agent()
        tools = agent.get_tools()
        
        assert len(tools) > 0
        tool_names = [t.__name__ for t in tools]
        
        assert "fetch_prices_tool" in tool_names
        assert "calculate_covariance_tool" in tool_names
        assert "get_risk_metrics_tool" in tool_names
    
    def test_agent_system_prompt(self):
        """Test that Data Agent has proper system prompt."""
        from agents.data_agent import create_data_agent
        
        agent = create_data_agent()
        prompt = agent.get_system_prompt()
        
        # Should contain key guidelines
        assert "Hot Potato" in prompt
        assert "audit" in prompt.lower()
        assert "NOT" in prompt  # Scope guards


# ============================================================================
# Risk Manager Tests
# ============================================================================

class TestRiskManager:
    """Tests for Risk Manager Agent."""
    
    def test_risk_manager_creation(self):
        """Test creating a Risk Manager."""
        from agents.risk_manager_agent import create_risk_manager
        
        manager = create_risk_manager(verbose=False)
        
        assert manager.name == "RiskManager"
        assert "validate_constraints" in manager.capabilities
    
    def test_constraint_validation(self):
        """Test constraint validation."""
        from agents.risk_manager_agent import create_risk_manager
        
        manager = create_risk_manager()
        
        # Valid constraints
        result = manager.validate_portfolio_constraints(
            max_volatility=0.12,
            max_weight=0.4,
            num_assets=4
        )
        assert result["valid"]
        
        # Invalid - very low volatility
        result = manager.validate_portfolio_constraints(
            max_volatility=0.02,
            max_weight=0.4,
            num_assets=4
        )
        assert len(result["warnings"]) > 0
    
    def test_concentration_check(self):
        """Test concentration risk checking."""
        from agents.risk_manager_agent import create_risk_manager

        manager = create_risk_manager()

        # Well-diversified portfolio (HHI = 0.25² * 4 = 0.0625 * 4 = 0.25)
        result = manager.check_concentration_risk({
            "SPY": 0.25, "TLT": 0.25, "GLD": 0.25, "VNQ": 0.25
        })
        # HHI = 0.25, which is exactly at the boundary - could be MODERATE or HIGH
        # Let's use a more diversified example
        
        # Very diversified (5 equal positions: HHI = 5 * 0.2² = 0.20)
        result = manager.check_concentration_risk({
            "SPY": 0.20, "TLT": 0.20, "GLD": 0.20, "VNQ": 0.20, "BND": 0.20
        })
        assert result["concentration_level"] in ["LOW", "MODERATE"]

        # Concentrated portfolio (HHI = 0.8² + 0.2² = 0.64 + 0.04 = 0.68)
        result = manager.check_concentration_risk({
            "SPY": 0.8, "TLT": 0.2
        })
        assert result["concentration_level"] == "HIGH"


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for Phase 5.1 components."""
    
    def test_full_data_pipeline(self, sample_prices, sample_weights):
        """Test full data processing pipeline."""
        from portfolio_tool.quant.returns import calculate_returns
        from portfolio_tool.quant.covariance import calculate_shrinkage_covariance
        from portfolio_tool.quant.risk_metrics import RiskMetricsCalculator
        
        # 1. Calculate returns
        returns = calculate_returns(sample_prices, method="simple")
        assert not returns.empty
        
        # 2. Estimate covariance
        cov_result = calculate_shrinkage_covariance(returns)
        assert cov_result.success
        
        # 3. Calculate portfolio risk
        calc = RiskMetricsCalculator(risk_free_rate=0.05)
        port_vol, risk_contrib = calc.calculate_portfolio_risk(
            sample_weights,
            cov_result.covariance_matrix
        )
        
        assert port_vol > 0
        assert abs(sum(risk_contrib.values()) - 1.0) < 0.01
        
        # 4. Calculate portfolio metrics
        weights_array = np.array([sample_weights.get(t, 0) for t in returns.columns])
        portfolio_returns = (returns * weights_array).sum(axis=1)
        
        metrics = calc.calculate_all(portfolio_returns)
        assert metrics.success
        assert metrics.sharpe_ratio is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
