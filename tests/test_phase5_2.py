"""
Tests for Phase 5.2: Optimization Agent

These tests cover:
- Mean-Variance (Markowitz) Optimization
- Risk Parity Optimization
- Efficient Frontier Generation
- Constraint Handling
- Optimization Agent
"""

import pytest
import numpy as np
import pandas as pd
from typing import Dict


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_returns() -> pd.Series:
    """Expected annual returns for test assets."""
    return pd.Series({
        "SPY": 0.10,   # 10% expected return
        "TLT": 0.04,   # 4%
        "GLD": 0.05,   # 5%
        "VNQ": 0.08,   # 8%
    })


@pytest.fixture
def sample_covariance() -> pd.DataFrame:
    """Annualized covariance matrix."""
    tickers = ["SPY", "TLT", "GLD", "VNQ"]
    
    # Volatilities (annual)
    vols = np.array([0.16, 0.12, 0.15, 0.20])
    
    # Correlation matrix
    corr = np.array([
        [1.00, -0.30, 0.05, 0.70],   # SPY
        [-0.30, 1.00, 0.20, -0.10],  # TLT (negative corr with stocks)
        [0.05, 0.20, 1.00, 0.10],    # GLD
        [0.70, -0.10, 0.10, 1.00],   # VNQ (correlated with SPY)
    ])
    
    # Convert to covariance
    cov = np.outer(vols, vols) * corr
    
    return pd.DataFrame(cov, index=tickers, columns=tickers)


@pytest.fixture
def simple_2asset_returns() -> pd.Series:
    """Simple 2-asset case for analytical verification."""
    return pd.Series({"A": 0.10, "B": 0.05})


@pytest.fixture
def simple_2asset_cov() -> pd.DataFrame:
    """Simple 2-asset covariance."""
    cov = np.array([
        [0.04, 0.00],
        [0.00, 0.01]
    ])
    return pd.DataFrame(cov, index=["A", "B"], columns=["A", "B"])


# ============================================================================
# Constraint Tests
# ============================================================================

class TestConstraints:
    """Tests for constraint handling."""
    
    def test_default_constraints(self):
        """Test default constraint creation."""
        from portfolio_tool.optimization.constraints import PortfolioConstraints
        
        c = PortfolioConstraints()
        
        assert c.min_weight == 0.0
        assert c.max_weight == 1.0
        assert c.long_only == True
        assert c.max_volatility is None
    
    def test_get_bounds(self):
        """Test bounds generation."""
        from portfolio_tool.optimization.constraints import PortfolioConstraints
        
        c = PortfolioConstraints(min_weight=0.05, max_weight=0.40)
        bounds = c.get_bounds(["SPY", "TLT", "GLD"])
        
        assert len(bounds) == 3
        assert bounds[0] == (0.05, 0.40)
    
    def test_asset_specific_bounds(self):
        """Test per-asset bound overrides."""
        from portfolio_tool.optimization.constraints import PortfolioConstraints
        
        c = PortfolioConstraints(
            min_weight=0.05,
            max_weight=0.40,
            asset_bounds={"SPY": (0.10, 0.50)}
        )
        
        bounds = c.get_bounds(["SPY", "TLT"])
        
        assert bounds[0] == (0.10, 0.50)  # SPY override
        assert bounds[1] == (0.05, 0.40)  # TLT default
    
    def test_scipy_constraints_creation(self):
        """Test scipy constraint dict creation."""
        from portfolio_tool.optimization.constraints import (
            PortfolioConstraints, 
            create_scipy_constraints
        )
        
        c = PortfolioConstraints(max_volatility=0.12)
        cov = np.array([[0.04, 0.01], [0.01, 0.02]])
        ret = np.array([0.10, 0.05])
        
        scipy_c = create_scipy_constraints(["A", "B"], cov, ret, c)
        
        assert len(scipy_c) >= 2
        
        sum_constraint = scipy_c[0]
        assert sum_constraint['type'] == 'eq'
        assert sum_constraint['fun']([0.5, 0.5]) == 0.0
    
    def test_constraint_satisfaction_check(self):
        """Test constraint satisfaction verification."""
        from portfolio_tool.optimization.constraints import (
            PortfolioConstraints,
            check_constraints_satisfied
        )
        
        c = PortfolioConstraints(max_weight=0.5)
        cov = np.array([[0.04, 0.01], [0.01, 0.02]])
        ret = np.array([0.10, 0.05])
        
        # Valid weights
        satisfied, violations = check_constraints_satisfied(
            np.array([0.5, 0.5]), ["A", "B"], cov, ret, c
        )
        assert satisfied
        assert len(violations) == 0
        
        # Invalid weights
        satisfied, violations = check_constraints_satisfied(
            np.array([0.7, 0.3]), ["A", "B"], cov, ret, c
        )
        assert not satisfied
        assert len(violations) > 0


# ============================================================================
# Mean-Variance Optimization Tests
# ============================================================================

class TestMeanVarianceOptimizer:
    """Tests for Markowitz Mean-Variance optimization."""
    
    def test_max_sharpe_basic(self, sample_returns, sample_covariance):
        """Test basic max Sharpe optimization."""
        from portfolio_tool.optimization.mean_variance import MeanVarianceOptimizer
        
        opt = MeanVarianceOptimizer(risk_free_rate=0.02)
        result = opt.max_sharpe(sample_returns, sample_covariance)
        
        assert result.success
        assert len(result.weights) == 4
        assert abs(sum(result.weights.values()) - 1.0) < 0.01
        assert all(w >= -0.001 for w in result.weights.values())
        assert result.sharpe_ratio > 0
    
    def test_min_volatility(self, sample_returns, sample_covariance):
        """Test minimum volatility optimization."""
        from portfolio_tool.optimization.mean_variance import MeanVarianceOptimizer
        
        opt = MeanVarianceOptimizer()
        result = opt.min_volatility(sample_returns, sample_covariance)
        
        assert result.success
        assert result.weights["TLT"] > 0.1
    
    def test_volatility_constraint(self, sample_returns, sample_covariance):
        """Test max volatility constraint."""
        from portfolio_tool.optimization.mean_variance import MeanVarianceOptimizer
        from portfolio_tool.optimization.constraints import PortfolioConstraints
        
        opt = MeanVarianceOptimizer()
        constraints = PortfolioConstraints(max_volatility=0.10)
        
        result = opt.max_sharpe(sample_returns, sample_covariance, constraints)
        
        assert result.success
        assert result.expected_volatility <= 0.10 + 0.005
    
    def test_weight_constraints(self, sample_returns, sample_covariance):
        """Test weight bound constraints."""
        from portfolio_tool.optimization.mean_variance import MeanVarianceOptimizer
        from portfolio_tool.optimization.constraints import PortfolioConstraints
        
        opt = MeanVarianceOptimizer()
        constraints = PortfolioConstraints(min_weight=0.10, max_weight=0.40)
        
        result = opt.max_sharpe(sample_returns, sample_covariance, constraints)
        
        assert result.success
        for w in result.weights.values():
            assert w >= 0.10 - 0.01
            assert w <= 0.40 + 0.01
    
    def test_simple_2asset_analytical(self, simple_2asset_returns, simple_2asset_cov):
        """Test 2-asset case against analytical solution."""
        from portfolio_tool.optimization.mean_variance import MeanVarianceOptimizer
        
        opt = MeanVarianceOptimizer(risk_free_rate=0.0)
        result = opt.min_volatility(simple_2asset_returns, simple_2asset_cov)
        
        # Analytical: w_A = 0.01/0.05 = 0.2, w_B = 0.04/0.05 = 0.8
        assert abs(result.weights["A"] - 0.2) < 0.05
        assert abs(result.weights["B"] - 0.8) < 0.05
    
    def test_risk_contributions_sum_to_one(self, sample_returns, sample_covariance):
        """Test that risk contributions sum to 100%."""
        from portfolio_tool.optimization.mean_variance import MeanVarianceOptimizer
        
        opt = MeanVarianceOptimizer()
        result = opt.max_sharpe(sample_returns, sample_covariance)
        
        assert result.success
        total_risk_contrib = sum(result.risk_contributions.values())
        assert abs(total_risk_contrib - 1.0) < 0.01


# ============================================================================
# Risk Parity Tests
# ============================================================================

class TestRiskParityOptimizer:
    """Tests for Risk Parity optimization."""
    
    def test_basic_risk_parity(self, sample_returns, sample_covariance):
        """Test basic risk parity optimization."""
        from portfolio_tool.optimization.risk_parity import RiskParityOptimizer
        
        opt = RiskParityOptimizer()
        result = opt.optimize(sample_returns, sample_covariance)
        
        assert result.success
        assert len(result.weights) == 4
        assert abs(sum(result.weights.values()) - 1.0) < 0.01
    
    def test_equal_risk_contributions(self, sample_returns, sample_covariance):
        """Test that risk contributions are approximately equal."""
        from portfolio_tool.optimization.risk_parity import RiskParityOptimizer
        
        opt = RiskParityOptimizer()
        result = opt.optimize(sample_returns, sample_covariance)
        
        assert result.success
        
        target = 1.0 / len(result.risk_contributions)
        for rc in result.risk_contributions.values():
            assert abs(rc - target) < 0.05
    
    def test_risk_parity_vs_equal_weight(self, sample_returns, sample_covariance):
        """Test risk parity differs from equal weight."""
        from portfolio_tool.optimization.risk_parity import RiskParityOptimizer
        
        opt = RiskParityOptimizer()
        result = opt.optimize(sample_returns, sample_covariance)
        
        assert result.success
        assert result.weights["TLT"] > 0.25  # Lower vol -> higher weight
        assert result.weights["VNQ"] < 0.25  # Higher vol -> lower weight
    
    def test_risk_parity_deterministic(self, sample_returns, sample_covariance):
        """Test risk parity is deterministic."""
        from portfolio_tool.optimization.risk_parity import RiskParityOptimizer
        
        opt = RiskParityOptimizer()
        results = [opt.optimize(sample_returns, sample_covariance) for _ in range(5)]
        
        for r in results[1:]:
            for ticker in results[0].weights:
                assert abs(r.weights[ticker] - results[0].weights[ticker]) < 0.001


# ============================================================================
# Efficient Frontier Tests
# ============================================================================

class TestEfficientFrontier:
    """Tests for efficient frontier generation."""
    
    def test_frontier_generation(self, sample_returns, sample_covariance):
        """Test efficient frontier generation."""
        from portfolio_tool.optimization.mean_variance import MeanVarianceOptimizer
        
        opt = MeanVarianceOptimizer()
        frontier = opt.efficient_frontier(sample_returns, sample_covariance, n_points=10)
        
        assert len(frontier.points) > 5
        
        vols = frontier.volatilities
        assert all(vols[i] <= vols[i+1] + 0.001 for i in range(len(vols)-1))
    
    def test_frontier_max_sharpe_portfolio(self, sample_returns, sample_covariance):
        """Test max Sharpe portfolio on frontier."""
        from portfolio_tool.optimization.mean_variance import MeanVarianceOptimizer
        
        opt = MeanVarianceOptimizer(risk_free_rate=0.02)
        frontier = opt.efficient_frontier(sample_returns, sample_covariance)
        
        max_sharpe = frontier.get_max_sharpe_portfolio()
        
        assert max_sharpe.sharpe_ratio > 0
        assert max_sharpe.sharpe_ratio == max(frontier.sharpe_ratios)


# ============================================================================
# Optimization Agent Tests
# ============================================================================

class TestOptimizationAgent:
    """Tests for Optimization Agent."""
    
    def test_agent_creation(self):
        """Test creating an Optimization Agent."""
        from agents.optimization_agent import create_optimization_agent
        
        agent = create_optimization_agent(risk_free_rate=0.05, verbose=False)
        
        assert agent.name == "OptimizationAgent"
        assert "optimize_mean_variance" in agent.capabilities
        assert "optimize_risk_parity" in agent.capabilities
    
    def test_agent_has_tools(self):
        """Test agent has required tools."""
        from agents.optimization_agent import create_optimization_agent
        
        agent = create_optimization_agent()
        tools = agent.get_tools()
        
        assert len(tools) >= 3
        tool_names = [t.__name__ for t in tools]
        
        assert "optimize_portfolio_tool" in tool_names
        assert "compare_methods_tool" in tool_names
        assert "efficient_frontier_tool" in tool_names
    
    def test_optimize_tool(self, sample_returns, sample_covariance):
        """Test optimize_portfolio_tool."""
        from agents.optimization_agent import create_optimization_agent
        import json
        
        agent = create_optimization_agent()
        
        result = agent.optimize_portfolio_tool(
            tickers="SPY,TLT,GLD,VNQ",
            expected_returns=json.dumps(sample_returns.to_dict()),
            covariance_matrix=json.dumps(sample_covariance.to_dict()),
            method="max_sharpe",
            max_weight=0.40
        )
        
        assert result["success"]
        assert "weights" in result
        assert "expected_return" in result
        assert "sharpe_ratio" in result
    
    def test_compare_methods_tool(self, sample_returns, sample_covariance):
        """Test compare_methods_tool."""
        from agents.optimization_agent import create_optimization_agent
        import json
        
        agent = create_optimization_agent()
        
        result = agent.compare_methods_tool(
            tickers="SPY,TLT,GLD,VNQ",
            expected_returns=json.dumps(sample_returns.to_dict()),
            covariance_matrix=json.dumps(sample_covariance.to_dict()),
        )
        
        assert result["success"]
        assert "mean_variance" in result
        assert "risk_parity" in result
        assert "comparison" in result


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for Phase 5.2."""
    
    def test_full_optimization_pipeline(self, sample_returns, sample_covariance):
        """Test complete optimization workflow."""
        from portfolio_tool.optimization.mean_variance import MeanVarianceOptimizer
        from portfolio_tool.optimization.risk_parity import RiskParityOptimizer
        from portfolio_tool.optimization.constraints import PortfolioConstraints
        
        constraints = PortfolioConstraints(
            min_weight=0.05,
            max_weight=0.40,
            max_volatility=0.12
        )
        
        # Run Mean-Variance
        mv_opt = MeanVarianceOptimizer(risk_free_rate=0.02)
        mv_result = mv_opt.max_sharpe(sample_returns, sample_covariance, constraints)
        
        assert mv_result.success
        assert mv_result.expected_volatility <= 0.12 + 0.01
        
        # Run Risk Parity
        rp_opt = RiskParityOptimizer()
        rp_result = rp_opt.optimize(sample_returns, sample_covariance, constraints)
        
        assert rp_result.success
    
    def test_data_to_optimization_flow(self):
        """Test data preparation to optimization flow."""
        from portfolio_tool.quant.returns import calculate_returns
        from portfolio_tool.quant.covariance import calculate_shrinkage_covariance
        from portfolio_tool.optimization.mean_variance import MeanVarianceOptimizer
        
        # Create synthetic price data
        np.random.seed(42)
        dates = pd.date_range("2020-01-01", periods=500, freq="B")
        
        prices = pd.DataFrame({
            "SPY": 100 * np.exp(np.cumsum(np.random.normal(0.0003, 0.01, 500))),
            "TLT": 100 * np.exp(np.cumsum(np.random.normal(0.0001, 0.008, 500))),
            "GLD": 100 * np.exp(np.cumsum(np.random.normal(0.0002, 0.012, 500))),
        }, index=dates)
        
        # Calculate returns
        returns = calculate_returns(prices)
        
        # Calculate covariance
        cov_result = calculate_shrinkage_covariance(returns)
        assert cov_result.success
        
        # Calculate expected returns
        expected_returns = returns.mean() * 252
        
        # Optimize
        optimizer = MeanVarianceOptimizer(risk_free_rate=0.02)
        result = optimizer.max_sharpe(expected_returns, cov_result.covariance_matrix)
        
        assert result.success
        assert abs(sum(result.weights.values()) - 1.0) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
