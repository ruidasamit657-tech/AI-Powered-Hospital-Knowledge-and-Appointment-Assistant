from typing import Optional, Dict, Type
from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.retrieval_only import RetrievalOnlyProvider
from app.llm.groq_provider import GroqProvider

class LLMFactory:
    """Factory class for creating LLM providers."""
    
    _providers = {
        "retrieval_only": RetrievalOnlyProvider,
        "groq": GroqProvider,
    }
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[LLMProvider]):
        """Register a new LLM provider."""
        cls._providers[name] = provider_class
    
    @classmethod
    def create_provider(
        cls,
        provider_type: str = "groq",
        model_name: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """
        Create an LLM provider instance.
        
        Args:
            provider_type: Type of provider ('groq', 'retrieval_only', etc.)
            model_name: Specific model name to use
            **kwargs: Additional provider-specific configuration
            
        Returns:
            LLMProvider instance
            
        Raises:
            ValueError: If provider_type is not registered
        """
        if provider_type not in cls._providers:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        provider_class = cls._providers[provider_type]
        
        # If provider is retrieval_only, it doesn't need an API key
        if provider_type == "retrieval_only":
            return provider_class(**kwargs)
        
        # For other providers, check if they're available
        try:
            provider = provider_class(model_name=model_name, **kwargs)
            if not provider.is_available():
                # Fallback to retrieval_only if provider is not available
                print(f"Warning: {provider_type} provider not available. Falling back to retrieval_only.")
                return cls._providers["retrieval_only"]()
            return provider
        except (ImportError, OSError, RuntimeError, TypeError, ValueError) as e:
            print(f"Error creating {provider_type} provider: {e}")
            # Fallback to retrieval_only
            return cls._providers["retrieval_only"]()
    
    @classmethod
    def get_default_provider(cls) -> LLMProvider:
        """Get the default LLM provider based on configuration."""
        # Check for Groq API key first
        if settings.GROQ_API_KEY:
            return cls.create_provider("groq")
        # Fallback to retrieval-only
        return cls.create_provider("retrieval_only")
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, bool]:
        """Get all available providers and their availability status."""
        available = {}
        for name, provider_class in cls._providers.items():
            try:
                provider = provider_class()
                available[name] = provider.is_available()
            except (ImportError, OSError, RuntimeError, TypeError, ValueError):
                available[name] = False
        return available

    _instance: Optional["LLMFactory"] = None

    @classmethod
    def get_instance(cls) -> "LLMFactory":
        """Get the singleton factory instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def get_llm_factory() -> LLMFactory:
    """Get a singleton instance of LLMFactory."""
    return LLMFactory.get_instance()
