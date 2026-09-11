from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
import asyncio
import json

from app.llm.base import LLMProvider
from app.services.retriever import Retriever
from app.services.promt_builder import PromptBuilder

class RetrievalOnlyProvider(LLMProvider):
    """
    LLM provider that returns only retrieved context without generating new text.
    Useful for testing and when no LLM API is available.
    """
    
    def __init__(self, **_kwargs):
        self._retriever = Retriever()
        self._prompt_builder = PromptBuilder()
        self._model_name = "retrieval-only"
        
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response by retrieving relevant context and formatting it.
        
        Args:
            prompt: The user's question
            context: Optional pre-retrieved context
            temperature: Ignored for retrieval-only
            max_tokens: Ignored for retrieval-only
            **kwargs: Additional parameters
            
        Returns:
            Dict containing the retrieved context as response
        """
        try:
            # Retrieve relevant chunks
            if context is None:
                # Extract query from prompt
                query = self._extract_query(prompt)
                retrieved_chunks = await self._retriever.retrieve(
                    query=query,
                    top_k=kwargs.get("top_k", 5)
                )
            else:
                # Use provided context
                retrieved_chunks = json.loads(context) if isinstance(context, str) else context
            
            # Format response
            sources = self._format_sources(retrieved_chunks)
            response_text = self._format_response(retrieved_chunks, prompt)
            
            return {
                "content": response_text,
                "sources": sources,
                "mode": "retrieval_only",
                "timestamp": datetime.utcnow().isoformat(),
                "provider": self.get_provider_name(),
                "model": self.get_model_name(),
                "chunks_retrieved": len(retrieved_chunks) if retrieved_chunks else 0
            }
            
        except (OSError, RuntimeError, TypeError, ValueError) as e:
            return {
                "content": "I encountered an error while retrieving information.",
                "sources": [],
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "provider": self.get_provider_name()
            }
    
    async def stream_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream the response by yielding chunks.
        For retrieval-only, we yield the complete response at once.
        """
        response = await self.generate_response(
            prompt=prompt,
            context=context,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Split response into chunks and yield them
        content = response.get("content", "")
        chunk_size = 50
        for i in range(0, len(content), chunk_size):
            yield content[i:i + chunk_size]
            await asyncio.sleep(0.05)  # Simulate streaming delay
    
    def get_provider_name(self) -> str:
        return "Retrieval-Only Provider"
    
    def is_available(self) -> bool:
        """Always available since it doesn't require external APIs."""
        return True
    
    def get_model_name(self) -> str:
        return self._model_name
    
    def _extract_query(self, prompt: str) -> str:
        """
        Extract the actual query from the prompt.
        Handles different prompt formats.
        """
        # If prompt contains a question, extract it
        # Simple extraction: remove system instructions if present
        lines = prompt.strip().split('\n')
        for line in reversed(lines):
            if '?' in line or '?' in line:
                return line.strip()
        
        # If no question mark found, return the last line
        return lines[-1].strip() if lines else prompt
    
    def _format_sources(self, chunks: list) -> list:
        """
        Format retrieved chunks as sources for the response.
        """
        sources = []
        seen_docs = set()
        
        for chunk in chunks:
            doc_id = chunk.get("metadata", {}).get("document_id", "")
            if doc_id and doc_id not in seen_docs:
                seen_docs.add(doc_id)
                sources.append({
                    "document_id": doc_id,
                    "title": chunk.get("metadata", {}).get("title", "Unknown Document"),
                    "content": chunk.get("content", "")[:200] + "...",
                    "relevance_score": chunk.get("score", 0.0)
                })
        
        return sources[:3]  # Limit to top 3 sources
    
    def _format_response(self, chunks: list, _original_prompt: str) -> str:
        """
        Format the retrieved chunks into a readable response.
        """
        if not chunks:
            return "I couldn't find relevant information in the knowledge base to answer your question."
        
        response = "Based on the hospital's knowledge base, here's what I found:\n\n"
        
        for i, chunk in enumerate(chunks[:3], 1):
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
            source = metadata.get("title", f"Document {i}")
            
            response += f"**Source {i}: {source}**\n"
            response += f"{content[:300]}...\n\n"
        
        response += "\n*This response is based on the hospital's official knowledge base documents.*"
        
        return response