import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models.chat_session import ChatSession
from app.db.models.chat_message import ChatMessage
from app.db.schemas.chat import ChatResponse
from app.services.rag_service import RAGService

logger = get_logger(__name__)

class ChatService:
    """Handles chat session management and message processing."""
    
    def __init__(self, rag_service: Optional[RAGService] = None):
        """
        Initialize chat service.
        
        Args:
            rag_service: RAG service instance
        """
        self.rag_service = rag_service or RAGService()
        self.active_sessions = {}  # In-memory session cache
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        mode: str = "rag",
        db: Optional[Session] = None
    ) -> ChatResponse:
        """
        Process a chat message.
        
        Args:
            user_id: ID of the user
            message: User message
            session_id: Optional session ID (creates new if not provided)
            mode: Processing mode (rag, retrieval_only, llm)
            db: Database session
        
        Returns:
            ChatResponse object
        """
        try:
            # Create or get session
            if not session_id:
                session_id = await self.create_session(user_id, db)
            
            # Save user message
            if db:
                await self.save_message(
                    session_id=session_id,
                    role="user",
                    content=message,
                    db=db
                )
            
            # Process with RAG
            result = await self.rag_service.process_query(
                query=message,
                session_id=session_id,
                mode=mode
            )
            
            # Save assistant response
            if db and result.get("response"):
                await self.save_message(
                    session_id=session_id,
                    role="assistant",
                    content=result["response"],
                    sources=result.get("sources", []),
                    db=db
                )
            
            # Return response
            return ChatResponse(
                session_id=session_id,
                message=result.get("response", "I apologize, but I couldn't generate a response."),
                sources=result.get("sources", []),
                mode=result.get("mode", mode),
                timestamp=datetime.now(timezone.utc)
            )
            
        except (OSError, RuntimeError, TypeError, ValueError) as e:
            logger.error(f"Error processing message: {str(e)}")
            return ChatResponse(
                session_id=session_id or "",
                message="I apologize, but I encountered an error processing your message.",
                sources=[],
                mode="error",
                timestamp=datetime.now(timezone.utc)
            )
    
    async def create_session(
        self,
        user_id: str,
        db: Optional[Session] = None,
        title: str = "New Chat"
    ) -> str:
        """
        Create a new chat session.
        
        Args:
            user_id: ID of the user
            db: Database session
            title: Session title
        
        Returns:
            Session ID
        """
        try:
            session_id = str(uuid.uuid4())
            
            if db:
                # Save to database
                session = ChatSession(
                    id=session_id,
                    user_id=user_id,
                    title=title
                )
                db.add(session)
                db.commit()
                db.refresh(session)
            else:
                # In-memory storage
                if user_id not in self.active_sessions:
                    self.active_sessions[user_id] = {}
                self.active_sessions[user_id][session_id] = {
                    "title": title,
                    "messages": [],
                    "created_at": datetime.now(timezone.utc)
                }
            
            logger.info(f"Created chat session: {session_id} for user: {user_id}")
            return session_id
            
        except (OSError, RuntimeError, TypeError, ValueError) as e:
            logger.error(f"Error creating session: {str(e)}")
            # Fallback to in-memory
            session_id = str(uuid.uuid4())
            if user_id not in self.active_sessions:
                self.active_sessions[user_id] = {}
            self.active_sessions[user_id][session_id] = {
                "title": title,
                "messages": [],
                "created_at": datetime.now(timezone.utc)
            }
            return session_id
    
    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        db: Optional[Session] = None
    ) -> None:
        """
        Save a chat message.
        
        Args:
            session_id: Session ID
            role: Message role (user, assistant, system)
            content: Message content
            sources: Sources for assistant messages
            db: Database session
        """
        try:
            if db:
                # Save to database
                message = ChatMessage(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    role=role,
                    content=content,
                    sources=json.dumps(sources) if sources else None
                )
                db.add(message)
                db.commit()
            else:
                # In-memory storage
                for user_sessions in self.active_sessions.values():
                    if session_id in user_sessions:
                        user_sessions[session_id]["messages"].append({
                            "role": role,
                            "content": content,
                            "sources": sources,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        break
            
        except (OSError, RuntimeError, TypeError, ValueError) as e:
            logger.error(f"Error saving message: {str(e)}")
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Get chat session history.
        
        Args:
            session_id: Session ID
            limit: Maximum number of messages to return
            db: Database session
        
        Returns:
            List of messages
        """
        try:
            if db:
                messages = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).order_by(
                    ChatMessage.created_at.desc()
                ).limit(limit).all()
                
                return [{
                    "role": msg.role,
                    "content": msg.content,
                    "sources": msg.sources,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None
                } for msg in reversed(messages)]
            else:
                # In-memory retrieval
                for user_sessions in self.active_sessions.values():
                    if session_id in user_sessions:
                        messages = user_sessions[session_id]["messages"]
                        return messages[-limit:]
                return []
                
        except (OSError, RuntimeError, TypeError, ValueError) as e:
            logger.error(f"Error retrieving session history: {str(e)}")
            return []
