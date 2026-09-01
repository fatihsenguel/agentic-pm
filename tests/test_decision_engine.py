# tests/test_decision_engine.py
"""
Test suite for the Decision Engine (Phase 6.6).

Run with: pytest tests/test_decision_engine.py -v

These tests validate:
1. Risk assessment correctly identifies breaches
2. Decision logic produces appropriate outputs
3. HOLD is correctly chosen when no action is warranted
4. Critical states trigger immediate action recommendations
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


import pytest
from agents.decision_schemas import (
    DecisionType,
    RiskStatus,
    RiskAssessment,
    PMDecisionSummary,
    DecisionContext
)

from agents.decision_engine import (
    assess_portfolio_risk,
    assess_decision_needed,
    run_decision_assessment,
    calculate_hhi,
    should_generate_decision_summary
)
from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.config import config


class TestHHICalculation:
    """Test Herfindahl-Hirschman Index calculation."""
    
    def test_equal_weights_low_hhi(self):
        """Equal weights across many assets = low concentration."""
        weights = {"A": 0.2, "B": 0.2, "C": 0.2, "D": 0.2, "E": 0.2}
        hhi = calculate_hhi(weights)
        assert hhi == pytest.approx(0.2, rel=0.01)  # 5 * 0.2^2 = 0.2
    
    def test_single_asset_max_hhi(self):
        """Single asset = maximum concentration."""
        weights = {"A": 1.0}
        hhi = calculate_hhi(weights)
        assert hhi == 1.0
    
    def test_concentrated_portfolio(self):
        """Concentrated portfolio has high HHI."""
        weights = {"A": 0.7, "B": 0.2, "C": 0.1}
        hhi = calculate_hhi(weights)
        assert hhi > 0.5  # 0.49 + 0.04 + 0.01 = 0.54


class TestRiskAssessment:
    """Test portfolio risk assessment."""
    
    def test_acceptable_risk(self):
        """Well-diversified portfolio with no breaches."""
        weights = {
            "SPY": 0.25, "TLT": 0.25, "GLD": 0.15, 
            "VEA": 0.15, "VWO": 0.10, "BND": 0.10
        }
        risk = assess_portfolio_risk(weights, config)
        
        assert risk.status == RiskStatus.ACCEPTABLE
        assert len(risk.breaches) == 0
        assert risk.suggested_action == DecisionType.HOLD
    
    def test_concentration_breach(self):
        """Single position exceeds max concentration."""
        weights = {"SPY": 0.50, "TLT": 0.30, "GLD": 0.20}
        risk = assess_portfolio_risk(weights, config)
        
        # SPY at 50% exceeds default 30% max concentration
        assert risk.status in (RiskStatus.ELEVATED, RiskStatus.CRITICAL)
        assert any("Concentration" in b for b in risk.breaches)
    
    def test_under_diversified(self):
        """Too few positions."""
        weights = {"SPY": 0.6, "TLT": 0.4}  # Only 2 positions
        risk = assess_portfolio_risk(weights, config)
        
        # Should flag under-diversification (min is 5)
        assert any("diversif" in b.lower() for b in risk.breaches)
    
    def test_empty_portfolio(self):
        """Empty portfolio is critical."""
        risk = assess_portfolio_risk({}, config)
        assert risk.status == RiskStatus.CRITICAL


class TestDecisionEngine:
    """Test the decision logic."""
    
    def test_hold_when_no_issues(self):
        """HOLD when drift is low and risk is acceptable."""
        weights = {
            "SPY": 0.25, "TLT": 0.25, "GLD": 0.15, 
            "VEA": 0.15, "VWO": 0.10, "BND": 0.10
        }
        
        risk, decision = run_decision_assessment(
            current_weights=weights,
            max_drift=0.02,  # 2% drift - well below 5% threshold
            macro_regime="neutral"
        )
        
        assert decision.decision == DecisionType.HOLD
        assert decision.trade_required == False
        assert decision.confidence >= 0.8
        print(f"\n{decision.format_summary()}")
    
    def test_rebalance_on_high_drift(self):
        """REBALANCE when drift significantly exceeds threshold."""
        weights = {"SPY": 0.25, "TLT": 0.25, "GLD": 0.15, "VEA": 0.15, "VWO": 0.10, "BND": 0.10}
        
        risk, decision = run_decision_assessment(
            current_weights=weights,
            max_drift=0.12,  # 12% drift - well above 5% threshold
            macro_regime="neutral"
        )
        
        assert decision.decision == DecisionType.REBALANCE
        assert decision.trade_required == True
        print(f"\n{decision.format_summary()}")
    
    def test_hedge_in_crisis(self):
        """HEDGE recommended in crisis regime."""
        weights = {"SPY": 0.25, "TLT": 0.25, "GLD": 0.15, "VEA": 0.15, "VWO": 0.10, "BND": 0.10}
        
        risk, decision = run_decision_assessment(
            current_weights=weights,
            max_drift=0.03,  # Low drift
            macro_regime="crisis"  # But crisis!
        )
        
        assert decision.decision == DecisionType.HEDGE
        assert decision.trade_required == True
        assert "crisis" in decision.rationale.lower() or "Crisis" in str(decision.key_risks)
        print(f"\n{decision.format_summary()}")
    
    def test_rebalance_on_critical_risk(self):
        """REBALANCE when risk status is CRITICAL."""
        weights = {"SPY": 0.60, "TLT": 0.40}  # Concentrated + under-diversified
        
        risk, decision = run_decision_assessment(
            current_weights=weights,
            max_drift=0.01,  # Low drift
            macro_regime="neutral"
        )
        
        # Should still recommend rebalance due to risk
        assert risk.status == RiskStatus.CRITICAL
        assert decision.decision == DecisionType.REBALANCE
        print(f"\n{decision.format_summary()}")
    
    def test_tilt_on_moderate_drift(self):
        """TILT or HOLD when drift is just above threshold."""
        weights = {"SPY": 0.20, "TLT": 0.20, "GLD": 0.20, "VEA": 0.20, "VWO": 0.20}
        
        risk, decision = run_decision_assessment(
            current_weights=weights,
            max_drift=0.06,  # 6% drift - just above 5% threshold
            macro_regime="neutral"
        )
        
        # Should be TILT or REBALANCE depending on exact logic
        assert decision.decision in (DecisionType.TILT, DecisionType.REBALANCE)
        print(f"\n{decision.format_summary()}")


class TestQueryIntentFilter:
    """Test that decision summary is only generated for DECISION queries."""
    
    def test_decision_query_generates_summary(self):
        assert should_generate_decision_summary("decision") == True
    
    def test_information_query_no_summary(self):
        assert should_generate_decision_summary("information") == False
    
    def test_operational_query_no_summary(self):
        assert should_generate_decision_summary("operational") == False
    
    def test_analysis_query_no_summary(self):
        assert should_generate_decision_summary("analysis") == False


class TestOutputFormatting:
    """Test the formatted output looks correct."""
    
    def test_decision_summary_format(self):
        """Decision summary should produce readable output."""
        weights = {"SPY": 0.25, "TLT": 0.25, "GLD": 0.15, "VEA": 0.15, "VWO": 0.10, "BND": 0.10}
        
        risk, decision = run_decision_assessment(
            current_weights=weights,
            max_drift=0.02,
            macro_regime="neutral"
        )
        
        formatted = decision.format_summary()
        
        # Check key elements are present
        assert "DECISION SUMMARY" in formatted
        assert "HOLD" in formatted
        assert "Confidence" in formatted
        assert "Trade Required" in formatted
        assert "RISK ASSESSMENT" in formatted
        
        print(f"\n{formatted}")
    
    def test_risk_assessment_format(self):
        """Risk assessment should produce readable output."""
        weights = {"SPY": 0.50, "TLT": 0.30, "GLD": 0.20}
        
        risk = assess_portfolio_risk(weights, config)
        formatted = risk.format_summary()
        
        assert "Status" in formatted
        print(f"\n{formatted}")


# =============================================================================
# INTEGRATION TEST: Full Pipeline
# =============================================================================

class TestFullPipeline:
    """Test the complete decision pipeline."""
    
    def test_interview_scenario_hold(self):
        """
        Interview scenario: "Show me when the system recommends NOT trading"
        
        Setup: Well-balanced portfolio, low drift, neutral macro
        Expected: HOLD with clear rationale
        """
        weights = {
            "SPY": 0.30, "TLT": 0.25, "GLD": 0.10, 
            "VEA": 0.15, "VWO": 0.10, "BND": 0.10
        }
        
        risk, decision = run_decision_assessment(
            current_weights=weights,
            target_weights={
                "SPY": 0.30, "TLT": 0.25, "GLD": 0.10, 
                "VEA": 0.15, "VWO": 0.10, "BND": 0.10
            },
            max_drift=0.02,  # 2% drift
            macro_regime="neutral",
            portfolio_volatility=0.12
        )
        
        assert decision.decision == DecisionType.HOLD
        assert "within tolerance" in decision.rationale.lower() or "no action" in decision.rationale.lower()
        
        print("\n" + "="*60)
        print("INTERVIEW SCENARIO: When NOT to trade")
        print("="*60)
        print(decision.format_summary())
    
    def test_interview_scenario_action_needed(self):
        """
        Interview scenario: "Show me when the system recommends action"
        
        Setup: High drift, elevated risk
        Expected: REBALANCE with clear rationale
        """
        weights = {
            "SPY": 0.45,  # Drifted up
            "TLT": 0.15,  # Drifted down
            "GLD": 0.10, 
            "VEA": 0.15, 
            "VWO": 0.10, 
            "BND": 0.05   # Drifted down
        }
        
        risk, decision = run_decision_assessment(
            current_weights=weights,
            target_weights={
                "SPY": 0.30, "TLT": 0.25, "GLD": 0.10, 
                "VEA": 0.15, "VWO": 0.10, "BND": 0.10
            },
            max_drift=0.15,  # 15% drift
            macro_regime="risk_off"
        )
        
        assert decision.decision in (DecisionType.REBALANCE, DecisionType.TILT)
        assert decision.trade_required == True
        
        print("\n" + "="*60)
        print("INTERVIEW SCENARIO: When to take action")
        print("="*60)
        print(decision.format_summary())


if __name__ == "__main__":
    # Quick manual test
    print("Running quick validation...\n")
    
    test = TestFullPipeline()
    test.test_interview_scenario_hold()
    test.test_interview_scenario_action_needed()
    
    print("\n✅ Quick validation passed!")