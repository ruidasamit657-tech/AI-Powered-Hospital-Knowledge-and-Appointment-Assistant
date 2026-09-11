from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.core.logging import get_logger
from app.services.retriever import Retriever
from app.services.promt_builder import PromptBuilder
from app.services.medical_guard import MedicalGuard
from app.services.emergency_guard import EmergencyGuard
from app.llm.factory import LLMFactory

logger = get_logger(__name__)

class RAGService:
    """Main RAG (Retrieval-Augmented Generation) service."""
    
    def __init__(
        self,
        retriever: Optional[Retriever] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        medical_guard: Optional[MedicalGuard] = None,
        emergency_guard: Optional[EmergencyGuard] = None
    ):
        """
        Initialize the RAG service.
        
        Args:
            retriever: Retriever instance for document retrieval
            prompt_builder: Prompt builder instance
            medical_guard: Medical guard for safety checks
            emergency_guard: Emergency guard for detecting emergencies
        """
        self.retriever = retriever or Retriever()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.medical_guard = medical_guard or MedicalGuard()
        self.emergency_guard = emergency_guard or EmergencyGuard()
        self.llm_factory = LLMFactory()
        
        logger.info("Initialized RAG Service")
    
    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
        mode: str = "rag"
    ) -> Dict[str, Any]:
        """
        Process a query using RAG pipeline.
        
        Args:
            query: User query
            session_id: Session ID for chat history
            top_k: Number of documents to retrieve
            mode: Processing mode (rag, retrieval_only, llm)
        
        Returns:
            Dictionary with response, sources, and metadata
        """
        logger.debug("Processing query for session %s", session_id)
        try:
            # 1. Emergency check
            emergency_check = self.emergency_guard.check_emergency(query)
            if emergency_check["is_emergency"]:
                return {
                    "response": emergency_check["response"],
                    "sources": [],
                    "mode": "emergency",
                    "emergency_type": emergency_check["type"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # 2. Medical safety check
            safety_check = self.medical_guard.check_safety(query)
            if not safety_check["is_safe"]:
                return {
                    "response": safety_check["response"],
                    "sources": [],
                    "mode": "safety",
                    "safety_warnings": safety_check["warnings"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # 3. Retrieve relevant documents
            retrieved_docs = []
            if mode != "llm":
                retrieved_docs = self.retriever.retrieve(
                    query=query,
                    top_k=top_k,
                    min_score=0.3
                )
                logger.info(f"Retrieved {len(retrieved_docs)} documents")
            
            # 4. Process based on mode
            if mode == "retrieval_only":
                # Return only retrieved documents
                return {
                    "response": self._format_retrieval_response(retrieved_docs),
                    "sources": retrieved_docs,
                    "mode": "retrieval_only",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            elif mode == "llm":
                # Use LLM without retrieval
                response = await self._generate_llm_response(
                    query=query,
                    context=[],
                    use_rag=False
                )
                return {
                    "response": response,
                    "sources": [],
                    "mode": "llm",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            else:  # rag mode
                # Use RAG with LLM
                response, sources = await self._generate_rag_response(
                    query=query,
                    documents=retrieved_docs
                )
                
                return {
                    "response": response,
                    "sources": sources,
                    "mode": "rag",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except (RuntimeError, TypeError, ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "sources": [],
                "mode": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _generate_rag_response(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Generate response using RAG.
        
        Args:
            query: User query
            documents: Retrieved documents
        
        Returns:
            Tuple of (response, sources)
        """
        try:
            # Prepare context
            context = []
            for doc in documents[:3]:  # Limit context size
                context.append({
                    "content": doc.get("content", ""),
                    "metadata": doc.get("metadata", {}),
                    "score": doc.get("score", 0)
                })
            
            # Build prompt
            prompt = self.prompt_builder.build_rag_prompt(
                query=query,
                context=context
            )
            
            # Generate response using LLM
            response = await self._generate_with_llm(prompt)
            
            # Extract sources
            sources = []
            for doc in documents[:3]:
                if doc.get("content"):
                    sources.append({
                        "content": doc["content"][:500],  # Truncate for display
                        "metadata": doc.get("metadata", {}),
                        "score": doc.get("score", 0)
                    })
            
            return response, sources
            
        except (RuntimeError, TypeError, ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error in RAG generation: {str(e)}")
            return "I apologize, but I encountered an error generating a response. Please try again.", []
    
    async def _generate_llm_response(
        self,
        query: str,
        context: List[Dict[str, Any]] = None,
        use_rag: bool = False
    ) -> str:
        """Generate response using LLM."""
        try:
            if use_rag and context:
                prompt = self.prompt_builder.build_rag_prompt(query, context)
            else:
                prompt = self.prompt_builder.build_llm_prompt(query)
            
            response = await self._generate_with_llm(prompt)
            return response
            
        except (RuntimeError, TypeError, ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error in LLM generation: {str(e)}")
            return "I apologize, but I encountered an error generating a response."
    
    async def _generate_with_llm(self, prompt: str) -> str:
        """Generate response using LLM provider."""
        try:
            # Get LLM provider
            llm_provider = self.llm_factory.get_default_provider()
            
            # Generate response
            response = await llm_provider.generate_response(prompt)
            
            return response
            
        except (RuntimeError, TypeError, ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error generating with LLM: {str(e)}")
            raise
    
    def _format_retrieval_response(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieval-only response."""
        if not documents:
            return "No relevant documents found."
        
        response = "Here are the relevant documents I found:\n\n"
        for i, doc in enumerate(documents[:3], 1):
            content = doc.get("content", "")
            if content:
                response += f"{i}. {content[:300]}...\n\n"
        
        return response
    
    async def stream_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 5
    ):
        """
        Stream processing of a query for real-time responses.
        
        Yields:
            Streaming responses with status updates
        """
        logger.debug("Streaming query for session %s", session_id)
        try:
            # 1. Emergency check
            yield {"status": "checking_emergency"}
            emergency_check = self.emergency_guard.check_emergency(query)
            if emergency_check["is_emergency"]:
                yield {
                    "status": "emergency",
                    "response": emergency_check["response"],
                    "emergency_type": emergency_check["type"]
                }
                return
            
            # 2. Medical safety check
            yield {"status": "checking_safety"}
            safety_check = self.medical_guard.check_safety(query)
            if not safety_check["is_safe"]:
                yield {
                    "status": "safety_warning",
                    "response": safety_check["response"],
                    "warnings": safety_check["warnings"]
                }
                return
            
            # 3. Retrieval
            yield {"status": "retrieving_documents"}
            retrieved_docs = self.retriever.retrieve(
                query=query,
                top_k=top_k,
                min_score=0.3
            )
            
            yield {
                "status": "documents_retrieved",
                "count": len(retrieved_docs)
            }
            
            # 4. Generate response
            yield {"status": "generating_response"}
            response, sources = await self._generate_rag_response(
                query=query,
                documents=retrieved_docs
            )
            
            # 5. Return final response
            yield {
                "status": "complete",
                "response": response,
                "sources": sources,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except (RuntimeError, TypeError, ValueError, KeyError, AttributeError) as e:
            logger.error(f"Error in stream query: {str(e)}")
            yield {
                "status": "error",
                "error": str(e),
                "response": "I apologize, but I encountered an error processing your request."
            }