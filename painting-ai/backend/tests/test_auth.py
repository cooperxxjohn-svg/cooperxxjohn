"""
Authentication System Unit Tests

Tests for user registration, login, JWT token generation/validation,
password hashing, and authentication flows.
"""

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import jwt

from auth_jwt import (
    AuthManager,
    UserRegister,
    UserLogin,
    Token,
    TokenData,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


# ============================================================================
# Password Hashing Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.auth
class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_hash_password_creates_hash(self, auth_manager):
        """Test that hashing creates a bcrypt hash"""
        password = "SecurePassword123!"
        hashed = auth_manager.hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix
        assert len(hashed) == 60  # bcrypt hash length

    def test_verify_password_with_correct_password(self, auth_manager):
        """Test password verification with correct password"""
        password = "SecurePassword123!"
        hashed = auth_manager.hash_password(password)

        assert auth_manager.verify_password(password, hashed) is True

    def test_verify_password_with_wrong_password(self, auth_manager):
        """Test password verification with wrong password"""
        password = "SecurePassword123!"
        hashed = auth_manager.hash_password(password)

        assert auth_manager.verify_password("WrongPassword!", hashed) is False

    def test_hash_different_passwords_produce_different_hashes(self, auth_manager):
        """Test that different passwords produce different hashes"""
        password1 = "Password1"
        password2 = "Password2"

        hash1 = auth_manager.hash_password(password1)
        hash2 = auth_manager.hash_password(password2)

        assert hash1 != hash2

    def test_hash_same_password_twice_produces_different_hashes(self, auth_manager):
        """Test that hashing same password twice produces different hashes (salt)"""
        password = "SecurePassword123!"

        hash1 = auth_manager.hash_password(password)
        hash2 = auth_manager.hash_password(password)

        assert hash1 != hash2
        # But both should verify
        assert auth_manager.verify_password(password, hash1)
        assert auth_manager.verify_password(password, hash2)


# ============================================================================
# JWT Token Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.auth
class TestJWTTokens:
    """Test JWT token creation and validation"""

    def test_create_access_token_returns_valid_token(self, auth_manager):
        """Test creating an access token"""
        data = {"user_id": "user123", "email": "test@example.com"}
        token = auth_manager.create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_includes_expiration(self, auth_manager):
        """Test that access token includes expiration"""
        data = {"user_id": "user123", "email": "test@example.com"}
        token = auth_manager.create_access_token(data)

        # Decode without verification to check contents
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert "exp" in payload
        assert "type" in payload
        assert payload["type"] == "access"
        assert "user_id" in payload
        assert "email" in payload

    def test_create_access_token_with_custom_expiration(self, auth_manager):
        """Test creating token with custom expiration"""
        data = {"user_id": "user123", "email": "test@example.com"}
        custom_delta = timedelta(minutes=5)
        token = auth_manager.create_access_token(data, expires_delta=custom_delta)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"])

        # Should expire in roughly 5 minutes (allow 1 second tolerance)
        time_diff = exp_time - datetime.utcnow()
        assert 4 * 60 < time_diff.total_seconds() < 6 * 60

    def test_create_refresh_token_returns_valid_token(self, auth_manager):
        """Test creating a refresh token"""
        data = {"user_id": "user123", "email": "test@example.com"}
        token = auth_manager.create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["type"] == "refresh"

    def test_decode_token_with_valid_token(self, auth_manager):
        """Test decoding a valid token"""
        data = {"user_id": "user123", "email": "test@example.com"}
        token = auth_manager.create_access_token(data)

        token_data = auth_manager.decode_token(token)

        assert token_data.user_id == "user123"
        assert token_data.email == "test@example.com"

    def test_decode_token_with_invalid_token_raises_exception(self, auth_manager):
        """Test decoding an invalid token raises HTTPException"""
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            auth_manager.decode_token(invalid_token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail

    def test_decode_token_with_expired_token_raises_exception(self, auth_manager):
        """Test decoding an expired token raises HTTPException"""
        data = {"user_id": "user123", "email": "test@example.com"}
        expired_delta = timedelta(seconds=-1)  # Already expired
        token = auth_manager.create_access_token(data, expires_delta=expired_delta)

        with pytest.raises(HTTPException) as exc_info:
            auth_manager.decode_token(token)

        assert exc_info.value.status_code == 401

    def test_decode_token_with_missing_user_id_raises_exception(self, auth_manager):
        """Test decoding token without user_id raises exception"""
        # Create token manually without user_id
        payload = {
            "email": "test@example.com",
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "type": "access"
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            auth_manager.decode_token(token)

        assert exc_info.value.status_code == 401


# ============================================================================
# User Registration Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.auth
class TestUserRegistration:
    """Test user registration functionality"""

    def test_register_user_with_valid_data(self, auth_manager, sample_user_data):
        """Test successful user registration"""
        user_data = UserRegister(**sample_user_data)
        user = auth_manager.register_user(user_data)

        assert user is not None
        assert user["email"] == sample_user_data["email"]
        assert user["name"] == sample_user_data["name"]
        assert "id" in user
        assert "api_key" in user
        assert "password_hash" not in user  # Password should be removed
        assert user["plan"] == "trial"
        assert user["subscription_status"] == "trialing"

    def test_register_user_creates_api_key(self, auth_manager, sample_user_data):
        """Test that registration creates a unique API key"""
        user_data = UserRegister(**sample_user_data)
        user = auth_manager.register_user(user_data)

        assert "api_key" in user
        assert user["api_key"].startswith("pk_")
        assert len(user["api_key"]) > 10

    def test_register_user_hashes_password(self, auth_manager, sample_user_data, mock_database):
        """Test that password is hashed during registration"""
        user_data = UserRegister(**sample_user_data)
        user = auth_manager.register_user(user_data)

        # Get the user from mock database (includes password_hash)
        stored_user = mock_database.users[user["id"]]
        assert "password_hash" in stored_user
        assert stored_user["password_hash"] != sample_user_data["password"]
        assert stored_user["password_hash"].startswith("$2b$")

    def test_register_user_with_duplicate_email_raises_exception(self, auth_manager, sample_user_data):
        """Test that registering duplicate email raises HTTPException"""
        user_data = UserRegister(**sample_user_data)
        auth_manager.register_user(user_data)

        # Try to register again with same email
        with pytest.raises(HTTPException) as exc_info:
            auth_manager.register_user(user_data)

        assert exc_info.value.status_code == 400
        assert "already registered" in exc_info.value.detail.lower()

    def test_register_user_with_organization_name(self, auth_manager, mock_database):
        """Test registration with organization name creates organization"""
        user_data = UserRegister(
            email="org@example.com",
            name="Org User",
            password="SecurePass123!",
            organization_name="Test Painting Company"
        )
        user = auth_manager.register_user(user_data)

        # Check that organization was created
        assert len(mock_database.organizations) == 1
        org = list(mock_database.organizations.values())[0]
        assert org["name"] == "Test Painting Company"
        assert org["owner_id"] == user["id"]

    def test_register_user_without_organization_name(self, auth_manager, mock_database):
        """Test registration without organization name doesn't create org"""
        user_data = UserRegister(
            email="noorg@example.com",
            name="No Org User",
            password="SecurePass123!"
        )
        auth_manager.register_user(user_data)

        # Check that no organization was created
        assert len(mock_database.organizations) == 0

    def test_register_user_sets_trial_dates(self, auth_manager, sample_user_data):
        """Test that registration sets trial start and end dates"""
        user_data = UserRegister(**sample_user_data)
        user = auth_manager.register_user(user_data)

        assert "settings" in user
        assert "trial_started" in user["settings"]
        assert "trial_ends" in user["settings"]


# ============================================================================
# User Authentication Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.auth
class TestUserAuthentication:
    """Test user authentication and login"""

    def test_authenticate_user_with_valid_credentials(self, auth_manager, sample_user_data, registered_user):
        """Test authentication with correct credentials"""
        user = auth_manager.authenticate_user(
            email=sample_user_data["email"],
            password=sample_user_data["password"]
        )

        assert user is not None
        assert user["email"] == sample_user_data["email"]
        assert "password_hash" not in user

    def test_authenticate_user_with_wrong_password(self, auth_manager, sample_user_data, registered_user):
        """Test authentication with wrong password returns None"""
        user = auth_manager.authenticate_user(
            email=sample_user_data["email"],
            password="WrongPassword123!"
        )

        assert user is None

    def test_authenticate_user_with_nonexistent_email(self, auth_manager):
        """Test authentication with non-existent email returns None"""
        user = auth_manager.authenticate_user(
            email="nonexistent@example.com",
            password="SomePassword"
        )

        assert user is None

    def test_login_user_with_valid_credentials(self, auth_manager, sample_user_data, registered_user):
        """Test login returns access and refresh tokens"""
        login_data = UserLogin(
            email=sample_user_data["email"],
            password=sample_user_data["password"]
        )
        tokens = auth_manager.login_user(login_data)

        assert isinstance(tokens, Token)
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in > 0

    def test_login_user_with_invalid_credentials_raises_exception(self, auth_manager, sample_user_data, registered_user):
        """Test login with wrong password raises HTTPException"""
        login_data = UserLogin(
            email=sample_user_data["email"],
            password="WrongPassword!"
        )

        with pytest.raises(HTTPException) as exc_info:
            auth_manager.login_user(login_data)

        assert exc_info.value.status_code == 401
        assert "Incorrect email or password" in exc_info.value.detail

    def test_login_user_tokens_are_valid(self, auth_manager, sample_user_data, registered_user):
        """Test that login returns valid tokens that can be decoded"""
        login_data = UserLogin(
            email=sample_user_data["email"],
            password=sample_user_data["password"]
        )
        tokens = auth_manager.login_user(login_data)

        # Decode and verify access token
        token_data = auth_manager.decode_token(tokens.access_token)
        assert token_data.user_id == registered_user["id"]
        assert token_data.email == registered_user["email"]


# ============================================================================
# Refresh Token Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.auth
class TestRefreshToken:
    """Test refresh token functionality"""

    def test_refresh_access_token_with_valid_refresh_token(self, auth_manager, registered_user):
        """Test refreshing access token with valid refresh token"""
        token_data = {"user_id": registered_user["id"], "email": registered_user["email"]}
        refresh_token = auth_manager.create_refresh_token(token_data)

        new_tokens = auth_manager.refresh_access_token(refresh_token)

        assert isinstance(new_tokens, Token)
        assert new_tokens.access_token is not None
        assert new_tokens.refresh_token is not None
        assert new_tokens.access_token != refresh_token

    def test_refresh_access_token_with_access_token_raises_exception(self, auth_manager, registered_user):
        """Test that using access token as refresh token fails"""
        token_data = {"user_id": registered_user["id"], "email": registered_user["email"]}
        access_token = auth_manager.create_access_token(token_data)

        with pytest.raises(HTTPException) as exc_info:
            auth_manager.refresh_access_token(access_token)

        assert exc_info.value.status_code == 401
        assert "Invalid token type" in exc_info.value.detail

    def test_refresh_access_token_with_invalid_token_raises_exception(self, auth_manager):
        """Test refreshing with invalid token raises exception"""
        with pytest.raises(HTTPException) as exc_info:
            auth_manager.refresh_access_token("invalid.token.here")

        assert exc_info.value.status_code == 401

    def test_refresh_access_token_with_expired_refresh_token(self, auth_manager, registered_user):
        """Test refreshing with expired refresh token fails"""
        # Create expired refresh token
        token_data = {"user_id": registered_user["id"], "email": registered_user["email"]}
        exp_time = datetime.utcnow() - timedelta(days=1)  # Expired yesterday

        payload = {
            **token_data,
            "exp": exp_time,
            "type": "refresh"
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            auth_manager.refresh_access_token(expired_token)

        assert exc_info.value.status_code == 401


# ============================================================================
# API Key Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.auth
class TestAPIKey:
    """Test API key generation"""

    def test_generate_api_key_returns_valid_key(self, auth_manager):
        """Test API key generation"""
        api_key = auth_manager.generate_api_key()

        assert api_key is not None
        assert api_key.startswith("pk_")
        assert len(api_key) > 10

    def test_generate_api_key_creates_unique_keys(self, auth_manager):
        """Test that each generated API key is unique"""
        key1 = auth_manager.generate_api_key()
        key2 = auth_manager.generate_api_key()
        key3 = auth_manager.generate_api_key()

        assert key1 != key2
        assert key2 != key3
        assert key1 != key3


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

@pytest.mark.unit
@pytest.mark.auth
class TestAuthEdgeCases:
    """Test edge cases and error handling"""

    def test_register_user_with_empty_email_raises_validation_error(self):
        """Test registration with empty email"""
        with pytest.raises(Exception):  # Pydantic validation error
            UserRegister(
                email="",
                name="Test User",
                password="SecurePass123!"
            )

    def test_register_user_with_empty_password_raises_validation_error(self):
        """Test registration with empty password"""
        with pytest.raises(Exception):  # Pydantic validation error
            UserRegister(
                email="test@example.com",
                name="Test User",
                password=""
            )

    def test_authenticate_with_case_sensitive_email(self, auth_manager, sample_user_data, registered_user):
        """Test that email comparison is case-sensitive (or not, depending on implementation)"""
        # Try login with different case
        user = auth_manager.authenticate_user(
            email=sample_user_data["email"].upper(),
            password=sample_user_data["password"]
        )

        # Depending on implementation, this might return None or the user
        # This tests current behavior
        assert user is None or user["email"] == sample_user_data["email"]

    def test_decode_token_with_tampered_token_raises_exception(self, auth_manager, valid_access_token):
        """Test that tampering with token raises exception"""
        # Tamper with the token by modifying a character
        tampered_token = valid_access_token[:-5] + "XXXXX"

        with pytest.raises(HTTPException) as exc_info:
            auth_manager.decode_token(tampered_token)

        assert exc_info.value.status_code == 401
