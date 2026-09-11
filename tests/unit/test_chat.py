"""
Unit tests for chat endpoints
"""

from fastapi.testclient import TestClient

class TestChat:
    """Test chat functionality"""
    
    def test_chat_regular_question(self, client: TestClient, auth_headers):
        """Test chat with regular question"""
        response = client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={
                "question": "What are the hospital visiting hours?",
                "use_groq": False,
                "include_sources": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "mode" in data
        assert "timestamp" in data
        assert data.get("is_emergency") == False

    def test_chat_emergency_detection(self, client: TestClient, auth_headers):
        """Test emergency detection in chat"""
        response = client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={
                "question": "I think I'm having a heart attack!",
                "use_groq": False,
                "include_sources": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert data.get("is_emergency") == True
        assert "emergency" in data["answer"].lower()
        assert "emergency_keywords" in data

    def test_chat_no_context(self, client: TestClient, auth_headers):
        """Test chat when no relevant context found"""
        response = client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={
                "question": "What is the capital of France?",
                "use_groq": False,
                "include_sources": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "I don't have any relevant information" in data["answer"]
        assert data.get("is_emergency") == False

    def test_chat_with_sources_disabled(self, client: TestClient, auth_headers):
        """Test chat with sources disabled"""
        response = client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={
                "question": "What are the hospital visiting hours?",
                "use_groq": False,
                "include_sources": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sources"] == []