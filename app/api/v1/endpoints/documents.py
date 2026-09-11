from datetime import datetime
from pathlib import Path
from typing import List, Optional
import hashlib
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_staff_user, get_db
from app.core.config import settings
from app.services.document_loader import DocumentLoader
from app.services.chunking import TextChunker
from app.db.models.knowledge_document import KnowledgeDocument
from app.db.schemas.document import DocumentResponse

router = APIRouter()
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _get_document(db: Session, document_id: int) -> KnowledgeDocument:
    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_indexed: Optional[bool] = None,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_staff_user),
):
    query = db.query(KnowledgeDocument)
    if is_indexed is not None:
        query = query.filter(KnowledgeDocument.is_indexed == is_indexed)
    return query.order_by(KnowledgeDocument.uploaded_at.desc()).offset(skip).limit(limit).all()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_staff_user),
):
    return _get_document(db, document_id)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_staff_user),
):
    filename = file.filename or "uploaded-file"
    extension = Path(filename).suffix.lower()
    if extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not allowed")

    stored_name = f"{uuid.uuid4()}_{Path(filename).name}"
    file_path = UPLOAD_DIR / stored_name
    file_size = 0
    digest = hashlib.sha256()
    with file_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            file_size += len(chunk)
            if file_size > settings.MAX_UPLOAD_SIZE:
                file_path.unlink(missing_ok=True)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is too large")
            digest.update(chunk)
            buffer.write(chunk)

    try:
        content = DocumentLoader.extract_text(file_path.read_bytes(), extension)
    except (OSError, ValueError) as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to extract text: {exc}") from exc

    document = KnowledgeDocument(
        filename=stored_name,
        original_filename=filename,
        file_type=file.content_type,
        file_size=file_size,
        file_hash=digest.hexdigest(),
        title=title or filename,
        description=content[:5000],
        document_metadata={"path": str(file_path)},
        uploaded_by=current_user.get("sub"),
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.post("/{document_id}/index", response_model=DocumentResponse)
async def index_document(
    document_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_staff_user),
):
    document = _get_document(db, document_id)
    path = (document.document_metadata or {}).get("path")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stored document file not found")
    file_extension = Path(path).suffix.lower()
    try:
        content = DocumentLoader.extract_text(Path(path).read_bytes(), file_extension)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to extract text: {exc}") from exc

    chunks = TextChunker().chunk_text(content, metadata={"document_id": document.id})
    document.chunk_count = len(chunks)
    document.is_indexed = True
    document.indexed_at = datetime.utcnow()
    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_staff_user),
):
    document = _get_document(db, document_id)
    path = (document.document_metadata or {}).get("path")
    if path:
        Path(path).unlink(missing_ok=True)
    db.delete(document)
    db.commit()