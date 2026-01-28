# src/portfolio_tool/rag/chunker.py
"""
Section-Aware Document Chunking for RAG Pipeline.

Phase: 6.7 - RAG Integration (Phase 1: Document Ingestion)

PURPOSE:
Split documents into chunks suitable for vector embedding:
- Respects section boundaries (doesn't split mid-section)
- Maintains overlap for context continuity
- Tracks page numbers and section titles for citations
- Optimized for financial documents (earnings, 10-K, Fed minutes)

DESIGN PRINCIPLES:
- Section-aware: Prefers splitting at headers/sections, not arbitrary positions
- Configurable: Chunk size and overlap from config.py
- Metadata-rich: Each chunk knows its source location
- Token-based: Sizes in tokens, not characters (more accurate for LLMs)

KEY INSIGHT:
Financial documents have structure (Risk Factors, Revenue, Guidance).
Chunking should preserve that structure, not blindly split every N chars.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple
import logging

from .schemas import Document, Chunk
from .document_loader import count_tokens

logger = logging.getLogger(__name__)


# =============================================================================
# SECTION DETECTION PATTERNS
# =============================================================================

# Common section headers in financial documents
SECTION_PATTERNS = [
    # 10-K / 10-Q patterns
    r'^(?:ITEM\s+\d+[A-Z]?\.?\s*)(.+)$',                    # ITEM 1A. Risk Factors
    r'^(?:PART\s+[IVX]+\.?\s*)(.+)?$',                       # PART I, PART II
    
    # Earnings report patterns
    r'^(?:Q[1-4]\s+\d{4}\s+)(.+)$',                         # Q3 2024 Results
    r'^(?:Financial\s+Highlights)$',
    r'^(?:Business\s+Outlook)$',
    r'^(?:Revenue\s+(?:by\s+)?(?:Segment|Region))$',
    
    # Fed minutes patterns
    r'^(?:Developments\s+in\s+Financial\s+Markets).*$',
    r'^(?:Staff\s+Review\s+of\s+.+)$',
    r'^(?:Participants.\s+Views\s+on\s+.+)$',
    r'^(?:Committee\s+Policy\s+Action)$',
    
    # Generic section headers (ALL CAPS or Title Case with colon)
    r'^([A-Z][A-Z\s]{5,50})$',                              # ALL CAPS HEADERS
    r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):?\s*$',            # Title Case Headers
    
    # Numbered sections
    r'^(\d+\.\s+[A-Z].{5,50})$',                           # 1. Introduction
    r'^(\d+\.\d+\s+.{5,50})$',                             # 1.1 Subsection
]

# Compile patterns for efficiency
COMPILED_PATTERNS = [re.compile(p, re.MULTILINE | re.IGNORECASE) for p in SECTION_PATTERNS]


def detect_sections(content: str) -> List[Tuple[int, str]]:
    """
    Detect section headers in content.
    
    Args:
        content: Document text
    
    Returns:
        List of (char_position, section_title) tuples, sorted by position
    """
    sections = []
    
    for pattern in COMPILED_PATTERNS:
        for match in pattern.finditer(content):
            # Get the matched text (full match or first group)
            title = match.group(1) if match.lastindex else match.group(0)
            title = title.strip()
            
            # Filter out very short or very long "headers"
            if 3 <= len(title) <= 100:
                sections.append((match.start(), title))
    
    # Sort by position and remove duplicates at same position
    sections = sorted(set(sections), key=lambda x: x[0])
    
    return sections


def extract_page_number(text: str) -> Optional[int]:
    """
    Extract page number from text chunk if present.
    
    Looks for [Page N] markers inserted by PDF loader.
    """
    match = re.search(r'\[Page\s+(\d+)\]', text)
    if match:
        return int(match.group(1))
    return None


# =============================================================================
# CHUNKER CLASS
# =============================================================================

@dataclass
class ChunkerConfig:
    """Configuration for chunking behavior."""
    chunk_size: int = 1000          # Target tokens per chunk
    chunk_overlap: int = 100        # Overlap tokens between chunks
    min_chunk_size: int = 50        # Minimum chunk size (don't create tiny chunks)
    respect_sections: bool = True   # Try to split at section boundaries
    include_section_title: bool = True  # Prepend section title to chunk


class Chunker:
    """
    Section-aware document chunker.
    
    Usage:
        chunker = Chunker(chunk_size=1000, chunk_overlap=100)
        chunks = chunker.chunk_document(document)
    
    Strategy:
    1. Detect section headers in document
    2. Split into sections
    3. If section > chunk_size, split further with overlap
    4. If section < min_chunk_size, merge with adjacent
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        min_chunk_size: int = 50,
        respect_sections: bool = True,
    ):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target tokens per chunk
            chunk_overlap: Overlap tokens between chunks
            min_chunk_size: Minimum chunk size
            respect_sections: Whether to respect section boundaries
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.respect_sections = respect_sections
    
    def chunk_document(self, document: Document) -> List[Chunk]:
        """
        Split document into chunks.
        
        Args:
            document: Document to chunk
        
        Returns:
            List of Chunk objects with metadata
        """
        if not document.content or document.content.strip() == "":
            logger.warning(f"Empty document: {document.filename}")
            return []
        
        content = document.content
        
        # Step 1: Detect sections
        if self.respect_sections:
            sections = detect_sections(content)
            chunks = self._chunk_with_sections(content, sections, document)
        else:
            chunks = self._chunk_simple(content, document)
        
        # Step 2: Merge tiny chunks
        chunks = self._merge_small_chunks(chunks)
        
        # Step 3: Assign indices and add document metadata
        for i, chunk in enumerate(chunks):
            chunk.index = i
            chunk.metadata.update({
                "filename": document.filename,
                "doc_type": document.doc_type.value,
                "ticker": document.ticker,
                "document_date": document.document_date.isoformat() if document.document_date else None,
                "source": document.source.value,
            })
        
        # Update document with chunks
        document.chunks = chunks
        document.sections = [s[1] for s in detect_sections(content)]
        
        logger.info(f"Chunked {document.filename}: {len(chunks)} chunks from {document.total_tokens} tokens")
        
        return chunks
    
    def _chunk_with_sections(
        self,
        content: str,
        sections: List[Tuple[int, str]],
        document: Document,
    ) -> List[Chunk]:
        """
        Chunk content respecting section boundaries.
        
        Strategy:
        - Each section becomes one or more chunks
        - Large sections are split with overlap
        - Section title is preserved in metadata
        """
        chunks = []
        
        # Add end position for last section
        section_ranges = []
        for i, (pos, title) in enumerate(sections):
            end_pos = sections[i + 1][0] if i + 1 < len(sections) else len(content)
            section_ranges.append((pos, end_pos, title))
        
        # If no sections detected, treat entire content as one section
        if not section_ranges:
            section_ranges = [(0, len(content), None)]
        
        for start_pos, end_pos, section_title in section_ranges:
            section_text = content[start_pos:end_pos].strip()
            
            if not section_text:
                continue
            
            section_tokens = count_tokens(section_text)
            
            if section_tokens <= self.chunk_size:
                # Section fits in one chunk
                chunk = Chunk(
                    content=section_text,
                    index=0,  # Will be reassigned
                    token_count=section_tokens,
                    metadata={},
                    section_title=section_title,
                    page_number=extract_page_number(section_text),
                    start_char=start_pos,
                    end_char=end_pos,
                )
                chunks.append(chunk)
            else:
                # Section too large, split with overlap
                sub_chunks = self._split_large_section(
                    section_text,
                    section_title,
                    start_pos,
                )
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _split_large_section(
        self,
        text: str,
        section_title: Optional[str],
        start_char: int,
    ) -> List[Chunk]:
        """
        Split a large section into chunks with overlap.
        
        Uses paragraph boundaries where possible.
        """
        chunks = []
        
        # Split into paragraphs first
        paragraphs = re.split(r'\n\n+', text)
        
        current_chunk_text = ""
        current_chunk_start = start_char
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_tokens = count_tokens(para)
            current_tokens = count_tokens(current_chunk_text)
            
            if current_tokens + para_tokens <= self.chunk_size:
                # Add paragraph to current chunk
                if current_chunk_text:
                    current_chunk_text += "\n\n" + para
                else:
                    current_chunk_text = para
            else:
                # Save current chunk and start new one
                if current_chunk_text:
                    chunk = Chunk(
                        content=current_chunk_text,
                        index=0,
                        token_count=count_tokens(current_chunk_text),
                        metadata={},
                        section_title=section_title,
                        page_number=extract_page_number(current_chunk_text),
                        start_char=current_chunk_start,
                        end_char=current_chunk_start + len(current_chunk_text),
                    )
                    chunks.append(chunk)
                    
                    # Start new chunk with overlap
                    overlap_text = self._get_overlap_text(current_chunk_text)
                    current_chunk_text = overlap_text + "\n\n" + para if overlap_text else para
                    current_chunk_start = start_char + len(text) - len(current_chunk_text)
                else:
                    # Paragraph itself is too large, force split
                    sub_chunks = self._force_split(para, section_title, start_char)
                    chunks.extend(sub_chunks)
                    current_chunk_text = ""
        
        # Don't forget last chunk
        if current_chunk_text:
            chunk = Chunk(
                content=current_chunk_text,
                index=0,
                token_count=count_tokens(current_chunk_text),
                metadata={},
                section_title=section_title,
                page_number=extract_page_number(current_chunk_text),
                start_char=current_chunk_start,
                end_char=current_chunk_start + len(current_chunk_text),
            )
            chunks.append(chunk)
        
        return chunks
    
    def _force_split(
        self,
        text: str,
        section_title: Optional[str],
        start_char: int,
    ) -> List[Chunk]:
        """
        Force split text that's too large for a single chunk.
        
        Splits at sentence boundaries where possible.
        """
        chunks = []
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk_text = ""
        current_chunk_start = start_char
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sent_tokens = count_tokens(sentence)
            current_tokens = count_tokens(current_chunk_text)
            
            if current_tokens + sent_tokens <= self.chunk_size:
                current_chunk_text += " " + sentence if current_chunk_text else sentence
            else:
                if current_chunk_text:
                    chunk = Chunk(
                        content=current_chunk_text,
                        index=0,
                        token_count=count_tokens(current_chunk_text),
                        metadata={},
                        section_title=section_title,
                        page_number=extract_page_number(current_chunk_text),
                        start_char=current_chunk_start,
                        end_char=current_chunk_start + len(current_chunk_text),
                    )
                    chunks.append(chunk)
                    
                    overlap_text = self._get_overlap_text(current_chunk_text)
                    current_chunk_text = overlap_text + " " + sentence if overlap_text else sentence
                    current_chunk_start = start_char + len(text) - len(current_chunk_text)
                else:
                    # Single sentence too large - just truncate
                    current_chunk_text = sentence[:self.chunk_size * 4]  # ~4 chars per token
        
        if current_chunk_text:
            chunk = Chunk(
                content=current_chunk_text,
                index=0,
                token_count=count_tokens(current_chunk_text),
                metadata={},
                section_title=section_title,
                page_number=extract_page_number(current_chunk_text),
                start_char=current_chunk_start,
                end_char=current_chunk_start + len(current_chunk_text),
            )
            chunks.append(chunk)
        
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Get the last N tokens of text for overlap."""
        if self.chunk_overlap <= 0:
            return ""
        
        # Approximate: get last chunk_overlap * 4 characters
        approx_chars = self.chunk_overlap * 4
        if len(text) <= approx_chars:
            return text
        
        # Try to break at sentence boundary
        overlap_region = text[-approx_chars:]
        sentence_break = overlap_region.find('. ')
        
        if sentence_break > 0:
            return overlap_region[sentence_break + 2:]
        
        return overlap_region
    
    def _chunk_simple(self, content: str, document: Document) -> List[Chunk]:
        """
        Simple chunking without section awareness.
        
        Used when respect_sections=False or as fallback.
        """
        chunks = []
        
        # Split into paragraphs
        paragraphs = re.split(r'\n\n+', content)
        
        current_chunk_text = ""
        current_chunk_start = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_tokens = count_tokens(para)
            current_tokens = count_tokens(current_chunk_text)
            
            if current_tokens + para_tokens <= self.chunk_size:
                if current_chunk_text:
                    current_chunk_text += "\n\n" + para
                else:
                    current_chunk_text = para
            else:
                if current_chunk_text:
                    chunk = Chunk(
                        content=current_chunk_text,
                        index=len(chunks),
                        token_count=count_tokens(current_chunk_text),
                        metadata={},
                        page_number=extract_page_number(current_chunk_text),
                        start_char=current_chunk_start,
                        end_char=current_chunk_start + len(current_chunk_text),
                    )
                    chunks.append(chunk)
                    
                    overlap_text = self._get_overlap_text(current_chunk_text)
                    current_chunk_start += len(current_chunk_text) - len(overlap_text)
                    current_chunk_text = overlap_text + "\n\n" + para if overlap_text else para
                else:
                    current_chunk_text = para
        
        if current_chunk_text:
            chunk = Chunk(
                content=current_chunk_text,
                index=len(chunks),
                token_count=count_tokens(current_chunk_text),
                metadata={},
                page_number=extract_page_number(current_chunk_text),
                start_char=current_chunk_start,
                end_char=current_chunk_start + len(current_chunk_text),
            )
            chunks.append(chunk)
        
        return chunks
    
    def _merge_small_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Merge chunks that are too small.
        
        Preserves section boundaries where possible.
        """
        if not chunks:
            return chunks
        
        merged = []
        current = chunks[0]
        
        for next_chunk in chunks[1:]:
            combined_tokens = current.token_count + next_chunk.token_count
            
            # Merge if combined size is reasonable and same section
            same_section = current.section_title == next_chunk.section_title
            small_enough = combined_tokens <= self.chunk_size
            current_too_small = current.token_count < self.min_chunk_size
            
            if current_too_small and small_enough:
                # Merge chunks
                current = Chunk(
                    content=current.content + "\n\n" + next_chunk.content,
                    index=current.index,
                    token_count=combined_tokens,
                    metadata=current.metadata,
                    section_title=current.section_title or next_chunk.section_title,
                    page_number=current.page_number or next_chunk.page_number,
                    start_char=current.start_char,
                    end_char=next_chunk.end_char,
                )
            else:
                merged.append(current)
                current = next_chunk
        
        merged.append(current)
        
        return merged


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def chunk_document(
    document: Document,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
) -> List[Chunk]:
    """
    Convenience function to chunk a document.
    
    Usage:
        chunks = chunk_document(doc, chunk_size=1000)
    """
    chunker = Chunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.chunk_document(document)
