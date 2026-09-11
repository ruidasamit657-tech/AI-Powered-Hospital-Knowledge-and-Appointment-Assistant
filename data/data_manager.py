"""
Data manager for handling file operations across data directories.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from app.core.logging import logger

# Fix for Pylint E0401/E0611 & Pylance reportMissingImports: Added type ignore for static analyzers
try:
    from app.data import KNOWLEDGE_BASE_DIR, STORAGE_DIR, VECTOR_INDEX_DIR  # type: ignore
except (ImportError, ModuleNotFoundError):
    import os
    logger.warning("Could not import from 'app.data'. Falling back to environment variables or local paths.")
    # Reads environment variables if set by your runtime setup, otherwise builds safe local defaults
    KNOWLEDGE_BASE_DIR = os.getenv("KNOWLEDGE_BASE_DIR", "data/knowledge_base")
    STORAGE_DIR = os.getenv("STORAGE_DIR", "data/storage")
    VECTOR_INDEX_DIR = os.getenv("VECTOR_INDEX_DIR", "data/vector_index")


class DataManager:
    """Manages file operations across all data directories."""

    def __init__(self) -> None:
        # Wrap constants with Path to enforce type safety for pathlib methods
        self.knowledge_base_dir = Path(KNOWLEDGE_BASE_DIR)
        self.storage_dir = Path(STORAGE_DIR)
        self.vector_index_dir = Path(VECTOR_INDEX_DIR)

        # Ensure all directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for directory in [
            self.knowledge_base_dir,
            self.storage_dir,
            self.vector_index_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")

    # --- Knowledge Base Operations ---

    def save_document(
        self, content: bytes, filename: str, document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save a document to the knowledge base.

        Args:
            content: File content as bytes
            filename: Original filename
            document_id: Optional document ID (generated if not provided)

        Returns:
            Dictionary with file information
        """
        doc_id = document_id or str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = Path(filename).suffix

        # Create safe filename
        safe_filename = f"{doc_id}_{timestamp}_{Path(filename).stem}{extension}"
        file_path = self.knowledge_base_dir / safe_filename

        # Save file
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Saved document: {safe_filename} ({len(content)} bytes)")

        return {
            "id": doc_id,
            "filename": filename,
            "safe_filename": safe_filename,
            "file_path": str(file_path),
            "file_size": len(content),
            "extension": extension,
            "timestamp": timestamp,
        }

    def get_document(self, document_id: str) -> Optional[Path]:
        """Get a document by ID.

        Args:
            document_id: Document ID

        Returns:
            Path to the document or None if not found
        """
        # Search for document with this ID
        for file_path in self.knowledge_base_dir.iterdir():
            if file_path.is_file() and file_path.name.startswith(document_id):
                return file_path

        logger.warning(f"Document not found: {document_id}")
        return None

    def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID.

        Args:
            document_id: Document ID

        Returns:
            True if deleted successfully
        """
        file_path = self.get_document(document_id)
        if file_path and file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted document: {document_id}")
            return True

        logger.warning(f"Document not found for deletion: {document_id}")
        return False

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the knowledge base.

        Returns:
            List of document information dictionaries
        """
        documents = []

        for file_path in self.knowledge_base_dir.iterdir():
            if file_path.is_file() and not file_path.name.startswith("."):
                # Parse document info from filename safely
                parts = file_path.stem.split("_")
                document_id = parts[0] if parts else None
                timestamp = parts[1] if len(parts) > 1 else None
                original_name = (
                    "_".join(parts[2:]) if len(parts) > 2 else file_path.stem
                )

                # st_mtime represents modification time reliably across systems
                stat_result = file_path.stat()
                created_at = datetime.fromtimestamp(
                    stat_result.st_mtime
                ).isoformat()

                documents.append(
                    {
                        "id": document_id,
                        "filename": f"{original_name}{file_path.suffix}",
                        "safe_filename": file_path.name,
                        "file_path": str(file_path),
                        "file_size": stat_result.st_size,
                        "extension": file_path.suffix,
                        "timestamp": timestamp,
                        "created_at": created_at,
                    }
                )

        return sorted(
            documents, key=lambda x: x.get("created_at", ""), reverse=True
        )

    def get_document_count(self) -> int:
        """Get the total number of documents in the knowledge base."""
        return sum(
            1
            for item in self.knowledge_base_dir.iterdir()
            if item.is_file() and not item.name.startswith(".")
        )

    # --- Storage Operations ---

    def save_to_storage(
        self, content: bytes, filename: str, prefix: str = "temp"
    ) -> Dict[str, Any]:
        """Save a file to temporary storage.

        Args:
            content: File content as bytes
            filename: Original filename
            prefix: Prefix for the temporary file

        Returns:
            Dictionary with file information
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_id = str(uuid.uuid4())[:8]
        safe_filename = f"{prefix}_{timestamp}_{temp_id}_{Path(filename).name}"
        file_path = self.storage_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(content)

        logger.debug(f"Saved to storage: {safe_filename}")

        return {
            "filename": safe_filename,
            "file_path": str(file_path),
            "file_size": len(content),
        }

    def get_from_storage(self, filename: str) -> Optional[Path]:
        """Get a file from storage by filename."""
        file_path = self.storage_dir / filename
        return file_path if file_path.exists() else None

    def delete_from_storage(self, filename: str) -> bool:
        """Delete a file from storage."""
        file_path = self.storage_dir / filename
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"Deleted from storage: {filename}")
            return True
        return False

    def clear_storage(self, older_than_hours: int = 24) -> int:
        """Clear temporary storage files older than specified hours.

        Args:
            older_than_hours: Delete files older than this many hours

        Returns:
            Number of files deleted
        """
        deleted_count = 0
        current_time = datetime.now()

        for file_path in self.storage_dir.iterdir():
            if file_path.is_file():
                file_age = current_time - datetime.fromtimestamp(
                    file_path.stat().st_mtime
                )
                if file_age.total_seconds() > older_than_hours * 3600:
                    file_path.unlink()
                    deleted_count += 1

        if deleted_count > 0:
            logger.info(f"Cleared {deleted_count} files from storage")

        return deleted_count

    # --- Vector Index Operations ---

    def get_vector_index_path(self) -> Path:
        """Get the path to the vector index directory."""
        return self.vector_index_dir

    def get_vector_index_size(self) -> int:
        """Get the total size of the vector index in bytes."""
        total_size = 0
        for item in self.vector_index_dir.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
        return total_size

    def clear_vector_index(self) -> int:
        """Clear the entire vector index.

        Returns:
            Number of files deleted
        """
        deleted_count = 0
        for item in self.vector_index_dir.rglob("*"):
            if item.is_file():
                item.unlink()
                deleted_count += 1

        logger.info(f"Cleared {deleted_count} files from vector index")
        return deleted_count
