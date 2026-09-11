from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, text
from sqlalchemy.orm import relationship
from app.db.base import Base

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"))
    chunk_index = Column(Integer)
    content = Column(Text, nullable=False)
    document_metadata = Column("metadata", JSON, default={})
    embedding_id = Column(String(255))  # ID in vector store
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    
    # Relationships
    document = relationship("KnowledgeDocument", backref="chunks")