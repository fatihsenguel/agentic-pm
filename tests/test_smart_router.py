# tests/test_smart_router.py
# Purpose: the dependency table beside the roster, and the validators the
# router used and extraction still reads (Phase 6.12)
# Run with: pytest tests/test_smart_router.py -v

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.schemas import (
    AGENTS,
    REQUIRES,
    PortfolioWeights,
)
from agents.validators import (
    validate_ticker,
    validate_tickers,
    validate_weights,
    suggest_ticker,
    validate_optimization_request,
    is_known_ticker,
    is_valid_ticker_format,
)


class TestRequires:
    """REQUIRES: an agent runs only after what it needs."""

    def test_requires_names_only_roster_agents(self):
        for agent, needs in REQUIRES.items():
            assert agent in AGENTS
            assert set(needs) <= set(AGENTS)

    def test_requires_is_what_the_nodes_raise_on(self):
        """Each entry is a raise verified at the node: PortfolioAnalysisAgent
        on missing holdings, RebalanceAgent on missing prices; ResearchAgent
        on a missing screening block. The rebalance target is not an entry
        (KNOWN_GAPS: the target is the IPS's, never the optimiser's)."""
        assert REQUIRES == {
            "PortfolioAnalysisAgent": ("DataAgent",),
            "RebalanceAgent": ("DataAgent",),
            "ComplianceAgent": ("PortfolioAnalysisAgent",),
            "ResearchAgent": ("ScreeningAgent",),
        }


class TestPortfolioWeights:
    """Test portfolio weights validation."""
    
    def test_valid_weights(self):
        """Test valid portfolio weights."""
        weights = PortfolioWeights(weights={"SPY": 0.6, "TLT": 0.4})
        assert sum(weights.weights.values()) == 1.0
    
    def test_weights_must_sum_to_one(self):
        """Test that weights must sum to ~1.0."""
        with pytest.raises(ValueError):
            PortfolioWeights(weights={"SPY": 0.5, "TLT": 0.3})  # Sums to 0.8
    
    def test_negative_weights_rejected(self):
        """Test that negative weights are rejected."""
        with pytest.raises(ValueError):
            PortfolioWeights(weights={"SPY": 1.2, "TLT": -0.2})  # Negative weight


# =============================================================================
# VALIDATOR TESTS
# =============================================================================

class TestTickerValidation:
    """Test ticker validation functions."""
    
    def test_known_etfs(self):
        """Test that known ETFs are recognized."""
        assert is_known_ticker("SPY")
        assert is_known_ticker("TLT")
        assert is_known_ticker("GLD")
        assert is_known_ticker("VWO")
    
    def test_known_stocks(self):
        """Test that known stocks are recognized."""
        assert is_known_ticker("AAPL")
        assert is_known_ticker("MSFT")
        assert is_known_ticker("GOOGL")
    
    def test_unknown_ticker(self):
        """Test that unknown tickers are flagged."""
        assert not is_known_ticker("XYZZY")
        assert not is_known_ticker("FAKE123")
    
    def test_valid_ticker_format(self):
        """Test ticker format validation."""
        assert is_valid_ticker_format("SPY")
        assert is_valid_ticker_format("AAPL")
        assert is_valid_ticker_format("BRK.B")
        assert is_valid_ticker_format("^VIX")
        
        assert not is_valid_ticker_format("")
        assert not is_valid_ticker_format("TOOLONGTICKER")
    
    def test_validate_tickers_mixed(self):
        """Test validation of mixed ticker list."""
        valid, unknown, invalid = validate_tickers(["SPY", "TLT", "XYZZY", "123INVALID"])
        
        assert "SPY" in valid
        assert "TLT" in valid
        assert "XYZZY" in unknown  # Valid format but not in database
        # "123INVALID" may be filtered depending on format rules
    
    def test_suggest_ticker(self):
        """Test ticker suggestion for common mistakes."""
        assert suggest_ticker("GOLD") == "GLD"
        assert suggest_ticker("BONDS") == "BND"
        assert suggest_ticker("SP500") == "SPY"
        assert suggest_ticker("BITCOIN") is None  # No valid suggestion


class TestWeightValidation:
    """Test weight validation functions."""
    
    def test_valid_weights(self):
        """Test valid portfolio weights."""
        is_valid, errors = validate_weights({"SPY": 0.6, "TLT": 0.4})
        assert is_valid
        assert len(errors) == 0
    
    def test_weights_dont_sum_to_one(self):
        """Test weights that don't sum to 1.0."""
        is_valid, errors = validate_weights({"SPY": 0.5, "TLT": 0.3})
        assert not is_valid
        assert any("sum" in e.lower() for e in errors)
    
    def test_negative_weight(self):
        """Test negative weight detection."""
        is_valid, errors = validate_weights({"SPY": 1.2, "TLT": -0.2})
        assert not is_valid
        assert any("negative" in e.lower() for e in errors)


class TestOptimizationRequestValidation:
    """Test complete optimization request validation."""
    
    def test_valid_request(self):
        """Test a valid optimization request."""
        result = validate_optimization_request(
            tickers=["SPY", "TLT", "GLD"],
            max_volatility=0.12,
            period="5Y"
        )
        assert result.is_valid
    
    def test_no_tickers(self):
        """Test that no tickers causes error."""
        result = validate_optimization_request(
            tickers=[],
            max_volatility=0.12
        )
        assert not result.is_valid
        assert any("no tickers" in e.lower() for e in result.errors)
    
    def test_invalid_volatility(self):
        """Test invalid volatility constraint."""
        result = validate_optimization_request(
            tickers=["SPY", "TLT"],
            max_volatility=2.0  # 200% is unrealistic
        )
        assert not result.is_valid
    
    def test_unknown_ticker_warning(self):
        """Test that unknown tickers generate warnings."""
        result = validate_optimization_request(
            tickers=["SPY", "XYZZY"],
            max_volatility=0.12
        )
        # XYZZY is valid format but unknown - should be warning, not error
        assert len(result.warnings) > 0


# =============================================================================
# SAFE PARSE TESTS
# =============================================================================
