# src/portfolio_tool/tools/rag_tools.py
"""
RAG Tool Wrappers for Agent Integration.

Phase: 6.7 - RAG Integration (Phase 3: RAG Agent)

PURPOSE:
Thin wrappers around RAG functionality for agent use:
- search_documents: Semantic search with filters
- get_document_insights: Extract insights for Decision Engine
- get_fed_sentiment: Analyze Fed minutes
- ingest_document: Add document to vector store

DESIGN PRINCIPLES:
- Tools are THIN wrappers (no business logic here)
- Business logic lives in rag/ module
- Returns dicts suitable for LLM consumption
- Handles errors gracefully with informative messages

USAGE:
    from portfolio_tool.tools.rag_tools import search_documents, get_fed_sentiment
    
    # Search for documents
    results = search_documents("NVIDIA revenue", ticker="NVDA", top_k=5)
    
    # Get Fed sentiment
    sentiment = get_fed_sentiment(fed_minutes_text)
"""

import logging
from datetime import date
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


# =============================================================================
# DOCUMENT SEARCH
# =============================================================================

def search_documents(
    query: str,
    ticker: Optional[str] = None,
    doc_type: Optional[str] = None,
    year: Optional[int] = None,
    top_k: int = 5,
    min_score: float = 0.2,
) -> Dict[str, Any]:
    """
    Semantic search across indexed documents.
    
    Args:
        query: Search query text
        ticker: Filter by stock ticker (e.g., "NVDA")
        doc_type: Filter by document type (e.g., "earnings", "10k", "fed_minutes")
        year: Filter by document year
        top_k: Number of results to return
        min_score: Minimum relevance score (0-1)
        
    Returns:
        Dict with:
            - success: bool
            - results: List of search results
            - count: Number of results
            - query: Original query
            - error: Error message if failed
    """
    try:
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.rag import VectorStore, VectorStoreConfig
        
        # Build filters
        filters = {}
        if ticker:
            filters["ticker"] = ticker.upper()
        if doc_type:
            filters["doc_type"] = doc_type
        if year:
            filters["year"] = year
        
        # Search
        store = VectorStore()
        results = store.search(
            query=query,
            filters=filters if filters else None,
            top_k=top_k,
            min_score=min_score,
        )
        
        # Format results for agent consumption
        formatted_results = []
        for r in results:
            formatted_results.append({
                "content": r.chunk.content,
                "score": round(r.score, 3),
                "ticker": r.ticker,
                "doc_type": r.doc_type.value if r.doc_type else None,
                "filename": r.filename,
                "document_date": r.document_date.isoformat() if r.document_date else None,
                "section": r.chunk.section_title,
                "page": r.chunk.page_number,
                "citation": r.get_citation(),
            })
        
        return {
            "success": True,
            "results": formatted_results,
            "count": len(formatted_results),
            "query": query,
            "filters": filters,
        }
        
    except ImportError as e:
        logger.error(f"RAG module not available: {e}")
        return {
            "success": False,
            "results": [],
            "count": 0,
            "query": query,
            "error": f"RAG module not available: {e}",
        }
    except Exception as e:
        logger.error(f"Document search failed: {e}")
        return {
            "success": False,
            "results": [],
            "count": 0,
            "query": query,
            "error": str(e),
        }


def get_document_insights(
    query: str,
    ticker: Optional[str] = None,
    doc_type: Optional[str] = None,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Get structured insights from documents for Decision Engine integration.
    
    This is the main function for feeding document context into decisions.
    Returns a DocumentInsights-compatible structure.
    
    Args:
        query: What to search for
        ticker: Filter by ticker
        doc_type: Filter by document type
        top_k: Number of chunks to consider
        
    Returns:
        Dict matching DocumentInsights structure:
            - sources: List of source documents
            - key_findings: Extracted facts
            - risk_factors: Identified risks
            - citations: Quotable excerpts
            - sentiment: Overall document sentiment
    """
    try:
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.rag import (
            VectorStore, DocumentInsights, create_empty_insights
        )
        
        # Build filters
        filters = {}
        if ticker:
            filters["ticker"] = ticker.upper()
        if doc_type:
            filters["doc_type"] = doc_type
        
        # Search
        store = VectorStore()
        results = store.search(
            query=query,
            filters=filters if filters else None,
            top_k=top_k,
            min_score=0.2,
        )
        
        if not results:
            insights = create_empty_insights(query)
            return insights.to_dict()
        
        # Extract insights from results
        sources = list(set(r.filename for r in results if r.filename))
        relevant_tickers = list(set(r.ticker for r in results if r.ticker))
        
        # Extract key findings (top scoring chunks)
        key_findings = []
        for r in results[:3]:
            # Truncate long content
            content = r.chunk.content[:200] + "..." if len(r.chunk.content) > 200 else r.chunk.content
            key_findings.append(content)
        
        # Look for risk factors in content
        risk_factors = []
        risk_keywords = ["risk", "concern", "uncertainty", "challenge", "restriction", "limitation"]
        for r in results:
            content_lower = r.chunk.content.lower()
            if any(kw in content_lower for kw in risk_keywords):
                # Extract the risk-related sentence
                sentences = r.chunk.content.split('.')
                for sent in sentences:
                    if any(kw in sent.lower() for kw in risk_keywords):
                        risk_text = sent.strip()[:150]
                        if risk_text and risk_text not in risk_factors:
                            citation = f"({r.filename}, p.{r.chunk.page_number})" if r.chunk.page_number else f"({r.filename})"
                            risk_factors.append(f"{risk_text} {citation}")
                            break
        
        # Build citations
        citations = []
        for r in results[:3]:
            citations.append({
                "text": r.chunk.content[:150],
                "source": r.get_citation(),
            })
        
        # Calculate average relevance
        avg_score = sum(r.score for r in results) / len(results) if results else 0
        
        # Build insights
        insights = DocumentInsights(
            sources=sources[:5],
            key_findings=key_findings[:5],
            risk_factors=risk_factors[:3],
            citations=citations,
            query=query,
            relevant_tickers=relevant_tickers,
            total_chunks_searched=len(results),
            top_k_returned=len(results),
            avg_relevance_score=avg_score,
        )
        
        return insights.to_dict()
        
    except ImportError as e:
        logger.error(f"RAG module not available: {e}")
        return {
            "sources": [],
            "key_findings": [f"RAG module not available: {e}"],
            "risk_factors": [],
            "citations": [],
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Failed to get document insights: {e}")
        return {
            "sources": [],
            "key_findings": [f"Error: {e}"],
            "risk_factors": [],
            "citations": [],
            "error": str(e),
        }


# =============================================================================
# FED SENTIMENT
# =============================================================================

def get_fed_sentiment(
    text: str,
    use_llm: bool = True,
) -> Dict[str, Any]:
    """
    Analyze Fed minutes for hawkish/dovish sentiment.
    
    Uses hybrid approach: rule-based + LLM when uncertain.
    
    Args:
        text: Fed minutes text (full or excerpt)
        use_llm: Whether to enable LLM refinement (default True)
        
    Returns:
        Dict with:
            - success: bool
            - score: -1 (dovish) to +1 (hawkish)
            - confidence: 0-1
            - method: "rule_based", "llm", or "hybrid"
            - signals: Detected keywords
            - error/warning: If any issues
    """
    try:
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.rag.sentiment import FedSentimentAnalyzer, SentimentConfig
        
        config = SentimentConfig(llm_enabled=use_llm)
        analyzer = FedSentimentAnalyzer(config)
        
        return analyzer.analyze(text)
        
    except ImportError as e:
        logger.error(f"Sentiment module not available: {e}")
        return {
            "success": False,
            "score": 0.0,
            "confidence": 0.0,
            "method": "none",
            "error": f"Sentiment module not available: {e}",
        }
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return {
            "success": False,
            "score": 0.0,
            "confidence": 0.0,
            "method": "none",
            "error": str(e),
        }


def analyze_fed_minutes(
    year: Optional[int] = None,
    month: Optional[int] = None,
    use_llm: bool = True,
) -> Dict[str, Any]:
    """
    Fetch and analyze Fed minutes by date.
    
    Combines fed_scraper + sentiment analysis.
    
    Args:
        year: Meeting year (default: latest)
        month: Meeting month (default: latest)
        use_llm: Whether to use LLM for sentiment
        
    Returns:
        Dict with meeting info + sentiment analysis
    """
    try:
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.rag.fed_scraper import FedMinutesScraper, DownloadStatus
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.rag.sentiment import FedSentimentAnalyzer, SentimentConfig
        
        scraper = FedMinutesScraper()
        
        # Get minutes
        if year and month:
            doc = scraper.get_minutes_by_date(year, month)
        else:
            doc = scraper.get_latest_minutes()
        
        if doc.download_status not in [DownloadStatus.SUCCESS, DownloadStatus.CACHED]:
            return {
                "success": False,
                "meeting_date": None,
                "sentiment": None,
                "error": doc.error_message or "Failed to fetch Fed minutes",
            }
        
        # Analyze sentiment
        config = SentimentConfig(llm_enabled=use_llm)
        analyzer = FedSentimentAnalyzer(config)
        sentiment = analyzer.analyze(doc.content)
        
        return {
            "success": True,
            "meeting_date": doc.metadata.meeting_date.isoformat(),
            "title": doc.metadata.title,
            "content_length": len(doc.content),
            "sentiment": sentiment,
            "download_status": doc.download_status.value,
        }
        
    except ImportError as e:
        logger.error(f"Fed scraper not available: {e}")
        return {
            "success": False,
            "error": f"Fed scraper not available: {e}",
        }
    except Exception as e:
        logger.error(f"Fed minutes analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# =============================================================================
# DOCUMENT INGESTION
# =============================================================================

def ingest_document(
    filepath: str,
    ticker: Optional[str] = None,
    doc_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ingest a document into the vector store.
    
    Handles: load → chunk → embed → store
    
    Args:
        filepath: Path to document (PDF or text)
        ticker: Stock ticker (auto-detected if not provided)
        doc_type: Document type (auto-detected if not provided)
        
    Returns:
        Dict with:
            - success: bool
            - doc_id: Document ID (content hash)
            - filename: Document filename
            - chunk_count: Number of chunks created
            - error: Error message if failed
    """
    try:
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.rag import (
            DocumentLoader, Chunker, VectorStore,
            DocumentType
        )
        
        # Load document
        loader = DocumentLoader()
        doc = loader.load(filepath, ticker=ticker)
        
        # Override doc_type if provided
        if doc_type:
            try:
                doc.doc_type = DocumentType(doc_type)
            except ValueError:
                doc.doc_type = DocumentType.OTHER
        
        # Chunk
        chunker = Chunker(chunk_size=1000, chunk_overlap=100)
        chunks = chunker.chunk_document(doc)
        
        if not chunks:
            return {
                "success": False,
                "error": "Document produced no chunks (possibly empty)",
            }
        
        # Store
        store = VectorStore()
        doc_id = store.add_document(doc)
        
        return {
            "success": True,
            "doc_id": doc_id,
            "filename": doc.filename,
            "ticker": doc.ticker,
            "doc_type": doc.doc_type.value,
            "chunk_count": len(chunks),
            "total_tokens": doc.total_tokens,
        }
        
    except FileNotFoundError as e:
        return {
            "success": False,
            "error": f"File not found: {filepath}",
        }
    except ImportError as e:
        return {
            "success": False,
            "error": f"RAG module not available: {e}",
        }
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def list_indexed_documents() -> Dict[str, Any]:
    """
    List all documents in the vector store.
    
    Returns:
        Dict with:
            - success: bool
            - documents: List of document summaries
            - count: Total document count
    """
    try:
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.rag import VectorStore
        
        store = VectorStore()
        documents = store.list_documents()
        
        return {
            "success": True,
            "documents": documents,
            "count": len(documents),
        }
        
    except ImportError as e:
        return {
            "success": False,
            "documents": [],
            "count": 0,
            "error": f"RAG module not available: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "documents": [],
            "count": 0,
            "error": str(e),
        }


def get_vector_store_stats() -> Dict[str, Any]:
    """
    Get vector store statistics.
    
    Returns:
        Dict with store stats (chunk count, tickers, doc types, etc.)
    """
    try:
        from Finance.Korrekte_Versionen.AGENTIC_FINANCE.src.portfolio_tool.rag import VectorStore
        
        store = VectorStore()
        stats = store.get_stats()
        
        return {
            "success": True,
            **stats,
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"RAG module not available: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
