# src/portfolio_tool/rag/schemas.py
"""
RAG Data Structures for Document Processing and Search.

Phase: 6.7 - RAG Integration

PURPOSE:
These schemas define the data structures for:
- Document ingestion (loading PDFs, text files)
- Chunking (section-aware splitting)
- Vector search results
- Document insights for Decision Engine integration

DESIGN PRINCIPLES:
- Dataclasses for immutability and type safety
- to_dict() methods for serialization (matches decision_schemas.py pattern)
- format_summary() for human-readable output
- All fields typed for IDE support

INTEGRATION:
- DocumentInsights feeds into DecisionEngine.run_decision_assessment()
- SearchResult provides citations for PMDecisionSummary
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import List, Dict, Optional, Any


# =============================================================================
# ENUMS
# =============================================================================

class DocumentType(str, Enum):
    """
    Supported document types.
    
    Each type has specific extraction logic in document_loader.py
    """
    EARNINGS = "earnings"           # Quarterly/annual earnings reports
    FILING_10K = "10k"              # SEC 10-K annual filing
    FILING_10Q = "10q"              # SEC 10-Q quarterly filing
    FED_MINUTES = "fed_minutes"     # Federal Reserve meeting minutes
    RESEARCH = "research"           # Analyst research notes
    NEWS = "news"                   # News articles
    MEMO = "memo"                   # Internal investment memos
    OTHER = "other"                 # Unclassified documents


class DocumentSource(str, Enum):
    """Where the document came from."""
    SEC_EDGAR = "sec_edgar"
    FEDERAL_RESERVE = "federal_reserve"
    USER_UPLOAD = "user_upload"
    NEWS_API = "news_api"
    MANUAL = "manual"


class DocumentStatus(str, Enum):
    """Processing status for documents."""
    PENDING = "pending"         # Uploaded, not yet processed
    PROCESSING = "processing"   # Currently being chunked/embedded
    PROCESSED = "processed"     # Successfully indexed
    FAILED = "failed"           # Processing error


# =============================================================================
# CORE DATA STRUCTURES
# =============================================================================

@dataclass
class Chunk:
    """
    A single chunk of text from a document.
    
    Chunks are the unit of storage in the vector store.
    Each chunk maintains metadata for filtering and citation.
    
    Design Decision:
    - chunk_id is assigned during vector store insertion
    - section_title helps with navigation ("Risk Factors" section)
    - page_number enables precise citations
    """
    content: str
    index: int                                  # Position within document (0-indexed)
    token_count: int                            # For context window management
    
    # Metadata (inherited from parent document + chunk-specific)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Chunk-specific location info
    section_title: Optional[str] = None         # e.g., "Risk Factors", "Revenue"
    page_number: Optional[int] = None           # For PDF citations
    start_char: Optional[int] = None            # Character offset in original
    end_char: Optional[int] = None
    
    # Assigned after vector store insertion
    chunk_id: Optional[str] = None              # ChromaDB ID
    embedding_id: Optional[str] = None          # Reference to embedding
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "index": self.index,
            "token_count": self.token_count,
            "metadata": self.metadata,
            "section_title": self.section_title,
            "page_number": self.page_number,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "chunk_id": self.chunk_id,
            "embedding_id": self.embedding_id,
        }
    
    def get_citation(self) -> str:
        """Generate a citation string for this chunk."""
        parts = []
        if self.metadata.get("filename"):
            parts.append(self.metadata["filename"])
        if self.section_title:
            parts.append(f"§{self.section_title}")
        if self.page_number:
            parts.append(f"p.{self.page_number}")
        return ", ".join(parts) if parts else f"Chunk {self.index}"


@dataclass
class Document:
    """
    A complete document with its content and metadata.
    
    Documents are processed into Chunks for vector storage.
    The original content is preserved for re-chunking if needed.
    
    Design Decision:
    - content_hash enables deduplication (don't re-index same doc)
    - ticker links documents to portfolio holdings
    - document_date is the date OF the content, not upload date
    """
    # Core content
    content: str
    filename: str
    
    # Classification
    doc_type: DocumentType
    source: DocumentSource
    
    # Linking to portfolio context
    ticker: Optional[str] = None                # e.g., "NVDA" for NVIDIA earnings
    
    # Dates
    document_date: Optional[date] = None        # Date of the document content
    upload_date: datetime = field(default_factory=datetime.utcnow)
    
    # Processing state
    status: DocumentStatus = DocumentStatus.PENDING
    content_hash: Optional[str] = None          # SHA256 for deduplication
    
    # Extracted structure
    sections: List[str] = field(default_factory=list)  # Section headers found
    chunks: List[Chunk] = field(default_factory=list)
    
    # Statistics
    total_tokens: int = 0
    page_count: int = 0
    
    # Database reference (after persistence)
    document_id: Optional[int] = None
    
    # Error tracking
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "doc_type": self.doc_type.value,
            "source": self.source.value,
            "ticker": self.ticker,
            "document_date": self.document_date.isoformat() if self.document_date else None,
            "upload_date": self.upload_date.isoformat(),
            "status": self.status.value,
            "content_hash": self.content_hash,
            "sections": self.sections,
            "total_tokens": self.total_tokens,
            "page_count": self.page_count,
            "chunk_count": len(self.chunks),
            "error_message": self.error_message,
        }
    
    def format_summary(self) -> str:
        """Human-readable document summary."""
        lines = [
            f"Document: {self.filename}",
            f"Type: {self.doc_type.value}",
            f"Ticker: {self.ticker or 'N/A'}",
            f"Date: {self.document_date or 'Unknown'}",
            f"Status: {self.status.value}",
            f"Chunks: {len(self.chunks)}",
            f"Tokens: {self.total_tokens:,}",
        ]
        if self.sections:
            lines.append(f"Sections: {', '.join(self.sections[:5])}")
        return "\n".join(lines)


# =============================================================================
# SEARCH RESULTS
# =============================================================================

@dataclass
class SearchResult:
    """
    A single search result from the vector store.
    
    Contains the matched chunk plus relevance scoring.
    Used to build DocumentInsights for the Decision Engine.
    """
    chunk: Chunk
    score: float                                # Similarity score (0-1, higher = better)
    
    # Parent document info (denormalized for convenience)
    document_id: Optional[int] = None
    filename: Optional[str] = None
    doc_type: Optional[DocumentType] = None
    ticker: Optional[str] = None
    document_date: Optional[date] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.chunk.content,
            "score": self.score,
            "citation": self.chunk.get_citation(),
            "document_id": self.document_id,
            "filename": self.filename,
            "doc_type": self.doc_type.value if self.doc_type else None,
            "ticker": self.ticker,
            "document_date": self.document_date.isoformat() if self.document_date else None,
            "section_title": self.chunk.section_title,
            "page_number": self.chunk.page_number,
        }
    
    def get_citation(self) -> str:
        """Full citation including document and chunk info."""
        doc_part = self.filename or f"Doc#{self.document_id}"
        chunk_part = self.chunk.get_citation()
        return f"{doc_part} - {chunk_part}" if chunk_part else doc_part


# =============================================================================
# DECISION ENGINE INTEGRATION
# =============================================================================

@dataclass
class DocumentInsights:
    """
    Structured insights from RAG for the Decision Engine.
    
    This is the OUTPUT of RAG Agent and INPUT to Decision Engine.
    It feeds into run_decision_assessment() to enhance decisions.
    
    KEY PRINCIPLE:
    RAG insights are ONE input alongside current_weights, macro_regime, etc.
    The Decision Engine synthesizes ALL inputs into HOLD/TILT/REBALANCE/HEDGE.
    
    Interview talking point:
    "Documents don't make decisions - they inform the Decision Engine.
    A bullish earnings report might increase confidence in a TILT,
    or reveal risks that lead to HOLD despite positive headlines."
    """
    # Sources used
    sources: List[str] = field(default_factory=list)
    # e.g., ["NVDA_Q3_2024_Earnings.pdf", "Fed_Minutes_Dec2024.txt"]
    
    # Key findings (facts, metrics, quotes)
    key_findings: List[str] = field(default_factory=list)
    # e.g., ["Revenue: $18.1B (+12% vs consensus)", "Data center growth: +279% YoY"]
    
    # Identified risks from documents
    risk_factors: List[str] = field(default_factory=list)
    # e.g., ["China export restrictions (NVDA 10-K, p.12)", "Customer concentration"]
    
    # Overall sentiment (derived from document content)
    sentiment: Optional[str] = None  # "bullish", "bearish", "neutral", "mixed"
    sentiment_score: Optional[float] = None  # -1.0 to 1.0
    
    # Citable excerpts with references
    citations: List[Dict[str, str]] = field(default_factory=list)
    # e.g., [{"text": "Revenue exceeded...", "source": "NVDA_Q3.pdf, p.3"}]
    
    # Query that generated these insights
    query: Optional[str] = None
    
    # Tickers mentioned/relevant
    relevant_tickers: List[str] = field(default_factory=list)
    
    # Search metadata
    total_chunks_searched: int = 0
    top_k_returned: int = 0
    avg_relevance_score: float = 0.0
    
    # Timestamp
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sources": self.sources,
            "key_findings": self.key_findings,
            "risk_factors": self.risk_factors,
            "sentiment": self.sentiment,
            "sentiment_score": self.sentiment_score,
            "citations": self.citations,
            "query": self.query,
            "relevant_tickers": self.relevant_tickers,
            "total_chunks_searched": self.total_chunks_searched,
            "top_k_returned": self.top_k_returned,
            "avg_relevance_score": self.avg_relevance_score,
            "generated_at": self.generated_at.isoformat(),
        }
    
    def format_summary(self) -> str:
        """
        Format for human-readable output in synthesizer.
        This becomes the DOCUMENT INSIGHTS section in the response.
        """
        lines = [
            "═" * 60,
            "DOCUMENT INSIGHTS",
            "═" * 60,
        ]
        
        # Sources
        if self.sources:
            lines.append(f"Sources: {', '.join(self.sources[:3])}")
            if len(self.sources) > 3:
                lines.append(f"         (+{len(self.sources) - 3} more)")
        else:
            lines.append("Sources: No relevant documents found")
        
        lines.append("")
        
        # Key findings
        if self.key_findings:
            lines.append("Key Findings:")
            for finding in self.key_findings[:5]:
                lines.append(f"  • {finding}")
        
        lines.append("")
        
        # Risk factors
        if self.risk_factors:
            lines.append("Risk Factors (from filings):")
            for risk in self.risk_factors[:3]:
                lines.append(f"  ⚠ {risk}")
        
        # Sentiment
        if self.sentiment:
            sentiment_emoji = {
                "bullish": "📈",
                "bearish": "📉", 
                "neutral": "➡️",
                "mixed": "↔️"
            }.get(self.sentiment, "")
            lines.append("")
            lines.append(f"Document Sentiment: {sentiment_emoji} {self.sentiment.upper()}")
        
        return "\n".join(lines)
    
    def has_insights(self) -> bool:
        """Check if any meaningful insights were found."""
        return bool(self.key_findings or self.risk_factors or self.citations)
    
    def get_risk_factors_for_decision(self) -> List[str]:
        """
        Get risk factors formatted for PMDecisionSummary.key_risks.
        Prefixes with source for auditability.
        """
        return [f"[DOC] {rf}" for rf in self.risk_factors[:3]]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_empty_insights(query: str = "") -> DocumentInsights:
    """Create an empty DocumentInsights when no documents are found."""
    return DocumentInsights(
        sources=[],
        key_findings=["No relevant documents found in knowledge base"],
        risk_factors=[],
        sentiment=None,
        citations=[],
        query=query,
    )
