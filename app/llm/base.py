from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class LLMProvider(ABC):
    """Base abstract class for all LLM providers."""
    
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            context: Optional context to include in the prompt
            temperature: Temperature for response generation (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dict containing response and metadata
        """
        raise NotImplementedError
    
    @abstractmethod
    async def stream_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        """
        Stream a response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            context: Optional context to include in the prompt
            temperature: Temperature for response generation (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Chunks of the response
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the LLM provider."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured."""

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the name of the model being used."""

    async def generate_with_retry(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response with retry logic.
        
        Args:
            prompt: The prompt to send to the LLM
            context: Optional context to include in the prompt
            max_retries: Maximum number of retry attempts
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dict containing response and metadata
        """
        import asyncio
        from datetime import datetime
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = await self.generate_response(
                    prompt=prompt,
                    context=context,
                    **kwargs
                )
                return response
            except (ConnectionError, OSError, RuntimeError, TimeoutError, ValueError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    await asyncio.sleep(wait_time)
                continue
        
        # If all retries failed
        return {
            "content": "I apologize, but I'm having trouble generating a response. Please try again later.",
            "error": str(last_error) if last_error else "Unknown error",
            "timestamp": datetime.utcnow().isoformat(),
            "provider": self.get_provider_name()
        }