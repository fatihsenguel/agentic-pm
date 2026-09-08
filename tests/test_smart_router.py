# tests/test_smart_router.py
# Purpose: Test the Smart Router and validation (Phase 6.1 + 6.12)
# Run with: pytest tests/test_smart_router.py -v

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.schemas import (
    AGENTS,
    REQUIRES,
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

    def test_out_of_scope_rejects_a_plan(self):
        """out_of_scope with agents planned must raise, not be trimmed."""
        data = {
            "intent": "out_of_scope",
            "confidence": 0.9,
            "agents_needed": [
                {"agent": "DataAgent", "task_description": "Fetch NVDA", "priority": 1}
            ],
            "execution_order": ["DataAgent"],
            "parameters": {},
            "reasoning": "Asks whether to buy a security",
        }

        with pytest.raises(ValueError):
            RouterDecision.model_validate(data)

    def test_out_of_scope_with_empty_plan_validates(self):
        data = {
            "intent": "out_of_scope",
            "confidence": 0.9,
            "agents_needed": [],
            "execution_order": [],
            "parameters": {},
            "reasoning": "Asks whether to buy a security",
        }

        decision = RouterDecision.model_validate(data)
        assert decision.intent == "out_of_scope"
        assert decision.execution_order == []

    # --- compliance: three plan shapes, decided by the parameters ---------

    @staticmethod
    def _compliance(plan, **params):
        return {
            "intent": "compliance",
            "confidence": 0.9,
            "agents_needed": [
                {"agent": a, "task_description": "check the policy", "priority": i + 1}
                for i, a in enumerate(plan)
            ],
            "execution_order": plan,
            "parameters": params,
            "reasoning": "policy question",
        }

    def test_compliance_portfolio_check_needs_the_analysis_agents(self):
        full = ["DataAgent", "PortfolioAnalysisAgent", "ComplianceAgent"]
        decision = RouterDecision.model_validate(self._compliance(full))
        assert decision.execution_order == full
        with pytest.raises(ValueError, match="over the portfolio"):
            RouterDecision.model_validate(self._compliance(["ComplianceAgent"]))
        with pytest.raises(ValueError, match="over the portfolio"):
            RouterDecision.model_validate(self._compliance(["DataAgent", "ComplianceAgent"]))

    def test_compliance_hypothetical_is_compliance_agent_alone(self):
        decision = RouterDecision.model_validate(
            self._compliance(["ComplianceAgent"], hypothetical_weight=0.15))
        assert decision.parameters.hypothetical_weight == 0.15
        with pytest.raises(ValueError, match="for hypothetical_weight"):
            RouterDecision.model_validate(self._compliance(
                ["DataAgent", "PortfolioAnalysisAgent", "ComplianceAgent"], hypothetical_weight=0.15))

    def test_compliance_topic_is_compliance_agent_alone(self):
        decision = RouterDecision.model_validate(
            self._compliance(["ComplianceAgent"], policy_topic="currency risk"))
        assert decision.parameters.policy_topic == "currency risk"
        with pytest.raises(ValueError, match="for policy_topic"):
            RouterDecision.model_validate(self._compliance(
                ["DataAgent", "PortfolioAnalysisAgent", "ComplianceAgent"], policy_topic="cash"))

    def test_compliance_rejects_both_modes(self):
        with pytest.raises(ValueError, match="at most one"):
            RouterDecision.model_validate(self._compliance(
                ["ComplianceAgent"], hypothetical_weight=0.15, policy_topic="cash"))

    def test_mode_parameters_belong_to_compliance(self):
        data = self._compliance(["DataAgent"], hypothetical_weight=0.15)
        data["intent"] = "data_fetch"
        with pytest.raises(ValueError, match="belong to intent compliance"):
            RouterDecision.model_validate(data)

    def test_hypothetical_weight_is_a_fraction(self):
        with pytest.raises(ValueError):
            RouterDecision.model_validate(self._compliance(["ComplianceAgent"], hypothetical_weight=15))


class TestDependencies:
    """REQUIRES: an agent runs only after what it needs, and ComplianceAgent
    only under intent compliance. The plan shapes below are the ones the
    "too big" flip and its two diagnostics produced on 8 September
    (KNOWN_GAPS): each validated and ran until a node raised on missing
    input. A rejection here is a repair attempt with the reason stated; a
    reorder would be the repair-instead-of-raise shape."""

    @staticmethod
    def _plan(intent, order):
        return {
            "intent": intent,
            "confidence": 0.9,
            "agents_needed": [
                {"agent": a, "task_description": "do the planned thing", "priority": i + 1}
                for i, a in enumerate(order)
            ],
            "execution_order": list(order),
            "parameters": {},
            "reasoning": "a plan shape from the diagnostics",
        }

    def test_requires_names_only_roster_agents(self):
        for agent, needs in REQUIRES.items():
            assert agent in AGENTS
            assert set(needs) <= set(AGENTS)
        assert REQUIRES["PortfolioAnalysisAgent"] == ("DataAgent",)

    def test_analysis_agent_alone_is_rejected(self):
        with pytest.raises(ValueError, match="PortfolioAnalysisAgent requires DataAgent before it"):
            RouterDecision.model_validate(self._plan("risk_analysis", ["PortfolioAnalysisAgent"]))

    def test_analysis_agent_before_data_agent_is_rejected_not_reordered(self):
        with pytest.raises(ValueError, match="requires DataAgent before it"):
            RouterDecision.model_validate(
                self._plan("data_fetch", ["PortfolioAnalysisAgent", "DataAgent"]))

    def test_an_autofilled_order_is_checked(self):
        data = self._plan("risk_analysis", ["PortfolioAnalysisAgent"])
        data["execution_order"] = []
        with pytest.raises(ValueError, match="requires DataAgent before it"):
            RouterDecision.model_validate(data)

    def test_analysis_agent_after_data_agent_validates(self):
        decision = RouterDecision.model_validate(
            self._plan("data_fetch", ["DataAgent", "PortfolioAnalysisAgent"]))
        assert decision.execution_order == ["DataAgent", "PortfolioAnalysisAgent"]

    def test_compliance_agent_under_another_intent_is_rejected(self):
        shapes = (
            ("risk_analysis", ["ComplianceAgent"]),
            ("data_fetch", ["DataAgent", "PortfolioAnalysisAgent", "ComplianceAgent"]),
            ("combined", ["DataAgent", "ComplianceAgent"]),
        )
        for intent, order in shapes:
            with pytest.raises(ValueError, match="only under intent compliance"):
                RouterDecision.model_validate(self._plan(intent, order))

    def test_the_error_names_the_plan(self):
        with pytest.raises(ValueError, match=r"the plan is \['PortfolioAnalysisAgent'\]"):
            RouterDecision.model_validate(self._plan("risk_analysis", ["PortfolioAnalysisAgent"]))

    def test_plans_still_accepted(self):
        """Shapes the router is shown or produces today and REQUIRES does not
        touch: rule 6's DataAgent alone, the prompt's own [OptimizationAgent]
        alone and backtest with no optimiser, the rebalance with no target.
        Whether they can run is the node's business until an entry is added."""
        shapes = (
            ("risk_analysis", ["DataAgent"]),
            ("optimization", ["OptimizationAgent"]),
            ("optimization", ["DataAgent", "OptimizationAgent"]),
            ("backtest", ["DataAgent", "BacktestAgent"]),
            ("rebalancing", ["DataAgent", "RebalanceAgent"]),
            ("macro_analysis", ["MacroAgent"]),
        )
        for intent, order in shapes:
            decision = RouterDecision.model_validate(self._plan(intent, order))
            assert decision.execution_order == order


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