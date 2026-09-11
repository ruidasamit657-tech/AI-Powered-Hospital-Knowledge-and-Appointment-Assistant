#!/usr/bin/env python3
"""
Ingest knowledge base documents into the vector store.
Run: python scripts/ingest_knowledge_base.py

Required packages (install if missing):
    pip install chromadb sentence-transformers pypdf python-docx markdown
"""

# pylint: disable=wrong-import-position,import-error,no-name-in-module,wrong-import-order

import sys
from pathlib import Path

# Add project root to path BEFORE importing app.*
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Third-party imports must come before first-party imports
import chromadb  # type: ignore[import-not-found]

# First-party imports
from app.core.config import settings
from app.services.document_loader import load_document  # type: ignore[import-not-found]
from app.services.chunking import chunk_text  # type: ignore[import-not-found]
from app.services.embedding import get_embedding  # type: ignore[import-not-found]


def main() -> None:
    """Load documents, chunk them, embed them, and store in ChromaDB."""
    base_dir = Path("data/knowledge_base")
    persist_dir = Path("data/vector_index")
    persist_dir.mkdir(parents=True, exist_ok=True)

    if not base_dir.exists():
        print(f"Knowledge base directory not found: {base_dir}")
        return

    # Initialize ChromaDB persistent client
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection = client.get_or_create_collection(name="hospital_knowledge")

    supported_ext = {".pdf", ".docx", ".txt", ".md"}
    files = [f for f in base_dir.iterdir() if f.suffix.lower() in supported_ext]

    if not files:
        print("No supported documents found in data/knowledge_base/")
        return

    total_chunks = 0
    for file_path in files:
        print(f"Processing {file_path.name} ...")
        try:
            text = load_document(str(file_path))
        except Exception as exc:  # pylint: disable=broad-except
            print(f"  Failed to load: {exc}")
            continue

        chunks = chunk_text(
            text,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP,
        )
        print(f"  Created {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            chunk_id = f"{file_path.stem}_{i}"
            embedding = get_embedding(chunk)
            collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[{"source": file_path.name, "chunk_index": i}],
                documents=[chunk],
            )
            total_chunks += 1

    print(f"\nIngestion complete. Total chunks stored: {total_chunks}")


if __name__ == "__main__":
    main()