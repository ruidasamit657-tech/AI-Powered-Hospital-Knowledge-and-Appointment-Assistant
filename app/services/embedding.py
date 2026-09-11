"""Utilities for generating and comparing text embeddings."""

from importlib import import_module
from typing import List, Union, Dict, Any

import numpy as np

try:
    HuggingFaceEmbeddings = import_module(
        "langchain_huggingface"
    ).HuggingFaceEmbeddings
except (ImportError, AttributeError):  # pragma: no cover - optional dependency
    HuggingFaceEmbeddings = None

try:
    import torch
except ImportError:  # pragma: no cover - optional dependency for CUDA detection
    torch = None

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating embeddings from text."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = None,
        batch_size: int = 32
    ):
        """
        Initialize the embedding service.

        Args:
            model_name: Name of the embedding model to use
            device: Device to use ('cpu', 'cuda', or None for auto)
            batch_size: Batch size for processing
        """
        self.model_name = model_name
        self.device = device or (
            "cuda" if torch is not None and torch.cuda.is_available() else "cpu"
        )
        self.batch_size = batch_size

        # Initialize model
        try:
            if HuggingFaceEmbeddings is not None:
                # Using HuggingFaceEmbeddings from LangChain for better compatibility
                self.model = HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs={'device': self.device},
                    encode_kwargs={'normalize_embeddings': True}
                )
                logger.info(f"Initialized embedding model: {model_name} on {self.device}")
                return

            raise ImportError("langchain_huggingface is not installed")
        except (ImportError, OSError, RuntimeError, TypeError, ValueError) as e:
            logger.warning(f"Failed to load embedding model via LangChain: {str(e)}")
            # Fallback to SentenceTransformer
            try:
                sentence_transformers = import_module("sentence_transformers")
                self.model = sentence_transformers.SentenceTransformer(
                    model_name,
                    device=self.device,
                )
                logger.info(f"Fallback to SentenceTransformer: {model_name}")
            except (ImportError, OSError, RuntimeError, TypeError, ValueError) as fallback_error:
                logger.error(
                    "No embedding backend available. Install 'langchain-huggingface' or "
                    "'sentence-transformers'."
                )
                raise ImportError(
                    "Unable to initialize embedding model. Install either "
                    "'langchain-huggingface' or 'sentence-transformers'."
                ) from fallback_error
    
    def generate_embeddings(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Single text string or list of text strings
        
        Returns:
            List of embedding vectors
        """
        try:
            if isinstance(texts, str):
                texts = [texts]
            
            if not texts:
                return []
            
            # Filter out empty texts
            valid_texts = [t for t in texts if t and t.strip()]
            if not valid_texts:
                return []
            
            # Generate embeddings
            if hasattr(self.model, 'embed_documents'):
                embeddings = self.model.embed_documents(valid_texts)
            else:
                # Fallback to SentenceTransformer
                embeddings = self.model.encode(
                    valid_texts,
                    batch_size=self.batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True
                )
                embeddings = [emb.tolist() if hasattr(emb, 'tolist') else emb for emb in embeddings]
            
            return embeddings
            
        except (RuntimeError, TypeError, ValueError) as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise ValueError(f"Failed to generate embeddings: {str(e)}") from e
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a query string."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        embeddings = self.generate_embeddings(query)
        return embeddings[0] if embeddings else []
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings."""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            if vec1.shape != vec2.shape:
                raise ValueError("Embeddings must have the same shape")
            
            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except (TypeError, ValueError, FloatingPointError) as e:
            logger.error(f"Error computing similarity: {str(e)}")
            return 0.0
    
    def batch_similarity(
        self,
        query_embedding: List[float],
        embeddings: List[List[float]]
    ) -> List[float]:
        """Compute similarity between query and multiple embeddings."""
        if not embeddings:
            return []
        
        query_vector = np.array(query_embedding)
        embedding_vectors = np.array(embeddings)
        
        # Normalize vectors
        query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-8)
        embeddings_norm = embedding_vectors / (np.linalg.norm(embedding_vectors, axis=1, keepdims=True) + 1e-8)
        
        # Compute similarities
        similarities = np.dot(embeddings_norm, query_norm)
        
        return similarities.tolist()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "batch_size": self.batch_size,
            "embedding_dim": self.get_embedding_dimension()
        }
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        try:
            test_text = "test"
            embedding = self.generate_embeddings(test_text)
            return len(embedding[0]) if embedding else 0
        except (RuntimeError, TypeError, ValueError):
            return 384  # Default for all-MiniLM-L6-v2
