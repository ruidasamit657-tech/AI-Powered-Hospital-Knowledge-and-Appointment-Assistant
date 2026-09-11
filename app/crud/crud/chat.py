from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models.chat_session import ChatSession
from app.db.models.chat_message import ChatMessage

class CRUDChat:
    def __init__(self):
        pass

    # Chat Session CRUD
    def create_session(self, db: Session, *, user_id: str, title: str = "New Chat") -> ChatSession:
        import uuid
        session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_session(self, db: Session, *, session_id: str, user_id: str) -> Optional[ChatSession]:
        return db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()

    def get_user_sessions(self, db: Session, *, user_id: str, skip: int = 0, limit: int = 50) -> List[ChatSession]:
        return db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(desc(ChatSession.updated_at)).offset(skip).limit(limit).all()

    def update_session_title(self, db: Session, *, session_id: str, title: str) -> Optional[ChatSession]:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.title = title
            db.add(session)
            db.commit()
            db.refresh(session)
        return session

    def delete_session(self, db: Session, *, session_id: str, user_id: str) -> bool:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if session:
            # Delete all messages in the session
            db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
            db.delete(session)
            db.commit()
            return True
        return False

    def delete_all_user_sessions(self, db: Session, *, user_id: str) -> bool:
        sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
        for session in sessions:
            db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
            db.delete(session)
        db.commit()
        return True

    # Chat Message CRUD
    def create_message(self, db: Session, *, session_id: str, role: str, content: str, sources: str = None) -> ChatMessage:
        import uuid
        message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            sources=sources
        )
        db.add(message)
        
        # Update session updated_at
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            from datetime import datetime
            session.updated_at = datetime.utcnow()
            db.add(session)
        
        db.commit()
        db.refresh(message)
        return message

    def get_session_messages(self, db: Session, *, session_id: str, skip: int = 0, limit: int = 100) -> List[ChatMessage]:
        return db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).offset(skip).limit(limit).all()

    def get_session_messages_recent(self, db: Session, *, session_id: str, limit: int = 10) -> List[ChatMessage]:
        return db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(desc(ChatMessage.created_at)).limit(limit).all()

    def get_last_message(self, db: Session, *, session_id: str) -> Optional[ChatMessage]:
        return db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(desc(ChatMessage.created_at)).first()

    def get_conversation_context(self, db: Session, *, session_id: str, limit: int = 5) -> List[Dict[str, str]]:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(desc(ChatMessage.created_at)).limit(limit).all()
        
        # Return in chronological order
        return [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(messages)
        ]

    def get_sessions_with_messages(self, db: Session, *, user_id: str) -> List[Dict[str, Any]]:
        sessions = self.get_user_sessions(db, user_id=user_id, limit=100)
        
        result = []
        for session in sessions:
            messages = self.get_session_messages(db, session_id=session.id, limit=5)
            result.append({
                "session": session,
                "message_count": db.query(ChatMessage).filter(
                    ChatMessage.session_id == session.id
                ).count(),
                "recent_messages": messages
            })
        
        return result

chat_crud = CRUDChat()