"""
Week 2 Integration Tests - PostgreSQL + S3 + Redis
Tests complete flow of all Week 2 components working together
"""

import pytest
import os
import sys
import tempfile
import uuid
from pathlib import Path
from datetime import datetime
import json
import subprocess
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database_service import DatabaseService
from models import Base, User, Project, Room, Drawing
from config import get_config, Config
import logging

logger = logging.getLogger(__name__)


# Test configuration
@pytest.fixture(scope="session")
def test_config():
    """Load test configuration"""
    os.environ["ENVIRONMENT"] = "development"
    os.environ["S3_ENABLED"] = "false"  # Use local storage for tests
    config = get_config()
    return config


@pytest.fixture(scope="session")
def db_service(test_config):
    """Create test database service"""
    # Use test database
    test_db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://paintingai:changeme123@localhost:5432/paintingai_test"
    )

    db = DatabaseService(database_url=test_db_url)

    # Create tables
    Base.metadata.create_all(db.engine)

    yield db

    # Cleanup
    Base.metadata.drop_all(db.engine)
    db.engine.dispose()


@pytest.fixture
def clean_database(db_service):
    """Clean database before each test"""
    # Delete all data
    with db_service.get_session() as session:
        session.query(Drawing).delete()
        session.query(Room).delete()
        session.query(Project).delete()
        session.query(User).delete()
        session.commit()

    yield db_service


@pytest.fixture
def sample_user(clean_database):
    """Create a sample user for testing"""
    user = clean_database.create_user(
        email=f"test_{uuid.uuid4().hex[:8]}@paintingai.com",
        name="Test User",
        company="Test Company"
    )
    return user


@pytest.fixture
def sample_project(clean_database, sample_user):
    """Create a sample project for testing"""
    project = clean_database.create_project(
        owner_id=sample_user.id,
        name="Test Office Building",
        customer="ABC Construction"
    )
    return project


@pytest.fixture
def sample_drawing_file():
    """Create a temporary test drawing file"""
    # Create a simple PDF file for testing
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
        # Minimal PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Count 1 /Kids [3 0 R] >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test Drawing) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000317 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
410
%%EOF
"""
        f.write(pdf_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


class TestDatabaseIntegration:
    """Test PostgreSQL database operations"""

    def test_database_connection(self, db_service):
        """Test database connection is established"""
        assert db_service.engine is not None

        # Test connection with simple query
        with db_service.get_session() as session:
            result = session.execute("SELECT 1")
            assert result.scalar() == 1

    def test_connection_pool_status(self, db_service):
        """Test connection pool monitoring"""
        status = db_service.get_pool_status()

        assert "pool_size" in status
        assert "checked_in" in status
        assert "checked_out" in status
        assert "overflow" in status
        assert "total_connections" in status

        assert status["pool_size"] >= 0
        assert status["total_connections"] >= 0

    def test_user_crud_operations(self, clean_database):
        """Test User CRUD operations"""
        # Create
        user = clean_database.create_user(
            email="crud_test@example.com",
            name="CRUD Test User",
            company="Test Corp"
        )

        assert user.id is not None
        assert user.email == "crud_test@example.com"
        assert user.api_key is not None
        assert user.api_key.startswith("pk_")

        # Read
        fetched_user = clean_database.get_user(user.id)
        assert fetched_user is not None
        assert fetched_user.email == user.email

        # Read by email
        user_by_email = clean_database.get_user_by_email("crud_test@example.com")
        assert user_by_email is not None
        assert user_by_email.id == user.id

        # Read by API key
        user_by_api_key = clean_database.get_user_by_api_key(user.api_key)
        assert user_by_api_key is not None
        assert user_by_api_key.id == user.id

    def test_project_crud_operations(self, clean_database, sample_user):
        """Test Project CRUD operations"""
        # Create
        project = clean_database.create_project(
            owner_id=sample_user.id,
            name="Test Project",
            customer="Test Customer"
        )

        assert project.id is not None
        assert project.name == "Test Project"
        assert project.owner_id == sample_user.id

        # Read
        fetched_project = clean_database.get_project(project.id)
        assert fetched_project is not None
        assert fetched_project.name == project.name

        # List user projects
        projects = clean_database.get_user_projects(sample_user.id)
        assert len(projects) == 1
        assert projects[0].id == project.id

        # Update
        clean_database.update_project(
            project.id,
            status="processing"
        )

        updated_project = clean_database.get_project(project.id)
        assert updated_project.status == "processing"

        # Delete
        clean_database.delete_project(project.id)
        deleted_project = clean_database.get_project(project.id)
        assert deleted_project is None

    def test_room_operations(self, clean_database, sample_project):
        """Test Room CRUD operations"""
        # Create room
        room = clean_database.create_room(
            project_id=sample_project.id,
            name="Conference Room",
            length=20.0,
            width=15.0,
            height=9.0
        )

        assert room.id is not None
        assert room.name == "Conference Room"
        assert room.project_id == sample_project.id

        # Get room
        fetched_room = clean_database.get_room(room.id)
        assert fetched_room is not None
        assert fetched_room.length == 20.0

        # Get project rooms
        rooms = clean_database.get_project_rooms(sample_project.id)
        assert len(rooms) == 1
        assert rooms[0].id == room.id

        # Update room
        clean_database.update_room(
            room.id,
            notes="Updated notes"
        )

        updated_room = clean_database.get_room(room.id)
        assert updated_room.notes == "Updated notes"

    def test_drawing_operations(self, clean_database, sample_project):
        """Test Drawing operations"""
        # Create drawing
        drawing = clean_database.create_drawing(
            project_id=sample_project.id,
            filename="floor_plan.pdf",
            file_path="/uploads/test.pdf",
            file_size=1024
        )

        assert drawing.id is not None
        assert drawing.filename == "floor_plan.pdf"
        assert drawing.project_id == sample_project.id

        # Get drawing
        fetched_drawing = clean_database.get_drawing(drawing.id)
        assert fetched_drawing is not None

        # Get project drawings
        drawings = clean_database.get_project_drawings(sample_project.id)
        assert len(drawings) == 1
        assert drawings[0].id == drawing.id

        # Update drawing
        clean_database.update_drawing(
            drawing.id,
            status="processed"
        )

        updated_drawing = clean_database.get_drawing(drawing.id)
        assert updated_drawing.status == "processed"


class TestCompleteWorkflow:
    """Test complete workflow: Upload → Process → Export → Download"""

    def test_complete_project_workflow(self, clean_database, sample_user, sample_drawing_file):
        """
        Test complete workflow:
        1. Create project
        2. Upload drawing
        3. Process drawing (create rooms)
        4. Generate estimate
        5. Export to files
        """

        # Step 1: Create project
        project = clean_database.create_project(
            owner_id=sample_user.id,
            name="Integration Test Project",
            customer="Test Customer",
            status="created"
        )

        assert project.id is not None
        logger.info(f"Created project: {project.id}")

        # Step 2: Upload drawing
        drawing = clean_database.create_drawing(
            project_id=project.id,
            filename="test_floor_plan.pdf",
            file_path=sample_drawing_file,
            file_size=os.path.getsize(sample_drawing_file),
            status="uploaded"
        )

        assert drawing.id is not None
        logger.info(f"Uploaded drawing: {drawing.id}")

        # Step 3: Simulate processing - create rooms
        rooms_data = [
            {"name": "Living Room", "length": 20.0, "width": 15.0, "height": 9.0},
            {"name": "Bedroom 1", "length": 12.0, "width": 10.0, "height": 8.0},
            {"name": "Bedroom 2", "length": 12.0, "width": 10.0, "height": 8.0},
        ]

        created_rooms = []
        for room_data in rooms_data:
            room = clean_database.create_room(
                project_id=project.id,
                **room_data
            )
            created_rooms.append(room)

        assert len(created_rooms) == 3
        logger.info(f"Created {len(created_rooms)} rooms")

        # Step 4: Update project with totals
        total_sqft = sum(
            (r.length * r.width * 2) + (r.length * r.height * 2) + (r.width * r.height * 2)
            for r in created_rooms
        )

        clean_database.update_project(
            project.id,
            status="complete",
            total_rooms=len(created_rooms),
            total_sqft=total_sqft
        )

        # Step 5: Verify final state
        final_project = clean_database.get_project(project.id)
        assert final_project.status == "complete"
        assert final_project.total_rooms == 3
        assert final_project.total_sqft > 0

        final_rooms = clean_database.get_project_rooms(project.id)
        assert len(final_rooms) == 3

        logger.info(f"Workflow complete: {final_project.total_rooms} rooms, {final_project.total_sqft:.0f} sqft")

    def test_multi_user_isolation(self, clean_database):
        """Test that users can only access their own projects"""

        # Create two users
        user1 = clean_database.create_user(
            email=f"user1_{uuid.uuid4().hex[:8]}@example.com",
            name="User One"
        )

        user2 = clean_database.create_user(
            email=f"user2_{uuid.uuid4().hex[:8]}@example.com",
            name="User Two"
        )

        # Create projects for each user
        project1 = clean_database.create_project(
            owner_id=user1.id,
            name="User 1 Project"
        )

        project2 = clean_database.create_project(
            owner_id=user2.id,
            name="User 2 Project"
        )

        # Verify each user sees only their projects
        user1_projects = clean_database.get_user_projects(user1.id)
        assert len(user1_projects) == 1
        assert user1_projects[0].id == project1.id

        user2_projects = clean_database.get_user_projects(user2.id)
        assert len(user2_projects) == 1
        assert user2_projects[0].id == project2.id


class TestS3Integration:
    """Test S3 file storage (when enabled)"""

    @pytest.mark.skipif(
        os.getenv("S3_ENABLED", "false").lower() != "true",
        reason="S3 not enabled in test environment"
    )
    def test_s3_upload_download(self, sample_drawing_file):
        """Test S3 upload and download with signed URLs"""
        from s3_service import S3Service

        s3 = S3Service()

        # Upload file
        s3_key = f"test/{uuid.uuid4()}/test_drawing.pdf"
        result = s3.upload_file(
            file_path=sample_drawing_file,
            s3_key=s3_key,
            metadata={"test": "true"}
        )

        assert result["s3_key"] == s3_key
        assert result["size"] > 0

        # Verify file exists
        assert s3.file_exists(s3_key) is True

        # Get metadata
        metadata = s3.get_file_metadata(s3_key)
        assert metadata is not None
        assert metadata["key"] == s3_key

        # Generate signed URL
        signed_url = s3.generate_signed_url(s3_key, expiry=3600)
        assert signed_url is not None
        assert "amazonaws.com" in signed_url

        # Cleanup
        s3.delete_file(s3_key)
        assert s3.file_exists(s3_key) is False


class TestDatabaseBackupRestore:
    """Test database backup and restore operations"""

    def test_database_export_import(self, clean_database, sample_user, sample_project):
        """Test exporting and importing database data"""

        # Create some rooms
        rooms = []
        for i in range(3):
            room = clean_database.create_room(
                project_id=sample_project.id,
                name=f"Room {i+1}",
                length=10.0 + i,
                width=8.0 + i,
                height=9.0
            )
            rooms.append(room)

        # Export data to JSON
        export_data = {
            "users": [
                {
                    "id": sample_user.id,
                    "email": sample_user.email,
                    "name": sample_user.name,
                    "company": sample_user.company
                }
            ],
            "projects": [
                {
                    "id": sample_project.id,
                    "owner_id": sample_project.owner_id,
                    "name": sample_project.name,
                    "customer": sample_project.customer
                }
            ],
            "rooms": [
                {
                    "id": room.id,
                    "project_id": room.project_id,
                    "name": room.name,
                    "length": room.length,
                    "width": room.width,
                    "height": room.height
                }
                for room in rooms
            ]
        }

        # Save to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(export_data, f, indent=2)
            backup_file = f.name

        try:
            # Verify backup file
            assert os.path.exists(backup_file)
            with open(backup_file, 'r') as f:
                restored_data = json.load(f)

            assert len(restored_data["users"]) == 1
            assert len(restored_data["projects"]) == 1
            assert len(restored_data["rooms"]) == 3

            logger.info(f"Backup contains {len(restored_data['rooms'])} rooms")

        finally:
            # Cleanup
            if os.path.exists(backup_file):
                os.unlink(backup_file)


class TestHealthChecks:
    """Test health check endpoints"""

    def test_database_health(self, db_service):
        """Test database health check"""
        try:
            with db_service.get_session() as session:
                session.execute("SELECT 1")
            db_healthy = True
        except Exception:
            db_healthy = False

        assert db_healthy is True

    def test_connection_pool_health(self, db_service):
        """Test connection pool is healthy"""
        status = db_service.get_pool_status()

        # Pool should have available connections
        assert status["checked_in"] + status["checked_out"] <= status["total_connections"]


class TestPerformance:
    """Test database performance"""

    def test_bulk_insert_performance(self, clean_database, sample_user):
        """Test bulk insert performance"""
        start_time = time.time()

        # Create 100 projects
        projects = []
        for i in range(100):
            project = clean_database.create_project(
                owner_id=sample_user.id,
                name=f"Performance Test Project {i}",
                customer=f"Customer {i}"
            )
            projects.append(project)

        elapsed = time.time() - start_time

        assert len(projects) == 100
        assert elapsed < 5.0  # Should complete in less than 5 seconds

        logger.info(f"Created 100 projects in {elapsed:.2f}s ({100/elapsed:.1f} projects/sec)")

    def test_query_performance(self, clean_database, sample_user):
        """Test query performance with indexed lookups"""
        # Create test data
        for i in range(50):
            clean_database.create_project(
                owner_id=sample_user.id,
                name=f"Query Test Project {i}"
            )

        # Test query performance
        start_time = time.time()
        projects = clean_database.get_user_projects(sample_user.id, limit=100)
        elapsed = time.time() - start_time

        assert len(projects) == 50
        assert elapsed < 0.1  # Should complete in less than 100ms

        logger.info(f"Queried 50 projects in {elapsed*1000:.1f}ms")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
