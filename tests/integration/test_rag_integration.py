"""
Integration tests for RAG (Retrieval-Augmented Generation) pipeline
"""
import os
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path so `app.*` imports resolve at runtime.
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# pylint: disable=wrong-import-position
import pytest

from app.services.document_loader import DocumentLoader
from app.services.chunking import TextChunker
from app.services.embedding import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.retriever import Retriever
from app.services.rag_service import RAGService
from app.services.emergency_guard import EmergencyGuard

# Pylint/Pylance cannot resolve this module from the test file's static
# import path even though it exists and works at runtime.
# pylint: disable=import-error,no-name-in-module
from app.services.prompt_builder import PromptBuilder  # type: ignore[import]
# pylint: enable=import-error,no-name-in-module
# pylint: enable=wrong-import-position


class TestDocumentLoader:
    """Test document loading functionality"""

    @pytest.fixture
    def loader(self):
        return DocumentLoader()

    def test_load_txt_file(self, loader):
        """Test loading a TXT file"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        ) as f:
            f.write("Hospital visiting hours are 8 AM to 8 PM.")
            f.write("\nEmergency services available 24/7.")
            temp_path = f.name

        try:
            result = loader.load_document(temp_path)
            assert "text" in result
            assert "source" in result
            assert "visiting hours" in result["text"]
            assert "24/7" in result["text"]
        finally:
            os.remove(temp_path)

    def test_load_markdown_file(self, loader):
        """Test loading a Markdown file"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write("# Hospital Guidelines\n\n")
            f.write("## Visiting Hours\n")
            f.write("- General: 8 AM to 8 PM\n")
            temp_path = f.name

        try:
            result = loader.load_document(temp_path)
            assert "text" in result
            assert "Hospital Guidelines" in result["text"]
        finally:
            os.remove(temp_path)

    def test_load_directory(self, loader):
        """Test loading all documents from a directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            for i in range(3):
                file_path = os.path.join(temp_dir, f"test_{i}.txt")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Test document {i} content about hospital policies.")

            results = loader.load_directory(temp_dir)
            assert len(results) == 3

    def test_unsupported_file_type(self, loader):
        """Test loading unsupported file type"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.xyz', delete=False
        ) as f:
            f.write("Unsupported content")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                loader.load_document(temp_path)
        finally:
            os.remove(temp_path)


class TestChunking:
    """Test text chunking functionality"""

    @pytest.fixture
    def chunker(self):
        # TextChunker accepts `chunk_overlap`, not `overlap`
        return TextChunker(chunk_size=100, chunk_overlap=20)

    def test_chunk_short_text(self, chunker):
        """Test chunking short text"""
        text = "This is a short text. It has two sentences."
        chunks = chunker.chunk_text(text, source="test.txt")
        assert len(chunks) >= 1
        assert chunks[0]["text"]
        assert chunks[0]["source"] == "test.txt"

    def test_chunk_long_text(self, chunker):
        """Test chunking long text"""
        text = " ".join(
            [f"Sentence number {i} contains important information." for i in range(50)]
        )
        chunks = chunker.chunk_text(text, source="long.txt")
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk["text"]) <= chunker.chunk_size + 50
            assert chunk["source"] == "long.txt"

    def test_chunk_overlap(self, chunker):
        """Test chunk overlap"""
        text = " ".join([f"Word{i}" for i in range(100)])
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 1

    def test_chunk_documents(self, chunker):
        """Test chunking multiple documents"""
        documents = [
            {"text": "Document 1 content. " * 20, "source": "doc1.txt"},
            {"text": "Document 2 content. " * 20, "source": "doc2.txt"},
        ]
        chunks = chunker.chunk_documents(documents)
        assert len(chunks) > 2
        sources = set(c["source"] for c in chunks)
        assert "doc1.txt" in sources
        assert "doc2.txt" in sources


class TestEmbedding:
    """Test embedding generation"""

    @pytest.fixture
    def embedding_service(self):
        return EmbeddingService()

    def test_generate_single_embedding(self, embedding_service):
        """Test generating a single embedding"""
        text = "Hospital visiting hours"
        embedding = embedding_service.generate_embedding(text)
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    def test_generate_multiple_embeddings(self, embedding_service):
        """Test generating multiple embeddings"""
        texts = [
            "Hospital visiting hours",
            "Emergency services",
            "Doctor appointments",
        ]
        embeddings = embedding_service.generate_embeddings(texts)
        assert len(embeddings) == 3
        for emb in embeddings:
            assert isinstance(emb, list)
            assert len(emb) > 0

    def test_embedding_similarity(self, embedding_service):
        """Test that similar texts have similar embeddings"""
        import numpy as np

        text1 = "The hospital visiting hours are from 8 AM to 8 PM"
        text2 = "Visiting hours at the hospital are 8 AM to 8 PM"
        text3 = "The weather today is sunny and warm"

        emb1 = np.array(embedding_service.generate_embedding(text1))
        emb2 = np.array(embedding_service.generate_embedding(text2))
        emb3 = np.array(embedding_service.generate_embedding(text3))

        sim12 = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        sim13 = np.dot(emb1, emb3) / (np.linalg.norm(emb1) * np.linalg.norm(emb3))

        assert sim12 > sim13

    def test_generate_chunk_embeddings(self, embedding_service):
        """Test generating embeddings for chunks"""
        chunks = [
            {"text": "Hospital visiting hours", "source": "doc1.txt"},
            {"text": "Emergency procedures", "source": "doc2.txt"},
        ]
        result = embedding_service.generate_chunk_embeddings(chunks)
        assert len(result) == 2
        assert "embedding" in result[0]
        assert "text" in result[0]
        assert "source" in result[0]


class TestVectorStore:
    """Test vector store operations"""

    @pytest.fixture
    def vector_store(self):
        temp_dir = tempfile.mkdtemp()
        store = VectorStore(persist_directory=temp_dir)
        yield store
        # Cleanup
        try:
            # pylint: disable=no-member
            store.delete_all()
        except (ValueError, RuntimeError) as exc:  # pylint: disable=broad-exception-caught
            print(f"Cleanup warning: {exc}")

    @pytest.fixture
    def embedding_service(self):
        return EmbeddingService()

    def test_add_and_search(self, vector_store, embedding_service):
        """Test adding chunks and searching"""
        chunks = [
            {
                "text": "Hospital visiting hours are 8 AM to 8 PM",
                "source": "policies.txt",
                "embedding": embedding_service.generate_embedding(
                    "Hospital visiting hours are 8 AM to 8 PM"
                ),
            },
            {
                "text": "Emergency services available 24/7",
                "source": "emergency.txt",
                "embedding": embedding_service.generate_embedding(
                    "Emergency services available 24/7"
                ),
            },
        ]
        # pylint: disable=no-member
        vector_store.add_chunks(chunks)
        assert vector_store.count() == 2

        query_embedding = embedding_service.generate_embedding("visiting hours")
        results = vector_store.search(query_embedding, top_k=2)
        assert len(results) > 0
        assert "text" in results[0]

    def test_delete_all(self, vector_store, embedding_service):
        """Test deleting all chunks"""
        chunks = [
            {
                "text": "Test content",
                "source": "test.txt",
                "embedding": embedding_service.generate_embedding("Test content"),
            }
        ]
        # pylint: disable=no-member
        vector_store.add_chunks(chunks)
        assert vector_store.count() == 1

        vector_store.delete_all()
        assert vector_store.count() == 0

    def test_empty_search(self, vector_store, embedding_service):
        """Test searching empty vector store"""
        query_embedding = embedding_service.generate_embedding("test query")
        results = vector_store.search(query_embedding, top_k=5)
        assert results == []


class TestRetriever:
    """Test retriever functionality"""

    @pytest.fixture
    def retriever(self):
        return Retriever()

    def test_retrieve_with_sources(self, retriever):
        """Test retrieval with source information"""
        result = retriever.retrieve_with_sources("hospital visiting hours", top_k=3)
        assert "chunks" in result
        assert "sources" in result
        assert "total_chunks" in result
        assert isinstance(result["chunks"], list)
        assert isinstance(result["sources"], dict)


class TestPromptBuilder:
    """Test prompt building"""

    @pytest.fixture
    def prompt_builder(self):
        return PromptBuilder()

    def test_build_prompt(self, prompt_builder):
        """Test building a prompt with context"""
        chunks = [
            {
                "text": "Hospital visiting hours are 8 AM to 8 PM",
                "source": "policies.txt",
            },
            {
                "text": "Emergency services available 24/7",
                "source": "emergency.txt",
            },
        ]
        prompt = prompt_builder.build_prompt("What are the visiting hours?", chunks)
        assert "What are the visiting hours?" in prompt
        assert "8 AM to 8 PM" in prompt
        assert "policies.txt" in prompt

    def test_build_prompt_no_chunks(self, prompt_builder):
        """Test building prompt with no chunks"""
        prompt = prompt_builder.build_prompt("What are the visiting hours?", [])
        assert "don't have any relevant information" in prompt

    def test_build_emergency_response(self, prompt_builder):
        """Test building emergency response"""
        response = prompt_builder.build_emergency_response("heart attack")
        assert "EMERGENCY" in response
        assert "heart attack" in response


class TestRAGService:
    """Test complete RAG service"""

    @pytest.fixture
    def rag_service(self):
        return RAGService()

    def test_rag_service_initialization(self, rag_service):
        """Test RAG service initializes correctly"""
        assert rag_service.document_loader is not None
        assert rag_service.chunker is not None
        assert rag_service.embedding_service is not None
        assert rag_service.vector_store is not None
        assert rag_service.retriever is not None
        assert rag_service.prompt_builder is not None
        assert rag_service.emergency_guard is not None

    def test_ingest_documents(self, rag_service):
        """Test document ingestion"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        ) as f:
            f.write("The hospital visiting hours are 8 AM to 8 PM. ")
            f.write("Emergency services are available 24 hours a day. ")
            f.write("Appointments can be scheduled by calling 555-0101.")
            temp_path = f.name

        try:
            # pylint: disable=no-member
            result = rag_service.ingest_documents([temp_path])
            assert "chunks_created" in result
            assert result["chunks_created"] > 0
        finally:
            os.remove(temp_path)

    def test_ingest_empty_document(self, rag_service):
        """Test ingesting empty document"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False
        ) as f:
            f.write("")
            temp_path = f.name

        try:
            # pylint: disable=no-member
            result = rag_service.ingest_documents([temp_path])
            assert "chunks_created" in result
        finally:
            os.remove(temp_path)


class TestEmergencyGuardIntegration:
    """Integration tests for emergency guard"""

    @pytest.fixture
    def guard(self):
        return EmergencyGuard()

    @pytest.mark.parametrize(
        "query,expected",
        [
            ("I think I'm having a heart attack!", True),
            ("I have severe chest pain", True),
            ("I can't breathe", True),
            ("I need an ambulance", True),
            ("Call 911", True),
            ("I'm bleeding heavily", True),
            ("My father is having a stroke", True),
            ("I feel like I might pass out", True),
            ("I'm having a seizure", True),
            ("What are the visiting hours?", False),
            ("How do I schedule an appointment?", False),
            ("What insurance do you accept?", False),
            ("Where is the cafeteria?", False),
        ],
    )
    def test_emergency_detection(self, guard, query, expected):
        """Test various emergency and non-emergency queries"""
        is_emergency, _keywords = guard.detect_emergency(query)
        assert is_emergency == expected, f"Failed for: {query}"

    def test_emergency_response_contains_key_info(self, guard):
        """Test emergency response contains essential information"""
        response = guard.get_emergency_response("heart attack")
        assert "911" in response or "emergency" in response.lower()
        assert "immediately" in response.lower()


class TestEndToEndRAG:
    """End-to-end RAG pipeline tests"""

    def test_full_rag_pipeline(self):
        """Test complete RAG pipeline from ingestion to retrieval"""
        rag_service = RAGService()

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        ) as f:
            f.write(
                "Cardiology Department: The cardiology department is located "
                "on the 3rd floor. "
            )
            f.write("Our cardiologists specialize in heart disease treatment. ")
            f.write(
                "To schedule an appointment with a cardiologist, call 555-0200. "
            )
            f.write("Visiting hours for cardiology patients are 10 AM to 6 PM.")
            temp_path = f.name

        try:
            # pylint: disable=no-member
            result = rag_service.ingest_documents([temp_path])
            assert result["chunks_created"] > 0

            retrieval = rag_service.retriever.retrieve_with_sources(
                "Where is the cardiology department?", top_k=3
            )
            assert len(retrieval["chunks"]) > 0

            prompt = rag_service.prompt_builder.build_prompt(
                "Where is the cardiology department?", retrieval["chunks"]
            )
            assert "cardiology" in prompt.lower()
        finally:
            os.remove(temp_path)

    def test_rag_with_hospital_documents(self):
        """Test RAG with actual hospital knowledge documents"""
        rag_service = RAGService()

        kb_path = Path("data/knowledge_base")
        if not kb_path.exists():
            pytest.skip("Knowledge base not found")

        result = rag_service.retriever.retrieve_with_sources(
            "visiting hours", top_k=3
        )
        assert "chunks" in result
        assert "sources" in result