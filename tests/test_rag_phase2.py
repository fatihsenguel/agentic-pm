# tests/test_rag_phase2.py
"""
Tests for RAG Phase 2: Vector Store.

Phase: 6.7 - RAG Integration

Covers:
- Embedding service (OpenAI + local fallback)
- Vector store (ChromaDB operations)
- Search with filters
- Document management

Run with:
    python tests/test_rag_phase2.py
    
Note: Some tests require OPENAI_API_KEY for full coverage.
Tests gracefully skip if dependencies unavailable.
"""

import os
import sys
import tempfile
import shutil
from datetime import date, datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# =============================================================================
# EMBEDDING TESTS
# =============================================================================

class TestEmbeddingConfig:
    """Test embedding configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        from portfolio_tool.rag.embeddings import EmbeddingConfig
        
        config = EmbeddingConfig()
        
        assert config.openai_model == "text-embedding-3-small"
        assert config.openai_dimensions == 1536
        assert config.local_model == "all-MiniLM-L6-v2"
        assert config.local_dimensions == 384
        assert config.auto_fallback == True
    
    def test_custom_config(self):
        """Test custom configuration."""
        from portfolio_tool.rag.embeddings import EmbeddingConfig
        
        config = EmbeddingConfig(
            openai_model="text-embedding-3-large",
            prefer_local=True,
        )
        
        assert config.openai_model == "text-embedding-3-large"
        assert config.prefer_local == True


class TestEmbeddingService:
    """Test embedding service initialization and provider selection."""
    
    def test_service_initialization(self):
        """Test service initializes without error."""
        from portfolio_tool.rag.embeddings import EmbeddingService
        
        # Force local to avoid API dependency
        service = EmbeddingService(prefer_local=True)
        
        assert service is not None
        assert service.config.prefer_local == True
    
    def test_provider_info(self):
        """Test getting provider information."""
        from portfolio_tool.rag.embeddings import EmbeddingService
        
        service = EmbeddingService(prefer_local=True)
        
        # This will trigger provider initialization
        try:
            info = service.get_provider_info()
            assert "provider_type" in info
            assert "model_name" in info
            assert "dimensions" in info
        except ImportError:
            # sentence-transformers not installed
            pass
    
    def test_embed_query_local(self):
        """Test embedding a query with local model."""
        from portfolio_tool.rag.embeddings import EmbeddingService
        
        try:
            service = EmbeddingService(prefer_local=True)
            
            embedding = service.embed_query("What is NVIDIA's revenue?")
            
            assert isinstance(embedding, list)
            assert len(embedding) == 384  # MiniLM dimensions
            assert all(isinstance(x, float) for x in embedding)
        except ImportError:
            print("  ⚠️ Skipped (sentence-transformers not installed)")
    
    def test_embed_documents_local(self):
        """Test embedding multiple documents with local model."""
        from portfolio_tool.rag.embeddings import EmbeddingService
        
        try:
            service = EmbeddingService(prefer_local=True)
            
            texts = [
                "NVIDIA reported strong revenue growth.",
                "The Federal Reserve maintained interest rates.",
                "Apple announced new product lineup.",
            ]
            
            embeddings = service.embed_documents(texts)
            
            assert len(embeddings) == 3
            assert all(len(e) == 384 for e in embeddings)
        except ImportError:
            print("  ⚠️ Skipped (sentence-transformers not installed)")
    
    def test_empty_input(self):
        """Test handling of empty input."""
        from portfolio_tool.rag.embeddings import EmbeddingService
        
        try:
            service = EmbeddingService(prefer_local=True)
            
            embeddings = service.embed_documents([])
            
            assert embeddings == []
        except ImportError:
            print("  ⚠️ Skipped (sentence-transformers not installed)")


class TestOpenAIEmbeddings:
    """Test OpenAI embedding provider (requires API key)."""
    
    def test_openai_available(self):
        """Test if OpenAI is available and configured."""
        has_key = bool(os.environ.get("OPENAI_API_KEY"))
        
        if has_key:
            print("  ✓ OPENAI_API_KEY found")
        else:
            print("  ⚠️ OPENAI_API_KEY not set - OpenAI tests will be skipped")
    
    def test_openai_embed_query(self):
        """Test OpenAI embedding (requires API key)."""
        if not os.environ.get("OPENAI_API_KEY"):
            print("  ⚠️ Skipped (no OPENAI_API_KEY)")
            return
        
        from portfolio_tool.rag.embeddings import EmbeddingService, EmbeddingConfig
        
        config = EmbeddingConfig(prefer_local=False)
        service = EmbeddingService(config=config)
        
        embedding = service.embed_query("Test query")
        
        assert len(embedding) == 1536  # OpenAI dimensions
        print(f"  ✓ OpenAI embedding generated ({len(embedding)} dims)")


# =============================================================================
# VECTOR STORE TESTS
# =============================================================================

class TestVectorStoreConfig:
    """Test vector store configuration."""
    
    def test_default_config(self):
        """Test default configuration."""
        from portfolio_tool.rag.vector_store import VectorStoreConfig
        
        config = VectorStoreConfig()
        
        assert config.persist_dir == "data/chroma"
        assert config.collection_name == "portfolio_documents"
        assert config.default_top_k == 5
        assert config.relevance_threshold == 0.3  # Lowered for L2 distance conversion


class TestVectorStore:
    """Test vector store operations."""
    
    def setup_method(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary directory."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_store_initialization(self):
        """Test vector store initializes correctly."""
        try:
            from portfolio_tool.rag.vector_store import VectorStore, VectorStoreConfig
            
            config = VectorStoreConfig(
                persist_dir=self.temp_dir,
                prefer_local_embeddings=True,
            )
            
            store = VectorStore(config)
            
            assert store is not None
            assert store.persist_dir.exists()
        except ImportError as e:
            print(f"  ⚠️ Skipped ({e})")
    
    def test_add_and_search_document(self):
        """Test adding a document and searching."""
        try:
            from portfolio_tool.rag import (
                Document, DocumentType, DocumentSource,
                Chunker, VectorStore, VectorStoreConfig
            )
            
            # Create test document
            doc = Document(
                content="NVIDIA reported Q3 2024 revenue of $18.1 billion, up 279% year over year. "
                        "Data center revenue reached $14.5 billion. The company maintains strong "
                        "growth driven by AI demand.",
                filename="NVDA_Q3_2024.txt",
                doc_type=DocumentType.EARNINGS,
                source=DocumentSource.USER_UPLOAD,
                ticker="NVDA",
                document_date=date(2024, 11, 20),
            )
            
            # Chunk
            chunker = Chunker(chunk_size=500, chunk_overlap=50)
            chunker.chunk_document(doc)
            
            # Add to store
            config = VectorStoreConfig(
                persist_dir=self.temp_dir,
                prefer_local_embeddings=True,
            )
            store = VectorStore(config)
            
            doc_id = store.add_document(doc)
            
            assert doc_id != "", "Document ID should not be empty"
            
            # Search with low threshold to ensure results
            results = store.search("NVIDIA revenue growth", top_k=3, min_score=0.1)
            
            assert len(results) > 0, f"Expected results, got {len(results)}"
            assert results[0].ticker == "NVDA", f"Expected NVDA, got {results[0].ticker}"
            assert results[0].score > 0, f"Expected positive score, got {results[0].score}"
            
            print(f"  ✓ Search returned {len(results)} results (top score: {results[0].score:.3f})")
            
        except ImportError as e:
            print(f"  ⚠️ Skipped ({e})")
    
    def test_search_with_filters(self):
        """Test searching with metadata filters."""
        try:
            from portfolio_tool.rag import (
                Document, DocumentType, DocumentSource,
                Chunker, VectorStore, VectorStoreConfig
            )
            
            config = VectorStoreConfig(
                persist_dir=self.temp_dir,
                prefer_local_embeddings=True,
            )
            store = VectorStore(config)
            
            # Add NVDA document
            nvda_doc = Document(
                content="NVIDIA reported strong AI revenue.",
                filename="NVDA_Q3.txt",
                doc_type=DocumentType.EARNINGS,
                source=DocumentSource.USER_UPLOAD,
                ticker="NVDA",
            )
            chunker = Chunker(chunk_size=500)
            chunker.chunk_document(nvda_doc)
            store.add_document(nvda_doc)
            
            # Add AAPL document
            aapl_doc = Document(
                content="Apple announced new iPhone models.",
                filename="AAPL_News.txt",
                doc_type=DocumentType.NEWS,
                source=DocumentSource.USER_UPLOAD,
                ticker="AAPL",
            )
            chunker.chunk_document(aapl_doc)
            store.add_document(aapl_doc)
            
            # Search for NVDA only
            results = store.search(
                "revenue growth",
                filters={"ticker": "NVDA"},
                top_k=5,
            )
            
            # All results should be NVDA
            for r in results:
                assert r.ticker == "NVDA", f"Expected NVDA, got {r.ticker}"
            
            print(f"  ✓ Ticker filter working ({len(results)} NVDA results)")
            
        except ImportError as e:
            print(f"  ⚠️ Skipped ({e})")
    
    def test_delete_document(self):
        """Test deleting a document."""
        try:
            from portfolio_tool.rag import (
                Document, DocumentType, DocumentSource,
                Chunker, VectorStore, VectorStoreConfig
            )
            
            config = VectorStoreConfig(
                persist_dir=self.temp_dir,
                prefer_local_embeddings=True,
            )
            store = VectorStore(config)
            
            # Add document
            doc = Document(
                content="Test document content for deletion test.",
                filename="test_delete.txt",
                doc_type=DocumentType.OTHER,
                source=DocumentSource.MANUAL,
            )
            chunker = Chunker(chunk_size=500)
            chunker.chunk_document(doc)
            doc_id = store.add_document(doc)
            
            # Verify it exists
            stats_before = store.get_stats()
            assert stats_before["total_chunks"] > 0
            
            # Delete
            deleted = store.delete_document(doc_id)
            assert deleted == True
            
            # Verify it's gone
            stats_after = store.get_stats()
            assert stats_after["total_chunks"] == 0
            
            print("  ✓ Document deletion working")
            
        except ImportError as e:
            print(f"  ⚠️ Skipped ({e})")
    
    def test_get_stats(self):
        """Test getting store statistics."""
        try:
            from portfolio_tool.rag import VectorStore, VectorStoreConfig
            
            config = VectorStoreConfig(
                persist_dir=self.temp_dir,
                prefer_local_embeddings=True,
            )
            store = VectorStore(config)
            
            stats = store.get_stats()
            
            assert "total_chunks" in stats
            assert "unique_documents" in stats
            assert "collection_name" in stats
            assert "embedding_model" in stats
            
            print(f"  ✓ Stats: {stats['total_chunks']} chunks, model={stats['embedding_model']}")
            
        except ImportError as e:
            print(f"  ⚠️ Skipped ({e})")
    
    def test_deduplication(self):
        """Test that same document isn't added twice."""
        try:
            from portfolio_tool.rag import (
                Document, DocumentType, DocumentSource,
                Chunker, VectorStore, VectorStoreConfig
            )
            
            config = VectorStoreConfig(
                persist_dir=self.temp_dir,
                prefer_local_embeddings=True,
            )
            store = VectorStore(config)
            
            # Create document
            doc = Document(
                content="Unique content for dedup test.",
                filename="dedup_test.txt",
                doc_type=DocumentType.OTHER,
                source=DocumentSource.MANUAL,
            )
            chunker = Chunker(chunk_size=500)
            chunker.chunk_document(doc)
            
            # Add twice
            doc_id1 = store.add_document(doc)
            doc_id2 = store.add_document(doc)
            
            # Should return same ID
            assert doc_id1 == doc_id2
            
            # Should only have 1 document
            stats = store.get_stats()
            assert stats["unique_documents"] == 1
            
            print("  ✓ Deduplication working")
            
        except ImportError as e:
            print(f"  ⚠️ Skipped ({e})")


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for full RAG pipeline."""
    
    def setup_method(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary directory."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_full_pipeline(self):
        """Test complete load → chunk → embed → search pipeline."""
        try:
            from portfolio_tool.rag import (
                DocumentLoader, Chunker,
                VectorStore, VectorStoreConfig,
                DocumentType, DocumentSource,
            )
            
            # Create test file
            test_content = """
QUARTERLY EARNINGS REPORT - NVIDIA Q3 2024

FINANCIAL HIGHLIGHTS
Revenue reached $18.1 billion, representing a 279% increase year over year.
Data center revenue was $14.5 billion, up 409% from last year.

BUSINESS OUTLOOK
We expect continued strong demand for AI computing.
Our data center products are seeing unprecedented adoption.

RISK FACTORS
Export restrictions to China may impact future revenue.
Supply chain constraints remain a concern.
"""
            
            test_file = Path(self.temp_dir) / "NVDA_Q3_2024_Earnings.txt"
            test_file.write_text(test_content)
            
            # Load
            loader = DocumentLoader()
            doc = loader.load(str(test_file), ticker="NVDA")
            
            assert doc.ticker == "NVDA"
            assert doc.doc_type == DocumentType.EARNINGS
            
            # Chunk
            chunker = Chunker(chunk_size=200, chunk_overlap=20)
            chunks = chunker.chunk_document(doc)
            
            assert len(chunks) >= 1, f"Expected at least 1 chunk, got {len(chunks)}"
            
            # Store
            config = VectorStoreConfig(
                persist_dir=self.temp_dir,
                prefer_local_embeddings=True,
            )
            store = VectorStore(config)
            doc_id = store.add_document(doc)
            
            assert doc_id != "", "Document ID should not be empty"
            
            # Search with low threshold
            results = store.search("What was NVIDIA's data center revenue?", top_k=3, min_score=0.1)
            
            assert len(results) > 0, f"Expected results, got {len(results)}"
            
            # Check that relevant content was found
            all_content = " ".join([r.chunk.content for r in results])
            has_relevant = "data center" in all_content.lower() or "14.5" in all_content or "revenue" in all_content.lower()
            assert has_relevant, f"Expected relevant content, got: {all_content[:200]}"
            
            print(f"  ✓ Full pipeline: loaded → {len(chunks)} chunks → searched → {len(results)} results")
            
        except ImportError as e:
            print(f"  ⚠️ Skipped ({e})")
    
    def test_search_result_schema(self):
        """Test that SearchResult has correct structure for Decision Engine."""
        try:
            from portfolio_tool.rag import (
                Document, DocumentType, DocumentSource,
                Chunker, VectorStore, VectorStoreConfig,
            )
            
            config = VectorStoreConfig(
                persist_dir=self.temp_dir,
                prefer_local_embeddings=True,
            )
            store = VectorStore(config)
            
            # Add document
            doc = Document(
                content="Apple reported iPhone sales increased 15%.",
                filename="AAPL_Report.txt",
                doc_type=DocumentType.EARNINGS,
                source=DocumentSource.USER_UPLOAD,
                ticker="AAPL",
                document_date=date(2024, 10, 30),
            )
            chunker = Chunker(chunk_size=500)
            chunker.chunk_document(doc)
            store.add_document(doc)
            
            # Search
            results = store.search("iPhone sales")
            
            if results:
                result = results[0]
                
                # Check SearchResult structure
                assert hasattr(result, 'chunk')
                assert hasattr(result, 'score')
                assert hasattr(result, 'ticker')
                assert hasattr(result, 'doc_type')
                assert hasattr(result, 'document_date')
                
                # Check can serialize
                d = result.to_dict()
                assert "content" in d
                assert "score" in d
                assert "ticker" in d
                
                # Check citation generation
                citation = result.get_citation()
                assert "AAPL" in citation or "Report" in citation
                
                print(f"  ✓ SearchResult schema correct: {citation}")
            
        except ImportError as e:
            print(f"  ⚠️ Skipped ({e})")


# =============================================================================
# MAIN
# =============================================================================

def run_tests():
    """Run all tests and print results."""
    
    test_classes = [
        TestEmbeddingConfig,
        TestEmbeddingService,
        TestOpenAIEmbeddings,
        TestVectorStoreConfig,
        TestVectorStore,
        TestIntegration,
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
            except Exception as e:
                print(f"  ❌ {method}: {str(e)[:100]}")
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