"""
Test database migration and CRUD operations
Ensures PostgreSQL setup works correctly
"""

import pytest
import os
import sys
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_service import DatabaseService
from models import User, Project, Room, Drawing, Organization, TeamMember, UserRole, ProjectStatus


class TestDatabaseMigration:
    """Test suite for database migration"""

    @pytest.fixture(scope="class")
    def db_service(self):
        """Create database service for testing"""
        # Use test database URL if available
        test_db_url = os.getenv(
            "TEST_DATABASE_URL",
            "postgresql://paintingai:changeme123@localhost:5432/paintingai_test"
        )
        db = DatabaseService(database_url=test_db_url)

        # Create tables
        db.create_tables()

        yield db

        # Cleanup would go here if needed

    def test_database_connection(self, db_service):
        """Test database connection is working"""
        assert db_service.engine is not None
        assert db_service.SessionLocal is not None

        # Test connection pool status
        pool_status = db_service.get_pool_status()
        assert pool_status["pool_size"] > 0
        print(f"✓ Database connection pool: {pool_status}")

    def test_create_tables(self, db_service):
        """Test that all tables are created"""
        # This should not raise any errors
        db_service.create_tables()
        print("✓ All database tables created successfully")

    def test_user_crud(self, db_service):
        """Test User CRUD operations"""
        # Create user
        user = db_service.create_user(
            email=f"test-{uuid.uuid4()}@paintingai.com",
            name="Test User",
            company="Test Company",
            phone="555-0100"
        )
        assert user.id is not None
        assert user.api_key is not None
        assert user.email.startswith("test-")
        print(f"✓ User created: {user.email} (ID: {user.id})")

        # Read user
        retrieved_user = db_service.get_user(user.id)
        assert retrieved_user is not None
        assert retrieved_user.email == user.email
        print(f"✓ User retrieved by ID")

        # Get user by email
        user_by_email = db_service.get_user_by_email(user.email)
        assert user_by_email is not None
        assert user_by_email.id == user.id
        print(f"✓ User retrieved by email")

        # Get user by API key
        user_by_key = db_service.get_user_by_api_key(user.api_key)
        assert user_by_key is not None
        assert user_by_key.id == user.id
        print(f"✓ User retrieved by API key")

    def test_project_crud(self, db_service):
        """Test Project CRUD operations"""
        # Create user first
        user = db_service.create_user(
            email=f"project-owner-{uuid.uuid4()}@paintingai.com",
            name="Project Owner"
        )

        # Create project
        project = db_service.create_project(
            owner_id=user.id,
            name="Test Office Building",
            customer="ABC Construction",
            customer_email="abc@example.com",
            address="123 Main St",
            city="San Francisco",
            state="CA",
            zip_code="94105",
            project_type="commercial"
        )
        assert project.id is not None
        assert project.name == "Test Office Building"
        assert project.owner_id == user.id
        print(f"✓ Project created: {project.name} (ID: {project.id})")

        # Read project
        retrieved_project = db_service.get_project(project.id)
        assert retrieved_project is not None
        assert retrieved_project.customer == "ABC Construction"
        print(f"✓ Project retrieved")

        # Get user projects
        user_projects = db_service.get_user_projects(user.id)
        assert len(user_projects) > 0
        assert user_projects[0].id == project.id
        print(f"✓ User projects retrieved: {len(user_projects)} project(s)")

        # Update project
        db_service.update_project(
            project.id,
            bid_amount=50000.0,
            status="submitted"
        )
        updated_project = db_service.get_project(project.id)
        assert updated_project.bid_amount == 50000.0
        print(f"✓ Project updated with bid amount")

    def test_room_crud(self, db_service):
        """Test Room CRUD operations"""
        # Create user and project
        user = db_service.create_user(
            email=f"room-owner-{uuid.uuid4()}@paintingai.com",
            name="Room Owner"
        )
        project = db_service.create_project(
            owner_id=user.id,
            name="Test Project for Rooms"
        )

        # Create room
        room = db_service.create_room(
            project_id=project.id,
            name="Conference Room",
            number="101",
            floor=1,
            length=20.0,
            width=15.0,
            height=9.0,
            total_area=300.0
        )
        assert room.id is not None
        assert room.name == "Conference Room"
        assert room.project_id == project.id
        print(f"✓ Room created: {room.name} (ID: {room.id})")

        # Read room
        retrieved_room = db_service.get_room(room.id)
        assert retrieved_room is not None
        assert retrieved_room.length == 20.0
        print(f"✓ Room retrieved")

        # Get project rooms
        project_rooms = db_service.get_project_rooms(project.id)
        assert len(project_rooms) > 0
        assert project_rooms[0].id == room.id
        print(f"✓ Project rooms retrieved: {len(project_rooms)} room(s)")

        # Update room
        db_service.update_room(
            room.id,
            total_gallons=5.5,
            labor_hours=8.0
        )
        updated_room = db_service.get_room(room.id)
        assert updated_room.total_gallons == 5.5
        print(f"✓ Room updated with calculations")

    def test_drawing_crud(self, db_service):
        """Test Drawing CRUD operations"""
        # Create user and project
        user = db_service.create_user(
            email=f"drawing-owner-{uuid.uuid4()}@paintingai.com",
            name="Drawing Owner"
        )
        project = db_service.create_project(
            owner_id=user.id,
            name="Test Project for Drawings"
        )

        # Create drawing
        drawing = db_service.create_drawing(
            project_id=project.id,
            filename="floor-plan-1.pdf",
            original_filename="Office Floor Plan.pdf",
            file_path="/uploads/floor-plan-1.pdf",
            file_size=1024000,
            file_type="pdf",
            drawing_type="floor_plan",
            status="processing"
        )
        assert drawing.id is not None
        assert drawing.filename == "floor-plan-1.pdf"
        print(f"✓ Drawing created: {drawing.filename} (ID: {drawing.id})")

        # Read drawing
        retrieved_drawing = db_service.get_drawing(drawing.id)
        assert retrieved_drawing is not None
        assert retrieved_drawing.file_type == "pdf"
        print(f"✓ Drawing retrieved")

        # Get project drawings
        project_drawings = db_service.get_project_drawings(project.id)
        assert len(project_drawings) > 0
        assert project_drawings[0].id == drawing.id
        print(f"✓ Project drawings retrieved: {len(project_drawings)} drawing(s)")

        # Update drawing
        db_service.update_drawing(
            drawing.id,
            status="complete",
            rooms_detected=5,
            ai_confidence=0.95
        )
        updated_drawing = db_service.get_drawing(drawing.id)
        assert updated_drawing.status == "complete"
        assert updated_drawing.rooms_detected == 5
        print(f"✓ Drawing updated with processing results")

    def test_organization_and_team(self, db_service):
        """Test Organization and TeamMember operations"""
        # Create owner
        owner = db_service.create_user(
            email=f"org-owner-{uuid.uuid4()}@paintingai.com",
            name="Organization Owner"
        )

        # Create organization
        org = db_service.create_organization(
            owner_id=owner.id,
            name="Test Painting Company"
        )
        assert org.id is not None
        assert org.name == "Test Painting Company"
        print(f"✓ Organization created: {org.name} (ID: {org.id})")

        # Create team member
        member_user = db_service.create_user(
            email=f"team-member-{uuid.uuid4()}@paintingai.com",
            name="Team Member"
        )

        team_member = db_service.add_team_member(
            org_id=org.id,
            user_id=member_user.id,
            role=UserRole.ESTIMATOR
        )
        assert team_member.id is not None
        assert team_member.organization_id == org.id
        assert team_member.user_id == member_user.id
        print(f"✓ Team member added to organization")

    def test_project_deletion_cascade(self, db_service):
        """Test that deleting a project cascades to rooms and drawings"""
        # Create user and project
        user = db_service.create_user(
            email=f"cascade-test-{uuid.uuid4()}@paintingai.com",
            name="Cascade Test"
        )
        project = db_service.create_project(
            owner_id=user.id,
            name="Test Project for Cascade"
        )

        # Create room and drawing
        room = db_service.create_room(
            project_id=project.id,
            name="Test Room"
        )
        drawing = db_service.create_drawing(
            project_id=project.id,
            filename="test.pdf"
        )

        # Delete project
        db_service.delete_project(project.id)

        # Verify project, room, and drawing are deleted
        assert db_service.get_project(project.id) is None
        assert db_service.get_room(room.id) is None
        assert db_service.get_drawing(drawing.id) is None
        print(f"✓ Cascade delete working correctly")

    def test_relationships(self, db_service):
        """Test SQLAlchemy relationships"""
        # Create user and project
        user = db_service.create_user(
            email=f"relationships-{uuid.uuid4()}@paintingai.com",
            name="Relationships Test"
        )
        project = db_service.create_project(
            owner_id=user.id,
            name="Relationships Test Project"
        )

        # Create multiple rooms
        for i in range(3):
            db_service.create_room(
                project_id=project.id,
                name=f"Room {i+1}"
            )

        # Test relationship loading
        with db_service.get_session() as session:
            loaded_project = session.query(Project).filter(Project.id == project.id).first()
            assert loaded_project is not None
            # Rooms should be loaded via relationship
            assert len(loaded_project.rooms) == 3
            print(f"✓ SQLAlchemy relationships working: {len(loaded_project.rooms)} rooms loaded")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
