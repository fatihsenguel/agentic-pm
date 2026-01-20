"""
Fed Minutes Scraper for Quant Portfolio Manager.

Automatically downloads Fed Minutes (FOMC meeting minutes) from the Federal Reserve website.
Primary source: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm

Design Principles:
- Robust: Handles network errors, missing files gracefully
- Cacheable: Stores downloaded PDFs locally to avoid redundant downloads
- Auditable: Returns metadata about downloads (date, source, status)
- Integration: Works with RAG pipeline (DocumentLoader)

Usage:
    scraper = FedMinutesScraper(cache_dir="./fed_minutes_cache")
    
    # Get latest minutes
    doc = scraper.get_latest_minutes()
    
    # Get specific minutes
    doc = scraper.get_minutes_by_date(2024, 1)  # January 2024 FOMC
    
    # List all available
    available = scraper.list_available_minutes()
"""

import os
import re
import logging
from pathlib import Path
from datetime import datetime, date
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class DownloadStatus(str, Enum):
    """Status of a download operation."""
    SUCCESS = "success"
    CACHED = "cached"
    NOT_FOUND = "not_found"
    NETWORK_ERROR = "network_error"
    PARSE_ERROR = "parse_error"


@dataclass
class FedMinutesMetadata:
    """Metadata for a Fed Minutes document."""
    meeting_date: date
    release_date: Optional[date] = None
    pdf_url: Optional[str] = None
    html_url: Optional[str] = None
    title: str = ""
    year: int = 0
    
    def __post_init__(self):
        if self.year == 0:
            self.year = self.meeting_date.year


@dataclass
class FedMinutesDocument:
    """A downloaded Fed Minutes document."""
    metadata: FedMinutesMetadata
    content: str  # Extracted text content
    source_path: str  # Local file path or URL
    download_status: DownloadStatus
    content_type: str = "text"  # "text" or "pdf"
    error_message: Optional[str] = None
    download_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "meeting_date": self.metadata.meeting_date.isoformat(),
            "release_date": self.metadata.release_date.isoformat() if self.metadata.release_date else None,
            "title": self.metadata.title,
            "year": self.metadata.year,
            "source_path": self.source_path,
            "download_status": self.download_status.value,
            "content_type": self.content_type,
            "content_length": len(self.content),
            "download_timestamp": self.download_timestamp.isoformat(),
            "error_message": self.error_message
        }


@dataclass
class ScraperConfig:
    """Configuration for Fed Minutes Scraper."""
    cache_dir: str = "./fed_minutes_cache"
    base_url: str = "https://www.federalreserve.gov"
    calendar_url: str = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
    historical_url_template: str = "https://www.federalreserve.gov/monetarypolicy/fomchistorical{year}.htm"
    request_timeout: int = 30
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    prefer_html: bool = True  # Prefer HTML over PDF for easier text extraction
    max_retries: int = 3


class FedMinutesScraper:
    """
    Scraper for Federal Reserve FOMC Meeting Minutes.
    
    Downloads minutes from the Fed website, caches them locally,
    and extracts text content for RAG pipeline integration.
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self.cache_dir = Path(self.config.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": self.config.user_agent
        })
        
        # Cache for available minutes metadata
        self._available_minutes_cache: Optional[List[FedMinutesMetadata]] = None
        self._cache_timestamp: Optional[datetime] = None
    
    # ==================== PUBLIC API ====================
    
    def get_latest_minutes(self) -> FedMinutesDocument:
        """
        Download and return the most recent Fed Minutes.
        
        Returns:
            FedMinutesDocument with content and metadata
        """
        available = self.list_available_minutes()
        
        if not available:
            return FedMinutesDocument(
                metadata=FedMinutesMetadata(meeting_date=date.today()),
                content="",
                source_path="",
                download_status=DownloadStatus.NOT_FOUND,
                error_message="No Fed Minutes found on website"
            )
        
        # Get most recent by meeting date
        latest = max(available, key=lambda x: x.meeting_date)
        return self._download_minutes(latest)
    
    def get_minutes_by_date(self, year: int, month: int) -> FedMinutesDocument:
        """
        Download Fed Minutes for a specific meeting date.
        
        Args:
            year: Meeting year (e.g., 2024)
            month: Meeting month (1-12)
            
        Returns:
            FedMinutesDocument with content and metadata
        """
        available = self.list_available_minutes(year=year)
        
        # Find closest match by month
        matches = [m for m in available if m.meeting_date.month == month]
        
        if not matches:
            # Try to find any meeting in adjacent months
            matches = [m for m in available if abs(m.meeting_date.month - month) <= 1]
        
        if not matches:
            return FedMinutesDocument(
                metadata=FedMinutesMetadata(meeting_date=date(year, month, 1)),
                content="",
                source_path="",
                download_status=DownloadStatus.NOT_FOUND,
                error_message=f"No Fed Minutes found for {year}-{month:02d}"
            )
        
        # Get the one closest to requested month
        target = min(matches, key=lambda x: abs(x.meeting_date.month - month))
        return self._download_minutes(target)
    
    def list_available_minutes(self, year: Optional[int] = None, force_refresh: bool = False) -> List[FedMinutesMetadata]:
        """
        List all available Fed Minutes.
        
        Args:
            year: Filter by year (optional)
            force_refresh: Force re-fetch from website
            
        Returns:
            List of FedMinutesMetadata
        """
        # Check cache (valid for 1 hour)
        if (not force_refresh 
            and self._available_minutes_cache 
            and self._cache_timestamp
            and (datetime.utcnow() - self._cache_timestamp).seconds < 3600):
            
            if year:
                return [m for m in self._available_minutes_cache if m.year == year]
            return self._available_minutes_cache
        
        # Fetch from website
        all_minutes = []
        
        # Current year calendar
        current_minutes = self._parse_calendar_page(self.config.calendar_url)
        all_minutes.extend(current_minutes)
        
        # Historical years (if needed)
        if year and year < datetime.now().year:
            historical = self._parse_historical_page(year)
            all_minutes.extend(historical)
        
        # Update cache
        self._available_minutes_cache = all_minutes
        self._cache_timestamp = datetime.utcnow()
        
        if year:
            return [m for m in all_minutes if m.year == year]
        return all_minutes
    
    def download_to_file(self, metadata: FedMinutesMetadata, output_path: Optional[str] = None) -> str:
        """
        Download minutes to a specific file path.
        
        Args:
            metadata: FedMinutesMetadata from list_available_minutes()
            output_path: Target file path (optional, uses cache_dir if not specified)
            
        Returns:
            Path to downloaded file
        """
        if output_path is None:
            filename = f"fed_minutes_{metadata.meeting_date.isoformat()}"
            if metadata.html_url:
                output_path = str(self.cache_dir / f"{filename}.html")
            else:
                output_path = str(self.cache_dir / f"{filename}.pdf")
        
        doc = self._download_minutes(metadata)
        
        if doc.download_status in [DownloadStatus.SUCCESS, DownloadStatus.CACHED]:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(doc.content)
        
        return output_path
    
    # ==================== INTERNAL METHODS ====================
    
    def _download_minutes(self, metadata: FedMinutesMetadata) -> FedMinutesDocument:
        """Download and extract content from Fed Minutes."""
        
        # Check local cache first
        cache_path = self._get_cache_path(metadata)
        if cache_path.exists():
            logger.info(f"Loading cached minutes: {cache_path}")
            content = cache_path.read_text(encoding='utf-8')
            return FedMinutesDocument(
                metadata=metadata,
                content=content,
                source_path=str(cache_path),
                download_status=DownloadStatus.CACHED,
                content_type="text"
            )
        
        # Prefer HTML for easier text extraction
        if self.config.prefer_html and metadata.html_url:
            return self._download_html_minutes(metadata)
        elif metadata.pdf_url:
            return self._download_pdf_minutes(metadata)
        elif metadata.html_url:
            return self._download_html_minutes(metadata)
        else:
            return FedMinutesDocument(
                metadata=metadata,
                content="",
                source_path="",
                download_status=DownloadStatus.NOT_FOUND,
                error_message="No download URL available"
            )
    
    def _download_html_minutes(self, metadata: FedMinutesMetadata) -> FedMinutesDocument:
        """Download and parse HTML version of minutes."""
        try:
            url = metadata.html_url
            if not url.startswith('http'):
                url = f"{self.config.base_url}{url}"
            
            logger.info(f"Downloading HTML minutes from: {url}")
            
            response = self._session.get(url, timeout=self.config.request_timeout)
            response.raise_for_status()
            
            # Parse HTML and extract main content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Fed minutes are typically in a div with class 'col-xs-12'
            # or in the main article content
            content_div = (
                soup.find('div', class_='col-xs-12 col-sm-8 col-md-8') or
                soup.find('article') or
                soup.find('div', id='article') or
                soup.find('div', class_='content')
            )
            
            if content_div:
                # Remove script and style elements
                for script in content_div(["script", "style", "nav", "header", "footer"]):
                    script.decompose()
                
                text = content_div.get_text(separator='\n', strip=True)
            else:
                # Fallback: get all text from body
                text = soup.body.get_text(separator='\n', strip=True) if soup.body else ""
            
            # Clean up text
            text = self._clean_text(text)
            
            # Cache the result
            cache_path = self._get_cache_path(metadata)
            cache_path.write_text(text, encoding='utf-8')
            
            return FedMinutesDocument(
                metadata=metadata,
                content=text,
                source_path=str(cache_path),
                download_status=DownloadStatus.SUCCESS,
                content_type="text"
            )
            
        except requests.RequestException as e:
            logger.error(f"Network error downloading minutes: {e}")
            return FedMinutesDocument(
                metadata=metadata,
                content="",
                source_path="",
                download_status=DownloadStatus.NETWORK_ERROR,
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Error parsing minutes: {e}")
            return FedMinutesDocument(
                metadata=metadata,
                content="",
                source_path="",
                download_status=DownloadStatus.PARSE_ERROR,
                error_message=str(e)
            )
    
    def _download_pdf_minutes(self, metadata: FedMinutesMetadata) -> FedMinutesDocument:
        """Download PDF version and extract text."""
        try:
            url = metadata.pdf_url
            if not url.startswith('http'):
                url = f"{self.config.base_url}{url}"
            
            logger.info(f"Downloading PDF minutes from: {url}")
            
            response = self._session.get(url, timeout=self.config.request_timeout)
            response.raise_for_status()
            
            # Save PDF to cache
            pdf_cache_path = self.cache_dir / f"fed_minutes_{metadata.meeting_date.isoformat()}.pdf"
            pdf_cache_path.write_bytes(response.content)
            
            # Extract text from PDF
            text = self._extract_pdf_text(pdf_cache_path)
            
            # Cache extracted text
            cache_path = self._get_cache_path(metadata)
            cache_path.write_text(text, encoding='utf-8')
            
            return FedMinutesDocument(
                metadata=metadata,
                content=text,
                source_path=str(cache_path),
                download_status=DownloadStatus.SUCCESS,
                content_type="text"
            )
            
        except requests.RequestException as e:
            logger.error(f"Network error downloading PDF: {e}")
            return FedMinutesDocument(
                metadata=metadata,
                content="",
                source_path="",
                download_status=DownloadStatus.NETWORK_ERROR,
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return FedMinutesDocument(
                metadata=metadata,
                content="",
                source_path="",
                download_status=DownloadStatus.PARSE_ERROR,
                error_message=str(e)
            )
    
    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF using available libraries."""
        text = ""
        
        # Try PyMuPDF (fitz) first - best quality
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
            return self._clean_text(text)
        except ImportError:
            pass
        
        # Try pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return self._clean_text(text)
        except ImportError:
            pass
        
        # Try PyPDF2
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                text += page.extract_text() or ""
            return self._clean_text(text)
        except ImportError:
            pass
        
        raise ImportError(
            "No PDF extraction library available. "
            "Install one of: PyMuPDF (fitz), pdfplumber, or PyPDF2"
        )
    
    def _parse_calendar_page(self, url: str) -> List[FedMinutesMetadata]:
        """Parse the FOMC calendar page for minutes links."""
        minutes_list = []
        
        try:
            response = self._session.get(url, timeout=self.config.request_timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all panels (each meeting is in a panel)
            panels = soup.find_all('div', class_='panel')
            
            for panel in panels:
                # Look for minutes links
                minutes_link = panel.find('a', string=re.compile(r'Minutes', re.IGNORECASE))
                if not minutes_link:
                    # Also check for "HTML" or "PDF" links in minutes section
                    minutes_link = panel.find('a', href=re.compile(r'fomcminutes'))
                
                if minutes_link:
                    href = minutes_link.get('href', '')
                    
                    # Extract date from link or panel heading
                    meeting_date = self._extract_date_from_panel(panel)
                    
                    if meeting_date:
                        metadata = FedMinutesMetadata(
                            meeting_date=meeting_date,
                            title=f"FOMC Minutes {meeting_date.strftime('%B %Y')}",
                            year=meeting_date.year
                        )
                        
                        # Determine if HTML or PDF
                        if 'htm' in href.lower():
                            metadata.html_url = href
                        else:
                            metadata.pdf_url = href
                        
                        # Check for both HTML and PDF versions
                        html_link = panel.find('a', href=re.compile(r'fomcminutes.*\.htm'))
                        pdf_link = panel.find('a', href=re.compile(r'fomcminutes.*\.pdf'))
                        
                        if html_link:
                            metadata.html_url = html_link.get('href')
                        if pdf_link:
                            metadata.pdf_url = pdf_link.get('href')
                        
                        minutes_list.append(metadata)
            
            logger.info(f"Found {len(minutes_list)} minutes on calendar page")
            
        except Exception as e:
            logger.error(f"Error parsing calendar page: {e}")
        
        return minutes_list
    
    def _parse_historical_page(self, year: int) -> List[FedMinutesMetadata]:
        """Parse historical FOMC page for a specific year."""
        minutes_list = []
        
        try:
            url = self.config.historical_url_template.format(year=year)
            response = self._session.get(url, timeout=self.config.request_timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all minutes links
            for link in soup.find_all('a', href=re.compile(r'fomcminutes')):
                href = link.get('href', '')
                
                # Extract date from URL
                date_match = re.search(r'fomcminutes(\d{8})', href)
                if date_match:
                    date_str = date_match.group(1)
                    meeting_date = datetime.strptime(date_str, '%Y%m%d').date()
                    
                    metadata = FedMinutesMetadata(
                        meeting_date=meeting_date,
                        title=f"FOMC Minutes {meeting_date.strftime('%B %Y')}",
                        year=year
                    )
                    
                    if 'htm' in href.lower():
                        metadata.html_url = href
                    else:
                        metadata.pdf_url = href
                    
                    minutes_list.append(metadata)
            
            logger.info(f"Found {len(minutes_list)} historical minutes for {year}")
            
        except Exception as e:
            logger.error(f"Error parsing historical page for {year}: {e}")
        
        return minutes_list
    
    def _extract_date_from_panel(self, panel) -> Optional[date]:
        """Extract meeting date from panel heading."""
        # Look for date in heading
        heading = panel.find(['h4', 'h5', 'strong'])
        if heading:
            text = heading.get_text()
            
            # Pattern: "January 28-29, 2025" or "December 17-18, 2024"
            match = re.search(r'(\w+)\s+(\d+)(?:-\d+)?,\s*(\d{4})', text)
            if match:
                month_name, day, year = match.groups()
                try:
                    return datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y").date()
                except ValueError:
                    pass
        
        return None
    
    def _get_cache_path(self, metadata: FedMinutesMetadata) -> Path:
        """Get cache file path for minutes."""
        return self.cache_dir / f"fed_minutes_{metadata.meeting_date.isoformat()}.txt"
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove common artifacts
        text = re.sub(r'Page \d+ of \d+', '', text)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        return text.strip()


# ==================== CONVENIENCE FUNCTIONS ====================

def get_latest_fed_minutes(cache_dir: str = "./fed_minutes_cache") -> FedMinutesDocument:
    """Convenience function to get latest Fed Minutes."""
    scraper = FedMinutesScraper(ScraperConfig(cache_dir=cache_dir))
    return scraper.get_latest_minutes()


def get_fed_minutes_by_date(year: int, month: int, cache_dir: str = "./fed_minutes_cache") -> FedMinutesDocument:
    """Convenience function to get Fed Minutes by date."""
    scraper = FedMinutesScraper(ScraperConfig(cache_dir=cache_dir))
    return scraper.get_minutes_by_date(year, month)


def list_fed_minutes(year: Optional[int] = None, cache_dir: str = "./fed_minutes_cache") -> List[Dict[str, Any]]:
    """Convenience function to list available Fed Minutes."""
    scraper = FedMinutesScraper(ScraperConfig(cache_dir=cache_dir))
    minutes = scraper.list_available_minutes(year=year)
    return [
        {
            "meeting_date": m.meeting_date.isoformat(),
            "title": m.title,
            "year": m.year,
            "has_html": bool(m.html_url),
            "has_pdf": bool(m.pdf_url)
        }
        for m in minutes
    ]


# ==================== INTEGRATION WITH RAG PIPELINE ====================
"""
Usage with existing RAG pipeline:

from portfolio_tool.rag import DocumentLoader, Document
from portfolio_tool.rag.fed_scraper import FedMinutesScraper

# Download Fed Minutes
scraper = FedMinutesScraper()
fed_doc = scraper.get_latest_minutes()

if fed_doc.download_status == DownloadStatus.SUCCESS:
    # Create Document for RAG pipeline
    rag_document = Document(
        content=fed_doc.content,
        metadata={
            "source": "federal_reserve",
            "document_type": "fed_minutes",
            "meeting_date": fed_doc.metadata.meeting_date.isoformat(),
            "title": fed_doc.metadata.title
        }
    )
    
    # Use with existing RAG pipeline
    from portfolio_tool.rag import TextChunker, EmbeddingStore
    
    chunker = TextChunker()
    chunks = chunker.chunk_by_paragraphs(rag_document)
    
    store = EmbeddingStore()
    store.add_documents(chunks)
"""
