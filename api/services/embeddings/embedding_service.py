# api/services/embeddings/embedding_service.py
"""
Embedding service for generating vector embeddings from text.
Uses sentence-transformers with all-MiniLM-L6-v2 (384 dimensions).
"""

import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

# Lazy load model to avoid startup delays
_model = None


def get_model():
    """Lazy load the embedding model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model: all-MiniLM-L6-v2")
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded successfully")
        except ImportError:
            raise ImportError(
                "sentence-transformers is required. "
                "Install with: pip install sentence-transformers"
            )
    return _model


class EmbeddingService:
    """
    Service for generating text embeddings.
    
    Uses all-MiniLM-L6-v2 which produces 384-dimensional vectors.
    This model is efficient and works well for semantic search.
    
    Usage:
        service = EmbeddingService()
        
        # Single text
        embedding = await service.embed("Hello world")
        
        # Multiple texts (more efficient)
        embeddings = await service.embed_batch(["Hello", "World"])
    """
    
    # Model produces 384-dimensional embeddings
    EMBEDDING_DIM = 384
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of sentence-transformers model to use
        """
        self.model_name = model_name
        self._model = None
    
    @property
    def model(self):
        """Lazy load model on first use."""
        if self._model is None:
            self._model = get_model()
        return self._model
    
    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            384-dimensional embedding as list of floats
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.EMBEDDING_DIM
        
        # sentence-transformers encode is synchronous but fast
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once
            show_progress: Show progress bar
            
        Returns:
            List of embeddings (each 384-dimensional)
        """
        if not texts:
            return []
        
        # Handle empty strings
        processed_texts = [t if t and t.strip() else " " for t in texts]
        
        embeddings = self.model.encode(
            processed_texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )
        
        return embeddings.tolist()
    
    def get_embedding_dim(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        return self.EMBEDDING_DIM


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


# Convenience functions
async def embed_text(text: str) -> list[float]:
    """Generate embedding for a single text."""
    service = get_embedding_service()
    return await service.embed(text)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts."""
    service = get_embedding_service()
    return await service.embed_batch(texts)
