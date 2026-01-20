"""
Embedding and Similarity Search for RAG Pipeline.

Provides:
- Text embedding (using sentence-transformers or OpenAI)
- In-memory vector storage
- Similarity search

For production, consider using:
- ChromaDB
- Pinecone
- Weaviate
- FAISS

This implementation uses a simple in-memory store for portability.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

from .chunker import Chunk


@dataclass
class EmbeddingResult:
    """Result from similarity search."""
    chunk: Chunk
    score: float  # Similarity score (higher = more similar)
    rank: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "score": f"{self.score:.4f}",
            "chunk_id": self.chunk.chunk_id,
            "section": self.chunk.section,
            "text_preview": self.chunk.text[:200] + "..." if len(self.chunk.text) > 200 else self.chunk.text,
        }


class EmbeddingStore:
    """
    Simple in-memory embedding store.
    
    Stores chunks with their embeddings for similarity search.
    
    Example:
        store = EmbeddingStore()
        store.add_chunks(chunks)
        results = store.search("inflation concerns", top_k=5)
    """
    
    def __init__(
        self,
        embedding_function: Optional[Callable[[str], List[float]]] = None,
        embedding_dim: int = 384
    ):
        """
        Initialize embedding store.
        
        Args:
            embedding_function: Function to embed text. If None, uses simple TF-IDF.
            embedding_dim: Dimension of embeddings (only used with custom function)
        """
        self.embedding_function = embedding_function or self._default_embedding
        self.embedding_dim = embedding_dim
        
        # Storage
        self.chunks: List[Chunk] = []
        self.embeddings: List[np.ndarray] = []
        
        # For TF-IDF
        self._vocabulary: Dict[str, int] = {}
        self._idf: Optional[np.ndarray] = None
    
    def add_chunks(self, chunks: List[Chunk]) -> None:
        """Add chunks to the store."""
        for chunk in chunks:
            embedding = self.embedding_function(chunk.text)
            self.chunks.append(chunk)
            self.embeddings.append(np.array(embedding))
        
        # Rebuild IDF for TF-IDF
        if self.embedding_function == self._default_embedding:
            self._build_idf()
    
    def add_chunk(self, chunk: Chunk) -> None:
        """Add a single chunk."""
        self.add_chunks([chunk])
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_section: Optional[str] = None
    ) -> List[EmbeddingResult]:
        """
        Search for similar chunks.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_section: Only return chunks from this section
            
        Returns:
            List of EmbeddingResult ordered by similarity
        """
        if not self.chunks:
            return []
        
        # Embed query
        query_embedding = np.array(self.embedding_function(query))
        
        # Calculate similarities
        results = []
        
        for i, (chunk, embedding) in enumerate(zip(self.chunks, self.embeddings)):
            # Apply section filter
            if filter_section and chunk.section != filter_section:
                continue
            
            # Cosine similarity
            score = self._cosine_similarity(query_embedding, embedding)
            results.append((chunk, score))
        
        # Sort by score (descending)
        results.sort(key=lambda x: -x[1])
        
        # Return top_k
        return [
            EmbeddingResult(chunk=chunk, score=score, rank=i+1)
            for i, (chunk, score) in enumerate(results[:top_k])
        ]
    
    def search_by_section(
        self,
        query: str,
        sections: List[str],
        top_k_per_section: int = 2
    ) -> Dict[str, List[EmbeddingResult]]:
        """
        Search within specific sections.
        
        Returns dict of section -> results.
        """
        results = {}
        
        for section in sections:
            section_results = self.search(
                query, 
                top_k=top_k_per_section,
                filter_section=section
            )
            if section_results:
                results[section] = section_results
        
        return results
    
    def get_all_chunks(self) -> List[Chunk]:
        """Get all stored chunks."""
        return self.chunks.copy()
    
    def clear(self) -> None:
        """Clear all stored data."""
        self.chunks = []
        self.embeddings = []
        self._vocabulary = {}
        self._idf = None
    
    def _default_embedding(self, text: str) -> List[float]:
        """
        Simple TF-IDF based embedding.
        
        For production, use sentence-transformers or OpenAI embeddings.
        """
        # Tokenize
        tokens = self._tokenize(text)
        
        # Build vocabulary if needed
        for token in tokens:
            if token not in self._vocabulary:
                self._vocabulary[token] = len(self._vocabulary)
        
        # Calculate TF
        tf = np.zeros(len(self._vocabulary))
        for token in tokens:
            if token in self._vocabulary:
                tf[self._vocabulary[token]] += 1
        
        # Normalize
        if tf.sum() > 0:
            tf = tf / tf.sum()
        
        # Apply IDF if available
        if self._idf is not None and len(self._idf) == len(tf):
            tf = tf * self._idf
        
        return tf.tolist()
    
    def _build_idf(self) -> None:
        """Build IDF weights from stored documents."""
        if not self.chunks:
            return
        
        n_docs = len(self.chunks)
        doc_freq = np.zeros(len(self._vocabulary))
        
        for chunk in self.chunks:
            tokens = set(self._tokenize(chunk.text))
            for token in tokens:
                if token in self._vocabulary:
                    doc_freq[self._vocabulary[token]] += 1
        
        # IDF = log(N / df)
        self._idf = np.log(n_docs / (doc_freq + 1)) + 1
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        import re
        # Lowercase and split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        
        # Remove stopwords
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this',
            'that', 'these', 'those', 'it', 'its', 'they', 'their', 'them',
        }
        
        return [t for t in tokens if t not in stopwords and len(t) > 2]
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity."""
        # Handle different lengths (vocabulary growth)
        min_len = min(len(a), len(b))
        a = a[:min_len]
        b = b[:min_len]
        
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot / (norm_a * norm_b))


def create_embedding_store(
    use_sentence_transformers: bool = False,
    model_name: str = "all-MiniLM-L6-v2"
) -> EmbeddingStore:
    """
    Create an embedding store with optional sentence-transformers.
    
    Args:
        use_sentence_transformers: Use sentence-transformers for embeddings
        model_name: Model name for sentence-transformers
        
    Returns:
        Configured EmbeddingStore
    """
    if use_sentence_transformers:
        try:
            from sentence_transformers import SentenceTransformer
            
            model = SentenceTransformer(model_name)
            
            def embed_fn(text: str) -> List[float]:
                embedding = model.encode(text)
                return embedding.tolist()
            
            return EmbeddingStore(
                embedding_function=embed_fn,
                embedding_dim=model.get_sentence_embedding_dimension()
            )
            
        except ImportError:
            print("sentence-transformers not installed, using TF-IDF fallback")
    
    # Default: TF-IDF based
    return EmbeddingStore()


def similarity_search(
    query: str,
    chunks: List[Chunk],
    top_k: int = 5
) -> List[EmbeddingResult]:
    """
    Convenience function for one-off similarity search.
    
    Creates a temporary store, adds chunks, and searches.
    """
    store = EmbeddingStore()
    store.add_chunks(chunks)
    return store.search(query, top_k=top_k)
