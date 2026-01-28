# src/portfolio_tool/rag/document_manager.py
"""
Document Manager for RAG Pipeline.

Phase: 6.7 - RAG Integration

PURPOSE:
Centralized management of document ingestion, listing, and auto-discovery.
This is the "glue" that makes RAG easy to use.

FEATURES:
- Auto-discover documents from configured folder
- Ingest documents (load → chunk → embed → store)
- List indexed documents
- Delete/re-index documents
- Fed minutes auto-fetch

USAGE:
    from portfolio_tool.rag import DocumentManager
    
    dm = DocumentManager()
    
    # Ingest a document
    dm.ingest("path/to/NVDA_10K.pdf", ticker="NVDA")
    
    # Ingest all documents in folder
    dm.ingest_folder()
    
    # List indexed documents
    dm.list_documents()
    
    # Fetch and ingest latest Fed minutes
    dm.ingest_fed_minutes()
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Result of document ingestion."""
    success: bool
    filepath: str
    doc_id: Optional[str] = None
    ticker: Optional[str] = None
    doc_type: Optional[str] = None
    chunk_count: int = 0
    error: Optional[str] = None
    skipped: bool = False  # True if already indexed
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "filepath": self.filepath,
            "doc_id": self.doc_id,
            "ticker": self.ticker,
            "doc_type": self.doc_type,
            "chunk_count": self.chunk_count,
            "error": self.error,
            "skipped": self.skipped,
        }


class DocumentManager:
    """
    Central manager for RAG document operations.
    
    Handles:
    - Document ingestion (file → vector store)
    - Auto-discovery from folder
    - Fed minutes fetching
    - Document listing and deletion
    """
    
    def __init__(self, config=None):
        """
        Initialize DocumentManager.
        
        Args:
            config: Optional RAGConfig (uses default from config.py if not provided)
        """
        self._config = config
        self._vector_store = None
        self._loader = None
        self._chunker = None
    
    @property
    def config(self):
        """Lazy load config."""
        if self._config is None:
            from config import config as app_config
            self._config = app_config.rag
        return self._config
    
    @property
    def documents_dir(self) -> Path:
        """Get documents directory, create if needed."""
        path = Path(self.config.documents_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def vector_store(self):
        """Lazy load vector store."""
        if self._vector_store is None:
            from portfolio_tool.rag import VectorStore
            self._vector_store = VectorStore()
        return self._vector_store
    
    @property
    def loader(self):
        """Lazy load document loader."""
        if self._loader is None:
            from portfolio_tool.rag import DocumentLoader
            self._loader = DocumentLoader()
        return self._loader
    
    @property
    def chunker(self):
        """Lazy load chunker."""
        if self._chunker is None:
            from portfolio_tool.rag import Chunker
            self._chunker = Chunker(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                min_chunk_size=self.config.min_chunk_size,
            )
        return self._chunker
    
    # =========================================================================
    # INGESTION
    # =========================================================================
    
    def ingest(
        self,
        filepath: str,
        ticker: Optional[str] = None,
        doc_type: Optional[str] = None,
        force: bool = False,
    ) -> IngestionResult:
        """
        Ingest a single document into the vector store.
        
        Args:
            filepath: Path to document (PDF, TXT, MD)
            ticker: Stock ticker (auto-detected if not provided)
            doc_type: Document type (auto-detected if not provided)
            force: Re-ingest even if already indexed
            
        Returns:
            IngestionResult with status and details
        """
        filepath = str(filepath)
        
        try:
            # Check file exists
            if not os.path.exists(filepath):
                return IngestionResult(
                    success=False,
                    filepath=filepath,
                    error=f"File not found: {filepath}"
                )
            
            # Check file extension
            ext = os.path.splitext(filepath)[1].lower()
            if ext not in self.config.supported_extensions:
                return IngestionResult(
                    success=False,
                    filepath=filepath,
                    error=f"Unsupported file type: {ext}. Supported: {self.config.supported_extensions}"
                )
            
            # Check file size
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            if size_mb > self.config.max_document_size_mb:
                return IngestionResult(
                    success=False,
                    filepath=filepath,
                    error=f"File too large: {size_mb:.1f}MB (max: {self.config.max_document_size_mb}MB)"
                )
            
            # Load document
            logger.info(f"Loading document: {filepath}")
            doc = self.loader.load(filepath, ticker=ticker)
            
            # Override doc_type if provided
            if doc_type:
                from portfolio_tool.rag import DocumentType
                try:
                    doc.doc_type = DocumentType(doc_type)
                except ValueError:
                    doc.doc_type = DocumentType.OTHER
            
            # Check if already indexed (unless force)
            if not force:
                existing = self.vector_store.get_document_by_hash(doc.content_hash)
                if existing:
                    logger.info(f"Document already indexed: {filepath}")
                    return IngestionResult(
                        success=True,
                        filepath=filepath,
                        doc_id=doc.content_hash,
                        ticker=doc.ticker,
                        doc_type=doc.doc_type.value if doc.doc_type else None,
                        skipped=True,
                    )
            
            # Chunk document
            logger.info(f"Chunking document: {doc.filename}")
            chunks = self.chunker.chunk_document(doc)
            
            if not chunks:
                return IngestionResult(
                    success=False,
                    filepath=filepath,
                    error="Document produced no chunks (possibly empty)"
                )
            
            # Add to vector store
            logger.info(f"Indexing {len(chunks)} chunks")
            doc_id = self.vector_store.add_document(doc)
            
            logger.info(f"✓ Ingested: {filepath} ({len(chunks)} chunks)")
            
            return IngestionResult(
                success=True,
                filepath=filepath,
                doc_id=doc_id,
                ticker=doc.ticker,
                doc_type=doc.doc_type.value if doc.doc_type else None,
                chunk_count=len(chunks),
            )
            
        except Exception as e:
            logger.error(f"Ingestion failed for {filepath}: {e}")
            return IngestionResult(
                success=False,
                filepath=filepath,
                error=str(e)
            )
    
    def ingest_folder(
        self,
        folder: Optional[str] = None,
        force: bool = False,
    ) -> List[IngestionResult]:
        """
        Ingest all documents from a folder.
        
        Args:
            folder: Folder path (uses config.documents_dir if not provided)
            force: Re-ingest even if already indexed
            
        Returns:
            List of IngestionResult for each file
        """
        folder = Path(folder) if folder else self.documents_dir
        
        if not folder.exists():
            logger.warning(f"Documents folder does not exist: {folder}")
            return []
        
        results = []
        
        # Find all supported files
        for ext in self.config.supported_extensions:
            for filepath in folder.glob(f"*{ext}"):
                result = self.ingest(str(filepath), force=force)
                results.append(result)
        
        # Summary
        success_count = sum(1 for r in results if r.success and not r.skipped)
        skip_count = sum(1 for r in results if r.skipped)
        fail_count = sum(1 for r in results if not r.success)
        
        logger.info(f"Folder ingestion complete: {success_count} added, {skip_count} skipped, {fail_count} failed")
        
        return results
    
    # =========================================================================
    # FED MINUTES
    # =========================================================================
    
    def ingest_fed_minutes(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        force: bool = False,
    ) -> IngestionResult:
        """
        Fetch and ingest Fed minutes.
        
        Args:
            year: Meeting year (default: latest)
            month: Meeting month (default: latest)
            force: Re-ingest even if already indexed
            
        Returns:
            IngestionResult
        """
        try:
            from portfolio_tool.rag.fed_scraper import FedMinutesScraper, DownloadStatus
            
            scraper = FedMinutesScraper()
            
            # Get minutes
            if year and month:
                doc = scraper.get_minutes_by_date(year, month)
            else:
                doc = scraper.get_latest_minutes()
            
            if doc.download_status not in [DownloadStatus.SUCCESS, DownloadStatus.CACHED]:
                return IngestionResult(
                    success=False,
                    filepath="Fed Minutes",
                    error=doc.error_message or "Failed to fetch Fed minutes"
                )
            
            # Save to documents folder
            meeting_date = doc.metadata.meeting_date
            filename = f"Fed_Minutes_{meeting_date.strftime('%Y_%m')}.txt"
            filepath = self.documents_dir / filename
            
            # Write content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(doc.content)
            
            # Ingest
            return self.ingest(
                str(filepath),
                ticker=None,
                doc_type="fed_minutes",
                force=force,
            )
            
        except ImportError as e:
            return IngestionResult(
                success=False,
                filepath="Fed Minutes",
                error=f"Fed scraper not available: {e}"
            )
        except Exception as e:
            return IngestionResult(
                success=False,
                filepath="Fed Minutes",
                error=str(e)
            )
    
    # =========================================================================
    # LISTING & MANAGEMENT
    # =========================================================================
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all indexed documents.
        
        Returns:
            List of document metadata dicts
        """
        return self.vector_store.list_documents()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get document statistics.
        
        Returns:
            Dict with counts, tickers, doc types, etc.
        """
        stats = self.vector_store.get_stats()
        
        # Add folder info
        stats["documents_dir"] = str(self.documents_dir)
        stats["files_in_folder"] = len(list(self.documents_dir.glob("*")))
        
        return stats
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the index.
        
        Args:
            doc_id: Document ID (content hash)
            
        Returns:
            True if deleted, False if not found
        """
        return self.vector_store.delete_document(doc_id)
    
    def clear_all(self) -> bool:
        """
        Clear all documents from the index.
        
        WARNING: This deletes ALL indexed documents.
        
        Returns:
            True if successful
        """
        logger.warning("Clearing all documents from vector store")
        return self.vector_store.clear()
    
    # =========================================================================
    # SEARCH (Convenience wrapper)
    # =========================================================================
    
    def search(
        self,
        query: str,
        ticker: Optional[str] = None,
        doc_type: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search indexed documents.
        
        Args:
            query: Search query
            ticker: Filter by ticker
            doc_type: Filter by document type
            top_k: Number of results
            
        Returns:
            List of search result dicts
        """
        filters = {}
        if ticker:
            filters["ticker"] = ticker.upper()
        if doc_type:
            filters["doc_type"] = doc_type
        
        results = self.vector_store.search(
            query=query,
            filters=filters if filters else None,
            top_k=top_k,
        )
        
        return [
            {
                "content": r.chunk.content,
                "score": r.score,
                "ticker": r.ticker,
                "doc_type": r.doc_type.value if r.doc_type else None,
                "filename": r.filename,
                "citation": r.get_citation(),
            }
            for r in results
        ]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_manager_instance: Optional[DocumentManager] = None


def get_document_manager() -> DocumentManager:
    """Get or create DocumentManager singleton."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = DocumentManager()
    return _manager_instance


def ingest_document(
    filepath: str,
    ticker: Optional[str] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Convenience function to ingest a document.
    
    Args:
        filepath: Path to document
        ticker: Optional ticker
        force: Re-ingest if already exists
        
    Returns:
        Result dict
    """
    dm = get_document_manager()
    result = dm.ingest(filepath, ticker=ticker, force=force)
    return result.to_dict()


def ingest_all_documents(force: bool = False) -> List[Dict[str, Any]]:
    """
    Ingest all documents from the configured folder.
    
    Args:
        force: Re-ingest if already exists
        
    Returns:
        List of result dicts
    """
    dm = get_document_manager()
    results = dm.ingest_folder(force=force)
    return [r.to_dict() for r in results]


def ingest_fed_minutes() -> Dict[str, Any]:
    """
    Fetch and ingest latest Fed minutes.
    
    Returns:
        Result dict
    """
    dm = get_document_manager()
    result = dm.ingest_fed_minutes()
    return result.to_dict()