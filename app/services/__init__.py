"""Application services.

Services are imported lazily so importing one lightweight service does not
require every optional AI/vector-store dependency to be installed.
"""

from importlib import import_module

_SERVICE_MODULES = {
    "DocumentLoader": ".document_loader",
    "TextChunker": ".chunking",
    "EmbeddingService": ".embedding",
    "VectorStore": ".vector_store",
    "Retriever": ".retriever",
    "PromptBuilder": ".promt_builder",
    "RAGService": ".rag_service",
    "ChatService": ".chat_service",
    "MedicalGuard": ".medical_guard",
    "EmergencyGuard": ".emergency_guard",
}


def __getattr__(name: str):
    """Load a service only when it is requested."""
    module_name = _SERVICE_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_name, __name__)
    service = getattr(module, name)
    globals()[name] = service
    return service
