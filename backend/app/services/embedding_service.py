"""
Service for generating embeddings using BAAI/bge-m3 model.
"""
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings


class EmbeddingService:
    """Generate embeddings using BAAI/bge-m3."""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        """Singleton pattern to share model across instances."""
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the embedding service (model loaded lazily)."""
        # Model is shared across all instances via class variable
        pass
    
    @property
    def model(self):
        """Lazy load the embedding model (shared across all instances)."""
        if EmbeddingService._model is None:
            print(f"🔄 Loading embedding model: {settings.embedding_model}...")
            print("   This may take a few minutes on first run...")
            EmbeddingService._model = SentenceTransformer(settings.embedding_model)
            print("✅ Embedding model loaded successfully")
            print("ℹ️  Model will be reused for all subsequent requests (singleton)")
        else:
            # Model already loaded - no need to reload
            pass
        return EmbeddingService._model
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        Optimized with batch processing and GPU support.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors (each is a list of floats)
        """
        if not texts:
            return []
        
        # Generate embeddings (bge-m3 produces 1024-dimensional vectors)
        # batch_size=32 is optimal for most hardware
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,  # Normalize for cosine similarity
            show_progress_bar=False,
            batch_size=32,  # Process 32 texts at a time
            convert_to_numpy=True,  # Faster conversion
        )
        
        # Convert numpy array to list of lists
        return embeddings.tolist()
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector as a list of floats
        """
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]

