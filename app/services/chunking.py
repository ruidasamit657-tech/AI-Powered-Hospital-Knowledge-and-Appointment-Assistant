from typing import List, Dict, Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken

from app.core.logging import get_logger

logger = get_logger(__name__)

class TextChunker:
    """Handles text chunking with various strategies."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
        keep_separator: bool = True
    ):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks
            separators: List of separators to use for splitting
            keep_separator: Whether to keep separators in chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",  # Paragraphs
            "\n",    # Lines
            ". ",    # Sentences
            " ",     # Words
            ""       # Characters
        ]
        self.keep_separator = keep_separator
        
        # Initialize LangChain text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            keep_separator=keep_separator,
            length_function=len,
            is_separator_regex=False
        )
    
    def chunk_text(
        self, 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None,
        model: str = "gpt-3.5-turbo"
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: The text to chunk
            metadata: Optional metadata to include with each chunk
            model: The LLM model to use for token estimation
        
        Returns:
            List of dictionaries containing chunk data and metadata
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        try:
            # Split text using LangChain
            chunks = self.text_splitter.split_text(text)
            
            # Create chunks with metadata
            chunked_data = []
            for i, chunk in enumerate(chunks):
                cleaned_chunk = chunk.strip()
                if cleaned_chunk:  # Skip empty chunks
                    chunk_metadata = {
                        "chunk_index": i,
                        "chunk_size": len(cleaned_chunk),
                        "char_count": len(cleaned_chunk),
                        "word_count": len(cleaned_chunk.split()),
                        "token_count": self.estimate_tokens(cleaned_chunk, model=model),
                        **(metadata or {})
                    }
                    
                    chunked_data.append({
                        "content": cleaned_chunk,
                        "metadata": chunk_metadata
                    })
            
            logger.info(f"Created {len(chunked_data)} chunks from text of length {len(text)}")
            return chunked_data
            
        except (ValueError, TypeError, RuntimeError) as e:
            logger.error(f"Error chunking text: {str(e)}")
            raise ValueError(f"Failed to chunk text: {str(e)}") from e
    
    def chunk_with_semantic_analysis(
        self, 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None,
        model: str = "gpt-3.5-turbo"
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks with semantic analysis (improved chunking).
        
        This method attempts to keep complete paragraphs and sections together.
        """
        if not text or not text.strip():
            return []
        
        try:
            # Split into paragraphs first
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            
            chunks = []
            current_chunk = ""
            
            for paragraph in paragraphs:
                # If adding this paragraph exceeds chunk size, start new chunk
                if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    # Start new chunk with overlap
                    if self.chunk_overlap > 0 and len(current_chunk) > self.chunk_overlap:
                        overlap_text = current_chunk[-self.chunk_overlap:]
                        current_chunk = overlap_text + " " + paragraph
                    else:
                        current_chunk = paragraph
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
            
            # Add the last chunk
            if current_chunk and current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            # Create chunks with metadata
            chunked_data = []
            for i, chunk in enumerate(chunks):
                cleaned_chunk = chunk.strip()
                if cleaned_chunk:
                    chunk_metadata = {
                        "chunk_index": i,
                        "chunk_size": len(cleaned_chunk),
                        "char_count": len(cleaned_chunk),
                        "word_count": len(cleaned_chunk.split()),
                        "token_count": self.estimate_tokens(cleaned_chunk, model=model),
                        **(metadata or {})
                    }
                    
                    chunked_data.append({
                        "content": cleaned_chunk,
                        "metadata": chunk_metadata
                    })
            
            logger.info(f"Created {len(chunked_data)} semantic chunks")
            return chunked_data
            
        except (ValueError, TypeError, RuntimeError) as e:
            logger.error(f"Error in semantic chunking: {str(e)}")
            return self.chunk_text(text, metadata, model=model)
    
    def estimate_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """Estimate the number of tokens in the text."""
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except (LookupError, ValueError):
            # Fallback: approximate tokens (4 chars ≈ 1 token)
            return len(text) // 4
    
    def get_chunk_stats(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the chunks."""
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chunk_size": 0,
                "max_chunk_size": 0,
                "min_chunk_size": 0,
                "total_chars": 0,
                "total_words": 0,
                "total_tokens": 0
            }
        
        sizes = [len(chunk["content"]) for chunk in chunks]
        tokens = [chunk["metadata"].get("token_count", 0) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(sizes) / len(sizes),
            "max_chunk_size": max(sizes),
            "min_chunk_size": min(sizes),
            "total_chars": sum(sizes),
            "total_words": sum([len(chunk["content"].split()) for chunk in chunks]),
            "total_tokens": sum(tokens)
        }
