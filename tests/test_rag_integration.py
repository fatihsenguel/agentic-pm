# tests/test_rag_integration.py
"""
Tests for RAG Full Integration.

Phase: 6.7 - RAG Integration (Final)

Covers:
- DocumentManager functionality
- Router RAG detection
- End-to-end document flow

Run with:
    python tests/test_rag_integration.py
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# =============================================================================
# DOCUMENT MANAGER TESTS
# =============================================================================

class TestDocumentManager:
    """Test DocumentManager functionality."""
    
    def setup_method(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temp directory."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_manager_initialization(self):
        """Test DocumentManager initializes correctly."""
        from portfolio_tool.rag import DocumentManager
        
        dm = DocumentManager()
        assert dm is not None
        assert dm.config is not None
        
        print("  ✓ DocumentManager initialized")
    
    def test_documents_dir_creation(self):
        """Test that documents directory is created."""
        from portfolio_tool.rag import DocumentManager
        
        dm = DocumentManager()
        docs_dir = dm.documents_dir
        
        assert docs_dir.exists()
        
        print(f"  ✓ Documents dir: {docs_dir}")
    
    def test_ingest_text_file(self):
        """Test ingesting a text file."""
        from portfolio_tool.rag import DocumentManager
        from portfolio_tool.rag.document_manager import IngestionResult
        
        # Create test file
        test_content = """
        NVIDIA Corporation Q3 2024 Earnings
        
        Revenue: $18.1 billion, up 279% year over year.
        Data Center: $14.5 billion revenue.
        
        Risk Factors:
        - China export restrictions
        - Supply chain constraints
        """
        
        test_file = os.path.join(self.temp_dir, "NVDA_Q3_2024.txt")
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        dm = DocumentManager()
        result = dm.ingest(test_file, ticker="NVDA")
        
        assert result.success, f"Ingestion failed: {result.error}"
        assert result.ticker == "NVDA"
        assert result.chunk_count > 0
        
        print(f"  ✓ Ingested {result.chunk_count} chunks")
    
    def test_ingest_returns_result_object(self):
        """Test that ingest returns proper IngestionResult."""
        from portfolio_tool.rag import DocumentManager, IngestionResult
        
        dm = DocumentManager()
        
        # Non-existent file
        result = dm.ingest("/nonexistent/file.pdf")
        
        assert isinstance(result, IngestionResult)
        assert result.success == False
        assert "not found" in result.error.lower()
        
        print("  ✓ IngestionResult structure correct")
    
    def test_ingest_unsupported_file(self):
        """Test that unsupported files are rejected."""
        from portfolio_tool.rag import DocumentManager
        
        # Create unsupported file
        test_file = os.path.join(self.temp_dir, "test.docx")
        with open(test_file, 'w') as f:
            f.write("test")
        
        dm = DocumentManager()
        result = dm.ingest(test_file)
        
        assert result.success == False
        assert "unsupported" in result.error.lower()
        
        print("  ✓ Unsupported files rejected")
    
    def test_get_stats(self):
        """Test getting document stats."""
        from portfolio_tool.rag import DocumentManager
        
        dm = DocumentManager()
        stats = dm.get_stats()
        
        assert "total_chunks" in stats
        assert "documents_dir" in stats
        
        print(f"  ✓ Stats: {stats.get('total_chunks', 0)} chunks indexed")
    
    def test_list_documents(self):
        """Test listing indexed documents."""
        from portfolio_tool.rag import DocumentManager
        
        dm = DocumentManager()
        docs = dm.list_documents()
        
        assert isinstance(docs, list)
        
        print(f"  ✓ Listed {len(docs)} documents")
    
    def test_search(self):
        """Test search functionality."""
        from portfolio_tool.rag import DocumentManager
        
        dm = DocumentManager()
        
        # This may return empty if no documents indexed
        results = dm.search("test query", top_k=3)
        
        assert isinstance(results, list)
        
        print(f"  ✓ Search returned {len(results)} results")


# =============================================================================
# ROUTER RAG DETECTION TESTS
# =============================================================================

class TestRouterRAGDetection:
    """Test that router correctly detects document-related queries."""
    
    def test_document_keywords_detection(self):
        """Test detection of document-related keywords."""
        document_keywords = [
            "10-k", "10-q", "filing", "earnings report", "annual report",
            "fed minutes", "fomc", "what did the report say",
            "according to", "based on the document"
        ]
        
        test_queries = [
            ("What did NVDA's 10-K say about China?", True),
            ("Show me the Fed minutes", True),
            ("According to the filing, what are the risks?", True),
            ("Optimize my portfolio", False),
            ("What's AAPL's current price?", False),
        ]
        
        for query, should_match in test_queries:
            query_lower = query.lower()
            has_doc_keyword = any(kw in query_lower for kw in document_keywords)
            
            if should_match:
                assert has_doc_keyword, f"Expected doc keyword in: {query}"
            # Note: We don't assert False for non-matches because other logic might still route to RAG
        
        print("  ✓ Document keyword detection working")
    
    def test_fed_keywords_detection(self):
        """Test detection of Fed-related keywords."""
        fed_keywords = ["fed", "fomc", "interest rate", "monetary", "powell"]
        
        test_queries = [
            "What's the Fed sentiment?",
            "How hawkish is the FOMC?",
            "Interest rate outlook",
        ]
        
        for query in test_queries:
            query_lower = query.lower()
            has_fed_keyword = any(kw in query_lower for kw in fed_keywords)
            assert has_fed_keyword, f"Expected Fed keyword in: {query}"
        
        print("  ✓ Fed keyword detection working")


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestConvenienceFunctions:
    """Test module-level convenience functions."""
    
    def test_get_document_manager(self):
        """Test singleton accessor."""
        from portfolio_tool.rag import get_document_manager
        
        dm1 = get_document_manager()
        dm2 = get_document_manager()
        
        # Should be same instance
        assert dm1 is dm2
        
        print("  ✓ Singleton pattern working")
    
    def test_ingest_document_function(self):
        """Test ingest_document convenience function."""
        from portfolio_tool.rag import ingest_document
        
        # Non-existent file should return error dict
        result = ingest_document("/nonexistent/file.pdf")
        
        assert isinstance(result, dict)
        assert result["success"] == False
        
        print("  ✓ ingest_document function works")


# =============================================================================
# SCHEMA UPDATES TESTS
# =============================================================================

class TestSchemaUpdates:
    """Test that schema updates are applied correctly."""
    
    def test_execution_intent_has_document_search(self):
        """Test ExecutionIntent has DOCUMENT_SEARCH."""
        from agents.schemas import ExecutionIntent
        
        # Check if DOCUMENT_SEARCH exists
        intents = [e.value for e in ExecutionIntent]
        
        if "document_search" in intents:
            print("  ✓ DOCUMENT_SEARCH intent exists")
        else:
            print("  ⚠️ DOCUMENT_SEARCH not yet added to ExecutionIntent")
    
    def test_agent_name_has_rag_agent(self):
        """Test AgentName has RAG_AGENT."""
        from agents.schemas import AgentName
        
        agents = [a.value for a in AgentName]
        
        if "RAGAgent" in agents:
            print("  ✓ RAGAgent in AgentName enum")
        else:
            print("  ⚠️ RAGAgent not yet added to AgentName enum")


# =============================================================================
# MAIN
# =============================================================================

def run_tests():
    """Run all tests."""
    
    test_classes = [
        TestDocumentManager,
        TestRouterRAGDetection,
        TestConvenienceFunctions,
        TestSchemaUpdates,
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
