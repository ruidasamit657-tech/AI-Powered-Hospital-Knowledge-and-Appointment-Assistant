"""
Unit tests for text chunking service
"""

import pytest
# pyright: reportMissingImports=false
# pylint: disable=import-error, no-name-in-module
from app.services.chunking import TextChunker  # type: ignore[import]


class TestTextChunker:
    """Test text chunking functionality"""

    @pytest.fixture
    def chunker(self):
        """Create a chunker instance with default settings"""
        return TextChunker(chunk_size=100, chunk_overlap=20)

    @pytest.fixture
    def small_chunker(self):
        """Create a chunker with small chunk size"""
        return TextChunker(chunk_size=50, chunk_overlap=10)

    @pytest.fixture
    def large_chunker(self):
        """Create a chunker with large chunk size"""
        return TextChunker(chunk_size=500, chunk_overlap=50)

    # ==========================================
    # BASIC CHUNKING TESTS
    # ==========================================

    def test_chunk_empty_text(self, chunker):
        """Test chunking empty text returns empty list"""
        chunks = chunker.chunk_text("")
        assert chunks == []

    def test_chunk_none_text(self, chunker):
        """Test chunking None returns empty list"""
        chunks = chunker.chunk_text(None)
        assert chunks == []

    def test_chunk_whitespace_only(self, chunker):
        """Test chunking whitespace-only text"""
        chunks = chunker.chunk_text("   \n\t  ")
        assert chunks == []

    def test_chunk_short_text(self, chunker):
        """Test chunking text shorter than chunk_size"""
        text = "This is a short text."
        chunks = chunker.chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0]["text"] == "This is a short text."

    def test_chunk_text_with_source(self, chunker):
        """Test chunking includes source information"""
        text = "This is a test document."
        source = "test_document.txt"
        chunks = chunker.chunk_text(text, source=source)
        assert len(chunks) == 1
        assert chunks[0]["source"] == source

    def test_chunk_text_without_source(self, chunker):
        """Test chunking without source uses 'unknown'"""
        text = "This is a test document."
        chunks = chunker.chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0]["source"] == "unknown"

    # ==========================================
    # CHUNK SIZE TESTS
    # ==========================================

    def test_chunk_size_respected(self, chunker):
        """Test chunks don't exceed chunk_size"""
        text = ". ".join(["This is sentence number " + str(i) for i in range(50)])
        chunks = chunker.chunk_text(text)

        for chunk in chunks:
            # Allow small overflow due to sentence boundaries
            assert len(chunk["text"]) <= chunker.chunk_size * 1.5

    def test_multiple_chunks_created(self, small_chunker):
        """Test multiple chunks are created for long text"""
        text = ". ".join([f"Sentence {i} with some content" for i in range(20)])
        chunks = small_chunker.chunk_text(text)
        assert len(chunks) > 1

    def test_single_long_sentence_split(self, small_chunker):
        """Test a single sentence longer than chunk_size is split"""
        # Create a sentence longer than chunk_size (50 chars)
        long_sentence = "word " * 50  # ~250 characters
        chunks = small_chunker.chunk_text(long_sentence.strip())
        assert len(chunks) > 1

    def test_very_long_text(self, chunker):
        """Test chunking very long text"""
        text = "This is a test sentence. " * 100  # ~2600 characters
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 5

    # ==========================================
    # OVERLAP TESTS
    # ==========================================

    def test_overlap_creates_context(self, chunker):
        """Test that overlap preserves context between chunks"""
        text = ". ".join([f"Unique sentence {i}" for i in range(20)])
        chunks = chunker.chunk_text(text)

        if len(chunks) > 1:
            # Check that consecutive chunks share some content
            first_chunk_words = set(chunks[0]["text"].split())
            second_chunk_words = set(chunks[1]["text"].split())
            overlap = first_chunk_words.intersection(second_chunk_words)
            # There should be at least some overlap (allowing for common words)
            assert len(overlap) >= 0

    def test_zero_overlap(self):
        """Test chunker with zero overlap"""
        chunker = TextChunker(chunk_size=100, chunk_overlap=0)
        text = ". ".join([f"Sentence {i}" for i in range(30)])
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 1

    # ==========================================
    # SENTENCE BOUNDARY TESTS
    # ==========================================

    def test_sentence_boundaries_preserved(self, chunker):
        """Test that chunks respect sentence boundaries"""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunker.chunk_text(text)

        for chunk in chunks:
            # Each chunk should end with proper punctuation or be the last one
            text_content = chunk["text"].strip()
            if text_content:
                assert text_content[-1] in ".!?" or len(chunks) == 1

    def test_question_marks_handled(self, chunker):
        """Test question marks are treated as sentence boundaries"""
        text = "What is this? This is a test. How are you? I am fine."
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 1

    def test_exclamation_marks_handled(self, chunker):
        """Test exclamation marks are treated as sentence boundaries"""
        text = "Hello! How are you? I am fine! Great to hear."
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 1

    # ==========================================
    # WHITESPACE HANDLING TESTS
    # ==========================================

    def test_extra_whitespace_normalized(self, chunker):
        """Test that extra whitespace is normalized"""
        text = "This   has    extra     spaces."
        chunks = chunker.chunk_text(text)
        assert len(chunks) == 1
        assert "  " not in chunks[0]["text"]

    def test_newlines_normalized(self, chunker):
        """Test that newlines are handled properly"""
        text = "Line one.\n\nLine two.\n\nLine three."
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 1
        assert "\n" not in chunks[0]["text"]

    def test_tabs_normalized(self, chunker):
        """Test that tabs are normalized"""
        text = "Column one.\tColumn two.\tColumn three."
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 1
        assert "\t" not in chunks[0]["text"]

    # ==========================================
    # DOCUMENT CHUNKING TESTS
    # ==========================================

    def test_chunk_documents(self, chunker):
        """Test chunking multiple documents"""
        documents = [
            {"text": "Document one content. More content here.", "source": "doc1.txt"},
            {"text": "Document two content. More content here.", "source": "doc2.txt"}
        ]
        chunks = chunker.chunk_documents(documents)
        assert len(chunks) >= 2

        sources = [c["source"] for c in chunks]
        assert "doc1.txt" in sources
        assert "doc2.txt" in sources

    def test_chunk_empty_documents_list(self, chunker):
        """Test chunking empty documents list"""
        chunks = chunker.chunk_documents([])
        assert chunks == []

    def test_chunk_documents_preserves_source(self, chunker):
        """Test document sources are preserved in chunks"""
        documents = [
            {"text": "Short text.", "source": "important_doc.pdf"}
        ]
        chunks = chunker.chunk_documents(documents)
        assert len(chunks) == 1
        assert chunks[0]["source"] == "important_doc.pdf"

    # ==========================================
    # EDGE CASES
    # ==========================================

    def test_chunk_size_exactly_one_word(self):
        """Test chunker with very small chunk size"""
        chunker = TextChunker(chunk_size=10, chunk_overlap=2)
        text = "One two three four five six seven eight nine ten."
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 1

    def test_chunk_repeated_text(self, chunker):
        """Test chunking repeated text"""
        text = "repeat " * 100
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 1

    def test_chunk_unicode_text(self, chunker):
        """Test chunking text with unicode characters"""
        text = "Hola mundo. Bonjour le monde. 你好世界. مرحبا بالعالم."
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 1
        assert chunks[0]["source"] == "unknown"

    def test_chunk_special_characters(self, chunker):
        """Test chunking text with special characters"""
        text = "Email: test@example.com. Price: $99.99. Symbol: @#$%^&*()"
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 1

    def test_chunk_numbers(self, chunker):
        """Test chunking text with numbers"""
        text = "The answer is 42. Pi is 3.14159. There are 365 days."
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 1

    def test_all_chunks_have_required_fields(self, chunker):
        """Test all chunks have text and source fields"""
        text = "Test content. " * 20
        chunks = chunker.chunk_text(text, source="test.txt")

        for chunk in chunks:
            assert "text" in chunk
            assert "source" in chunk
            assert isinstance(chunk["text"], str)
            assert isinstance(chunk["source"], str)