"""
Text Chunking for RAG Pipeline.

Splits documents into smaller chunks for embedding and retrieval.

Chunking strategies:
- By paragraphs (best for structured documents)
- By sentences (best for dense text)
- By tokens (best for LLM context management)
- By sections (best for Fed Minutes with clear structure)

Fed Minutes have a specific structure:
- Developments in Financial Markets
- Staff Review of the Economic Situation
- Staff Review of the Financial Situation
- Staff Economic Outlook
- Participants' Views on Current Conditions
- Committee Policy Action

We optimize chunking for this structure.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import re

from .document_loader import Document


@dataclass
class Chunk:
    """
    A chunk of text from a document.
    
    Contains the text plus metadata about its position
    and the source document.
    """
    
    text: str
    chunk_id: int
    
    # Position info
    start_char: int = 0
    end_char: int = 0
    
    # Source info
    source: str = ""
    doc_type: str = ""
    
    # Section info (for structured documents)
    section: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def char_count(self) -> int:
        return len(self.text)
    
    @property
    def word_count(self) -> int:
        return len(self.text.split())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text[:200] + "..." if len(self.text) > 200 else self.text,
            "char_count": self.char_count,
            "word_count": self.word_count,
            "section": self.section,
            "source": self.source,
        }


class TextChunker:
    """
    Configurable text chunker.
    
    Example:
        chunker = TextChunker(chunk_size=1000, overlap=200)
        chunks = chunker.chunk(document)
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
        min_chunk_size: int = 100,
        respect_sections: bool = True
    ):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target chunk size in characters
            overlap: Overlap between consecutive chunks
            min_chunk_size: Minimum chunk size (smaller chunks merged)
            respect_sections: Keep section boundaries (for structured docs)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        self.respect_sections = respect_sections
    
    def chunk(self, document: Document) -> List[Chunk]:
        """
        Chunk a document.
        
        Uses appropriate strategy based on document type.
        """
        if document.doc_type == "fed_minutes" and self.respect_sections:
            return self._chunk_fed_minutes(document)
        else:
            return self._chunk_by_size(document)
    
    def _chunk_by_size(self, document: Document) -> List[Chunk]:
        """Chunk by target size with overlap."""
        text = document.content
        chunks = []
        
        # Split into paragraphs first
        paragraphs = self._split_paragraphs(text)
        
        current_chunk = ""
        current_start = 0
        chunk_id = 0
        
        for para in paragraphs:
            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(Chunk(
                    text=current_chunk.strip(),
                    chunk_id=chunk_id,
                    start_char=current_start,
                    end_char=current_start + len(current_chunk),
                    source=document.source,
                    doc_type=document.doc_type,
                ))
                chunk_id += 1
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap(current_chunk)
                current_chunk = overlap_text + para
                current_start = current_start + len(current_chunk) - len(overlap_text) - len(para)
            else:
                current_chunk += para + "\n\n"
        
        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(Chunk(
                text=current_chunk.strip(),
                chunk_id=chunk_id,
                start_char=current_start,
                end_char=current_start + len(current_chunk),
                source=document.source,
                doc_type=document.doc_type,
            ))
        
        # Merge small chunks
        chunks = self._merge_small_chunks(chunks)
        
        return chunks
    
    def _chunk_fed_minutes(self, document: Document) -> List[Chunk]:
        """
        Chunk Fed Minutes respecting section structure.
        
        Fed Minutes sections:
        - Developments in Financial Markets and Open Market Operations
        - Staff Review of the Economic Situation
        - Staff Review of the Financial Situation
        - Staff Economic Outlook
        - Participants' Views on Current Conditions and the Economic Outlook
        - Committee Policy Action
        """
        text = document.content
        chunks = []
        chunk_id = 0
        
        # Section patterns
        section_patterns = [
            (r"Developments in Financial Markets", "financial_markets"),
            (r"Staff Review of the Economic Situation", "economic_review"),
            (r"Staff Review of the Financial Situation", "financial_review"),
            (r"Staff Economic Outlook", "economic_outlook"),
            (r"Participants['']?\s*Views", "participants_views"),
            (r"Committee Policy Action", "policy_action"),
            (r"Voting for this action", "voting"),
        ]
        
        # Find section boundaries
        sections = []
        for pattern, section_name in section_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                sections.append((match.start(), section_name))
        
        # Sort by position
        sections.sort(key=lambda x: x[0])
        
        if not sections:
            # No sections found, use regular chunking
            return self._chunk_by_size(document)
        
        # Extract text for each section
        for i, (start, section_name) in enumerate(sections):
            # End is start of next section or end of document
            end = sections[i + 1][0] if i + 1 < len(sections) else len(text)
            
            section_text = text[start:end].strip()
            
            # If section is too long, sub-chunk it
            if len(section_text) > self.chunk_size * 2:
                # Create sub-chunks within section
                sub_chunks = self._chunk_text(section_text, section_name, document.source)
                for sub in sub_chunks:
                    sub.chunk_id = chunk_id
                    sub.section = section_name
                    chunks.append(sub)
                    chunk_id += 1
            else:
                chunks.append(Chunk(
                    text=section_text,
                    chunk_id=chunk_id,
                    start_char=start,
                    end_char=end,
                    source=document.source,
                    doc_type=document.doc_type,
                    section=section_name,
                ))
                chunk_id += 1
        
        return chunks
    
    def _chunk_text(
        self, 
        text: str, 
        section: str, 
        source: str
    ) -> List[Chunk]:
        """Chunk a piece of text into smaller pieces."""
        chunks = []
        paragraphs = self._split_paragraphs(text)
        
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                chunks.append(Chunk(
                    text=current_chunk.strip(),
                    chunk_id=0,  # Will be set later
                    source=source,
                    section=section,
                ))
                current_chunk = para
            else:
                current_chunk += para + "\n\n"
        
        if current_chunk.strip():
            chunks.append(Chunk(
                text=current_chunk.strip(),
                chunk_id=0,
                source=source,
                section=section,
            ))
        
        return chunks
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split on double newlines or multiple newlines
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _get_overlap(self, text: str) -> str:
        """Get overlap text from end of chunk."""
        if len(text) <= self.overlap:
            return text
        
        # Try to break at sentence boundary
        overlap_region = text[-self.overlap * 2:]
        sentences = re.split(r'(?<=[.!?])\s+', overlap_region)
        
        if len(sentences) > 1:
            # Return last complete sentence(s) that fit in overlap
            result = ""
            for sent in reversed(sentences):
                if len(result) + len(sent) <= self.overlap:
                    result = sent + " " + result
                else:
                    break
            return result.strip()
        
        return text[-self.overlap:]
    
    def _merge_small_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Merge chunks that are too small."""
        if not chunks:
            return chunks
        
        merged = []
        current = chunks[0]
        
        for chunk in chunks[1:]:
            if current.char_count < self.min_chunk_size:
                # Merge with next chunk
                current = Chunk(
                    text=current.text + "\n\n" + chunk.text,
                    chunk_id=current.chunk_id,
                    start_char=current.start_char,
                    end_char=chunk.end_char,
                    source=current.source,
                    doc_type=current.doc_type,
                    section=current.section or chunk.section,
                )
            else:
                merged.append(current)
                current = chunk
        
        merged.append(current)
        
        # Re-number chunk IDs
        for i, chunk in enumerate(merged):
            chunk.chunk_id = i
        
        return merged


# Convenience functions

def chunk_by_paragraphs(
    document: Document,
    max_paragraphs: int = 3
) -> List[Chunk]:
    """Chunk by grouping paragraphs."""
    text = document.content
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    chunks = []
    for i in range(0, len(paragraphs), max_paragraphs):
        group = paragraphs[i:i + max_paragraphs]
        chunks.append(Chunk(
            text="\n\n".join(group),
            chunk_id=len(chunks),
            source=document.source,
            doc_type=document.doc_type,
        ))
    
    return chunks


def chunk_by_sentences(
    document: Document,
    sentences_per_chunk: int = 5
) -> List[Chunk]:
    """Chunk by grouping sentences."""
    text = document.content
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    for i in range(0, len(sentences), sentences_per_chunk):
        group = sentences[i:i + sentences_per_chunk]
        chunks.append(Chunk(
            text=" ".join(group),
            chunk_id=len(chunks),
            source=document.source,
            doc_type=document.doc_type,
        ))
    
    return chunks


def chunk_by_tokens(
    document: Document,
    max_tokens: int = 500,
    overlap_tokens: int = 50
) -> List[Chunk]:
    """
    Chunk by approximate token count.
    
    Assumes ~4 characters per token (rough approximation).
    """
    chars_per_token = 4
    chunker = TextChunker(
        chunk_size=max_tokens * chars_per_token,
        overlap=overlap_tokens * chars_per_token
    )
    return chunker.chunk(document)
