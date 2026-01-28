"""
Document Loading for RAG Pipeline.

Supports:
- Plain text files (.txt)
- PDF files (.pdf)
- Fed Minutes (special handling)
- Web URLs (future)

Documents are loaded into a standardized Document format
for downstream processing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import re


@dataclass
class Document:
    """
    Standardized document representation.
    
    All loaders produce Document objects for consistent downstream processing.
    """
    
    content: str
    source: str  # File path or URL
    
    # Metadata
    title: Optional[str] = None
    date: Optional[datetime] = None
    doc_type: str = "unknown"  # "fed_minutes", "earnings", "research", etc.
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Processing info
    char_count: int = 0
    word_count: int = 0
    
    def __post_init__(self):
        """Calculate basic stats."""
        if self.content:
            self.char_count = len(self.content)
            self.word_count = len(self.content.split())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "title": self.title,
            "date": self.date.isoformat() if self.date else None,
            "doc_type": self.doc_type,
            "char_count": self.char_count,
            "word_count": self.word_count,
            "metadata": self.metadata,
        }


class DocumentLoader:
    """
    Universal document loader.
    
    Automatically detects file type and uses appropriate loader.
    
    Example:
        loader = DocumentLoader()
        doc = loader.load("path/to/fed_minutes.pdf")
    """
    
    def __init__(self, default_encoding: str = "utf-8"):
        """Initialize loader."""
        self.default_encoding = default_encoding
    
    def load(self, path: Union[str, Path]) -> Document:
        """
        Load document from path.
        
        Automatically detects file type.
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        suffix = path.suffix.lower()
        
        if suffix == ".txt":
            return self.load_text(path)
        elif suffix == ".pdf":
            return self.load_pdf(path)
        elif suffix in [".md", ".markdown"]:
            return self.load_text(path)
        else:
            # Try as text
            return self.load_text(path)
    
    def load_text(self, path: Union[str, Path]) -> Document:
        """Load plain text file."""
        path = Path(path)
        
        try:
            content = path.read_text(encoding=self.default_encoding)
        except UnicodeDecodeError:
            # Try with different encoding
            content = path.read_text(encoding="latin-1")
        
        # Try to extract title from first line
        lines = content.split("\n")
        title = lines[0].strip() if lines else None
        
        # Try to detect if it's Fed Minutes
        doc_type = "text"
        if self._is_fed_minutes(content):
            doc_type = "fed_minutes"
            title = self._extract_fed_title(content)
        
        return Document(
            content=content,
            source=str(path),
            title=title,
            doc_type=doc_type,
            metadata={"filename": path.name}
        )
    
    def load_pdf(self, path: Union[str, Path]) -> Document:
        """
        Load PDF file.
        
        Requires pypdf or pdfplumber to be installed.
        """
        path = Path(path)
        
        try:
            # Try pypdf first
            from pypdf import PdfReader
            
            reader = PdfReader(str(path))
            pages = []
            
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            
            content = "\n\n".join(pages)
            
        except ImportError:
            try:
                # Fallback to pdfplumber
                import pdfplumber
                
                with pdfplumber.open(path) as pdf:
                    pages = [page.extract_text() for page in pdf.pages]
                    content = "\n\n".join(filter(None, pages))
                    
            except ImportError:
                raise ImportError(
                    "PDF loading requires 'pypdf' or 'pdfplumber'. "
                    "Install with: pip install pypdf"
                )
        
        # Detect document type
        doc_type = "pdf"
        title = None
        
        if self._is_fed_minutes(content):
            doc_type = "fed_minutes"
            title = self._extract_fed_title(content)
        
        return Document(
            content=content,
            source=str(path),
            title=title,
            doc_type=doc_type,
            metadata={
                "filename": path.name,
                "num_pages": len(pages) if 'pages' in dir() else None
            }
        )
    
    def load_from_string(
        self,
        content: str,
        source: str = "string",
        doc_type: str = "text"
    ) -> Document:
        """Create document from string content."""
        return Document(
            content=content,
            source=source,
            doc_type=doc_type
        )
    
    def _is_fed_minutes(self, content: str) -> bool:
        """Detect if content is Fed Minutes."""
        fed_indicators = [
            "federal open market committee",
            "fomc",
            "federal reserve",
            "monetary policy",
            "committee decided",
            "target range for the federal funds rate",
        ]
        
        content_lower = content.lower()
        matches = sum(1 for indicator in fed_indicators if indicator in content_lower)
        
        return matches >= 3
    
    def _extract_fed_title(self, content: str) -> Optional[str]:
        """Extract title from Fed Minutes."""
        # Look for date patterns
        date_pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}[-–]\d{1,2},?\s+\d{4}"
        
        match = re.search(date_pattern, content)
        if match:
            return f"FOMC Minutes - {match.group()}"
        
        return "FOMC Minutes"


# Convenience functions

def load_text_file(path: Union[str, Path]) -> Document:
    """Load a text file."""
    loader = DocumentLoader()
    return loader.load_text(path)


def load_pdf_file(path: Union[str, Path]) -> Document:
    """Load a PDF file."""
    loader = DocumentLoader()
    return loader.load_pdf(path)


def load_fed_minutes(path: Union[str, Path]) -> Document:
    """
    Load Fed Minutes with specialized parsing.
    
    Handles both PDF and TXT formats.
    """
    loader = DocumentLoader()
    doc = loader.load(path)
    
    # Ensure it's marked as Fed Minutes
    doc.doc_type = "fed_minutes"
    
    # Extract date if possible
    doc.date = _extract_fed_date(doc.content)
    
    return doc


def _extract_fed_date(content: str) -> Optional[datetime]:
    """Extract meeting date from Fed Minutes content."""
    # Pattern: "January 30-31, 2024" or "March 19-20, 2024"
    pattern = r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})[-–](\d{1,2}),?\s+(\d{4})"
    
    match = re.search(pattern, content)
    if match:
        month_str, day1, day2, year = match.groups()
        
        months = {
            "January": 1, "February": 2, "March": 3, "April": 4,
            "May": 5, "June": 6, "July": 7, "August": 8,
            "September": 9, "October": 10, "November": 11, "December": 12
        }
        
        try:
            return datetime(int(year), months[month_str], int(day2))
        except (ValueError, KeyError):
            pass
    
    return None
