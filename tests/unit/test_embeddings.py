"""
Unit tests for embedding service
"""

import pytest
from app.services.embedding import EmbeddingService
import numpy as np


class TestEmbeddingService:
    """Test embedding generation functionality"""

    @pytest.fixture(scope="class")
    def embedding_service(self):
        """Create a shared embedding service instance (expensive to load)"""
        return EmbeddingService()

    # ==========================================
    # SINGLE EMBEDDING TESTS
    # ==========================================

    def test_generate_single_embedding(self, embedding_service):
        """Test generating embedding for a single text"""
        text = "This is a test sentence for embedding."
        embedding = embedding_service.generate_embedding(text)
        
        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    def test_embedding_dimension_consistent(self, embedding_service):
        """Test embeddings have consistent dimensions"""
        text1 = "First text"
        text2 = "Second different text"
        
        emb1 = embedding_service.generate_embedding(text1)
        emb2 = embedding_service.generate_embedding(text2)
        
        assert len(emb1) == len(emb2)

    def test_embedding_empty_text(self, embedding_service):
        """Test embedding empty text"""
        embedding = embedding_service.generate_embedding("")
        assert embedding is not None
        assert isinstance(embedding, list)

    def test_embedding_whitespace_text(self, embedding_service):
        """Test embedding whitespace-only text"""
        embedding = embedding_service.generate_embedding("   ")
        assert embedding is not None
        assert isinstance(embedding, list)

    # ==========================================
    # BATCH EMBEDDING TESTS
    # ==========================================

    def test_generate_batch_embeddings(self, embedding_service):
        """Test generating embeddings for multiple texts"""
        texts = [
            "First document about hospitals.",
            "Second document about doctors.",
            "Third document about patients."
        ]
        embeddings = embedding_service.generate_embeddings(texts)
        
        assert len(embeddings) == len(texts)
        for embedding in embeddings:
            assert isinstance(embedding, list)
            assert len(embedding) > 0

    def test_batch_embeddings_same_dimension(self, embedding_service):
        """Test all batch embeddings have same dimension"""
        texts = ["Text one", "Text two", "Text three"]
        embeddings = embedding_service.generate_embeddings(texts)
        
        dimensions = [len(emb) for emb in embeddings]
        assert len(set(dimensions)) == 1  # All same dimension

    def test_batch_empty_list(self, embedding_service):
        """Test generating embeddings for empty list"""
        embeddings = embedding_service.generate_embeddings([])
        assert embeddings == []

    def test_batch_single_item(self, embedding_service):
        """Test batch with single item"""
        embeddings = embedding_service.generate_embeddings(["Single text"])
        assert len(embeddings) == 1
        assert len(embeddings[0]) > 0

    # ==========================================
    # CHUNK EMBEDDING TESTS
    # ==========================================

    def test_generate_chunk_embeddings(self, embedding_service):
        """Test generating embeddings for chunks"""
        chunks = [
            {"text": "First chunk content", "source": "doc1.txt"},
            {"text": "Second chunk content", "source": "doc1.txt"},
            {"text": "Third chunk content", "source": "doc2.txt"}
        ]
        result = embedding_service.generate_chunk_embeddings(chunks)
        
        assert len(result) == len(chunks)
        for i, item in enumerate(result):
            assert "text" in item
            assert "source" in item
            assert "embedding" in item
            assert item["text"] == chunks[i]["text"]
            assert item["source"] == chunks[i]["source"]

    def test_chunk_embeddings_empty(self, embedding_service):
        """Test generating embeddings for empty chunks list"""
        result = embedding_service.generate_chunk_embeddings([])
        assert result == []

    def test_chunk_embeddings_preserve_source(self, embedding_service):
        """Test chunk embeddings preserve source information"""
        chunks = [
            {"text": "Test content", "source": "important.pdf"}
        ]
        result = embedding_service.generate_chunk_embeddings(chunks)
        assert result[0]["source"] == "important.pdf"

    def test_chunk_embeddings_missing_source(self, embedding_service):
        """Test chunks without source use 'unknown'"""
        chunks = [
            {"text": "Test content"}  # No source
        ]
        result = embedding_service.generate_chunk_embeddings(chunks)
        assert result[0]["source"] == "unknown"

    # ==========================================
    # SEMANTIC SIMILARITY TESTS
    # ==========================================

    def test_similar_texts_have_similar_embeddings(self, embedding_service):
        """Test similar texts produce similar embeddings"""
        text1 = "The patient has high blood pressure"
        text2 = "The patient has hypertension"
        text3 = "The weather is sunny today"
        
        emb1 = embedding_service.generate_embedding(text1)
        emb2 = embedding_service.generate_embedding(text2)
        emb3 = embedding_service.generate_embedding(text3)
        
        # Cosine similarity
        sim_12 = self._cosine_similarity(emb1, emb2)
        sim_13 = self._cosine_similarity(emb1, emb3)
        
        # Similar medical texts should be more similar
        assert sim_12 > sim_13

    def test_dissimilar_texts_have_different_embeddings(self, embedding_service):
        """Test dissimilar texts produce different embeddings"""
        text1 = "Hospital emergency room services"
        text2 = "Chocolate cake recipe with frosting"
        
        emb1 = embedding_service.generate_embedding(text1)
        emb2 = embedding_service.generate_embedding(text2)
        
        similarity = self._cosine_similarity(emb1, emb2)
        
        # Should not be identical
        assert similarity < 0.99

    def test_identical_texts_have_identical_embeddings(self, embedding_service):
        """Test identical texts produce identical embeddings"""
        text = "The patient needs immediate attention"
        
        emb1 = embedding_service.generate_embedding(text)
        emb2 = embedding_service.generate_embedding(text)
        
        similarity = self._cosine_similarity(emb1, emb2)
        assert similarity > 0.999

    # ==========================================
    # HELPER METHODS
    # ==========================================

    @staticmethod
    def _cosine_similarity(vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        a = np.array(vec1)
        b = np.array(vec2)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    # ==========================================
    # EDGE CASES
    # ==========================================

    def test_embedding_unicode_text(self, embedding_service):
        """Test embedding unicode text"""
        text = "Hola mundo. 你好世界. مرحبا بالعالم."
        embedding = embedding_service.generate_embedding(text)
        assert embedding is not None
        assert len(embedding) > 0

    def test_embedding_special_characters(self, embedding_service):
        """Test embedding text with special characters"""
        text = "Email: test@example.com, Price: $99.99"
        embedding = embedding_service.generate_embedding(text)
        assert embedding is not None
        assert len(embedding) > 0

    def test_embedding_long_text(self, embedding_service):
        """Test embedding very long text"""
        text = "This is a test sentence. " * 100  # ~2600 chars
        embedding = embedding_service.generate_embedding(text)
        assert embedding is not None
        assert len(embedding) > 0

    def test_embedding_numbers(self, embedding_service):
        """Test embedding text with numbers"""
        text = "The answer is 42 and Pi is 3.14159"
        embedding = embedding_service.generate_embedding(text)
        assert embedding is not None