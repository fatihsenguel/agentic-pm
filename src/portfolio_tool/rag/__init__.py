# src/portfolio_tool/rag/__init__.py
"""
RAG (Retrieval-Augmented Generation) Module for Portfolio Decision Support.

Phase: 6.7 - RAG Integration

PURPOSE:
Enable document-backed decision making by:
1. Ingesting financial documents (earnings, 10-K, Fed minutes)
2. Chunking with section awareness
3. Embedding and storing in vector database
4. Semantic search for relevant context
5. Feeding insights into the Decision Engine

ARCHITECTURE:
    Document → Loader → Chunker → Embeddings → VectorStore
                                                    ↓
                                              SearchResults
                                                    ↓
                                            DocumentInsights
                                                    ↓
                                            Decision Engine

USAGE:
    from portfolio_tool.rag import (
        DocumentLoader,
        Chunker,
        Document,
        DocumentInsights,
    )
    
    # Load and chunk a document
    loader = DocumentLoader()
    doc = loader.load_pdf("NVDA_10K.pdf", ticker="NVDA")
    
    chunker = Chunker(chunk_size=1000)
    chunks = chunker.chunk_document(doc)

MODULE STRUCTURE:
    rag/
    ├── __init__.py          # This file - exports
    ├── schemas.py           # Data structures (Document, Chunk, SearchResult)
    ├── document_loader.py   # Load PDFs, text files
    ├── chunker.py           # Section-aware chunking
    ├── embeddings.py        # Generate embeddings (Phase 2)
    └── vector_store.py      # ChromaDB wrapper (Phase 2)
"""

# =============================================================================
# SCHEMAS
# =============================================================================
from .schemas import (
    # Enums
    DocumentType,
    DocumentSource,
    DocumentStatus,
    
    # Core data structures
    Document,
    Chunk,
    SearchResult,
    
    # Decision Engine integration
    DocumentInsights,
    create_empty_insights,
)

# =============================================================================
# DOCUMENT LOADING
# =============================================================================
from .document_loader import (
    DocumentLoader,
    load_document,
    load_fed_minutes,
    
    # Utilities
    count_tokens,
    compute_content_hash,
    extract_ticker_from_filename,
    extract_date_from_filename,
    infer_document_type,
)

# =============================================================================
# CHUNKING
# =============================================================================
from .chunker import (
    Chunker,
    ChunkerConfig,
    chunk_document,
    detect_sections,
)

# =============================================================================
# EMBEDDINGS (Phase 2)
# =============================================================================
from .embeddings import (
    EmbeddingService,
    EmbeddingConfig,
    OpenAIEmbeddingProvider,
    LocalEmbeddingProvider,
    get_embedding_service,
    embed_texts,
    embed_query,
)

# =============================================================================
# VECTOR STORE (Phase 2)
# =============================================================================
from .vector_store import (
    VectorStore,
    VectorStoreConfig,
    get_vector_store,
    add_document_to_store,
    search_documents,
)

# =============================================================================
# SENTIMENT ANALYSIS (Phase 3)
# =============================================================================
from .sentiment import (
    FedSentimentAnalyzer,
    SentimentConfig,
    SentimentResult,
    RuleBasedSentiment,
    LLMSentiment,
    analyze_fed_sentiment,
    get_rule_based_sentiment,
)

# =============================================================================
# DOCUMENT MANAGER (Phase 3.5 - Usability)
# =============================================================================
from .document_manager import (
    DocumentManager,
    IngestionResult,
    get_document_manager,
    ingest_document,
    ingest_all_documents,
    ingest_fed_minutes,
)

# =============================================================================
# VERSION
# =============================================================================
__version__ = "0.4.0"
__phase__ = "6.7"

# =============================================================================
# ALL EXPORTS
# =============================================================================
__all__ = [
    # Enums
    "DocumentType",
    "DocumentSource", 
    "DocumentStatus",
    
    # Core schemas
    "Document",
    "Chunk",
    "SearchResult",
    "DocumentInsights",
    "create_empty_insights",
    
    # Document loading
    "DocumentLoader",
    "load_document",
    "load_fed_minutes",
    "count_tokens",
    "compute_content_hash",
    "extract_ticker_from_filename",
    "extract_date_from_filename",
    "infer_document_type",
    
    # Chunking
    "Chunker",
    "ChunkerConfig",
    "chunk_document",
    "detect_sections",
    
    # Embeddings (Phase 2)
    "EmbeddingService",
    "EmbeddingConfig",
    "OpenAIEmbeddingProvider",
    "LocalEmbeddingProvider",
    "get_embedding_service",
    "embed_texts",
    "embed_query",
    
    # Vector Store (Phase 2)
    "VectorStore",
    "VectorStoreConfig",
    "get_vector_store",
    "add_document_to_store",
    "search_documents",
    
    # Sentiment Analysis (Phase 3)
    "FedSentimentAnalyzer",
    "SentimentConfig",
    "SentimentResult",
    "RuleBasedSentiment",
    "LLMSentiment",
    "analyze_fed_sentiment",
    "get_rule_based_sentiment",
    
    # Document Manager (Phase 3.5)
    "DocumentManager",
    "IngestionResult",
    "get_document_manager",
    "ingest_document",
    "ingest_all_documents",
    "ingest_fed_minutes",
]