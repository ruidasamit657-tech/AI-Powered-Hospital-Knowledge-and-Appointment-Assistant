# pyright: reportMissingImports=false
# pylint: disable=import-error, no-name-in-module, unused-argument

"""
Unit tests for authentication endpoints
"""

from fastapi.testclient import TestClient

from app.core.security import (  # type: ignore[import]
    get_password_hash,
    verify_password,
)


class TestAuthentication:
    """Test authentication endpoints"""

    def test_register_user(self, client: TestClient):
        """Test user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "full_name": "New User",
                "password": "NewPass123!",
                "role": "patient",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["full_name"] == "New User"
        assert data["role"] == "patient"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_register_duplicate_email(self, client: TestClient, test_user):
        """Test registration with duplicate email"""
        assert test_user.email == "testuser@example.com"

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "testuser@example.com",
                "username": "newuser2",
                "full_name": "New User 2",
                "password": "NewPass123!",
                "role": "patient",
            },
        )
        assert response.status_code == 400
        assert "Email already registered" in response.text

    def test_register_duplicate_username(self, client: TestClient, test_user):
        """Test registration with duplicate username"""
        assert test_user.username == "testuser"

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser2@example.com",
                "username": "testuser",
                "full_name": "New User 2",
                "password": "NewPass123!",
                "role": "patient",
            },
        )
        assert response.status_code == 400
        assert "Username already taken" in response.text

    def test_login_success(self, client: TestClient, test_user):
        """Test successful login"""
        assert test_user.username == "testuser"

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "Test123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "patient"

    def test_login_wrong_password(self, client: TestClient, test_user):
        """Test login with wrong password"""
        assert test_user.username == "testuser"

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "testuser",
                "password": "WrongPassword!",
            },
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.text

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent",
                "password": "password",
            },
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.text

    def test_get_current_user(self, client: TestClient, auth_headers):
        """Test getting current user info"""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "testuser@example.com"
        assert "role" in data
        assert "id" in data

    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting user info without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_password_hashing(self):
        """Test password hashing functionality"""
        password = "SecurePass123!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False