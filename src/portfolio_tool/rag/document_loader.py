# src/portfolio_tool/rag/document_loader.py
"""
Document Loading for RAG Pipeline.

Phase: 6.7 - RAG Integration (Phase 1: Document Ingestion)

PURPOSE:
Load documents from various sources into the Document schema:
- PDF files (earnings reports, 10-K/10-Q filings)
- Text files (Fed minutes, research notes)
- User uploads

DESIGN PRINCIPLES:
- Each loader method returns a Document schema
- Metadata extraction is automatic where possible (ticker from filename, dates)
- Content hash computed for deduplication
- Graceful error handling with status tracking

DEPENDENCIES:
- PyMuPDF (fitz) for PDF parsing
- tiktoken for token counting
"""

import hashlib
import os
import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Tuple, List
import logging

from .schemas import (
    Document,
    DocumentType,
    DocumentSource,
    DocumentStatus,
)

logger = logging.getLogger(__name__)


# =============================================================================
# TOKEN COUNTING
# =============================================================================

def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    Count tokens in text using tiktoken.
    
    Falls back to word-based estimation if tiktoken unavailable.
    
    Args:
        text: Text to count
        model: Tokenizer model (cl100k_base for GPT-4/Claude)
    
    Returns:
        Approximate token count
    """
    try:
        import tiktoken
        encoding = tiktoken.get_encoding(model)
        return len(encoding.encode(text))
    except ImportError:
        # Fallback: ~4 chars per token (rough approximation)
        return len(text) // 4
    except Exception as e:
        logger.warning(f"Token counting failed: {e}, using estimation")
        return len(text) // 4


def compute_content_hash(content: str) -> str:
    """Compute SHA256 hash of content for deduplication."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


# =============================================================================
# METADATA EXTRACTION
# =============================================================================

def extract_ticker_from_filename(filename: str) -> Optional[str]:
    """
    Extract stock ticker from filename.
    
    Patterns recognized:
    - NVDA_Q3_2024.pdf → NVDA
    - nvidia_10k_2024.pdf → (no match, not a ticker)
    - AAPL-earnings-Q2.txt → AAPL
    - 10K_MSFT_2024.pdf → MSFT
    
    Returns:
        Ticker string (uppercase) or None
    """
    # Common ticker patterns (1-5 uppercase letters, possibly at start or after underscore/hyphen)
    patterns = [
        r'^([A-Z]{1,5})[-_]',           # NVDA_Q3_2024.pdf
        r'[-_]([A-Z]{1,5})[-_]',        # 10K_MSFT_2024.pdf
        r'[-_]([A-Z]{1,5})$',           # report_GOOG (at end of basename, before extension)
        r'^([A-Z]{1,5})\.',             # NVDA.pdf
    ]
    
    base_name = os.path.splitext(filename)[0]
    
    for pattern in patterns:
        match = re.search(pattern, base_name)
        if match:
            ticker = match.group(1)
            # Validate it looks like a real ticker (not common words)
            if ticker not in {'THE', 'AND', 'FOR', 'PDF', 'DOC', 'TXT', 'Q1', 'Q2', 'Q3', 'Q4'}:
                return ticker
    
    return None


def extract_date_from_filename(filename: str) -> Optional[date]:
    """
    Extract date from filename.
    
    Patterns recognized:
    - NVDA_Q3_2024.pdf → 2024-09-30 (Q3 end)
    - Fed_Minutes_2024-12-18.txt → 2024-12-18
    - earnings_20241115.pdf → 2024-11-15
    
    Returns:
        Date object or None
    """
    base_name = os.path.splitext(filename)[0]
    
    # Pattern 1: YYYY-MM-DD or YYYY_MM_DD
    match = re.search(r'(\d{4})[-_](\d{2})[-_](\d{2})', base_name)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            pass
    
    # Pattern 2: YYYYMMDD
    match = re.search(r'(\d{4})(\d{2})(\d{2})', base_name)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            pass
    
    # Pattern 3: Quarter + Year (Q1-Q4 2024)
    match = re.search(r'Q([1-4])[-_]?(\d{4})', base_name, re.IGNORECASE)
    if match:
        quarter = int(match.group(1))
        year = int(match.group(2))
        # Return quarter end date
        quarter_end_months = {1: 3, 2: 6, 3: 9, 4: 12}
        quarter_end_days = {1: 31, 2: 30, 3: 30, 4: 31}
        return date(year, quarter_end_months[quarter], quarter_end_days[quarter])
    
    # Pattern 4: Just year (2024)
    match = re.search(r'(\d{4})', base_name)
    if match:
        year = int(match.group(1))
        if 2000 <= year <= 2100:
            return date(year, 12, 31)  # Default to year end
    
    return None


def infer_document_type(filename: str, content: str = "") -> DocumentType:
    """
    Infer document type from filename and content.
    
    Priority:
    1. Filename keywords
    2. Content keywords (if available)
    3. Default to OTHER
    """
    filename_lower = filename.lower()
    content_lower = content[:5000].lower() if content else ""
    
    # Check filename first
    if any(kw in filename_lower for kw in ['10-k', '10k', 'annual_report']):
        return DocumentType.FILING_10K
    if any(kw in filename_lower for kw in ['10-q', '10q', 'quarterly_report']):
        return DocumentType.FILING_10Q
    if any(kw in filename_lower for kw in ['earnings', 'q1', 'q2', 'q3', 'q4', 'quarter']):
        return DocumentType.EARNINGS
    if any(kw in filename_lower for kw in ['fed_minutes', 'fomc', 'federal_reserve']):
        return DocumentType.FED_MINUTES
    if any(kw in filename_lower for kw in ['research', 'analysis', 'report']):
        return DocumentType.RESEARCH
    if any(kw in filename_lower for kw in ['news', 'article', 'press']):
        return DocumentType.NEWS
    if any(kw in filename_lower for kw in ['memo', 'note', 'thesis']):
        return DocumentType.MEMO
    
    # Check content keywords
    if content_lower:
        if 'form 10-k' in content_lower or 'annual report' in content_lower:
            return DocumentType.FILING_10K
        if 'form 10-q' in content_lower:
            return DocumentType.FILING_10Q
        if 'earnings' in content_lower and 'quarter' in content_lower:
            return DocumentType.EARNINGS
        if 'federal open market committee' in content_lower or 'fomc' in content_lower:
            return DocumentType.FED_MINUTES
    
    return DocumentType.OTHER


# =============================================================================
# DOCUMENT LOADER CLASS
# =============================================================================

class DocumentLoader:
    """
    Load documents from various sources.
    
    Usage:
        loader = DocumentLoader()
        
        # Load PDF
        doc = loader.load_pdf("path/to/NVDA_10K.pdf", ticker="NVDA")
        
        # Load text file
        doc = loader.load_text("path/to/fed_minutes.txt")
        
        # Load with auto-detection
        doc = loader.load("path/to/file.pdf")
    """
    
    def __init__(self, documents_dir: Optional[str] = None):
        """
        Initialize loader.
        
        Args:
            documents_dir: Base directory for document storage (optional)
        """
        self.documents_dir = documents_dir
    
    def load(
        self,
        filepath: str,
        ticker: Optional[str] = None,
        doc_type: Optional[DocumentType] = None,
        source: DocumentSource = DocumentSource.USER_UPLOAD,
        document_date: Optional[date] = None,
    ) -> Document:
        """
        Load a document with automatic format detection.
        
        Args:
            filepath: Path to the file
            ticker: Stock ticker (auto-extracted if not provided)
            doc_type: Document type (auto-inferred if not provided)
            source: Where the document came from
            document_date: Date of the document (auto-extracted if not provided)
        
        Returns:
            Document object with content and metadata
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format not supported
        """
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        extension = path.suffix.lower()
        
        if extension == '.pdf':
            return self.load_pdf(filepath, ticker, doc_type, source, document_date)
        elif extension in ['.txt', '.md', '.text']:
            return self.load_text(filepath, ticker, doc_type, source, document_date)
        else:
            raise ValueError(f"Unsupported file format: {extension}. Supported: .pdf, .txt, .md")
    
    def load_pdf(
        self,
        filepath: str,
        ticker: Optional[str] = None,
        doc_type: Optional[DocumentType] = None,
        source: DocumentSource = DocumentSource.USER_UPLOAD,
        document_date: Optional[date] = None,
    ) -> Document:
        """
        Load a PDF file.
        
        Uses PyMuPDF (fitz) for extraction.
        Handles multi-page documents, extracts text per page.
        
        Args:
            filepath: Path to PDF file
            ticker: Stock ticker (auto-extracted from filename if not provided)
            doc_type: Document type (auto-inferred if not provided)
            source: Document source
            document_date: Date of document (auto-extracted if not provided)
        
        Returns:
            Document with extracted content
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError(
                "PyMuPDF (fitz) is required for PDF loading. "
                "Install with: pip install pymupdf"
            )
        
        path = Path(filepath)
        filename = path.name
        
        try:
            # Extract text from PDF
            doc = fitz.open(filepath)
            pages_text = []
            
            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    pages_text.append(f"[Page {page_num + 1}]\n{text}")
            
            content = "\n\n".join(pages_text)
            page_count = len(doc)
            doc.close()
            
            if not content.strip():
                logger.warning(f"PDF appears to be empty or image-only: {filename}")
                content = "[No extractable text found in PDF]"
            
            # Auto-extract metadata
            extracted_ticker = ticker or extract_ticker_from_filename(filename)
            extracted_date = document_date or extract_date_from_filename(filename)
            extracted_type = doc_type or infer_document_type(filename, content)
            
            # Create Document
            return Document(
                content=content,
                filename=filename,
                doc_type=extracted_type,
                source=source,
                ticker=extracted_ticker,
                document_date=extracted_date,
                status=DocumentStatus.PENDING,
                content_hash=compute_content_hash(content),
                total_tokens=count_tokens(content),
                page_count=page_count,
            )
            
        except Exception as e:
            logger.error(f"Error loading PDF {filename}: {e}")
            return Document(
                content="",
                filename=filename,
                doc_type=doc_type or DocumentType.OTHER,
                source=source,
                ticker=ticker,
                status=DocumentStatus.FAILED,
                error_message=str(e),
            )
    
    def load_text(
        self,
        filepath: str,
        ticker: Optional[str] = None,
        doc_type: Optional[DocumentType] = None,
        source: DocumentSource = DocumentSource.USER_UPLOAD,
        document_date: Optional[date] = None,
        encoding: str = 'utf-8',
    ) -> Document:
        """
        Load a text file (.txt, .md).
        
        Args:
            filepath: Path to text file
            ticker: Stock ticker
            doc_type: Document type
            source: Document source
            document_date: Date of document
            encoding: File encoding (default utf-8)
        
        Returns:
            Document with content
        """
        path = Path(filepath)
        filename = path.name
        
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
            
            if not content.strip():
                logger.warning(f"Text file is empty: {filename}")
                content = "[Empty file]"
            
            # Auto-extract metadata
            extracted_ticker = ticker or extract_ticker_from_filename(filename)
            extracted_date = document_date or extract_date_from_filename(filename)
            extracted_type = doc_type or infer_document_type(filename, content)
            
            return Document(
                content=content,
                filename=filename,
                doc_type=extracted_type,
                source=source,
                ticker=extracted_ticker,
                document_date=extracted_date,
                status=DocumentStatus.PENDING,
                content_hash=compute_content_hash(content),
                total_tokens=count_tokens(content),
                page_count=1,
            )
            
        except UnicodeDecodeError:
            logger.warning(f"UTF-8 decode failed for {filename}, trying latin-1")
            return self.load_text(filepath, ticker, doc_type, source, document_date, encoding='latin-1')
            
        except Exception as e:
            logger.error(f"Error loading text file {filename}: {e}")
            return Document(
                content="",
                filename=filename,
                doc_type=doc_type or DocumentType.OTHER,
                source=source,
                ticker=ticker,
                status=DocumentStatus.FAILED,
                error_message=str(e),
            )
    
    def load_from_string(
        self,
        content: str,
        filename: str,
        ticker: Optional[str] = None,
        doc_type: Optional[DocumentType] = None,
        source: DocumentSource = DocumentSource.MANUAL,
        document_date: Optional[date] = None,
    ) -> Document:
        """
        Create a Document from a string (for programmatic loading).
        
        Useful for:
        - Fed minutes from fed_scraper.py
        - API responses
        - Test data
        
        Args:
            content: Document text content
            filename: Name to assign to document
            ticker: Stock ticker
            doc_type: Document type
            source: Document source
            document_date: Date of document
        
        Returns:
            Document object
        """
        extracted_type = doc_type or infer_document_type(filename, content)
        
        return Document(
            content=content,
            filename=filename,
            doc_type=extracted_type,
            source=source,
            ticker=ticker,
            document_date=document_date,
            status=DocumentStatus.PENDING,
            content_hash=compute_content_hash(content),
            total_tokens=count_tokens(content),
            page_count=1,
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def load_document(filepath: str, **kwargs) -> Document:
    """
    Convenience function to load a document.
    
    Usage:
        doc = load_document("path/to/file.pdf", ticker="NVDA")
    """
    loader = DocumentLoader()
    return loader.load(filepath, **kwargs)


def load_fed_minutes(content: str, meeting_date: date) -> Document:
    """
    Create a Document from Fed minutes content.
    
    Integration point for fed_scraper.py.
    
    Args:
        content: Fed minutes text
        meeting_date: Date of the FOMC meeting
    
    Returns:
        Document configured for Fed minutes
    """
    filename = f"Fed_Minutes_{meeting_date.isoformat()}.txt"
    
    loader = DocumentLoader()
    return loader.load_from_string(
        content=content,
        filename=filename,
        doc_type=DocumentType.FED_MINUTES,
        source=DocumentSource.FEDERAL_RESERVE,
        document_date=meeting_date,
    )
