"""
Pytest Configuration and Shared Fixtures

Provides common test fixtures for database, authentication, and test data.
Supports both unit tests and integration tests.
"""

import pytest
import sys
import os
from pathlib import Path
import uuid
from datetime import datetime, timedelta
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from httpx import AsyncClient
from fastapi.testclient import TestClient
from main import app
from database import Database
from auth_jwt import AuthManager, UserRegister, UserLogin
from painting_detector import Room, Surface, PaintCalculator
from materials import MaterialDatabase


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def db():
    """Database fixture with cleanup"""
    database = Database()
    yield database
    # Cleanup after test


@pytest.fixture
def auth_manager(db):
    """AuthManager fixture"""
    return AuthManager(db)


@pytest.fixture
def test_client():
    """Synchronous test client for simple tests"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async test client for testing async endpoints"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_user_data():
    """Test user registration data"""
    return {
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "name": "Test User",
        "password": "SecurePassword123!",
        "organization_name": "Test Company"
    }


@pytest.fixture
def test_user(auth_manager, test_user_data):
    """Create a test user and return user data with tokens"""
    # Register user
    user_register = UserRegister(**test_user_data)
    user = auth_manager.register_user(user_register)

    # Login to get tokens
    login_data = UserLogin(
        email=test_user_data["email"],
        password=test_user_data["password"]
    )
    tokens = auth_manager.login_user(login_data)

    return {
        "user": user,
        "tokens": tokens,
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }


@pytest.fixture
def auth_headers(test_user):
    """Authentication headers with JWT token"""
    return {
        "Authorization": f"Bearer {test_user['tokens'].access_token}"
    }


@pytest.fixture
def api_key_headers(test_user):
    """API key headers for public API"""
    return {
        "X-API-Key": test_user['user']['api_key']
    }


@pytest.fixture
def test_project_data():
    """Test project data"""
    return {
        "name": f"Test Project {uuid.uuid4().hex[:6]}",
        "customer": "Test Customer Inc."
    }


@pytest.fixture
def test_project(test_client, test_project_data):
    """Create a test project"""
    response = test_client.post("/projects", json=test_project_data)
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def test_room_data():
    """Test room data"""
    return {
        "name": "Living Room",
        "dimensions": {
            "length": 20.0,
            "width": 15.0,
            "height": 9.0
        },
        "notes": "Test room for integration testing"
    }


@pytest.fixture
def sample_room_with_surfaces():
    """Sample room data with calculated surfaces"""
    return {
        "id": str(uuid.uuid4()),
        "name": "Office",
        "number": "101",
        "dimensions": {
            "length": 12.0,
            "width": 10.0,
            "height": 8.0
        },
        "surfaces": {
            "walls": {
                "type": "wall",
                "area": 352.0,
                "linear_feet": 44.0,
                "height": 8.0,
                "deductions": 0.0
            },
            "ceiling": {
                "type": "ceiling",
                "area": 120.0,
                "linear_feet": 0.0,
                "height": 0.0,
                "deductions": 0.0
            }
        },
        "total_area": 472.0
    }


@pytest.fixture
def estimate_params():
    """Default estimate parameters"""
    return {
        "paint_price": 55.0,
        "labor_rate": 50.0,
        "surface_type": "smooth_drywall"
    }


@pytest.fixture
def invalid_jwt_token():
    """Invalid JWT token for unauthorized tests"""
    return "Bearer invalid.jwt.token.here"


@pytest.fixture
def expired_jwt_token(auth_manager):
    """Expired JWT token for testing token expiration"""
    # Create token that expired 1 hour ago
    data = {
        "user_id": str(uuid.uuid4()),
        "email": "expired@example.com"
    }
    expired_delta = timedelta(hours=-1)
    return auth_manager.create_access_token(data, expires_delta=expired_delta)


@pytest.fixture
def mock_file_upload():
    """Mock file upload data"""
    return {
        "filename": "test_drawing.pdf",
        "content_type": "application/pdf",
        "size": 1024 * 100  # 100KB
    }


@pytest.fixture
def cleanup_uploads():
    """Cleanup uploaded files after tests"""
    yield
    # Cleanup logic here
    upload_dir = Path("uploads")
    if upload_dir.exists():
        for project_dir in upload_dir.iterdir():
            if project_dir.is_dir():
                for file in project_dir.iterdir():
                    if file.name.startswith("test_"):
                        file.unlink()


# ============================================================================
# Unit Test Specific Fixtures
# ============================================================================

@pytest.fixture
def mock_database():
    """Mock database for unit testing without real DB connection"""
    db = Mock()

    # Mock user storage
    db.users = {}
    db.organizations = {}

    def save_user(user):
        db.users[user["id"]] = user
        return user

    def get_user_by_id(user_id):
        return db.users.get(user_id)

    def get_user_by_email(email):
        for user in db.users.values():
            if user.get("email") == email:
                return user
        return None

    def save_organization(org):
        db.organizations[org["id"]] = org
        return org

    db.save_user = save_user
    db.get_user_by_id = get_user_by_id
    db.get_user_by_email = get_user_by_email
    db.save_organization = save_organization

    return db


@pytest.fixture
def temp_materials_db(tmp_path):
    """Create a temporary material database for testing"""
    materials_file = tmp_path / "materials.json"
    db = MaterialDatabase(str(materials_file))
    return db


@pytest.fixture
def paint_calculator():
    """Create PaintCalculator instance"""
    return PaintCalculator()


@pytest.fixture
def simple_room():
    """Create a simple room with basic dimensions"""
    room = Room(
        id="room_1",
        name="Living Room",
        number="101",
        floor=1,
        dimensions={
            "length": 20.0,
            "width": 15.0,
            "height": 9.0
        },
        surfaces={}
    )

    # Add typical surfaces
    perimeter = 2 * (20.0 + 15.0)  # 70 feet
    wall_area = perimeter * 9.0  # 630 sqft

    # Deduct standard door and 2 windows
    door_area = 3.0 * 7.0  # 21 sqft
    window_area = 2 * (3.0 * 5.0)  # 30 sqft
    net_wall_area = wall_area - door_area - window_area  # 579 sqft

    room.surfaces = {
        "walls": Surface(
            type="wall",
            area=net_wall_area,
            height=9.0,
            deductions=door_area + window_area
        ),
        "ceiling": Surface(
            type="ceiling",
            area=20.0 * 15.0  # 300 sqft
        ),
        "trim": Surface(
            type="trim",
            area=67.0 * 0.5,  # 70 - 3 (door) = 67 linear feet
            linear_feet=67.0,
            height=0.5
        ),
        "doors": Surface(
            type="door",
            area=21.0 * 2  # Both sides
        )
    }

    room.total_area = sum(s.area for s in room.surfaces.values())

    return room


@pytest.fixture
def commercial_room():
    """Create a commercial space room"""
    room = Room(
        id="room_2",
        name="Conference Room",
        number="205",
        floor=2,
        dimensions={
            "length": 30.0,
            "width": 25.0,
            "height": 10.0
        },
        surfaces={}
    )

    perimeter = 2 * (30.0 + 25.0)  # 110 feet
    wall_area = perimeter * 10.0  # 1100 sqft

    # 2 doors, 4 windows
    door_area = 2 * (3.0 * 7.0)  # 42 sqft
    window_area = 4 * (4.0 * 6.0)  # 96 sqft
    net_wall_area = wall_area - door_area - window_area  # 962 sqft

    room.surfaces = {
        "walls": Surface(
            type="wall",
            area=net_wall_area,
            height=10.0,
            deductions=door_area + window_area
        ),
        "ceiling": Surface(
            type="ceiling",
            area=30.0 * 25.0  # 750 sqft
        ),
        "trim": Surface(
            type="trim",
            area=104.0 * 0.5,  # 110 - 6 (doors) = 104 linear feet
            linear_feet=104.0,
            height=0.5
        )
    }

    room.total_area = sum(s.area for s in room.surfaces.values())

    return room


@pytest.fixture
def surface_wall():
    """Create a standard wall surface"""
    return Surface(
        type="wall",
        area=500.0,
        height=9.0,
        deductions=35.0
    )


@pytest.fixture
def surface_ceiling():
    """Create a standard ceiling surface"""
    return Surface(
        type="ceiling",
        area=300.0
    )


@pytest.fixture
def sample_user_data():
    """Sample user registration data"""
    return {
        "email": "test@paintingai.com",
        "name": "Test User",
        "password": "SecurePassword123!",
        "organization_name": "Test Painting Co"
    }


@pytest.fixture
def registered_user(auth_manager, sample_user_data):
    """Pre-registered user for testing"""
    user_data = UserRegister(**sample_user_data)
    user = auth_manager.register_user(user_data)
    return user


@pytest.fixture
def valid_access_token(auth_manager, registered_user):
    """Generate a valid access token for testing"""
    token_data = {"user_id": registered_user["id"], "email": registered_user["email"]}
    return auth_manager.create_access_token(token_data)


@pytest.fixture
def valid_refresh_token(auth_manager, registered_user):
    """Generate a valid refresh token for testing"""
    token_data = {"user_id": registered_user["id"], "email": registered_user["email"]}
    return auth_manager.create_refresh_token(token_data)


# ============================================================================
# Environment Variables
# ============================================================================

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "test-stripe-key")
    monkeypatch.setenv("SENDGRID_API_KEY", "test-sendgrid-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
