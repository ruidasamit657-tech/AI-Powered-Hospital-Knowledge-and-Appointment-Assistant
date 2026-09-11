from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON, text
from sqlalchemy.orm import relationship

from app.db.base import Base

class ChatMessage(Base):
    """Chat message model for storing individual messages in a session"""
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Sources from RAG retrieval (stored as JSON)
    sources = Column(JSON, default=list)
    
    # Additional metadata
    # ``metadata`` is reserved by SQLAlchemy's declarative API, so expose the
    # column through a different Python attribute while keeping its DB name.
    message_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage {self.id} - {self.role}>"