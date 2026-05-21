"""
Integration tests for authentication endpoints
Tests: POST /auth/register, /auth/login, /auth/refresh, GET /auth/me
"""

import pytest
import uuid
from fastapi.testclient import TestClient


class TestAuthRegistration:
    """Test user registration endpoint"""

    def test_register_success(self, test_client):
        """Test successful user registration"""
        user_data = {
            "email": f"newuser_{uuid.uuid4().hex[:8]}@example.com",
            "name": "New User",
            "password": "SecurePass123!",
            "organization_name": "New Company"
        }

        response = test_client.post("/auth/register", json=user_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "user" in data
        assert "tokens" in data
        assert "message" in data

        # Verify user data
        user = data["user"]
        assert user["email"] == user_data["email"]
        assert user["name"] == user_data["name"]
        assert "id" in user
        assert "api_key" in user
        assert user["plan"] == "trial"

        # Verify tokens
        tokens = data["tokens"]
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

    def test_register_duplicate_email(self, test_client, test_user):
        """Test registration with duplicate email fails"""
        user_data = {
            "email": test_user["email"],
            "name": "Another User",
            "password": "Password123!",
        }

        response = test_client.post("/auth/register", json=user_data)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_register_missing_email(self, test_client):
        """Test registration without email returns 422"""
        user_data = {
            "name": "Test User",
            "password": "Password123!"
        }

        response = test_client.post("/auth/register", json=user_data)

        assert response.status_code == 422

    def test_register_missing_password(self, test_client):
        """Test registration without password returns 422"""
        user_data = {
            "email": "test@example.com",
            "name": "Test User"
        }

        response = test_client.post("/auth/register", json=user_data)

        assert response.status_code == 422

    def test_register_invalid_email(self, test_client):
        """Test registration with invalid email format"""
        user_data = {
            "email": "not-an-email",
            "name": "Test User",
            "password": "Password123!"
        }

        response = test_client.post("/auth/register", json=user_data)

        # Should fail validation
        assert response.status_code in [400, 422]


class TestAuthLogin:
    """Test user login endpoint"""

    def test_login_success(self, test_client, test_user_data, auth_manager):
        """Test successful login"""
        # First register a user
        from auth_jwt import UserRegister
        auth_manager.register_user(UserRegister(**test_user_data))

        # Now login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }

        response = test_client.post("/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_wrong_password(self, test_client, test_user):
        """Test login with incorrect password fails"""
        login_data = {
            "email": test_user["email"],
            "password": "WrongPassword123!"
        }

        response = test_client.post("/auth/login", json=login_data)

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, test_client):
        """Test login with non-existent email fails"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "Password123!"
        }

        response = test_client.post("/auth/login", json=login_data)

        assert response.status_code == 401

    def test_login_missing_email(self, test_client):
        """Test login without email returns 422"""
        login_data = {
            "password": "Password123!"
        }

        response = test_client.post("/auth/login", json=login_data)

        assert response.status_code == 422

    def test_login_missing_password(self, test_client):
        """Test login without password returns 422"""
        login_data = {
            "email": "test@example.com"
        }

        response = test_client.post("/auth/login", json=login_data)

        assert response.status_code == 422


class TestAuthRefresh:
    """Test token refresh endpoint"""

    def test_refresh_token_success(self, test_client, test_user):
        """Test successful token refresh"""
        refresh_token = test_user["tokens"].refresh_token

        response = test_client.post(
            "/auth/refresh",
            params={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_invalid_token(self, test_client):
        """Test refresh with invalid token fails"""
        response = test_client.post(
            "/auth/refresh",
            params={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == 401

    def test_refresh_missing_token(self, test_client):
        """Test refresh without token returns 422"""
        response = test_client.post("/auth/refresh")

        assert response.status_code == 422


class TestAuthMe:
    """Test current user info endpoint"""

    def test_get_current_user_success(self, test_client, test_user, auth_headers):
        """Test getting current user info with valid token"""
        response = test_client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "user" in data
        user = data["user"]
        assert user["email"] == test_user["email"]
        assert "id" in user
        assert "api_key" in user

    def test_get_current_user_no_token(self, test_client):
        """Test getting current user without token fails"""
        response = test_client.get("/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, test_client, invalid_jwt_token):
        """Test getting current user with invalid token fails"""
        headers = {"Authorization": invalid_jwt_token}
        response = test_client.get("/auth/me", headers=headers)

        assert response.status_code == 401

    def test_get_current_user_malformed_header(self, test_client):
        """Test with malformed authorization header"""
        headers = {"Authorization": "NotBearer token"}
        response = test_client.get("/auth/me", headers=headers)

        assert response.status_code == 401


class TestAuthLogout:
    """Test logout endpoint"""

    def test_logout_success(self, test_client):
        """Test logout returns success message"""
        response = test_client.post("/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()
