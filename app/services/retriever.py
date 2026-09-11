from typing import List, Dict, Any, Optional

from app.core.logging import get_logger
from app.services.vector_store import VectorStore
from app.services.embedding import EmbeddingService

logger = get_logger(__name__)

class Retriever:
    """Handles document retrieval with advanced search strategies."""
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        default_top_k: int = 5
    ):
        """
        Initialize the retriever.
        
        Args:
            vector_store: Vector store instance
            embedding_service: Embedding service instance
            default_top_k: Default number of results to return
        """
        self.vector_store = vector_store or VectorStore()
        self.embedding_service = embedding_service or EmbeddingService()
        self.default_top_k = default_top_k
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0,
        diversity: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Query text
            top_k: Number of results to return
            filter_metadata: Metadata filter
            min_score: Minimum similarity score
            diversity: Whether to apply diversity reranking
        
        Returns:
            List of retrieved documents
        """
        if not query or not query.strip():
            return []
        
        try:
            top_k = top_k or self.default_top_k
            
            # Get results from vector store
            results = self.vector_store.search(
                query=query,
                top_k=top_k * 2 if diversity else top_k,
                filter_metadata=filter_metadata
            )
            
            # Apply min score filter
            if min_score > 0:
                results = [r for r in results if r.get('score', 1.0) <= min_score]
            
            # Apply diversity if requested
            if diversity and len(results) > top_k:
                results = self._rerank_with_diversity(results, top_k)
            else:
                results = results[:top_k]
            
            logger.info(f"Retrieved {len(results)} documents for query")
            return results
            
        except (KeyError, TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []
    
    def retrieve_by_embedding(
        self,
        embedding: List[float],
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve documents using an embedding vector."""
        try:
            top_k = top_k or self.default_top_k
            results = self.vector_store.search_by_embedding(
                embedding=embedding,
                top_k=top_k,
                filter_metadata=filter_metadata
            )
            logger.info(f"Retrieved {len(results)} documents by embedding")
            return results
        except (KeyError, TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Error retrieving by embedding: {str(e)}")
            return []
    
    def retrieve_with_context(
        self,
        query: str,
        top_k: int = 5,
        context_window: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents with context window around each result.
        
        This is useful for getting more context around the retrieved chunks.
        """
        try:
            # Get initial results
            results = self.retrieve(query, top_k=top_k * 2)
            
            if not results:
                return []
            
            # Group results by document
            doc_chunks = {}
            for result in results:
                doc_id = result.get('metadata', {}).get('document_id')
                if doc_id:
                    if doc_id not in doc_chunks:
                        doc_chunks[doc_id] = []
                    doc_chunks[doc_id].append(result)
            
            # Add context chunks
            expanded_results = []
            for doc_id, chunks in doc_chunks.items():
                # Sort by chunk index
                chunks.sort(key=lambda x: x.get('metadata', {}).get('chunk_index', 0))
                
                # Get relevant chunks with context
                for i, chunk in enumerate(chunks):
                    context_chunks = []
                    
                    # Add previous chunks
                    for j in range(max(0, i - context_window), i):
                        if j < len(chunks):
                            context_chunks.append(chunks[j])
                    
                    context_chunks.append(chunk)
                    
                    # Add next chunks
                    for j in range(i + 1, min(i + context_window + 1, len(chunks))):
                        context_chunks.append(chunks[j])
                    
                    # Create combined result
                    combined_content = "\n\n".join([c['content'] for c in context_chunks])
                    expanded_results.append({
                        'id': chunk['id'],
                        'content': combined_content,
                        'metadata': {
                            **chunk.get('metadata', {}),
                            'context_size': len(context_chunks),
                            'original_chunk_index': i
                        },
                        'score': chunk.get('score', 0)
                    })
            
            # Sort by score and limit
            expanded_results.sort(key=lambda x: x.get('score', 1.0))
            return expanded_results[:top_k]
            
        except (KeyError, TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Error retrieving with context: {str(e)}")
            return self.retrieve(query, top_k=top_k)
    
    def _rerank_with_diversity(
        self,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Rerank results to increase diversity."""
        if len(results) <= top_k:
            return results
        
        try:
            # Get embeddings for all results
            contents = [r['content'] for r in results]
            embeddings = self.embedding_service.generate_embeddings(contents)
            
            # MMR (Maximum Marginal Relevance) style reranking
            selected = []
            remaining = list(range(len(results)))
            
            while len(selected) < top_k and remaining:
                best_score = -float('inf')
                best_idx = -1
                
                for idx in remaining:
                    # Relevance score (lower is better in ChromaDB)
                    relevance = results[idx].get('score', 1.0)
                    
                    # Diversity score (higher is better)
                    diversity = 0
                    if selected:
                        max_similarity = max([
                            self.embedding_service.compute_similarity(
                                embeddings[idx],
                                embeddings[sel_idx]
                            )
                            for sel_idx in selected
                        ])
                        diversity = 1 - max_similarity
                    else:
                        diversity = 1
                    
                    # Combined score (lambda = 0.7 for relevance, 0.3 for diversity)
                    combined = 0.7 * (1 - relevance) + 0.3 * diversity
                    
                    if combined > best_score:
                        best_score = combined
                        best_idx = idx
                
                selected.append(best_idx)
                remaining.remove(best_idx)
            
            return [results[i] for i in selected]
            
        except (KeyError, TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Error in diversity reranking: {str(e)}")
            return results[:top_k]
    
    def get_relevant_sources(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Get relevant sources with minimal processing."""
        results = self.retrieve(query, top_k=top_k)
        
        sources = []
        for result in results:
            source = {
                'content': result.get('content', ''),
                'score': result.get('score', 0),
                'source': result.get('metadata', {}).get('source', 'Unknown'),
                'document_id': result.get('metadata', {}).get('document_id', ''),
                'chunk_index': result.get('metadata', {}).get('chunk_index', 0)
            }
            sources.append(source)
        
        return sources