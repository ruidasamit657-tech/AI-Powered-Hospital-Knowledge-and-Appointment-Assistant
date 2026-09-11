from typing import Optional, Dict, Any
from fastapi import WebSocket
from sqlalchemy.exc import SQLAlchemyError
from starlette.websockets import WebSocketDisconnect
import json
import uuid
import logging
from datetime import datetime

from app.websocket.manager import manager
from app.services.rag_service import RAGService
from app.services.medical_guard import MedicalGuard
from app.services.emergency_guard import EmergencyGuard
from app.services.chat_service import ChatService
from app.db.session import SessionLocal
from app.db.models.chat_session import ChatSession
from app.db.models.chat_message import ChatMessage

logger = logging.getLogger(__name__)

class ChatHandler:
    """
    Handles WebSocket chat interactions including message processing,
    RAG integration, and session management.
    """
    
    def __init__(self):
        self.rag_service = RAGService()
        self.medical_guard = MedicalGuard()
        self.emergency_guard = EmergencyGuard()
        self.chat_service = ChatService()
        self._processing_sessions: Dict[str, bool] = {}
    
    async def handle_chat(self, websocket: WebSocket, session_id: str, user_id: Optional[str] = None):
        """
        Main handler for WebSocket chat connections.
        Processes incoming messages and sends responses.
        """
        try:
            # Ensure session exists
            session_id = await self._ensure_session(session_id, user_id)
            
            # Send session info
            await manager.send_personal_message({
                "type": "session_info",
                "session_id": session_id,
                "message": "Chat session initialized"
            }, websocket)
            
            # Process messages
            while True:
                try:
                    # Receive message
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Process message
                    await self._process_message(
                        websocket,
                        session_id,
                        message_data
                    )
                    
                except json.JSONDecodeError as e:
                    await manager.send_error(session_id, f"Invalid JSON format: {str(e)}")
                except WebSocketDisconnect:
                    return
                except (ConnectionError, OSError, RuntimeError, TypeError, ValueError) as e:
                    logger.error("Error processing message: %s", e)
                    await manager.send_error(session_id, f"Error processing message: {str(e)}")
                    
        except (ConnectionError, OSError, RuntimeError, TypeError, ValueError) as e:
            logger.error("Error in chat handler: %s", e)
            await manager.send_error(session_id, f"Chat error: {str(e)}")
    
    async def _process_message(
        self,
        _websocket: WebSocket,
        session_id: str,
        message_data: Dict[str, Any]
    ):
        """Process a single chat message."""
        
        # Extract message content
        message_content = message_data.get("message", "")
        mode = message_data.get("mode", "rag")
        
        if not message_content:
            await manager.send_error(session_id, "Message cannot be empty")
            return
        
        # Check if already processing
        if self._processing_sessions.get(session_id, False):
            await manager.send_error(session_id, "Another message is being processed")
            return
        
        try:
            self._processing_sessions[session_id] = True
            
            # Send typing indicator
            await manager.send_typing_indicator(session_id, True)
            
            # Save user message
            await self._save_message(
                session_id,
                "user",
                message_content
            )
            
            # Step 1: Emergency check
            await manager.send_status(session_id, "checking_emergency", "Checking for emergency content")
            emergency_result = self.emergency_guard.check_emergency(message_content)
            
            if emergency_result.get("is_emergency"):
                await self._handle_emergency_response(session_id, emergency_result)
                return
            
            # Step 2: Medical guard check
            await manager.send_status(session_id, "medical_guard_check", "Verifying medical content safety")
            medical_check = self.medical_guard.check_safety(message_content)
            
            if not medical_check.get("is_safe"):
                await self._handle_unsafe_response(session_id, medical_check)
                return
            
            # Step 3: Process with RAG
            await manager.send_status(session_id, "processing", "Searching knowledge base...")
            
            # Get response based on mode
            response_data = await self.rag_service.process_query(
                query=message_content,
                session_id=session_id,
                mode=mode,
            )
            
            # Step 4: Generate final response
            await manager.send_status(session_id, "finalizing", "Preparing response...")
            
            response_message = await self._format_response(response_data)
            
            # Save assistant message
            await self._save_message(
                session_id,
                "assistant",
                response_message.get("content", ""),
                sources=response_message.get("sources")
            )
            
            # Send response
            await manager.broadcast_to_session(session_id, {
                "type": "message",
                "role": "assistant",
                "content": response_message.get("content", ""),
                "sources": response_message.get("sources", []),
                "mode": mode,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except (ConnectionError, OSError, RuntimeError, TypeError, ValueError, SQLAlchemyError) as e:
            logger.error("Error processing message: %s", e)
            await manager.send_error(session_id, f"Error: {str(e)}")
        finally:
            self._processing_sessions[session_id] = False
            await manager.send_typing_indicator(session_id, False)
    
    async def _ensure_session(self, session_id: Optional[str], user_id: Optional[str] = None) -> str:
        """Ensure a chat session exists, create if not."""
        if session_id:
            return session_id
        
        # Create new session
        new_session_id = str(uuid.uuid4())
        
        # Save to database
        db = SessionLocal()
        try:
            chat_session = ChatSession(
                id=new_session_id,
                user_id=user_id,
                title="New Chat Session"
            )
            db.add(chat_session)
            db.commit()
        finally:
            db.close()
        
        return new_session_id
    
    async def _save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[list] = None
    ):
        """Save a message to the database."""
        db = SessionLocal()
        try:
            message = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role=role,
                content=content,
                sources=json.dumps(sources) if sources else None
            )
            db.add(message)
            
            # Update session timestamp
            if role == "user":
                session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
                if session:
                    session.updated_at = datetime.utcnow()
            
            db.commit()
        except SQLAlchemyError as e:
            logger.error("Error saving message: %s", e)
            db.rollback()
        finally:
            db.close()
    
    async def _format_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format the response data for display."""
        return {
            "content": response_data.get("response", "No response generated."),
            "sources": response_data.get("sources", []),
            "metadata": response_data.get("metadata", {})
        }
    
    async def _handle_emergency_response(
        self,
        session_id: str,
        emergency_result: Dict[str, Any]
    ):
        """Handle emergency responses."""
        response = {
            "type": "emergency",
            "level": emergency_result.get("level", "high"),
            "message": emergency_result.get("response", "Emergency situation detected."),
            "actions": emergency_result.get("actions", []),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.broadcast_to_session(session_id, response)
        
        # Send follow-up emergency resources
        resources = emergency_result.get("resources", [])
        if resources:
            await manager.broadcast_to_session(session_id, {
                "type": "emergency_resources",
                "resources": resources,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _handle_unsafe_response(
        self,
        session_id: str,
        medical_check: Dict[str, Any]
    ):
        """Handle unsafe medical responses."""
        response = {
            "type": "safety_warning",
            "message": "I notice your question may involve medical advice. Please note:",
            "warnings": medical_check.get("warnings", [
                "This is not medical advice",
                "Please consult a healthcare professional",
                "Always verify medical information"
            ]),
            "suggestions": medical_check.get("suggestions", [
                "Contact your healthcare provider",
                "Visit a medical facility",
                "Call a medical helpline"
            ]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await manager.broadcast_to_session(session_id, response)
    
    async def get_chat_history(self, session_id: str, limit: int = 50):
        """Retrieve chat history for a session."""
        db = SessionLocal()
        try:
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "sources": json.loads(msg.sources) if msg.sources else [],
                    "timestamp": msg.created_at.isoformat()
                }
                for msg in reversed(messages)
            ]
        finally:
            db.close()
    
    async def delete_chat_session(self, session_id: str):
        """Delete a chat session and its messages."""
        db = SessionLocal()
        try:
            # Delete all messages
            db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
            # Delete session
            db.query(ChatSession).filter(ChatSession.id == session_id).delete()
            db.commit()
            
            await manager.broadcast_to_session(session_id, {
                "type": "session_deleted",
                "message": "Chat session deleted",
                "timestamp": datetime.utcnow().isoformat()
            })
        except SQLAlchemyError as e:
            logger.error("Error deleting chat session: %s", e)
            db.rollback()
            raise
        finally:
            db.close()

# Additional utility functions for the WebSocket handler

def create_websocket_message(
    message_type: str,
    data: Dict[str, Any],
    session_id: str
) -> str:
    """Create a standardized WebSocket message."""
    return json.dumps({
        "type": message_type,
        "session_id": session_id,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    })

def parse_websocket_message(message_str: str) -> Dict[str, Any]:
    """Parse a WebSocket message string."""
    try:
        return json.loads(message_str)
    except json.JSONDecodeError:
        return {"message": message_str}

# Export key components
__all__ = ["manager", "ChatHandler", "create_websocket_message", "parse_websocket_message"]