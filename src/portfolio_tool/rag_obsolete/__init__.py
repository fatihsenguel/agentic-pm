"""
RAG (Retrieval Augmented Generation) Module.

This module provides document analysis capabilities:
- Document loading (PDF, TXT, Fed Minutes)
- Smart chunking optimized for financial documents
- Embedding and semantic search
- Sentiment extraction (Hawkish/Dovish)

Primary use case: Analyzing Fed Minutes and other macro documents
to extract sentiment signals for Tactical Asset Allocation.

Design Principles:
- Modular: Each component can be used independently
- Configurable: Chunk size, overlap, embedding model
- Financial-aware: Optimized for Fed/economic document structure
"""

from .document_loader import (
    DocumentLoader,
    Document,
    load_text_file,
    load_pdf_file,
    load_fed_minutes,
)

from .chunker import (
    TextChunker,
    Chunk,
    chunk_by_paragraphs,
    chunk_by_sentences,
    chunk_by_tokens,
)

from .embeddings import (
    EmbeddingStore,
    EmbeddingResult,
    create_embedding_store,
    similarity_search,
)

from .sentiment import (
    FedSentimentAnalyzer,
    SentimentResult,
    SentimentScore,
    analyze_fed_sentiment,
    extract_key_themes,
)


__all__ = [
    # Document Loading
    "DocumentLoader",
    "Document",
    "load_text_file",
    "load_pdf_file",
    "load_fed_minutes",
    # Chunking
    "TextChunker",
    "Chunk",
    "chunk_by_paragraphs",
    "chunk_by_sentences",
    "chunk_by_tokens",
    # Embeddings
    "EmbeddingStore",
    "EmbeddingResult",
    "create_embedding_store",
    "similarity_search",
    # Sentiment
    "FedSentimentAnalyzer",
    "SentimentResult",
    "SentimentScore",
    "analyze_fed_sentiment",
    "extract_key_themes",
]
