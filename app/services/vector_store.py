"""Vector storage and retrieval utilities for hospital knowledge."""

import importlib
import os
import uuid
from typing import List, Dict, Any, Optional

chromadb = importlib.import_module("chromadb")

from app.core.config import settings
from app.core.logging import get_logger
from app.services.embedding import EmbeddingService

logger = get_logger(__name__)

class VectorStore:
    """Handles vector storage and retrieval using ChromaDB."""
    
    def __init__(
        self,
        collection_name: str = "hospital_knowledge",
        persist_directory: str = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        """
        Initialize vector store.
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist vector data
            embedding_service: Custom embedding service (if None, creates default)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or settings.VECTOR_STORE_DIR
        
        # Create persist directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize embedding service
        self.embedding_service = embedding_service or EmbeddingService()
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory
        )
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
        
        logger.info(f"Initialized vector store: {collection_name} at {self.persist_directory}")
    
    def _get_or_create_collection(self) -> Any:
        """Get existing collection or create a new one."""
        try:
            # Check if collection exists
            collections = self.client.list_collections()
            collection_names = [c.name for c in collections]
            
            if self.collection_name in collection_names:
                collection = self.client.get_collection(self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            else:
                # Create new collection
                collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
            
            return collection
        except (TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Error accessing collection: {str(e)}")
            raise
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
        batch_size: int = 100
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document dictionaries with 'content' and 'metadata'
            ids: Optional list of document IDs
            batch_size: Batch size for processing
        
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        try:
            # Extract contents and metadata
            contents = [doc.get("content", "") for doc in documents]
            metadata_list = [doc.get("metadata", {}) for doc in documents]
            
            # Filter out empty documents
            valid_indices = [i for i, content in enumerate(contents) if content and content.strip()]
            if not valid_indices:
                logger.warning("No valid documents to add")
                return []
            
            # Filter contents and metadata
            filtered_contents = [contents[i] for i in valid_indices]
            filtered_metadata = [metadata_list[i] for i in valid_indices]
            
            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in filtered_contents]
            else:
                ids = [ids[i] for i in valid_indices]
            
            # Generate embeddings in batches
            all_embeddings = []
            for i in range(0, len(filtered_contents), batch_size):
                batch = filtered_contents[i:i + batch_size]
                batch_embeddings = self.embedding_service.generate_embeddings(batch)
                all_embeddings.extend(batch_embeddings)
            
            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                documents=filtered_contents,
                embeddings=all_embeddings,
                metadatas=filtered_metadata
            )
            
            logger.info(f"Added {len(ids)} documents to vector store")
            return ids
            
        except (TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise ValueError(f"Failed to add documents: {str(e)}") from e
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Query text
            top_k: Number of results to return
            filter_metadata: Metadata filter for search
        
        Returns:
            List of search results with content, metadata, and score
        """
        if not query or not query.strip():
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_query_embedding(query)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata
            )
            
            # Format results
            formatted_results = []
            if results and results.get('ids') and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = {
                        "id": results['ids'][0][i],
                        "content": results['documents'][0][i] if results.get('documents') else "",
                        "metadata": results['metadatas'][0][i] if results.get('metadatas') else {},
                        "score": results['distances'][0][i] if results.get('distances') else 0
                    }
                    formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} results for query")
            return formatted_results
            
        except (TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []
    
    def search_by_embedding(
        self,
        embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search using an embedding vector directly."""
        try:
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where=filter_metadata
            )
            
            formatted_results = []
            if results and results.get('ids') and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = {
                        "id": results['ids'][0][i],
                        "content": results['documents'][0][i] if results.get('documents') else "",
                        "metadata": results['metadatas'][0][i] if results.get('metadatas') else {},
                        "score": results['distances'][0][i] if results.get('distances') else 0
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except (TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Error searching by embedding: {str(e)}")
            return []
    
    def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents from the vector store."""
        try:
            self.collection.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents")
            return True
        except (TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Error deleting documents: {str(e)}")
            return False
    
    def delete_collection(self) -> bool:
        """Delete the entire collection."""
        try:
            self.client.delete_collection(self.collection_name)
            # Recreate collection
            self.collection = self._get_or_create_collection()
            logger.info(f"Deleted collection: {self.collection_name}")
            return True
        except (TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Error deleting collection: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory,
                "embedding_model": self.embedding_service.get_model_info()
            }
        except (TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}
    
    def clear_collection(self) -> bool:
        """Clear all documents from the collection."""
        try:
            # Get all IDs
            all_ids = self.collection.get()['ids']
            if all_ids:
                self.collection.delete(ids=all_ids)
                logger.info(f"Cleared {len(all_ids)} documents from collection")
            else:
                logger.info("Collection was already empty")
            return True
        except (TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Error clearing collection: {str(e)}")
            return False