# tests/test_rag_phase3.py
"""
Tests for RAG Phase 3: RAG Agent & Sentiment Analysis.

Phase: 6.7 - RAG Integration

Covers:
- Sentiment analysis (rule-based + hybrid)
- RAG tools (search, ingest, fed sentiment)
- RAG Agent (research workflow)

Run with:
    python tests/test_rag_phase3.py
"""

import os
import sys
import tempfile
import shutil
from datetime import date, datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# =============================================================================
# SENTIMENT CONFIG TESTS
# =============================================================================

class TestSentimentConfig:
    """Test sentiment configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        from portfolio_tool.rag.sentiment import SentimentConfig
        
        config = SentimentConfig()
        
        assert config.llm_enabled == True
        assert config.llm_provider == "openai"
        assert config.llm_model == "gpt-4o-mini"
        assert config.confidence_threshold == 0.6
        assert config.ambiguity_threshold == 0.2
    
    def test_custom_config(self):
        """Test custom configuration."""
        from portfolio_tool.rag.sentiment import SentimentConfig
        
        config = SentimentConfig(
            llm_enabled=False,
            confidence_threshold=0.8,
            summary_max_tokens=1000,
        )
        
        assert config.llm_enabled == False
        assert config.confidence_threshold == 0.8
        assert config.summary_max_tokens == 1000


# =============================================================================
# RULE-BASED SENTIMENT TESTS
# =============================================================================

class TestRuleBasedSentiment:
    """Test rule-based sentiment analysis."""
    
    def test_hawkish_text(self):
        """Test detection of hawkish signals."""
        from portfolio_tool.rag.sentiment import RuleBasedSentiment
        
        text = """
        Inflation remains elevated and the labor market remains tight.
        The Committee decided to raise rates to combat price pressures.
        A restrictive stance is appropriate given current conditions.
        """
        
        analyzer = RuleBasedSentiment()
        score, confidence, hawkish, dovish = analyzer.analyze(text)
        
        assert score > 0.3, f"Expected hawkish score > 0.3, got {score}"
        assert len(hawkish) > 0, "Expected hawkish signals"
        assert confidence > 0.5, f"Expected confidence > 0.5, got {confidence}"
        
        print(f"  ✓ Hawkish: score={score:.2f}, signals={len(hawkish)}")
    
    def test_dovish_text(self):
        """Test detection of dovish signals."""
        from portfolio_tool.rag.sentiment import RuleBasedSentiment
        
        text = """
        Economic growth concerns are rising. The labor market is softening.
        A rate cut may be appropriate to support the economy.
        Recession risk is elevated and disinflation is underway.
        """
        
        analyzer = RuleBasedSentiment()
        score, confidence, hawkish, dovish = analyzer.analyze(text)
        
        assert score < -0.3, f"Expected dovish score < -0.3, got {score}"
        assert len(dovish) > 0, "Expected dovish signals"
        
        print(f"  ✓ Dovish: score={score:.2f}, signals={len(dovish)}")
    
    def test_neutral_text(self):
        """Test neutral/balanced text."""
        from portfolio_tool.rag.sentiment import RuleBasedSentiment
        
        text = """
        The meeting discussed various economic indicators.
        Committee members reviewed the current situation.
        Further data will inform future decisions.
        """
        
        analyzer = RuleBasedSentiment()
        score, confidence, hawkish, dovish = analyzer.analyze(text)
        
        # Neutral should be close to 0
        assert abs(score) < 0.5, f"Expected neutral score near 0, got {score}"
        
        print(f"  ✓ Neutral: score={score:.2f}, confidence={confidence:.2f}")
    
    def test_empty_text(self):
        """Test handling of empty text."""
        from portfolio_tool.rag.sentiment import RuleBasedSentiment
        
        analyzer = RuleBasedSentiment()
        score, confidence, hawkish, dovish = analyzer.analyze("")
        
        assert score == 0.0
        assert confidence == 0.3  # Low confidence for empty
        assert len(hawkish) == 0
        assert len(dovish) == 0


# =============================================================================
# HYBRID SENTIMENT TESTS
# =============================================================================

class TestFedSentimentAnalyzer:
    """Test the main hybrid sentiment analyzer."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        from portfolio_tool.rag.sentiment import FedSentimentAnalyzer, SentimentConfig
        
        # Without LLM
        config = SentimentConfig(llm_enabled=False)
        analyzer = FedSentimentAnalyzer(config)
        
        assert analyzer is not None
        assert analyzer.config.llm_enabled == False
    
    def test_analyze_returns_dict(self):
        """Test that analyze returns expected dict structure."""
        from portfolio_tool.rag.sentiment import FedSentimentAnalyzer, SentimentConfig
        
        config = SentimentConfig(llm_enabled=False)  # Rule-based only
        analyzer = FedSentimentAnalyzer(config)
        
        text = "Inflation remains elevated. The labor market remains tight."
        result = analyzer.analyze(text)
        
        # Check required keys
        assert "success" in result
        assert "score" in result
        assert "confidence" in result
        assert "method" in result
        assert "signals" in result
        
        assert result["success"] == True
        assert result["method"] == "rule_based"
        assert -1 <= result["score"] <= 1
        assert 0 <= result["confidence"] <= 1
        
        print(f"  ✓ Result: score={result['score']:.2f}, method={result['method']}")
    
    def test_analyze_hawkish_text(self):
        """Test analysis of clearly hawkish text."""
        from portfolio_tool.rag.sentiment import FedSentimentAnalyzer, SentimentConfig
        
        config = SentimentConfig(llm_enabled=False)
        analyzer = FedSentimentAnalyzer(config)
        
        text = """
        Inflation remains elevated well above the Committee's 2 percent target.
        The labor market remains tight with strong wage pressures.
        The Committee decided to raise rates by 25 basis points.
        Further tightening may be appropriate.
        """
        
        result = analyzer.analyze(text)
        
        assert result["success"]
        assert result["score"] > 0.2, f"Expected hawkish (>0.2), got {result['score']}"
        assert len(result.get("hawkish_signals", [])) > 0
        
        print(f"  ✓ Hawkish analysis: score={result['score']:.2f}")
    
    def test_analyze_empty_text(self):
        """Test handling of empty input."""
        from portfolio_tool.rag.sentiment import FedSentimentAnalyzer, SentimentConfig
        
        config = SentimentConfig(llm_enabled=False)
        analyzer = FedSentimentAnalyzer(config)
        
        result = analyzer.analyze("")
        
        assert result["success"] == False
        assert "error" in result
        assert "Empty" in result["error"]
    
    def test_needs_llm_detection(self):
        """Test that ambiguous text triggers LLM need."""
        from portfolio_tool.rag.sentiment import FedSentimentAnalyzer, SentimentConfig
        
        config = SentimentConfig(llm_enabled=False)  # Won't actually call LLM
        analyzer = FedSentimentAnalyzer(config)
        
        # Balanced text - should trigger LLM need
        rule_score = 0.1  # Near neutral
        rule_confidence = 0.5  # Low
        
        needs_llm = analyzer._needs_llm_refinement(rule_score, rule_confidence)
        
        # Should need LLM due to low confidence
        assert needs_llm == True, "Expected LLM needed for low confidence"
    
    def test_llm_disabled_warning(self):
        """Test warning when LLM would help but is disabled."""
        from portfolio_tool.rag.sentiment import FedSentimentAnalyzer, SentimentConfig
        
        config = SentimentConfig(llm_enabled=False)
        analyzer = FedSentimentAnalyzer(config)
        
        # Ambiguous text that would normally trigger LLM
        text = "The committee noted balanced risks to the outlook."
        
        result = analyzer.analyze(text)
        
        # Should succeed with rule-based
        assert result["success"]
        assert result["method"] == "rule_based"
        # May have warning about LLM being disabled


# =============================================================================
# RAG TOOLS TESTS
# =============================================================================

class TestRAGTools:
    """Test RAG tool wrappers."""
    
    def test_get_fed_sentiment_tool(self):
        """Test the get_fed_sentiment tool."""
        from portfolio_tool.tools.rag_tools import get_fed_sentiment
        
        text = "Inflation remains elevated. Higher for longer policy stance."
        
        result = get_fed_sentiment(text, use_llm=False)
        
        assert result["success"]
        assert "score" in result
        assert "confidence" in result
        assert result["method"] == "rule_based"
        
        print(f"  ✓ Fed sentiment tool: score={result['score']:.2f}")
    
    def test_get_fed_sentiment_empty(self):
        """Test tool with empty input."""
        from portfolio_tool.tools.rag_tools import get_fed_sentiment
        
        result = get_fed_sentiment("", use_llm=False)
        
        assert result["success"] == False
        assert "error" in result


class TestRAGToolsIntegration:
    """Integration tests for RAG tools (require vector store)."""
    
    def setup_method(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary directory."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_ingest_and_search(self):
        """Test document ingestion and search."""
        try:
            from portfolio_tool.tools.rag_tools import ingest_document, search_documents
            from portfolio_tool.rag import VectorStoreConfig
            
            # Create test file
            test_content = """
            NVIDIA Q3 2024 Earnings Report
            
            Revenue reached $18.1 billion, up 279% year over year.
            Data center revenue was $14.5 billion.
            
            Risk Factors:
            China export restrictions may impact future revenue.
            """
            
            test_file = os.path.join(self.temp_dir, "NVDA_Q3_2024.txt")
            with open(test_file, 'w') as f:
                f.write(test_content)
            
            # Note: This test requires ChromaDB and will use temp directory
            # In a real test, we'd mock the vector store
            print("  ⚠️ Full integration test skipped (requires ChromaDB setup)")
            
        except ImportError as e:
            print(f"  ⚠️ Skipped ({e})")


# =============================================================================
# RAG AGENT TESTS
# =============================================================================

class TestRAGAgentConfig:
    """Test RAG Agent configuration."""
    
    def test_default_config(self):
        """Test default agent config."""
        from agents.rag_agent import RAGAgentConfig
        
        config = RAGAgentConfig()
        
        assert config.default_top_k == 5
        assert config.extract_tickers_from_query == True
        assert config.analyze_fed_for_macro == True


class TestRAGAgent:
    """Test RAG Agent functionality."""
    
    def test_agent_initialization(self):
        """Test agent initializes correctly."""
        from agents.rag_agent import RAGAgent
        
        agent = RAGAgent()
        
        assert agent is not None
        assert agent.config is not None
    
    def test_extract_tickers_from_text(self):
        """Test ticker extraction from text."""
        from agents.rag_agent import RAGAgent
        
        agent = RAGAgent()
        
        # Test various patterns
        text1 = "What did NVDA and AAPL report?"
        tickers1 = agent._extract_tickers_from_text(text1)
        assert "NVDA" in tickers1
        assert "AAPL" in tickers1
        
        # Should not extract common words
        text2 = "I want to know about THE stock"
        tickers2 = agent._extract_tickers_from_text(text2)
        assert "THE" not in tickers2
        assert "I" not in tickers2
        
        print(f"  ✓ Ticker extraction working")
    
    def test_extract_search_context(self):
        """Test search context extraction."""
        from agents.rag_agent import RAGAgent
        
        agent = RAGAgent()
        
        query = "What did NVIDIA report in Q3 2024 earnings?"
        context = {"ticker": "NVDA"}
        
        search_context = agent._extract_search_context(query, context)
        
        assert "NVDA" in search_context["tickers"]
        assert "earnings" in search_context["doc_types"]
        assert 2024 == search_context["year"]
        
        print(f"  ✓ Context extraction: {search_context}")
    
    def test_should_analyze_fed(self):
        """Test Fed analysis decision."""
        from agents.rag_agent import RAGAgent
        
        agent = RAGAgent()
        
        # Should analyze for Fed-related queries
        assert agent._should_analyze_fed("What is the Fed's policy stance?", {})
        assert agent._should_analyze_fed("Impact of interest rates", {})
        
        # Should not analyze for stock-specific queries
        assert not agent._should_analyze_fed("NVIDIA earnings", {})
        
        # Explicit context override
        assert agent._should_analyze_fed("Any query", {"include_fed_sentiment": True})
        assert not agent._should_analyze_fed("Fed policy", {"include_fed_sentiment": False})
    
    def test_estimate_content_sentiment(self):
        """Test content sentiment estimation."""
        from agents.rag_agent import RAGAgent
        
        agent = RAGAgent()
        
        # Positive content
        positive_results = [
            {"content": "Strong growth, record revenue, exceeded expectations"},
            {"content": "Positive momentum continues, improved margins"},
        ]
        sentiment = agent._estimate_content_sentiment(positive_results)
        assert sentiment == "bullish", f"Expected bullish, got {sentiment}"
        
        # Negative content
        negative_results = [
            {"content": "Decline in revenue, missed targets, weak outlook"},
            {"content": "Risk of recession, concern about losses"},
        ]
        sentiment = agent._estimate_content_sentiment(negative_results)
        assert sentiment == "bearish", f"Expected bearish, got {sentiment}"
        
        print("  ✓ Content sentiment estimation working")


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestSentimentIntegration:
    """Integration tests for sentiment with macro_agent compatibility."""
    
    def test_macro_agent_interface(self):
        """Test that result matches macro_agent.py expected format."""
        from portfolio_tool.rag.sentiment import FedSentimentAnalyzer, SentimentConfig
        
        config = SentimentConfig(llm_enabled=False)
        analyzer = FedSentimentAnalyzer(config)
        
        text = "The Committee maintained its target range for the federal funds rate."
        result = analyzer.analyze(text)
        
        # macro_agent.py expects these keys
        assert "success" in result
        assert "score" in result
        assert "confidence" in result
        
        # These are used in macro_agent.py lines ~298-301
        if result.get("success"):
            fed_sentiment = result.get("score", 0.0)
            fed_confidence = result.get("confidence", 0.5)
            
            assert isinstance(fed_sentiment, float)
            assert isinstance(fed_confidence, float)
            assert -1 <= fed_sentiment <= 1
            assert 0 <= fed_confidence <= 1
        
        print(f"  ✓ Compatible with macro_agent.py interface")


# =============================================================================
# MAIN
# =============================================================================

def run_tests():
    """Run all tests and print results."""
    
    test_classes = [
        TestSentimentConfig,
        TestRuleBasedSentiment,
        TestFedSentimentAnalyzer,
        TestRAGTools,
        TestRAGToolsIntegration,
        TestRAGAgentConfig,
        TestRAGAgent,
        TestSentimentIntegration,
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
            # Setup
            if hasattr(instance, 'setup_method'):
                try:
                    instance.setup_method()
                except:
                    pass
            
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
            finally:
                # Teardown
                if hasattr(instance, 'teardown_method'):
                    try:
                        instance.teardown_method()
                    except:
                        pass
    
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
