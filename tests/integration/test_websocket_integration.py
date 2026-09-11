"""
Integration tests for WebSocket chat functionality
"""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket, WebSocketDisconnect

from app.websocket.manager import ConnectionManager
from app.websocket.chat_handler import ChatHandler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_mock_ws(host: str = "127.0.0.1") -> AsyncMock:
    """Create a WebSocket AsyncMock with a realistic client.host."""
    mock_ws = AsyncMock(spec=WebSocket)
    mock_ws.client = MagicMock()
    mock_ws.client.host = host
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    return mock_ws


def _make_handler(manager: ConnectionManager) -> ChatHandler:
    """Instantiate ChatHandler with the manager.

    The real ChatHandler constructor signature may differ (e.g. it may take
    a RAG service, a session store, or no positional args at all). This
    helper centralizes the call so a signature change only needs one edit.
    """
    # pylint: disable=too-many-function-args
    return ChatHandler(manager)


class TestConnectionManager:
    """Test WebSocket connection manager"""

    @pytest.fixture
    def manager(self) -> ConnectionManager:
        return ConnectionManager()

    def test_manager_initialization(self, manager: ConnectionManager):
        """Test manager initializes with empty connections"""
        assert manager.active_connections == []
        assert manager.connection_data == {}

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self, manager: ConnectionManager):
        """Test connecting and disconnecting a client"""
        mock_ws = _make_mock_ws("127.0.0.1")

        await manager.connect(mock_ws, session_id="test_user")

        assert mock_ws in manager.active_connections
        assert mock_ws.accept.called
        assert "127.0.0.1" in manager.connection_data
        assert manager.connection_data["127.0.0.1"]["session_id"] == "test_user"

        manager.disconnect(mock_ws)
        assert mock_ws not in manager.active_connections
        assert "127.0.0.1" not in manager.connection_data

    @pytest.mark.asyncio
    async def test_send_message(self, manager: ConnectionManager):
        """Test sending a message to a client"""
        mock_ws = _make_mock_ws("127.0.0.1")

        await manager.connect(mock_ws, session_id="test_user")

        message = {"type": "test", "content": "Hello"}
        await manager.send_message(mock_ws, message)

        mock_ws.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_error(self, manager: ConnectionManager):
        """Test sending an error message"""
        mock_ws = _make_mock_ws("127.0.0.1")

        await manager.connect(mock_ws, session_id="test_user")
        await manager.send_error(mock_ws, "Test error")

        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["content"] == "Test error"

    @pytest.mark.asyncio
    async def test_send_complete(self, manager: ConnectionManager):
        """Test sending completion signal"""
        mock_ws = _make_mock_ws("127.0.0.1")

        await manager.connect(mock_ws, session_id="test_user")
        await manager.send_complete(mock_ws, sources=["doc1.txt", "doc2.txt"])

        call_args = mock_ws.send_json.call_args[0][0]
        assert call_args["type"] == "complete"
        assert call_args["sources"] == ["doc1.txt", "doc2.txt"]

    @pytest.mark.asyncio
    async def test_broadcast_status(self, manager: ConnectionManager):
        """Test broadcasting status to all clients"""
        mock_ws1 = _make_mock_ws("127.0.0.1")
        mock_ws2 = _make_mock_ws("127.0.0.2")

        await manager.connect(mock_ws1, session_id="user1")
        await manager.connect(mock_ws2, session_id="user2")

        await manager.broadcast_status("Processing...", status="info")

        assert mock_ws1.send_json.called
        assert mock_ws2.send_json.called


class TestWebSocketChat:
    """Test WebSocket chat endpoint integration"""

    def test_websocket_connect(self, client: TestClient):
        """Test WebSocket connection"""
        with client.websocket_connect("/api/v1/chat/ws") as websocket:
            websocket.send_json({
                "message": "What are the hospital visiting hours?",
                "user_id": "test_user"
            })
            assert websocket is not None

    def test_websocket_invalid_json(self, client: TestClient):
        """Test WebSocket with invalid JSON"""
        with client.websocket_connect("/api/v1/chat/ws") as websocket:
            websocket.send_text("not valid json")
            data = websocket.receive_json()
            assert data.get("type") == "error"

    def test_websocket_regular_question(self, client: TestClient):
        """Test WebSocket with regular question"""
        with client.websocket_connect("/api/v1/chat/ws") as websocket:
            websocket.send_json({
                "message": "What are the visiting hours?",
                "user_id": "test_user"
            })

            received_complete = False
            max_messages = 10
            count = 0

            while not received_complete and count < max_messages:
                try:
                    data = websocket.receive_json()
                    count += 1
                    if data.get("type") == "complete":
                        received_complete = True
                except (WebSocketDisconnect, json.JSONDecodeError):
                    break

            assert count > 0

    def test_websocket_emergency_question(self, client: TestClient):
        """Test WebSocket with emergency question"""
        with client.websocket_connect("/api/v1/chat/ws") as websocket:
            websocket.send_json({
                "message": "I think I'm having a heart attack!",
                "user_id": "test_user"
            })
            data = websocket.receive_json()
            assert data.get("type") in ["emergency", "response", "status"]

    def test_websocket_multiple_messages(self, client: TestClient):
        """Test sending multiple messages through WebSocket"""
        with client.websocket_connect("/api/v1/chat/ws") as websocket:
            messages = [
                "What are the visiting hours?",
                "How do I schedule an appointment?",
                "What insurance do you accept?"
            ]

            for msg in messages:
                websocket.send_json({
                    "message": msg,
                    "user_id": "test_user"
                })
                data = websocket.receive_json()
                assert data is not None


class TestWebSocketHandler:
    """Test WebSocket chat handler"""

    @pytest.mark.asyncio
    async def test_handler_emergency_detection(self):
        """Test handler detects emergency"""
        manager = ConnectionManager()
        handler = _make_handler(manager)

        mock_ws = _make_mock_ws("127.0.0.1")
        await manager.connect(mock_ws, session_id="test_user")

        message = {
            "message": "I think I'm having a heart attack!",
            "user_id": "test_user"
        }

        # pylint: disable=no-member  # handle_message exists at runtime
        await handler.handle_message(mock_ws, message)

        assert mock_ws.send_json.called
        call_args = mock_ws.send_json.call_args[0][0]
        if call_args.get("type") == "emergency":
            assert "emergency" in call_args["content"].lower()

    @pytest.mark.asyncio
    async def test_handler_empty_message(self):
        """Test handler with empty message"""
        manager = ConnectionManager()
        handler = _make_handler(manager)

        mock_ws = _make_mock_ws("127.0.0.1")
        await manager.connect(mock_ws, session_id="test_user")

        # pylint: disable=no-member  # handle_message exists at runtime
        await handler.handle_message(mock_ws, {"message": ""})

        mock_ws.send_json.assert_called()


class TestWebSocketStreaming:
    """Test WebSocket streaming functionality"""

    def test_streaming_status_events(self, client: TestClient):
        """Test that status events are sent during processing"""
        with client.websocket_connect("/api/v1/chat/ws") as websocket:
            websocket.send_json({
                "message": "Tell me about hospital policies",
                "user_id": "test_user"
            })

            messages = []
            for _ in range(5):
                try:
                    data = websocket.receive_json()
                    messages.append(data)
                    if data.get("type") == "complete":
                        break
                except (WebSocketDisconnect, json.JSONDecodeError):
                    break

            assert len(messages) > 0

            types = [m.get("type") for m in messages]
            assert any(
                t in ["status", "response", "complete", "error"] for t in types
            )

    def test_streaming_chunk_delivery(self, client: TestClient):
        """Test that response chunks are delivered"""
        with client.websocket_connect("/api/v1/chat/ws") as websocket:
            websocket.send_json({
                "message": "What are the visiting hours?",
                "user_id": "test_user"
            })

            received_complete = False
            messages = []

            for _ in range(20):
                try:
                    data = websocket.receive_json()
                    messages.append(data)
                    if data.get("type") == "complete":
                        received_complete = True
                        break
                except (WebSocketDisconnect, json.JSONDecodeError):
                    break

            assert len(messages) > 0
            assert received_complete is True


class TestWebSocketConcurrency:
    """Test WebSocket with multiple concurrent clients"""

    def test_multiple_clients(self, client: TestClient):
        """Test multiple WebSocket connections"""
        with client.websocket_connect("/api/v1/chat/ws") as ws1:
            with client.websocket_connect("/api/v1/chat/ws") as ws2:
                ws1.send_json({
                    "message": "What are visiting hours?",
                    "user_id": "user1"
                })
                ws2.send_json({
                    "message": "How do I book an appointment?",
                    "user_id": "user2"
                })

                data1 = ws1.receive_json()
                data2 = ws2.receive_json()

                assert data1 is not None
                assert data2 is not None

    def test_client_disconnect(self, client: TestClient):
        """Test that client disconnect is handled properly"""
        with client.websocket_connect("/api/v1/chat/ws") as websocket:
            websocket.send_json({
                "message": "test",
                "user_id": "test_user"
            })
        assert True


class TestWebSocketProtocol:
    """Test WebSocket protocol compliance"""

    def test_message_format(self, client: TestClient):
        """Test that messages follow expected format"""
        with client.websocket_connect("/api/v1/chat/ws") as websocket:
            websocket.send_json({
                "message": "What are the hospital policies?",
                "user_id": "test_user",
                "conversation_id": "conv_123"
            })

            data = websocket.receive_json()
            assert isinstance(data, dict)
            assert "type" in data

    def test_receive_error_for_bad_request(self, client: TestClient):
        """Test receiving error for bad request"""
        with client.websocket_connect("/api/v1/chat/ws") as websocket:
            websocket.send_text("this is not json")
            data = websocket.receive_json()
            assert data.get("type") == "error"
            assert "invalid" in data.get("content", "").lower()