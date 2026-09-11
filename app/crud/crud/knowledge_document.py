from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from app.crud.crud.base import CRUDBase
from app.db.models.knowledge_document import KnowledgeDocument
from app.db.models.knowledge_chunk import KnowledgeChunk

class CRUDKnowledgeDocument(CRUDBase[KnowledgeDocument, BaseModel, BaseModel]):
    def get_by_filename(self, db: Session, *, filename: str) -> Optional[KnowledgeDocument]:
        return db.query(KnowledgeDocument).filter(KnowledgeDocument.filename == filename).first()

    def get_by_uploader(self, db: Session, *, uploader_id: str) -> List[KnowledgeDocument]:
        return db.query(KnowledgeDocument).filter(
            KnowledgeDocument.uploaded_by == uploader_id
        ).order_by(KnowledgeDocument.uploaded_at.desc()).all()

    def get_indexed_documents(self, db: Session) -> List[KnowledgeDocument]:
        return db.query(KnowledgeDocument).filter(
            KnowledgeDocument.is_indexed == True
        ).all()

    def get_unindexed_documents(self, db: Session) -> List[KnowledgeDocument]:
        return db.query(KnowledgeDocument).filter(
            KnowledgeDocument.is_indexed == False
        ).all()

    def search_documents(self, db: Session, *, search_term: str) -> List[KnowledgeDocument]:
        return db.query(KnowledgeDocument).filter(
            or_(
                KnowledgeDocument.title.ilike(f"%{search_term}%"),
                KnowledgeDocument.filename.ilike(f"%{search_term}%"),
                KnowledgeDocument.description.ilike(f"%{search_term}%")
            )
        ).all()

    def mark_as_indexed(self, db: Session, *, document_id: str, chunk_count: int) -> Optional[KnowledgeDocument]:
        document = self.get(db, object_id=document_id)
        if document:
            document.is_indexed = True
            document.chunk_count = chunk_count
            db.add(document)
            db.commit()
            db.refresh(document)
        return document

    def mark_as_unindexed(self, db: Session, *, document_id: str) -> Optional[KnowledgeDocument]:
        document = self.get(db, object_id=document_id)
        if document:
            document.is_indexed = False
            document.chunk_count = 0
            db.add(document)
            db.commit()
            db.refresh(document)
        return document

    def get_document_with_chunks(self, db: Session, *, document_id: str) -> Dict[str, Any]:
        document = self.get(db, object_id=document_id)
        if not document:
            return None
        
        chunks = db.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == document_id
        ).order_by(KnowledgeChunk.chunk_index).all()
        
        return {
            "document": document,
            "chunks": chunks
        }

    def get_documents_by_type(self, db: Session, *, file_type: str) -> List[KnowledgeDocument]:
        return db.query(KnowledgeDocument).filter(
            KnowledgeDocument.file_type.ilike(f"%{file_type}%")
        ).all()

    def get_total_documents_count(self, db: Session) -> Dict[str, int]:
        total = db.query(KnowledgeDocument).count()
        indexed = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.is_indexed == True
        ).count()
        
        return {
            "total": total,
            "indexed": indexed,
            "unindexed": total - indexed
        }

knowledge_document_crud = CRUDKnowledgeDocument(KnowledgeDocument)