from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, text
from app.db.base import Base

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    file_hash = Column(String(64))
    title = Column(String(255))
    description = Column(Text)
    document_metadata = Column("metadata", JSON, default={})
    is_indexed = Column(Boolean, default=False)
    chunk_count = Column(Integer, default=0)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    indexed_at = Column(DateTime(timezone=True))