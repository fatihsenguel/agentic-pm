# src/portfolio_tool/rag/embeddings.py
"""
Embedding Service for RAG Pipeline.

Phase: 6.7 - RAG Integration (Phase 2: Vector Store)

PURPOSE:
Generate vector embeddings for document chunks:
- Primary: OpenAI text-embedding-3-small (best quality, uses existing OPENAI_API_KEY)
- Fallback: sentence-transformers all-MiniLM-L6-v2 (local, no API needed)

DESIGN PRINCIPLES:
- Lazy loading: Models loaded only when first used
- Automatic fallback: If OpenAI fails, falls back to local
- Batching: Process multiple texts efficiently
- Caching: Optional embedding cache to avoid redundant API calls

USAGE:
    from portfolio_tool.rag.embeddings import EmbeddingService
    
    # Auto-selects best available provider
    service = EmbeddingService()
    
    # Embed a single query
    vector = service.embed_query("What is NVIDIA's revenue?")
    
    # Embed multiple documents (batched)
    vectors = service.embed_documents(["chunk 1", "chunk 2", "chunk 3"])
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class EmbeddingConfig:
    """Configuration for embedding service."""
    # OpenAI settings
    openai_model: str = "text-embedding-3-small"
    openai_dimensions: int = 1536
    openai_batch_size: int = 100  # Max texts per API call
    
    # Local fallback settings
    local_model: str = "all-MiniLM-L6-v2"
    local_dimensions: int = 384
    
    # Behavior
    prefer_local: bool = False  # Set True to always use local
    auto_fallback: bool = True  # Fallback to local if OpenAI fails


# =============================================================================
# ABSTRACT BASE
# =============================================================================

class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return model identifier."""
        pass
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents."""
        pass
    
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        pass


# =============================================================================
# OPENAI PROVIDER
# =============================================================================

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    OpenAI embedding provider using text-embedding-3-small.
    
    Uses the same OPENAI_API_KEY as your LLM.
    """
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._client = None
    
    @property
    def dimensions(self) -> int:
        return self.config.openai_dimensions
    
    @property
    def model_name(self) -> str:
        return self.config.openai_model
    
    @property
    def client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI()  # Uses OPENAI_API_KEY env var
                logger.info("OpenAI client initialized for embeddings")
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. "
                    "Install with: pip install openai"
                )
            except Exception as e:
                raise RuntimeError(f"Failed to initialize OpenAI client: {e}")
        return self._client
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents with batching.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), self.config.openai_batch_size):
            batch = texts[i:i + self.config.openai_batch_size]
            
            # Clean texts (OpenAI doesn't like empty strings)
            batch = [t if t.strip() else " " for t in batch]
            
            try:
                response = self.client.embeddings.create(
                    model=self.config.openai_model,
                    input=batch,
                )
                
                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"OpenAI embedding error: {e}")
                raise
        
        return all_embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        result = self.embed_documents([text])
        return result[0] if result else []


# =============================================================================
# LOCAL PROVIDER (SENTENCE-TRANSFORMERS)
# =============================================================================

class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """
    Local embedding provider using sentence-transformers.
    
    No API key needed, runs entirely on CPU/GPU.
    Quality is ~90% of OpenAI for most use cases.
    """
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._model = None
    
    @property
    def dimensions(self) -> int:
        return self.config.local_dimensions
    
    @property
    def model_name(self) -> str:
        return self.config.local_model
    
    @property
    def model(self):
        """Lazy-load sentence-transformers model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading local embedding model: {self.config.local_model}")
                self._model = SentenceTransformer(self.config.local_model)
                logger.info("Local embedding model loaded successfully")
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents."""
        if not texts:
            return []
        
        # sentence-transformers handles batching internally
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100,
        )
        
        # Convert to list of lists
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()


# =============================================================================
# MAIN EMBEDDING SERVICE
# =============================================================================

class EmbeddingService:
    """
    Main embedding service with automatic provider selection and fallback.
    
    Usage:
        # Auto-selects best available provider
        service = EmbeddingService()
        
        # Force local only
        service = EmbeddingService(prefer_local=True)
        
        # Embed documents
        vectors = service.embed_documents(["text1", "text2"])
        
        # Embed query
        query_vector = service.embed_query("search query")
    """
    
    def __init__(
        self,
        config: Optional[EmbeddingConfig] = None,
        prefer_local: bool = False,
    ):
        """
        Initialize embedding service.
        
        Args:
            config: Embedding configuration (optional)
            prefer_local: If True, always use local model
        """
        self.config = config or EmbeddingConfig()
        if prefer_local:
            self.config.prefer_local = True
        
        self._provider: Optional[BaseEmbeddingProvider] = None
        self._fallback_provider: Optional[BaseEmbeddingProvider] = None
    
    @property
    def provider(self) -> BaseEmbeddingProvider:
        """Get or initialize the embedding provider."""
        if self._provider is None:
            self._provider = self._initialize_provider()
        return self._provider
    
    @property
    def dimensions(self) -> int:
        """Return embedding dimensions of current provider."""
        return self.provider.dimensions
    
    @property
    def model_name(self) -> str:
        """Return model name of current provider."""
        return self.provider.model_name
    
    def _initialize_provider(self) -> BaseEmbeddingProvider:
        """Initialize the best available provider."""
        
        # If prefer_local, go straight to local
        if self.config.prefer_local:
            logger.info("Using local embedding provider (prefer_local=True)")
            return LocalEmbeddingProvider(self.config)
        
        # Try OpenAI first
        if self._has_openai_key():
            try:
                provider = OpenAIEmbeddingProvider(self.config)
                # Test the connection
                _ = provider.client
                logger.info(f"Using OpenAI embedding provider: {provider.model_name}")
                return provider
            except Exception as e:
                logger.warning(f"OpenAI initialization failed: {e}")
                if self.config.auto_fallback:
                    logger.info("Falling back to local embedding provider")
                else:
                    raise
        
        # Fallback to local
        logger.info("Using local embedding provider (no OpenAI key or fallback)")
        return LocalEmbeddingProvider(self.config)
    
    def _has_openai_key(self) -> bool:
        """Check if OpenAI API key is available."""
        return bool(os.environ.get("OPENAI_API_KEY"))
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        try:
            return self.provider.embed_documents(texts)
        except Exception as e:
            # Try fallback if available and auto_fallback enabled
            if self.config.auto_fallback and not isinstance(self.provider, LocalEmbeddingProvider):
                logger.warning(f"Primary provider failed: {e}, trying fallback")
                if self._fallback_provider is None:
                    self._fallback_provider = LocalEmbeddingProvider(self.config)
                return self._fallback_provider.embed_documents(texts)
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query.
        
        Args:
            text: Query text
            
        Returns:
            Embedding vector
        """
        try:
            return self.provider.embed_query(text)
        except Exception as e:
            if self.config.auto_fallback and not isinstance(self.provider, LocalEmbeddingProvider):
                logger.warning(f"Primary provider failed: {e}, trying fallback")
                if self._fallback_provider is None:
                    self._fallback_provider = LocalEmbeddingProvider(self.config)
                return self._fallback_provider.embed_query(text)
            raise
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about current provider."""
        return {
            "provider_type": type(self.provider).__name__,
            "model_name": self.provider.model_name,
            "dimensions": self.provider.dimensions,
            "has_fallback": self._fallback_provider is not None,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Module-level singleton for convenience
_default_service: Optional[EmbeddingService] = None


def get_embedding_service(prefer_local: bool = False) -> EmbeddingService:
    """
    Get or create the default embedding service.
    
    Args:
        prefer_local: If True, use local model
        
    Returns:
        EmbeddingService instance
    """
    global _default_service
    
    if _default_service is None or (prefer_local and not _default_service.config.prefer_local):
        _default_service = EmbeddingService(prefer_local=prefer_local)
    
    return _default_service


def embed_texts(texts: List[str], prefer_local: bool = False) -> List[List[float]]:
    """
    Convenience function to embed multiple texts.
    
    Args:
        texts: List of text strings
        prefer_local: If True, use local model
        
    Returns:
        List of embedding vectors
    """
    service = get_embedding_service(prefer_local=prefer_local)
    return service.embed_documents(texts)


def embed_query(text: str, prefer_local: bool = False) -> List[float]:
    """
    Convenience function to embed a query.
    
    Args:
        text: Query text
        prefer_local: If True, use local model
        
    Returns:
        Embedding vector
    """
    service = get_embedding_service(prefer_local=prefer_local)
    return service.embed_query(text)
