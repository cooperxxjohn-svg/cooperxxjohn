"""
JWT Authentication System
Production-ready authentication with bcrypt password hashing and JWT tokens
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict

from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-min-32-chars")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# Pydantic Models
class UserRegister(BaseModel):
    """User registration request"""
    email: str
    name: str
    password: str
    organization_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login request"""
    email: str
    password: str


class Token(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Data stored in JWT token"""
    user_id: str
    email: str
    exp: Optional[datetime] = None


class User(BaseModel):
    """User model for responses"""
    id: str
    email: str
    name: str
    plan: str
    api_key: str
    created_at: str


class AuthManager:
    """Manage authentication with JWT and bcrypt"""

    def __init__(self, database):
        """
        Initialize with database instance

        Args:
            database: Database or DatabaseService instance
        """
        self.db = database

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token

        Args:
            data: Data to encode in token (should include user_id, email)
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "type": "access"})

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """
        Create a JWT refresh token (longer expiration)

        Args:
            data: Data to encode in token

        Returns:
            Encoded JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode.update({"exp": expire, "type": "refresh"})

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def decode_token(self, token: str) -> TokenData:
        """
        Decode and validate a JWT token

        Args:
            token: JWT token string

        Returns:
            TokenData with user_id and email

        Raises:
            HTTPException: If token is invalid or expired
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("user_id")
            email: str = payload.get("email")

            if user_id is None or email is None:
                raise credentials_exception

            return TokenData(user_id=user_id, email=email)

        except JWTError:
            raise credentials_exception

    def generate_api_key(self) -> str:
        """Generate a random API key"""
        return f"pk_{uuid.uuid4().hex}"

    def register_user(self, user_data: UserRegister) -> Dict:
        """
        Register a new user

        Args:
            user_data: UserRegister model with email, name, password

        Returns:
            User dict with id, email, name, api_key

        Raises:
            HTTPException: If email already exists
        """
        # Check if user exists
        existing_user = self.db.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user
        user_id = str(uuid.uuid4())
        hashed_password = self.hash_password(user_data.password)
        api_key = self.generate_api_key()

        user = {
            "id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "password_hash": hashed_password,
            "api_key": api_key,
            "plan": "trial",
            "subscription_status": "trialing",
            "settings": {
                "trial_started": datetime.utcnow().isoformat(),
                "trial_ends": (datetime.utcnow() + timedelta(days=14)).isoformat()
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        self.db.save_user(user)

        # Create organization if provided
        if user_data.organization_name:
            org_id = str(uuid.uuid4())
            organization = {
                "id": org_id,
                "name": user_data.organization_name,
                "owner_id": user_id,
                "plan": "trial",
                "settings": {},
                "created_at": datetime.utcnow().isoformat()
            }
            self.db.save_organization(organization)

        # Return user without password
        user.pop("password_hash", None)
        return user

    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user with email and password

        Args:
            email: User email
            password: Plain text password

        Returns:
            User dict if authentication successful, None otherwise
        """
        user = self.db.get_user_by_email(email)
        if not user:
            return None

        if not self.verify_password(password, user.get("password_hash", "")):
            return None

        # Remove password hash before returning
        user.pop("password_hash", None)
        return user

    def login_user(self, login_data: UserLogin) -> Token:
        """
        Login user and return JWT tokens

        Args:
            login_data: UserLogin model with email and password

        Returns:
            Token model with access_token and refresh_token

        Raises:
            HTTPException: If credentials are invalid
        """
        user = self.authenticate_user(login_data.email, login_data.password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create tokens
        token_data = {"user_id": user["id"], "email": user["email"]}
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        )

    def refresh_access_token(self, refresh_token: str) -> Token:
        """
        Generate new access token from refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            New Token with fresh access_token

        Raises:
            HTTPException: If refresh token is invalid
        """
        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )

            user_id = payload.get("user_id")
            email = payload.get("email")

            if not user_id or not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )

            # Create new tokens
            token_data = {"user_id": user_id, "email": email}
            new_access_token = self.create_access_token(token_data)
            new_refresh_token = self.create_refresh_token(token_data)

            return Token(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> Dict:
        """
        Dependency to get current user from JWT token

        Args:
            token: JWT token from Authorization header

        Returns:
            User dict

        Raises:
            HTTPException: If token is invalid or user not found
        """
        token_data = self.decode_token(token)

        user = self.db.get_user_by_id(token_data.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        # Remove password hash
        user.pop("password_hash", None)
        return user


# Helper function to create AuthManager instance
def get_auth_manager(db) -> AuthManager:
    """Create AuthManager instance with database"""
    return AuthManager(db)


if __name__ == "__main__":
    # Test password hashing
    print("🔐 Testing JWT Authentication System\n")

    manager = AuthManager(None)  # No database for testing

    # Test password hashing
    password = "secure_password_123"
    hashed = manager.hash_password(password)
    print(f"✓ Password hashed: {hashed[:50]}...")
    print(f"✓ Verification: {manager.verify_password(password, hashed)}")
    print(f"✗ Wrong password: {manager.verify_password('wrong', hashed)}")

    # Test token creation
    token_data = {"user_id": "user123", "email": "test@example.com"}
    access_token = manager.create_access_token(token_data)
    print(f"\n✓ Access token created: {access_token[:50]}...")

    # Test token decoding
    decoded = manager.decode_token(access_token)
    print(f"✓ Token decoded: user_id={decoded.user_id}, email={decoded.email}")

    # Test API key generation
    api_key = manager.generate_api_key()
    print(f"\n✓ API key generated: {api_key}")

    print("\n✅ All authentication functions working!")
