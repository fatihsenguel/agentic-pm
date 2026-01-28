# src/portfolio_tool/rag/vector_store.py
"""
Vector Store for RAG Pipeline using ChromaDB.

Phase: 6.7 - RAG Integration (Phase 2: Vector Store)

PURPOSE:
Store and retrieve document embeddings with rich metadata filtering:
- Semantic similarity search
- Filter by ticker, doc_type, date range
- Automatic document management (add, update, delete)
- Integration with embedding service

DESIGN PRINCIPLES:
- Persistent storage: ChromaDB persists to disk
- Metadata-rich: Every chunk has searchable metadata
- Idempotent: Safe to re-add same document (uses content_hash)
- Financial-aware: Filters designed for portfolio management use cases

USAGE:
    from portfolio_tool.rag.vector_store import VectorStore
    
    store = VectorStore()
    
    # Add a document (auto-chunks and embeds)
    doc_id = store.add_document(document)
    
    # Search with filters
    results = store.search(
        query="NVIDIA revenue growth",
        filters={"ticker": "NVDA", "doc_type": "earnings"},
        top_k=5
    )
    
    # Delete a document
    store.delete_document(doc_id)
"""

import os
import logging
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from .schemas import Document, Chunk, SearchResult, DocumentType
from .embeddings import EmbeddingService, EmbeddingConfig

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class VectorStoreConfig:
    """Configuration for vector store."""
    # ChromaDB settings
    persist_dir: str = "data/chroma"
    collection_name: str = "portfolio_documents"
    
    # Search settings
    default_top_k: int = 5
    relevance_threshold: float = 0.3  # Minimum similarity (0-1), lower for L2 distance
    
    # Embedding settings (passed to EmbeddingService)
    embedding_config: Optional[EmbeddingConfig] = None
    prefer_local_embeddings: bool = False


# =============================================================================
# VECTOR STORE
# =============================================================================

class VectorStore:
    """
    ChromaDB-based vector store for document retrieval.
    
    Features:
    - Persistent storage to disk
    - Rich metadata filtering (ticker, doc_type, date)
    - Automatic embedding generation
    - Deduplication via content_hash
    """
    
    def __init__(self, config: Optional[VectorStoreConfig] = None):
        """
        Initialize vector store.
        
        Args:
            config: Vector store configuration
        """
        self.config = config or VectorStoreConfig()
        
        # Ensure persist directory exists
        self.persist_dir = Path(self.config.persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components (lazy)
        self._client = None
        self._collection = None
        self._embedding_service = None
    
    # =========================================================================
    # PROPERTIES (LAZY LOADING)
    # =========================================================================
    
    @property
    def client(self):
        """Lazy-load ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
                
                self._client = chromadb.PersistentClient(
                    path=str(self.persist_dir),
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True,
                    )
                )
                logger.info(f"ChromaDB client initialized at {self.persist_dir}")
            except ImportError:
                raise ImportError(
                    "ChromaDB not installed. "
                    "Install with: pip install chromadb"
                )
        return self._client
    
    @property
    def collection(self):
        """Get or create the document collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"description": "Portfolio document embeddings"}
            )
            logger.info(f"Using collection: {self.config.collection_name} "
                       f"({self._collection.count()} documents)")
        return self._collection
    
    @property
    def embedding_service(self) -> EmbeddingService:
        """Lazy-load embedding service."""
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService(
                config=self.config.embedding_config,
                prefer_local=self.config.prefer_local_embeddings,
            )
        return self._embedding_service
    
    # =========================================================================
    # DOCUMENT OPERATIONS
    # =========================================================================
    
    def add_document(self, document: Document) -> str:
        """
        Add a document to the vector store.
        
        Document must already be chunked (document.chunks populated).
        If document with same content_hash exists, it's skipped.
        
        Args:
            document: Document with chunks to add
            
        Returns:
            Document ID (content_hash)
        """
        if not document.chunks:
            logger.warning(f"Document {document.filename} has no chunks, skipping")
            return ""
        
        if not document.content_hash:
            from .document_loader import compute_content_hash
            document.content_hash = compute_content_hash(document.content)
        
        doc_id = document.content_hash
        
        # Check if already exists
        existing = self._get_chunks_by_doc_id(doc_id)
        if existing:
            logger.info(f"Document {document.filename} already indexed, skipping")
            return doc_id
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        for chunk in document.chunks:
            chunk_id = f"{doc_id}_{chunk.index}"
            ids.append(chunk_id)
            documents.append(chunk.content)
            
            # Build metadata (ChromaDB requires flat dict with simple types)
            metadata = {
                "doc_id": doc_id,
                "chunk_index": chunk.index,
                "filename": document.filename,
                "doc_type": document.doc_type.value,
                "source": document.source.value,
                "ticker": document.ticker or "",
                "section_title": chunk.section_title or "",
                "page_number": chunk.page_number or 0,
                "token_count": chunk.token_count,
            }
            
            # Add dates (as ISO strings for filtering)
            if document.document_date:
                metadata["document_date"] = document.document_date.isoformat()
                metadata["document_year"] = document.document_date.year
                metadata["document_month"] = document.document_date.month
            
            metadata["upload_date"] = document.upload_date.isoformat()
            
            metadatas.append(metadata)
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(documents)} chunks...")
        embeddings = self.embedding_service.embed_documents(documents)
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        
        logger.info(f"Added document {document.filename}: {len(document.chunks)} chunks")
        
        return doc_id
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document and all its chunks.
        
        Args:
            doc_id: Document ID (content_hash)
            
        Returns:
            True if document was deleted
        """
        # Find all chunks with this doc_id
        results = self.collection.get(
            where={"doc_id": doc_id},
            include=["metadatas"]
        )
        
        if not results["ids"]:
            logger.warning(f"Document {doc_id} not found")
            return False
        
        # Delete chunks
        self.collection.delete(ids=results["ids"])
        
        logger.info(f"Deleted document {doc_id}: {len(results['ids'])} chunks removed")
        return True
    
    def _get_chunks_by_doc_id(self, doc_id: str) -> List[str]:
        """Get chunk IDs for a document."""
        results = self.collection.get(
            where={"doc_id": doc_id},
            include=[]
        )
        return results["ids"]
    
    # =========================================================================
    # SEARCH OPERATIONS
    # =========================================================================
    
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Semantic search with optional filters.
        
        Args:
            query: Search query text
            filters: Optional metadata filters:
                - ticker: str (e.g., "NVDA")
                - doc_type: str (e.g., "earnings", "10k")
                - year: int (document year)
                - days_back: int (documents from last N days)
            top_k: Number of results (default from config)
            min_score: Minimum similarity score (default from config)
            
        Returns:
            List of SearchResult objects, sorted by relevance
        """
        top_k = top_k or self.config.default_top_k
        min_score = min_score or self.config.relevance_threshold
        
        # Build ChromaDB where clause
        where_clause = self._build_where_clause(filters)
        
        # Generate query embedding
        query_embedding = self.embedding_service.embed_query(query)
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause if where_clause else None,
            include=["documents", "metadatas", "distances"],
        )
        
        # Convert to SearchResult objects
        search_results = []
        
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # ChromaDB returns L2 distance, convert to similarity score
                # Lower distance = more similar
                distance = results["distances"][0][i]
                # Convert L2 distance to similarity (approximate)
                # This gives ~1.0 for identical, ~0 for very different
                score = 1.0 / (1.0 + distance)
                
                # Skip low-relevance results
                if score < min_score:
                    continue
                
                metadata = results["metadatas"][0][i]
                content = results["documents"][0][i]
                
                # Reconstruct Chunk
                chunk = Chunk(
                    content=content,
                    index=metadata.get("chunk_index", 0),
                    token_count=metadata.get("token_count", 0),
                    metadata=metadata,
                    section_title=metadata.get("section_title") or None,
                    page_number=metadata.get("page_number") or None,
                    chunk_id=chunk_id,
                )
                
                # Parse doc_type
                doc_type_str = metadata.get("doc_type", "other")
                try:
                    doc_type = DocumentType(doc_type_str)
                except ValueError:
                    doc_type = DocumentType.OTHER
                
                # Parse document_date
                doc_date = None
                if metadata.get("document_date"):
                    try:
                        doc_date = date.fromisoformat(metadata["document_date"])
                    except ValueError:
                        pass
                
                result = SearchResult(
                    chunk=chunk,
                    score=score,
                    document_id=metadata.get("doc_id"),
                    filename=metadata.get("filename"),
                    doc_type=doc_type,
                    ticker=metadata.get("ticker") or None,
                    document_date=doc_date,
                )
                
                search_results.append(result)
        
        # Sort by score (highest first)
        search_results.sort(key=lambda x: x.score, reverse=True)
        
        logger.debug(f"Search '{query[:50]}...' returned {len(search_results)} results")
        
        return search_results
    
    def _build_where_clause(self, filters: Optional[Dict[str, Any]]) -> Optional[Dict]:
        """Build ChromaDB where clause from filters."""
        if not filters:
            return None
        
        conditions = []
        
        # Ticker filter
        if filters.get("ticker"):
            conditions.append({"ticker": filters["ticker"]})
        
        # Document type filter
        if filters.get("doc_type"):
            doc_type = filters["doc_type"]
            if isinstance(doc_type, DocumentType):
                doc_type = doc_type.value
            conditions.append({"doc_type": doc_type})
        
        # Year filter
        if filters.get("year"):
            conditions.append({"document_year": filters["year"]})
        
        # Days back filter (recent documents)
        if filters.get("days_back"):
            cutoff = date.today().isoformat()
            # Note: ChromaDB doesn't support date comparison well
            # We'd need to filter post-query or use year/month
            # For now, we'll rely on year filter
            pass
        
        # Combine conditions with AND
        if not conditions:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        count = self.collection.count()
        
        # Sample metadata to get unique values
        sample = self.collection.get(
            limit=1000,
            include=["metadatas"]
        )
        
        tickers = set()
        doc_types = set()
        doc_ids = set()
        
        for metadata in sample.get("metadatas", []):
            if metadata.get("ticker"):
                tickers.add(metadata["ticker"])
            if metadata.get("doc_type"):
                doc_types.add(metadata["doc_type"])
            if metadata.get("doc_id"):
                doc_ids.add(metadata["doc_id"])
        
        return {
            "total_chunks": count,
            "unique_documents": len(doc_ids),
            "unique_tickers": list(tickers),
            "document_types": list(doc_types),
            "collection_name": self.config.collection_name,
            "persist_dir": str(self.persist_dir),
            "embedding_model": self.embedding_service.model_name,
            "embedding_dimensions": self.embedding_service.dimensions,
        }
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all indexed documents (not chunks)."""
        # Get all unique doc_ids
        all_data = self.collection.get(
            limit=10000,
            include=["metadatas"]
        )
        
        documents = {}
        
        for metadata in all_data.get("metadatas", []):
            doc_id = metadata.get("doc_id")
            if doc_id and doc_id not in documents:
                documents[doc_id] = {
                    "doc_id": doc_id,
                    "filename": metadata.get("filename"),
                    "ticker": metadata.get("ticker"),
                    "doc_type": metadata.get("doc_type"),
                    "document_date": metadata.get("document_date"),
                    "chunk_count": 0,
                }
            if doc_id:
                documents[doc_id]["chunk_count"] += 1
        
        return list(documents.values())
    
    def get_document_by_hash(self, content_hash: str) -> Optional[str]:
        """
        Check if a document with given content hash is already indexed.
        
        Args:
            content_hash: The content hash to look for
            
        Returns:
            Document ID if found, None otherwise
        """
        try:
            # Query for documents with matching content_hash
            results = self.collection.get(
                where={"content_hash": content_hash},
                limit=1,
            )
            
            if results and results.get("ids"):
                return results["ids"][0]
            
            return None
            
        except Exception as e:
            logger.debug(f"Error checking document hash: {e}")
            return None
    
    def clear(self) -> int:
        """
        Clear all documents from the collection.
        
        Returns:
            Number of chunks deleted
        """
        count = self.collection.count()
        
        if count > 0:
            # Get all IDs and delete
            all_ids = self.collection.get(include=[])["ids"]
            if all_ids:
                self.collection.delete(ids=all_ids)
        
        logger.info(f"Cleared {count} chunks from collection")
        return count
    



# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Module-level singleton
_default_store: Optional[VectorStore] = None


def get_vector_store(config: Optional[VectorStoreConfig] = None) -> VectorStore:
    """Get or create the default vector store."""
    global _default_store
    
    if _default_store is None:
        _default_store = VectorStore(config)
    
    return _default_store


def add_document_to_store(document: Document) -> str:
    """Convenience function to add a document."""
    store = get_vector_store()
    return store.add_document(document)


def search_documents(
    query: str,
    ticker: Optional[str] = None,
    doc_type: Optional[str] = None,
    top_k: int = 5,
) -> List[SearchResult]:
    """
    Convenience function for document search.
    
    Args:
        query: Search query
        ticker: Filter by ticker
        doc_type: Filter by document type
        top_k: Number of results
        
    Returns:
        List of SearchResult
    """
    store = get_vector_store()
    
    filters = {}
    if ticker:
        filters["ticker"] = ticker
    if doc_type:
        filters["doc_type"] = doc_type
    
    return store.search(query, filters=filters, top_k=top_k)