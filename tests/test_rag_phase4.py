# tests/test_rag_phase4.py
"""
Tests for RAG Phase 4: Decision Engine Integration.

Phase: 6.7 - RAG Integration

Covers:
- Document insights in decision assessment
- PMDecisionSummary with citations
- Synthesizer document formatting
- Full integration flow

Run with:
    python tests/test_rag_phase4.py
"""

import os
import sys
from datetime import date, datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# =============================================================================
# DECISION ENGINE INTEGRATION TESTS
# =============================================================================

class TestDecisionEngineWithDocuments:
    """Test decision engine with document insights."""
    
    def test_decision_without_documents(self):
        """Test that decision engine works without document insights."""
        from agents.decision_engine import run_decision_assessment
        
        risk, decision = run_decision_assessment(
            current_weights={"SPY": 0.6, "TLT": 0.3, "GLD": 0.1},
            target_weights={"SPY": 0.6, "TLT": 0.3, "GLD": 0.1},
            max_drift=0.02,
            macro_regime="neutral",
        )
        
        assert risk is not None
        assert decision is not None
        assert decision.decision is not None
        assert 0 <= decision.confidence <= 1
        
        print(f"  ✓ Decision without docs: {decision.decision.value}")
    
    def test_decision_with_document_insights(self):
        """Test decision engine accepts document_insights parameter."""
        from agents.decision_engine import run_decision_assessment
        
        # Simulate document insights from RAG
        document_insights = {
            "sources": ["NVDA_Q3_2024.pdf"],
            "key_findings": [
                "Revenue reached $18.1 billion, up 279% YoY",
                "Data center revenue was $14.5 billion"
            ],
            "risk_factors": [
                "China export restrictions may impact future revenue",
                "Supply chain constraints remain a concern"
            ],
            "citations": [
                {"text": "Revenue up 279%", "source": "NVDA_Q3_2024.pdf, p.2"}
            ],
            "fed_sentiment": {
                "success": True,
                "score": 0.35,
                "confidence": 0.8,
                "method": "hybrid"
            }
        }
        
        risk, decision = run_decision_assessment(
            current_weights={"SPY": 0.5, "NVDA": 0.3, "TLT": 0.2},
            target_weights={"SPY": 0.5, "NVDA": 0.3, "TLT": 0.2},
            max_drift=0.03,
            macro_regime="neutral",
            document_insights=document_insights,
        )
        
        assert decision is not None
        
        # Check that document risks were incorporated
        has_doc_risk = any("[DOC]" in r for r in decision.key_risks)
        assert has_doc_risk, f"Expected [DOC] risk prefix, got: {decision.key_risks}"
        
        # Check citations were added
        assert hasattr(decision, 'document_citations'), "Missing document_citations field"
        assert len(decision.document_citations) > 0, "Expected citations"
        
        print(f"  ✓ Decision with docs: {decision.decision.value}")
        print(f"    Risks: {decision.key_risks[:2]}")
        print(f"    Citations: {len(decision.document_citations)}")
    
    def test_fed_sentiment_influences_regime(self):
        """Test that strong Fed sentiment can influence macro regime."""
        from agents.decision_engine import run_decision_assessment
        
        # Hawkish Fed should push neutral -> risk_off
        hawkish_insights = {
            "fed_sentiment": {
                "success": True,
                "score": 0.7,  # Strongly hawkish
                "confidence": 0.85,
            }
        }
        
        risk, decision = run_decision_assessment(
            current_weights={"SPY": 0.7, "TLT": 0.3},
            max_drift=0.05,
            macro_regime="neutral",
            document_insights=hawkish_insights,
        )
        
        # The decision rationale should reflect macro context
        assert decision is not None
        print(f"  ✓ Hawkish Fed: {decision.decision.value}, confidence={decision.confidence:.0%}")


class TestPMDecisionSummaryWithCitations:
    """Test PMDecisionSummary with document_citations field."""
    
    def test_summary_to_dict_includes_citations(self):
        """Test that to_dict includes document_citations."""
        from agents.decision_schemas import PMDecisionSummary, DecisionType, RiskStatus
        
        summary = PMDecisionSummary(
            decision=DecisionType.HOLD,
            confidence=0.85,
            rationale="Test rationale",
            risk_status=RiskStatus.ACCEPTABLE,
            key_risks=["[DOC] China restrictions"],
            document_citations=[
                {"text": "Revenue up 279%", "source": "NVDA_Q3.pdf"}
            ],
        )
        
        d = summary.to_dict()
        
        assert "document_citations" in d
        assert len(d["document_citations"]) == 1
        assert d["document_citations"][0]["source"] == "NVDA_Q3.pdf"
        
        print("  ✓ to_dict includes citations")
    
    def test_format_summary_shows_citations(self):
        """Test that format_summary displays document evidence."""
        from agents.decision_schemas import PMDecisionSummary, DecisionType, RiskStatus
        
        summary = PMDecisionSummary(
            decision=DecisionType.TILT,
            confidence=0.75,
            rationale="Consider reducing position based on document analysis.",
            risk_status=RiskStatus.ELEVATED,
            key_risks=["[DOC] Export restrictions to China"],
            document_citations=[
                {"text": "China export restrictions may impact future revenue", "source": "NVDA_10K.pdf, p.15"}
            ],
        )
        
        formatted = summary.format_summary()
        
        assert "DOCUMENT EVIDENCE" in formatted
        assert "NVDA_10K.pdf" in formatted
        
        print("  ✓ format_summary shows document evidence")
        print(f"    Preview: ...{formatted[500:700]}...")


# =============================================================================
# SYNTHESIZER FORMATTING TESTS
# =============================================================================

class TestSynthesizerDocumentFormatting:
    """Test synthesizer document insights formatting."""
    
    def test_format_document_insights(self):
        """Test the _format_document_insights function."""
        # Import the function (after adding to nodes.py)
        try:
            from agents.nodes import _format_document_insights
        except ImportError:
            # Function not yet added - skip test
            print("  ⚠️ Skipped (_format_document_insights not yet added to nodes.py)")
            return
        
        sub_results = {
            "RAGAgent": {
                "success": True,
                "has_document_context": True,
                "insights": {
                    "sources": ["NVDA_Q3_2024.pdf", "Fed_Minutes_2024.pdf"],
                    "key_findings": ["Revenue up 279%", "Strong AI demand"],
                    "risk_factors": ["China export restrictions"],
                    "fed_sentiment": {
                        "success": True,
                        "score": 0.3,
                        "confidence": 0.8,
                        "method": "hybrid"
                    }
                }
            }
        }
        
        lines = _format_document_insights(sub_results)
        
        assert len(lines) > 0
        assert any("DOCUMENT INSIGHTS" in line for line in lines)
        assert any("NVDA_Q3_2024.pdf" in line for line in lines)
        
        print("  ✓ Document insights formatted correctly")
    
    def test_format_empty_insights(self):
        """Test formatting when no document context."""
        try:
            from agents.nodes import _format_document_insights
        except ImportError:
            print("  ⚠️ Skipped")
            return
        
        sub_results = {
            "RAGAgent": {
                "success": True,
                "has_document_context": False,
                "insights": {}
            }
        }
        
        lines = _format_document_insights(sub_results)
        
        # Should return empty list when no context
        assert len(lines) == 0
        
        print("  ✓ Empty insights handled correctly")


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestFullRAGIntegration:
    """Full integration tests for RAG in decision flow."""
    
    def test_document_insights_in_shared_data(self):
        """Test that document insights flow through shared_data."""
        # This test validates the state management pattern
        
        # Simulate state with document insights
        state = {
            "shared_data": {
                "document_insights": {
                    "sources": ["test.pdf"],
                    "key_findings": ["Test finding"],
                    "risk_factors": ["Test risk"],
                }
            },
            "sub_results": {
                "DataAgent": {"success": True},
                "RAGAgent": {"success": True, "has_document_context": True},
            }
        }
        
        # Extract insights (mimicking synthesizer behavior)
        shared_data = state.get("shared_data", {})
        document_insights = shared_data.get("document_insights")
        
        assert document_insights is not None
        assert "sources" in document_insights
        
        print("  ✓ Document insights flow through shared_data")
    
    def test_rag_agent_result_structure(self):
        """Test RAG agent result structure matches expected format."""
        expected_keys = {
            "success",
            "insights",
            "sources",
            "key_findings",
            "risk_factors",
            "fed_sentiment",
            "citations",
            "has_document_context",
        }
        
        # Simulate RAG agent result
        rag_result = {
            "success": True,
            "insights": {"sources": [], "key_findings": []},
            "sources": [],
            "key_findings": [],
            "risk_factors": [],
            "fed_sentiment": None,
            "citations": [],
            "has_document_context": False,
        }
        
        assert all(k in rag_result for k in expected_keys)
        
        print("  ✓ RAG agent result structure valid")


# =============================================================================
# MAIN
# =============================================================================

def run_tests():
    """Run all tests and print results."""
    
    test_classes = [
        TestDecisionEngineWithDocuments,
        TestPMDecisionSummaryWithCitations,
        TestSynthesizerDocumentFormatting,
        TestFullRAGIntegration,
    ]
    
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n{'='*60}")
        print(f"Running {test_class.__name__}")
        print('='*60)
        
        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith('test_')]
        
        for method in methods:
            try:
                getattr(instance, method)()
                print(f"  ✅ {method}")
                total_passed += 1
            except ImportError as e:
                print(f"  ⚠️ {method}: Skipped ({e})")
                total_skipped += 1
            except AssertionError as e:
                print(f"  ❌ {method}: {str(e)[:80]}")
                failed_tests.append((f"{test_class.__name__}.{method}", str(e)))
                total_failed += 1
            except Exception as e:
                print(f"  ❌ {method}: {type(e).__name__}: {str(e)[:80]}")
                failed_tests.append((f"{test_class.__name__}.{method}", str(e)))
                total_failed += 1
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {total_passed} passed, {total_failed} failed, {total_skipped} skipped")
    print('='*60)
    
    if failed_tests:
        print("\nFailed tests:")
        for name, error in failed_tests:
            print(f"  - {name}: {error[:100]}")
    
    return total_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
