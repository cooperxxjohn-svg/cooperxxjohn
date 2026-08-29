"""
Authentication middleware for Painting.ai
Uses simple API key authentication for MVP
"""

from fastapi import Header, HTTPException, Depends
from typing import Optional
import secrets
import json
from pathlib import Path


class AuthManager:
    """Simple API key based authentication"""

    def __init__(self, users_file: str = "data/users.json"):
        self.users_file = Path(users_file)
        self.users_file.parent.mkdir(exist_ok=True)

        if not self.users_file.exists():
            self._init_users()

    def _init_users(self):
        """Initialize with demo user"""
        demo_user = {
            "demo@paintingai.com": {
                "api_key": "demo_key_12345",
                "name": "Demo User",
                "plan": "starter",
                "projects_limit": 50,
                "created_at": "2026-05-20T00:00:00"
            }
        }
        self._save_users(demo_user)

    def _load_users(self):
        with open(self.users_file, "r") as f:
            return json.load(f)

    def _save_users(self, users):
        with open(self.users_file, "w") as f:
            json.dump(users, f, indent=2)

    def create_user(self, email: str, name: str, plan: str = "starter"):
        """Create a new user"""
        users = self._load_users()

        if email in users:
            raise ValueError("User already exists")

        api_key = f"pk_{secrets.token_urlsafe(32)}"

        users[email] = {
            "api_key": api_key,
            "name": name,
            "plan": plan,
            "projects_limit": 50 if plan == "starter" else -1,
            "created_at": "2026-05-20T00:00:00"
        }

        self._save_users(users)
        return api_key

    def verify_api_key(self, api_key: str) -> Optional[dict]:
        """Verify API key and return user info"""
        users = self._load_users()

        for email, user_data in users.items():
            if user_data["api_key"] == api_key:
                return {
                    "email": email,
                    **user_data
                }

        return None

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        users = self._load_users()

        if email in users:
            return {
                "email": email,
                **users[email]
            }

        return None


# Global auth manager instance
auth_manager = AuthManager()


async def get_current_user(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """Dependency to get current authenticated user"""

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Add X-API-Key header."
        )

    user = auth_manager.verify_api_key(x_api_key)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return user


async def get_optional_user(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """Optional authentication - returns None if no key provided"""

    if not x_api_key:
        return None

    return auth_manager.verify_api_key(x_api_key)


if __name__ == "__main__":
    # Test auth system
    auth = AuthManager()

    # Create test user
    api_key = auth.create_user(
        email="test@example.com",
        name="Test User",
        plan="pro"
    )

    print(f"Created user with API key: {api_key}")

    # Verify key
    user = auth.verify_api_key(api_key)
    print(f"Verified user: {user}")
