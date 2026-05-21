"""
Integration tests for user settings and profile endpoints
Tests: GET /auth/me, user profile management
"""

import pytest
import uuid
from fastapi.testclient import TestClient


class TestUserProfile:
    """Test user profile endpoints"""

    def test_get_user_profile(self, test_client, auth_headers):
        """Test getting current user profile"""
        response = test_client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "user" in data
        user = data["user"]

        # Verify user fields
        assert "id" in user
        assert "email" in user
        assert "name" in user
        assert "api_key" in user
        assert "plan" in user

    def test_user_profile_includes_settings(self, test_client, auth_headers):
        """Test that user profile includes settings"""
        response = test_client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        user = data["user"]

        # User should have plan and settings info
        assert "plan" in user

    def test_user_profile_without_auth(self, test_client):
        """Test getting profile without authentication fails"""
        response = test_client.get("/auth/me")

        assert response.status_code == 401


class TestAPIKey:
    """Test API key functionality"""

    def test_user_has_api_key(self, test_client, test_user):
        """Test that registered users receive an API key"""
        user = test_user["user"]

        assert "api_key" in user
        assert user["api_key"] is not None
        assert len(user["api_key"]) > 0

    def test_api_key_is_unique(self, test_client, auth_manager):
        """Test that API keys are unique per user"""
        # Create multiple users
        user1_data = {
            "email": f"user1_{uuid.uuid4().hex[:8]}@example.com",
            "name": "User 1",
            "password": "Password123!"
        }
        user2_data = {
            "email": f"user2_{uuid.uuid4().hex[:8]}@example.com",
            "name": "User 2",
            "password": "Password123!"
        }

        from auth_jwt import UserRegister
        user1 = auth_manager.register_user(UserRegister(**user1_data))
        user2 = auth_manager.register_user(UserRegister(**user2_data))

        # API keys should be different
        assert user1["api_key"] != user2["api_key"]


class TestUserPlan:
    """Test user subscription plan information"""

    def test_new_user_has_trial_plan(self, test_client, test_user):
        """Test that new users start with trial plan"""
        user = test_user["user"]

        assert user["plan"] == "trial"

    def test_user_plan_in_profile(self, test_client, auth_headers):
        """Test that plan information appears in profile"""
        response = test_client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        user = data["user"]

        assert "plan" in user
        assert user["plan"] in ["trial", "starter", "pro", "enterprise"]


class TestAuthorizationBoundaries:
    """Test that users can only access their own data"""

    def test_user_can_access_own_profile(self, test_client, auth_headers):
        """Test user can access their own profile"""
        response = test_client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200

    def test_invalid_token_cannot_access_profile(self, test_client):
        """Test invalid token cannot access any profile"""
        headers = {"Authorization": "Bearer invalid.token"}
        response = test_client.get("/auth/me", headers=headers)

        assert response.status_code == 401

    def test_expired_token_cannot_access_profile(self, test_client, expired_jwt_token):
        """Test expired token cannot access profile"""
        headers = {"Authorization": f"Bearer {expired_jwt_token}"}
        response = test_client.get("/auth/me", headers=headers)

        assert response.status_code == 401


class TestUserAuthentication:
    """Test user authentication flow"""

    def test_complete_auth_flow(self, test_client, test_user_data, auth_manager):
        """Test complete registration -> login -> access flow"""
        # 1. Register
        from auth_jwt import UserRegister
        user = auth_manager.register_user(UserRegister(**test_user_data))
        assert "id" in user

        # 2. Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = test_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        tokens = login_response.json()

        # 3. Access protected resource
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        me_response = test_client.get("/auth/me", headers=headers)
        assert me_response.status_code == 200

        # 4. Verify user data matches
        profile = me_response.json()["user"]
        assert profile["email"] == test_user_data["email"]

    def test_logout_message(self, test_client):
        """Test logout returns appropriate message"""
        response = test_client.post("/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestPasswordSecurity:
    """Test password security features"""

    def test_password_not_in_response(self, test_client, test_user):
        """Test that password is never returned in API responses"""
        # Check registration response
        user = test_user["user"]
        assert "password" not in user
        assert "hashed_password" not in user

    def test_password_not_in_profile(self, test_client, auth_headers):
        """Test that password is not in profile response"""
        response = test_client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        user = data["user"]

        assert "password" not in user
        assert "hashed_password" not in user

    def test_wrong_password_fails_login(self, test_client, test_user):
        """Test that wrong password prevents login"""
        login_data = {
            "email": test_user["email"],
            "password": "WrongPassword123!"
        }

        response = test_client.post("/auth/login", json=login_data)

        assert response.status_code == 401


class TestTokenManagement:
    """Test JWT token management"""

    def test_access_token_format(self, test_client, test_user):
        """Test that access token is in correct format"""
        tokens = test_user["tokens"]

        assert hasattr(tokens, "access_token")
        assert hasattr(tokens, "refresh_token")
        assert tokens.token_type == "bearer"

    def test_refresh_token_works(self, test_client, test_user):
        """Test that refresh token can get new access token"""
        refresh_token = test_user["tokens"].refresh_token

        response = test_client.post(
            "/auth/refresh",
            params={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        new_tokens = response.json()

        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens

    def test_new_access_token_works(self, test_client, test_user):
        """Test that refreshed access token works for authentication"""
        # Get new token via refresh
        refresh_token = test_user["tokens"].refresh_token
        refresh_response = test_client.post(
            "/auth/refresh",
            params={"refresh_token": refresh_token}
        )
        new_access_token = refresh_response.json()["access_token"]

        # Use new token to access protected resource
        headers = {"Authorization": f"Bearer {new_access_token}"}
        response = test_client.get("/auth/me", headers=headers)

        assert response.status_code == 200
