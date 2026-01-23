# tests/test_smart_router.py
# Purpose: Test the Smart Router and validation (Phase 6.1 + 6.12)
# Run with: pytest tests/test_smart_router.py -v

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.schemas import (
    RouterDecision,
    IntentType,
    AgentName,
    AgentTask,
    ExtractedParameters,
    PortfolioWeights,
    TradeProposal,
    TradeAction,
    safe_parse_router_response,
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


# =============================================================================
# SCHEMA TESTS
# =============================================================================

class TestRouterDecision:
    """Test RouterDecision schema validation."""
    
    def test_valid_simple_decision(self):
        """Test a simple valid routing decision."""
        data = {
            "intent": "macro_analysis",
            "confidence": 0.9,
            "agents_needed": [
                {"agent": "MacroAgent", "task_description": "Analyze VIX and regime", "priority": 1}
            ],
            "execution_order": ["MacroAgent"],
            "parameters": {"tickers": [], "period": None},
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "User asked about market conditions",
        }
        
        decision = RouterDecision.model_validate(data)
        assert decision.intent == IntentType.MACRO_ANALYSIS
        assert decision.confidence == 0.9
        assert len(decision.agents_needed) == 1
    
    def test_valid_multi_step_decision(self):
        """Test a multi-step workflow decision."""
        data = {
            "intent": "combined",
            "confidence": 0.85,
            "agents_needed": [
                {"agent": "MacroAgent", "task_description": "Check regime", "priority": 1},
                {"agent": "RebalanceAgent", "task_description": "Generate TAA signal", "priority": 2}
            ],
            "execution_order": ["MacroAgent", "RebalanceAgent"],
            "parameters": {"tickers": ["SPY", "TLT"]},
            "is_multi_step": True,
            "requires_confirmation": False,
            "reasoning": "Multi-step: macro then rebalance",
        }
        
        decision = RouterDecision.model_validate(data)
        assert decision.is_multi_step is True
        assert len(decision.execution_order) == 2
    
    def test_invalid_agent_name(self):
        """Test that invalid agent names are rejected."""
        data = {
            "intent": "optimization",
            "confidence": 0.9,
            "agents_needed": [
                {"agent": "FakeAgent", "task_description": "Do nothing", "priority": 1}
            ],
            "execution_order": ["FakeAgent"],
            "parameters": {},
            "reasoning": "Test",
        }
        
        # Should raise validation error for unknown agent
        with pytest.raises(ValueError):
            RouterDecision.model_validate(data)
    
    def test_execution_order_mismatch(self):
        """Test that execution_order must match agents_needed."""
        data = {
            "intent": "optimization",
            "confidence": 0.9,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch data", "priority": 1}
            ],
            "execution_order": ["DataAgent", "OptimizationAgent"],  # Mismatch!
            "parameters": {},
            "reasoning": "Test",
        }
        
        with pytest.raises(ValueError):
            RouterDecision.model_validate(data)
    
    def test_clarification_requires_question(self):
        """Test that clarification_needed intent requires question."""
        data = {
            "intent": "clarification_needed",
            "confidence": 0.3,
            "agents_needed": [],
            "execution_order": [],
            "parameters": {},
            "reasoning": "Unclear request",
            "clarification_question": None,  # Missing!
        }
        
        with pytest.raises(ValueError):
            RouterDecision.model_validate(data)


class TestExtractedParameters:
    """Test parameter extraction validation."""
    
    def test_valid_tickers(self):
        """Test valid ticker extraction."""
        params = ExtractedParameters(tickers=["SPY", "TLT", "GLD"])
        assert params.tickers == ["SPY", "TLT", "GLD"]
    
    def test_ticker_normalization(self):
        """Test that tickers are normalized to uppercase."""
        params = ExtractedParameters(tickers=["spy", "tlt"])
        assert params.tickers == ["SPY", "TLT"]
    
    def test_invalid_ticker_filtered(self):
        """Test that invalid tickers are filtered out."""
        params = ExtractedParameters(tickers=["SPY", "INVALID_TOO_LONG_TICKER", "TLT"])
        # Invalid tickers should be filtered
        assert "INVALID_TOO_LONG_TICKER" not in params.tickers
    
    def test_valid_period(self):
        """Test valid period formats."""
        params = ExtractedParameters(period="5Y")
        assert params.period == "5Y"
        
        params = ExtractedParameters(period="6M")
        assert params.period == "6M"
    
    def test_invalid_period(self):
        """Test that invalid periods are rejected."""
        with pytest.raises(ValueError):
            ExtractedParameters(period="5 years")  # Invalid format
    
    def test_volatility_range(self):
        """Test volatility constraint validation."""
        params = ExtractedParameters(max_volatility=0.12)
        assert params.max_volatility == 0.12
        
        with pytest.raises(ValueError):
            ExtractedParameters(max_volatility=1.5)  # > 100%


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

class TestSafeParse:
    """Test safe parsing functions."""
    
    def test_safe_parse_success(self):
        """Test successful safe parse."""
        data = {
            "intent": "macro_analysis",
            "confidence": 0.9,
            "agents_needed": [
                {"agent": "MacroAgent", "task_description": "Analyze VIX and regime", "priority": 1}
            ],
            "execution_order": ["MacroAgent"],
            "parameters": {"tickers": []},
            "is_multi_step": False,
            "requires_confirmation": False,
            "reasoning": "Test reasoning",
        }
        
        decision, error = safe_parse_router_response(data)
        assert decision is not None, f"Parse failed with error: {error}"
        assert error is None
    
    def test_safe_parse_failure(self):
        """Test safe parse with invalid data."""
        data = {
            "intent": "invalid_intent",
            "confidence": "not a number",
        }
        
        decision, error = safe_parse_router_response(data)
        assert decision is None
        assert error is not None


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])