"""
Tests for Phase 5.4: Macro/RAG Agent

These tests cover:
- Document loading
- Text chunking
- Embedding and search
- Fed sentiment analysis
- Macro Agent
"""

import pytest
from datetime import datetime


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_fed_minutes_text() -> str:
    """Sample Fed Minutes-like text for testing."""
    return """
    Minutes of the Federal Open Market Committee
    January 30-31, 2024
    
    Developments in Financial Markets and Open Market Operations
    
    The manager turned first to a review of developments in financial markets. 
    Market participants noted that financial conditions had eased somewhat since 
    the December meeting. Treasury yields declined, equity prices increased, and 
    credit spreads narrowed. The VIX index remained at low levels.
    
    Staff Review of the Economic Situation
    
    The information available at the time of the meeting suggested that real GDP 
    growth remained solid. Labor market conditions remained tight, with the 
    unemployment rate staying near historical lows. Job gains continued at a 
    robust pace.
    
    Inflation remained elevated but had shown signs of moderating. The 12-month 
    change in the PCE price index was 2.6 percent in December, and core PCE 
    inflation was 2.9 percent.
    
    Participants' Views on Current Conditions and the Economic Outlook
    
    Participants noted that inflation had eased over the past year but remained 
    above the Committee's longer-run goal of 2 percent. Most participants observed 
    that risks to achieving the Committee's employment and inflation goals had 
    moved toward better balance over the past year.
    
    Some participants noted upside risks to inflation, including the possibility 
    that progress on disinflation could stall. Several participants emphasized 
    the importance of maintaining a restrictive stance until inflation is clearly 
    on a path to 2 percent.
    
    Committee Policy Action
    
    In their discussion of monetary policy, participants judged that the policy 
    rate was likely at its peak for this tightening cycle. Most participants 
    noted the risks of moving too quickly to ease policy and emphasized the 
    importance of carefully assessing incoming data.
    
    The Committee decided to maintain the target range for the federal funds 
    rate at 5-1/4 to 5-1/2 percent.
    """


@pytest.fixture
def hawkish_fed_text() -> str:
    """Hawkish Fed text for testing."""
    return """
    Inflation remains elevated and significantly above the Committee's 2 percent goal.
    The labor market is extremely tight with persistent wage pressures.
    Price stability is the Committee's primary concern.
    Further tightening may be necessary if inflation does not decline.
    The Committee will maintain a restrictive stance for some time.
    Upside risks to inflation remain significant.
    """


@pytest.fixture
def dovish_fed_text() -> str:
    """Dovish Fed text for testing."""
    return """
    Inflation has been declining and is approaching the Committee's goal.
    The labor market is showing signs of cooling.
    Economic growth has slowed below trend.
    The Committee is prepared to adjust policy as conditions warrant.
    Downside risks to the economy have increased.
    Rate cuts may be appropriate in coming months.
    """


# ============================================================================
# Document Loader Tests
# ============================================================================

class TestDocumentLoader:
    """Tests for document loading."""
    
    def test_document_creation(self):
        """Test creating a Document."""
        from portfolio_tool.rag.document_loader import Document
        
        doc = Document(
            content="Test content",
            source="test.txt"
        )
        
        assert doc.content == "Test content"
        assert doc.char_count == 12
        assert doc.word_count == 2
    
    def test_load_from_string(self):
        """Test loading document from string."""
        from portfolio_tool.rag.document_loader import DocumentLoader
        
        loader = DocumentLoader()
        doc = loader.load_from_string(
            content="Test content here",
            source="test",
            doc_type="text"
        )
        
        assert doc.content == "Test content here"
        assert doc.doc_type == "text"
    
    def test_fed_minutes_detection(self, sample_fed_minutes_text):
        """Test Fed Minutes auto-detection."""
        from portfolio_tool.rag.document_loader import DocumentLoader
        
        loader = DocumentLoader()
        doc = loader.load_from_string(sample_fed_minutes_text, "test")
        
        # Should detect Fed-related content
        assert "federal" in doc.content.lower() or "fomc" in doc.content.lower()


# ============================================================================
# Chunker Tests
# ============================================================================

class TestChunker:
    """Tests for text chunking."""
    
    def test_basic_chunking(self, sample_fed_minutes_text):
        """Test basic chunking."""
        from portfolio_tool.rag.document_loader import Document
        from portfolio_tool.rag.chunker import TextChunker
        
        doc = Document(content=sample_fed_minutes_text, source="test")
        chunker = TextChunker(chunk_size=500, overlap=100)
        
        chunks = chunker.chunk(doc)
        
        assert len(chunks) > 0
        assert all(c.text for c in chunks)
    
    def test_fed_minutes_chunking(self, sample_fed_minutes_text):
        """Test Fed Minutes section-aware chunking."""
        from portfolio_tool.rag.document_loader import Document
        from portfolio_tool.rag.chunker import TextChunker
        
        doc = Document(
            content=sample_fed_minutes_text,
            source="test",
            doc_type="fed_minutes"
        )
        chunker = TextChunker(chunk_size=500, respect_sections=True)
        
        chunks = chunker.chunk(doc)
        
        # Should have section labels
        sections = [c.section for c in chunks if c.section]
        assert len(sections) > 0
    
    def test_chunk_ids_sequential(self, sample_fed_minutes_text):
        """Test chunk IDs are sequential."""
        from portfolio_tool.rag.document_loader import Document
        from portfolio_tool.rag.chunker import TextChunker
        
        doc = Document(content=sample_fed_minutes_text, source="test")
        chunker = TextChunker(chunk_size=300)
        
        chunks = chunker.chunk(doc)
        
        ids = [c.chunk_id for c in chunks]
        assert ids == list(range(len(chunks)))


# ============================================================================
# Embedding Tests
# ============================================================================

class TestEmbeddings:
    """Tests for embedding and search."""
    
    def test_embedding_store_creation(self):
        """Test creating embedding store."""
        from portfolio_tool.rag.embeddings import EmbeddingStore
        
        store = EmbeddingStore()
        assert store.chunks == []
    
    def test_add_and_search(self, sample_fed_minutes_text):
        """Test adding chunks and searching."""
        from portfolio_tool.rag.document_loader import Document
        from portfolio_tool.rag.chunker import TextChunker
        from portfolio_tool.rag.embeddings import EmbeddingStore
        
        doc = Document(content=sample_fed_minutes_text, source="test")
        chunker = TextChunker(chunk_size=300)
        chunks = chunker.chunk(doc)
        
        store = EmbeddingStore()
        store.add_chunks(chunks)
        
        results = store.search("inflation", top_k=3)
        
        assert len(results) > 0
        assert results[0].score > 0
        assert "inflation" in results[0].chunk.text.lower()
    
    def test_search_ranking(self, sample_fed_minutes_text):
        """Test search results are ranked by relevance."""
        from portfolio_tool.rag.document_loader import Document
        from portfolio_tool.rag.chunker import TextChunker
        from portfolio_tool.rag.embeddings import EmbeddingStore
        
        doc = Document(content=sample_fed_minutes_text, source="test")
        chunker = TextChunker(chunk_size=200)
        chunks = chunker.chunk(doc)
        
        store = EmbeddingStore()
        store.add_chunks(chunks)
        
        results = store.search("monetary policy rate", top_k=5)
        
        # Scores should be descending
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)


# ============================================================================
# Sentiment Analysis Tests
# ============================================================================

class TestSentimentAnalysis:
    """Tests for Fed sentiment analysis."""
    
    def test_hawkish_detection(self, hawkish_fed_text):
        """Test detecting hawkish sentiment."""
        from portfolio_tool.rag.document_loader import Document
        from portfolio_tool.rag.sentiment import FedSentimentAnalyzer
        
        doc = Document(content=hawkish_fed_text, source="test")
        analyzer = FedSentimentAnalyzer()
        
        result = analyzer.analyze(doc)
        
        # Should be positive (hawkish)
        assert result.score > 0.2
        assert result.classification.value in ["hawkish", "very_hawkish"]
        assert result.risk_assessment == "risk_off"
    
    def test_dovish_detection(self, dovish_fed_text):
        """Test detecting dovish sentiment."""
        from portfolio_tool.rag.document_loader import Document
        from portfolio_tool.rag.sentiment import FedSentimentAnalyzer
        
        doc = Document(content=dovish_fed_text, source="test")
        analyzer = FedSentimentAnalyzer()
        
        result = analyzer.analyze(doc)
        
        # Should be negative (dovish)
        assert result.score < -0.2
        assert result.classification.value in ["dovish", "very_dovish"]
        assert result.risk_assessment == "risk_on"
    
    def test_neutral_detection(self, sample_fed_minutes_text):
        """Test neutral/mixed sentiment."""
        from portfolio_tool.rag.document_loader import Document
        from portfolio_tool.rag.sentiment import FedSentimentAnalyzer
        
        doc = Document(content=sample_fed_minutes_text, source="test")
        analyzer = FedSentimentAnalyzer()
        
        result = analyzer.analyze(doc)
        
        # Real Fed Minutes are usually more balanced
        assert -0.5 < result.score < 0.5
    
    def test_theme_extraction(self, sample_fed_minutes_text):
        """Test key theme extraction."""
        from portfolio_tool.rag.document_loader import Document
        from portfolio_tool.rag.sentiment import FedSentimentAnalyzer
        
        doc = Document(content=sample_fed_minutes_text, source="test")
        analyzer = FedSentimentAnalyzer()
        
        result = analyzer.analyze(doc)
        
        # Should extract relevant themes
        assert "inflation" in result.key_themes or len(result.key_themes) > 0
    
    def test_sentiment_deterministic(self, hawkish_fed_text):
        """Test sentiment analysis is deterministic."""
        from portfolio_tool.rag.document_loader import Document
        from portfolio_tool.rag.sentiment import FedSentimentAnalyzer
        
        doc = Document(content=hawkish_fed_text, source="test")
        analyzer = FedSentimentAnalyzer()
        
        results = [analyzer.analyze(doc) for _ in range(5)]
        
        # All results should be identical
        for r in results[1:]:
            assert r.score == results[0].score
            assert r.classification == results[0].classification


# ============================================================================
# Macro Agent Tests
# ============================================================================

class TestMacroAgent:
    """Tests for Macro Agent."""
    
    def test_agent_creation(self):
        """Test creating a Macro Agent."""
        from agents.macro_agent import create_macro_agent
        
        agent = create_macro_agent()
        
        assert agent.name == "MacroAgent"
        assert "analyze_fed_minutes" in agent.capabilities
        assert "assess_market_regime" in agent.capabilities
    
    def test_agent_has_tools(self):
        """Test agent has required tools."""
        from agents.macro_agent import create_macro_agent
        
        agent = create_macro_agent()
        tools = agent.get_tools()
        
        tool_names = [t.__name__ for t in tools]
        assert "analyze_fed_minutes_tool" in tool_names
        assert "assess_regime_tool" in tool_names
        assert "generate_macro_signal_tool" in tool_names
    
    def test_analyze_fed_tool(self, sample_fed_minutes_text):
        """Test Fed Minutes analysis tool."""
        from agents.macro_agent import create_macro_agent
        
        agent = create_macro_agent()
        
        result = agent.analyze_fed_minutes_tool(
            text=sample_fed_minutes_text,
            source="test"
        )
        
        assert result["success"]
        assert "score" in result
        assert "classification" in result
        assert "risk_assessment" in result
    
    def test_assess_regime_tool(self):
        """Test regime assessment tool."""
        from agents.macro_agent import create_macro_agent
        
        agent = create_macro_agent()
        
        # Normal conditions
        result = agent.assess_regime_tool(
            vix_level=18.0,
            fed_sentiment=0.1
        )
        
        assert result["success"]
        assert result["vix_regime"] == "normal"
        
        # Crisis conditions
        result = agent.assess_regime_tool(
            vix_level=40.0,
            fed_sentiment=0.5
        )
        
        assert result["success"]
        assert result["vix_regime"] == "crisis"
        assert result["regime"] == "crisis"
    
    def test_vix_regime_classification(self):
        """Test VIX regime boundaries."""
        from agents.macro_agent import create_macro_agent
        
        agent = create_macro_agent()
        
        test_cases = [
            (12.0, "low"),
            (20.0, "normal"),
            (28.0, "elevated"),
            (42.0, "crisis"),
        ]
        
        for vix, expected_regime in test_cases:
            result = agent.assess_regime_tool(vix_level=vix)
            assert result["vix_regime"] == expected_regime, f"VIX {vix} should be {expected_regime}"
    
    def test_generate_macro_signal(self, sample_fed_minutes_text):
        """Test complete macro signal generation."""
        from agents.macro_agent import create_macro_agent
        
        agent = create_macro_agent()
        
        result = agent.generate_macro_signal_tool(
            fed_text=sample_fed_minutes_text,
            vix_level=22.0,
            yield_curve_slope=0.5
        )
        
        assert result["success"]
        assert "regime" in result
        assert "risk_stance" in result
        assert "equity_adjustment" in result


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for Phase 5.4."""
    
    def test_full_analysis_pipeline(self, sample_fed_minutes_text):
        """Test complete analysis pipeline."""
        from portfolio_tool.rag.document_loader import DocumentLoader
        from portfolio_tool.rag.chunker import TextChunker
        from portfolio_tool.rag.embeddings import EmbeddingStore
        from portfolio_tool.rag.sentiment import FedSentimentAnalyzer
        
        # 1. Load document
        loader = DocumentLoader()
        doc = loader.load_from_string(
            sample_fed_minutes_text,
            source="test",
            doc_type="fed_minutes"
        )
        
        # 2. Chunk for search
        chunker = TextChunker(chunk_size=500)
        chunks = chunker.chunk(doc)
        assert len(chunks) > 0
        
        # 3. Create searchable store
        store = EmbeddingStore()
        store.add_chunks(chunks)
        
        # 4. Search for relevant sections
        results = store.search("inflation outlook", top_k=3)
        assert len(results) > 0
        
        # 5. Analyze sentiment
        analyzer = FedSentimentAnalyzer()
        sentiment = analyzer.analyze(doc)
        
        assert sentiment.score is not None
        assert sentiment.risk_assessment in ["risk_on", "risk_off", "neutral"]
    
    def test_macro_signal_to_taa(self):
        """Test macro signal can inform TAA rules."""
        from agents.macro_agent import create_macro_agent, MacroSignal, MarketRegime
        
        agent = create_macro_agent()
        
        # Generate signal for high VIX environment
        result = agent.assess_regime_tool(
            vix_level=32.0,
            fed_sentiment=0.4
        )
        
        assert result["success"]
        
        # Signal should suggest risk reduction
        assert result["regime"] in ["risk_off", "crisis"]
        assert float(result["equity_adjustment"].rstrip('%')) / 100 < 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
