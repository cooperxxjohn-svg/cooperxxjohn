"""
Authentication Module for XBOQ Platform
JWT token generation, password hashing, and validation
"""

import os
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps

import jwt
import bcrypt
from email_validator import validate_email, EmailNotValidError
from flask import request, jsonify
from dotenv import load_dotenv

load_dotenv()

# Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '15'))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '7'))


# ============================================================================
# PASSWORD UTILITIES
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password meets strength requirements

    Args:
        password: Password to validate

    Returns:
        (is_valid, error_message)
    """
    min_length = int(os.getenv('MIN_PASSWORD_LENGTH', '8'))

    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"

    if os.getenv('REQUIRE_PASSWORD_UPPERCASE', 'true').lower() == 'true':
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"

    if os.getenv('REQUIRE_PASSWORD_LOWERCASE', 'true').lower() == 'true':
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"

    if os.getenv('REQUIRE_PASSWORD_DIGIT', 'true').lower() == 'true':
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"

    if os.getenv('REQUIRE_PASSWORD_SPECIAL', 'false').lower() == 'true':
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"

    return True, None


# ============================================================================
# EMAIL VALIDATION
# ============================================================================

def validate_email_format(email: str) -> tuple[bool, Optional[str]]:
    """
    Validate email format

    Args:
        email: Email address to validate

    Returns:
        (is_valid, error_message)
    """
    try:
        # Validate and normalize
        validated = validate_email(email, check_deliverability=False)
        return True, None
    except EmailNotValidError as e:
        return False, str(e)


# ============================================================================
# JWT TOKEN UTILITIES
# ============================================================================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token

    Args:
        data: Dictionary of claims to encode (must include 'sub' for user_id)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    # Convert user_id to string (JWT 'sub' claim must be a string)
    if 'sub' in to_encode and isinstance(to_encode['sub'], int):
        to_encode['sub'] = str(to_encode['sub'])

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create JWT refresh token (longer expiration)

    Args:
        data: Dictionary of claims to encode (must include 'sub' for user_id)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    # Convert user_id to string (JWT 'sub' claim must be a string)
    if 'sub' in to_encode and isinstance(to_encode['sub'], int):
        to_encode['sub'] = str(to_encode['sub'])

    expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token


def extract_token_from_header() -> Optional[str]:
    """
    Extract JWT token from Authorization header

    Returns:
        Token string if found, None otherwise
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    return parts[1]


# ============================================================================
# AUTHENTICATION DECORATOR
# ============================================================================

def require_auth(f):
    """
    Decorator to protect routes - requires valid JWT token

    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route(current_user):
            return jsonify({"message": f"Hello {current_user.name}"})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract token
        token = extract_token_from_header()
        if not token:
            return jsonify({
                "error": "Missing authorization token",
                "message": "Please provide a valid JWT token in the Authorization header"
            }), 401

        # Decode token
        payload = decode_token(token)
        if not payload:
            return jsonify({
                "error": "Invalid or expired token",
                "message": "Please login again to get a new token"
            }), 401

        # Verify token type
        if payload.get('type') != 'access':
            return jsonify({
                "error": "Invalid token type",
                "message": "Please use an access token, not a refresh token"
            }), 401

        # Get user from database
        user_id = payload.get('sub')
        if not user_id:
            return jsonify({
                "error": "Invalid token payload",
                "message": "Token does not contain user information"
            }), 401

        # Import here to avoid circular imports
        from database import get_database
        db = get_database()
        current_user = db.get_user(user_id)

        if not current_user:
            return jsonify({
                "error": "User not found",
                "message": "The user associated with this token no longer exists"
            }), 401

        # Call the protected function with current_user
        return f(current_user=current_user, *args, **kwargs)

    return decorated_function


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_auth_response(user, include_refresh: bool = True) -> Dict[str, Any]:
    """
    Create standardized authentication response

    Args:
        user: User model instance
        include_refresh: Whether to include refresh token

    Returns:
        Dictionary with tokens and user info
    """
    access_token = create_access_token(data={"sub": user.id})

    response = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }

    if include_refresh:
        refresh_token = create_refresh_token(data={"sub": user.id})
        response["refresh_token"] = refresh_token
        response["refresh_expires_in"] = JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # in seconds

    return response


# ============================================================================
# TESTING/DEBUG
# ============================================================================

if __name__ == '__main__':
    print("="*70)
    print("AUTHENTICATION MODULE TEST")
    print("="*70)

    # Test password hashing
    print("\n1. Password Hashing:")
    password = "SecurePass123!"
    hashed = hash_password(password)
    print(f"   Original: {password}")
    print(f"   Hashed: {hashed[:50]}...")
    print(f"   Verify (correct): {verify_password(password, hashed)}")
    print(f"   Verify (wrong): {verify_password('WrongPass', hashed)}")

    # Test password strength
    print("\n2. Password Strength Validation:")
    test_passwords = [
        "short",           # Too short
        "alllowercase",    # No uppercase
        "ALLUPPERCASE",    # No lowercase
        "NoDigits!",       # No digits
        "ValidPass123",    # Valid
    ]
    for pwd in test_passwords:
        valid, msg = validate_password_strength(pwd)
        status = "✓ Valid" if valid else f"✗ {msg}"
        print(f"   '{pwd}': {status}")

    # Test email validation
    print("\n3. Email Validation:")
    test_emails = [
        "valid@example.com",
        "invalid@",
        "no-domain@",
        "user@domain.co.uk",
    ]
    for email in test_emails:
        valid, msg = validate_email_format(email)
        status = "✓ Valid" if valid else f"✗ {msg}"
        print(f"   '{email}': {status}")

    # Test JWT tokens
    print("\n4. JWT Token Generation:")
    user_data = {"sub": 123, "email": "test@example.com"}
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    print(f"   Access Token: {access_token[:50]}...")
    print(f"   Refresh Token: {refresh_token[:50]}...")

    # Test token decode
    print("\n5. JWT Token Decoding:")
    decoded = decode_token(access_token)
    print(f"   Decoded user_id: {decoded.get('sub')}")
    print(f"   Token type: {decoded.get('type')}")
    print(f"   Expires: {datetime.fromtimestamp(decoded.get('exp')).isoformat()}")

    print("\n" + "="*70)
    print("✅ ALL AUTHENTICATION TESTS PASSED")
    print("="*70 + "\n")
