"""
Groq LLM provider implementation.
"""

# cspell:ignore groq

from datetime import datetime, timezone
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.core.config import settings
from app.llm.base import LLMProvider


class GroqProvider(LLMProvider):
    """
    LLM provider using Groq API for fast inference.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        **_kwargs
    ):
        """
        Initialize Groq provider.
        
        Args:
            model_name: Groq model to use (default: mixtral-8x7b-32768)
            api_key: Groq API key (defaults to settings.GROQ_API_KEY)
            **kwargs: Additional configuration
        """
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model_name = model_name or "mixtral-8x7b-32768"
        self._client = None
        self._initialized = False
        
        # Available Groq models
        self._available_models = {
            "mixtral-8x7b-32768": "Mistral AI Mixtral 8x7B",
            "llama2-70b-4096": "Meta Llama 2 70B",
            "gemma-7b-it": "Google Gemma 7B",
        }
        
        if model_name and model_name not in self._available_models:
            # Use as is if not in predefined list
            self._available_models[model_name] = model_name
    
    def _initialize_client(self):
        """Initialize the Groq client if API key is available."""
        if not self._initialized and self.is_available():
            try:
                # pylint: disable=import-outside-toplevel
                import groq  # type: ignore
                # pylint: enable=import-outside-toplevel
                
                self._client = groq.Groq(api_key=self.api_key)
                self._initialized = True
            except ImportError:
                print("Groq package not installed. Please install: pip install groq")
                self._initialized = False
            except (OSError, RuntimeError, ValueError) as e:
                print(f"Error initializing Groq client: {e}")
                self._initialized = False
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response using Groq API.
        
        Args:
            prompt: The prompt to send to the LLM
            context: Optional context to include in the prompt
            temperature: Temperature for response generation (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters (top_p, frequency_penalty, etc.)
            
        Returns:
            Dict containing response and metadata
        """
        if not self.is_available():
            return {
                "content": "Groq API is not available. Please check your API key.",
                "error": "GROQ_API_KEY not configured",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "provider": self.get_provider_name()
            }
        
        self._initialize_client()
        if not self._client:
            return {
                "content": "Failed to initialize Groq client.",
                "error": "Client initialization failed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "provider": self.get_provider_name()
            }
        
        try:
            # Build the full prompt with context if provided
            full_prompt = self._build_prompt(prompt, context)
            
            # Prepare parameters
            params = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": full_prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": kwargs.get("top_p", 1.0),
                "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
                "presence_penalty": kwargs.get("presence_penalty", 0.0),
                "stream": False
            }
            
            # Make API call
            response = self._client.chat.completions.create(**params)
            
            return {
                "content": response.choices[0].message.content,
                "sources": kwargs.get("sources", []),
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "mode": "llm",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "provider": self.get_provider_name(),
                "model": self.get_model_name(),
                "finish_reason": response.choices[0].finish_reason
            }
            
        except (OSError, RuntimeError, ValueError) as e:
            return {
                "content": "I encountered an error while processing your request.",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "provider": self.get_provider_name(),
                "model": self.get_model_name()
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
        Stream a response from the Groq API.
        
        Args:
            prompt: The prompt to send to the LLM
            context: Optional context to include in the prompt
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response
            **kwargs: Additional parameters
            
        Yields:
            Chunks of the response
        """
        if not self.is_available():
            yield "Groq API is not available. Please check your API key."
            return
        
        self._initialize_client()
        if not self._client:
            yield "Failed to initialize Groq client."
            return
        
        try:
            # Build the full prompt with context
            full_prompt = self._build_prompt(prompt, context)
            
            # Prepare parameters with streaming enabled
            params = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": full_prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": kwargs.get("top_p", 1.0),
                "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
                "presence_penalty": kwargs.get("presence_penalty", 0.0),
                "stream": True
            }
            
            # Make streaming API call
            stream = self._client.chat.completions.create(**params)
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except (OSError, RuntimeError, ValueError) as e:
            yield f"\n\n*Error: {str(e)}*"
    
    def get_provider_name(self) -> str:
        return "Groq"
    
    def is_available(self) -> bool:
        """Check if Groq API is available."""
        return bool(self.api_key)
    
    def get_model_name(self) -> str:
        return self.model_name
    
    def get_available_models(self) -> List[str]:
        """Get list of available Groq models."""
        return list(self._available_models.keys())
    
    def _get_system_prompt(self) -> str:
        """Get default system prompt for the hospital AI assistant."""
        return (
            "You are a helpful, professional hospital AI assistant. "
            "Use the provided context to answer user queries accurately. "
            "If you do not know the answer, state that you don't know."
        )
    
    def _build_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Build the full prompt with context.
        """
        if context:
            if isinstance(context, (list, dict)):
                context_str = json.dumps(context, indent=2)
            else:
                context_str = str(context)
            return f"Context:\n{context_str}\n\nQuestion: {prompt}"
        return prompt
