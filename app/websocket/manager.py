from typing import Dict, List, Set
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections and handles broadcasting messages
    to connected clients.
    """
    
    def __init__(self):
        # Store active connections: {session_id: [websocket1, websocket2, ...]}
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store user sessions: {user_id: [session_id1, session_id2, ...]}
        self.user_sessions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, user_id: str = None):
        """Accept a new WebSocket connection and store it."""
        await websocket.accept()
        
        # Add to active connections
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        
        # Track user sessions if user_id provided
        if user_id:
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = set()
            self.user_sessions[user_id].add(session_id)
        
        logger.info("WebSocket connected: session_id=%s, user_id=%s", session_id, user_id)
        
        # Send connection confirmation
        await self.send_personal_message(
            {"type": "connection", "status": "connected", "session_id": session_id},
            websocket
        )
    
    def disconnect(self, websocket: WebSocket, session_id: str, user_id: str = None):
        """Remove a disconnected WebSocket connection."""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            
            # Remove session if no more connections
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        # Remove from user sessions
        if user_id and user_id in self.user_sessions:
            if session_id in self.user_sessions[user_id]:
                self.user_sessions[user_id].remove(session_id)
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
        
        logger.info("WebSocket disconnected: session_id=%s, user_id=%s", session_id, user_id)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            await websocket.send_text(message)
        except (WebSocketDisconnect, RuntimeError, OSError) as e:
            logger.error("Error sending personal message: %s", e)
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        """Broadcast a message to all connections in a specific session."""
        if session_id not in self.active_connections:
            logger.warning("Session not found for broadcast: %s", session_id)
            return
        
        if isinstance(message, dict):
            message = json.dumps(message)
        
        disconnected_websockets = []
        
        for websocket in self.active_connections[session_id]:
            try:
                await websocket.send_text(message)
            except (WebSocketDisconnect, RuntimeError, OSError) as e:
                logger.error("Error broadcasting to websocket: %s", e)
                disconnected_websockets.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            self.disconnect(websocket, session_id)
    
    async def broadcast_to_user(self, user_id: str, message: dict):
        """Broadcast a message to all sessions of a specific user."""
        if user_id not in self.user_sessions:
            logger.warning("User not found for broadcast: %s", user_id)
            return
        
        if isinstance(message, dict):
            message = json.dumps(message)
        
        for session_id in self.user_sessions[user_id]:
            await self.broadcast_to_session(session_id, message)
    
    async def send_typing_indicator(self, session_id: str, is_typing: bool = True):
        """Send a typing indicator to a session."""
        await self.broadcast_to_session(
            session_id,
            {
                "type": "typing",
                "is_typing": is_typing,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def send_error(self, session_id: str, error_message: str):
        """Send an error message to a session."""
        await self.broadcast_to_session(
            session_id,
            {
                "type": "error",
                "message": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def send_status(self, session_id: str, status: str, message: str = ""):
        """Send a status update to a session."""
        await self.broadcast_to_session(
            session_id,
            {
                "type": "status",
                "status": status,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def get_session_count(self, session_id: str) -> int:
        """Get the number of active connections in a session."""
        return len(self.active_connections.get(session_id, []))
    
    def get_active_sessions(self) -> List[str]:
        """Get all active session IDs."""
        return list(self.active_connections.keys())
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all session IDs for a specific user."""
        return list(self.user_sessions.get(user_id, set()))

# Create a global instance
manager = ConnectionManager()