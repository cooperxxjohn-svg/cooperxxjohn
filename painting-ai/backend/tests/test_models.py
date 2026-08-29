"""
Database Models Unit Tests

Tests for SQLAlchemy model validation, relationships,
and data integrity for User, Project, and Room models.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from models import (
    Base,
    User,
    Organization,
    TeamMember,
    Project,
    Room,
    Drawing,
    MaterialItem,
    UserRole,
    ProjectStatus
)


# ============================================================================
# Test Database Setup
# ============================================================================

@pytest.fixture
def test_engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create test database session"""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()


# ============================================================================
# User Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestUserModel:
    """Test User model"""

    def test_create_user_with_required_fields(self, test_session):
        """Test creating user with required fields"""
        user = User(
            id="user_123",
            email="test@paintingai.com",
            name="Test User",
            api_key="pk_test123456"
        )

        test_session.add(user)
        test_session.commit()

        assert user.id == "user_123"
        assert user.email == "test@paintingai.com"
        assert user.name == "Test User"
        assert user.api_key == "pk_test123456"

    def test_user_default_values(self, test_session):
        """Test user default field values"""
        user = User(
            id="user_456",
            email="defaults@test.com",
            name="Defaults User",
            api_key="pk_defaults"
        )

        test_session.add(user)
        test_session.commit()

        assert user.plan == "trial"
        assert user.default_paint_price == 55.0
        assert user.default_labor_rate == 50.0
        assert user.default_surface_type == "smooth_drywall"
        assert user.is_active is True
        assert user.settings == {}

    def test_user_email_must_be_unique(self, test_session):
        """Test that email must be unique"""
        user1 = User(
            id="user_1",
            email="unique@test.com",
            name="User 1",
            api_key="pk_1"
        )
        test_session.add(user1)
        test_session.commit()

        user2 = User(
            id="user_2",
            email="unique@test.com",
            name="User 2",
            api_key="pk_2"
        )
        test_session.add(user2)

        with pytest.raises(IntegrityError):
            test_session.commit()

    def test_user_api_key_must_be_unique(self, test_session):
        """Test that API key must be unique"""
        user1 = User(
            id="user_1",
            email="user1@test.com",
            name="User 1",
            api_key="pk_unique"
        )
        test_session.add(user1)
        test_session.commit()

        user2 = User(
            id="user_2",
            email="user2@test.com",
            name="User 2",
            api_key="pk_unique"
        )
        test_session.add(user2)

        with pytest.raises(IntegrityError):
            test_session.commit()

    def test_user_subscription_fields(self, test_session):
        """Test user subscription-related fields"""
        user = User(
            id="user_sub",
            email="subscriber@test.com",
            name="Subscriber",
            api_key="pk_sub",
            plan="pro",
            stripe_customer_id="cus_123",
            stripe_subscription_id="sub_123",
            subscription_status="active"
        )

        test_session.add(user)
        test_session.commit()

        assert user.plan == "pro"
        assert user.stripe_customer_id == "cus_123"
        assert user.subscription_status == "active"

    def test_user_created_at_timestamp(self, test_session):
        """Test that created_at is automatically set"""
        user = User(
            id="user_time",
            email="time@test.com",
            name="Time User",
            api_key="pk_time"
        )

        test_session.add(user)
        test_session.commit()

        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)


# ============================================================================
# Organization Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestOrganizationModel:
    """Test Organization model"""

    def test_create_organization(self, test_session):
        """Test creating organization"""
        # Create user first
        user = User(
            id="user_org",
            email="org@test.com",
            name="Org Owner",
            api_key="pk_org"
        )
        test_session.add(user)
        test_session.commit()

        # Create organization
        org = Organization(
            id="org_123",
            name="Test Painting Co",
            owner_id=user.id
        )

        test_session.add(org)
        test_session.commit()

        assert org.id == "org_123"
        assert org.name == "Test Painting Co"
        assert org.owner_id == user.id

    def test_organization_default_values(self, test_session):
        """Test organization default values"""
        user = User(
            id="user_org2",
            email="org2@test.com",
            name="Owner",
            api_key="pk_org2"
        )
        test_session.add(user)

        org = Organization(
            id="org_456",
            name="Default Org",
            owner_id=user.id
        )

        test_session.add(org)
        test_session.commit()

        assert org.plan == "starter"
        assert org.seats == 1
        assert org.settings == {}


# ============================================================================
# Project Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestProjectModel:
    """Test Project model"""

    def test_create_project_with_required_fields(self, test_session):
        """Test creating project"""
        user = User(
            id="user_proj",
            email="project@test.com",
            name="Project Owner",
            api_key="pk_proj"
        )
        test_session.add(user)
        test_session.commit()

        project = Project(
            id="proj_123",
            name="Office Building Repaint",
            owner_id=user.id
        )

        test_session.add(project)
        test_session.commit()

        assert project.id == "proj_123"
        assert project.name == "Office Building Repaint"
        assert project.owner_id == user.id

    def test_project_default_values(self, test_session):
        """Test project default field values"""
        user = User(
            id="user_proj2",
            email="proj2@test.com",
            name="Owner",
            api_key="pk_proj2"
        )
        test_session.add(user)

        project = Project(
            id="proj_456",
            name="Default Project",
            owner_id=user.id
        )

        test_session.add(project)
        test_session.commit()

        assert project.status == ProjectStatus.DRAFT
        assert project.total_rooms == 0
        assert project.total_sqft == 0.0
        assert project.total_gallons == 0.0
        assert project.total_labor_hours == 0.0
        assert project.material_cost == 0.0
        assert project.labor_cost == 0.0
        assert project.markup_percentage == 30.0
        assert project.tags == []

    def test_project_status_enum(self, test_session):
        """Test project status enum values"""
        user = User(
            id="user_status",
            email="status@test.com",
            name="Status User",
            api_key="pk_status"
        )
        test_session.add(user)

        project = Project(
            id="proj_status",
            name="Status Test",
            owner_id=user.id,
            status=ProjectStatus.COMPLETE
        )

        test_session.add(project)
        test_session.commit()

        assert project.status == ProjectStatus.COMPLETE
        assert project.status.value == "complete"

    def test_project_customer_information(self, test_session):
        """Test project customer fields"""
        user = User(
            id="user_cust",
            email="cust@test.com",
            name="User",
            api_key="pk_cust"
        )
        test_session.add(user)

        project = Project(
            id="proj_cust",
            name="Customer Project",
            owner_id=user.id,
            customer="ABC Construction",
            customer_email="contact@abc.com",
            customer_phone="555-1234"
        )

        test_session.add(project)
        test_session.commit()

        assert project.customer == "ABC Construction"
        assert project.customer_email == "contact@abc.com"
        assert project.customer_phone == "555-1234"

    def test_project_location_fields(self, test_session):
        """Test project location fields"""
        user = User(
            id="user_loc",
            email="loc@test.com",
            name="User",
            api_key="pk_loc"
        )
        test_session.add(user)

        project = Project(
            id="proj_loc",
            name="Location Test",
            owner_id=user.id,
            address="123 Main St",
            city="Portland",
            state="OR",
            zip_code="97201"
        )

        test_session.add(project)
        test_session.commit()

        assert project.address == "123 Main St"
        assert project.city == "Portland"
        assert project.state == "OR"
        assert project.zip_code == "97201"

    def test_project_pricing_fields(self, test_session):
        """Test project pricing calculations"""
        user = User(
            id="user_price",
            email="price@test.com",
            name="User",
            api_key="pk_price"
        )
        test_session.add(user)

        project = Project(
            id="proj_price",
            name="Pricing Test",
            owner_id=user.id,
            material_cost=5000.0,
            labor_cost=7500.0,
            markup_percentage=25.0
        )

        test_session.add(project)
        test_session.commit()

        assert project.material_cost == 5000.0
        assert project.labor_cost == 7500.0
        assert project.markup_percentage == 25.0

    def test_project_cascade_delete_removes_rooms(self, test_session):
        """Test that deleting project removes associated rooms"""
        user = User(
            id="user_cascade",
            email="cascade@test.com",
            name="User",
            api_key="pk_cascade"
        )
        test_session.add(user)

        project = Project(
            id="proj_cascade",
            name="Cascade Test",
            owner_id=user.id
        )
        test_session.add(project)

        room = Room(
            id="room_cascade",
            project_id=project.id,
            name="Test Room"
        )
        test_session.add(room)
        test_session.commit()

        # Delete project
        test_session.delete(project)
        test_session.commit()

        # Room should be deleted too
        room_query = test_session.query(Room).filter_by(id="room_cascade").first()
        assert room_query is None


# ============================================================================
# Room Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestRoomModel:
    """Test Room model"""

    def test_create_room_with_required_fields(self, test_session):
        """Test creating room"""
        user = User(
            id="user_room",
            email="room@test.com",
            name="Room User",
            api_key="pk_room"
        )
        test_session.add(user)

        project = Project(
            id="proj_room",
            name="Room Project",
            owner_id=user.id
        )
        test_session.add(project)

        room = Room(
            id="room_123",
            project_id=project.id,
            name="Conference Room"
        )

        test_session.add(room)
        test_session.commit()

        assert room.id == "room_123"
        assert room.project_id == project.id
        assert room.name == "Conference Room"

    def test_room_dimension_fields(self, test_session):
        """Test room dimension fields"""
        user = User(
            id="user_dim",
            email="dim@test.com",
            name="User",
            api_key="pk_dim"
        )
        test_session.add(user)

        project = Project(
            id="proj_dim",
            name="Project",
            owner_id=user.id
        )
        test_session.add(project)

        room = Room(
            id="room_dim",
            project_id=project.id,
            name="Dimensional Room",
            length=20.0,
            width=15.0,
            height=9.0,
            perimeter=70.0,
            area=300.0
        )

        test_session.add(room)
        test_session.commit()

        assert room.length == 20.0
        assert room.width == 15.0
        assert room.height == 9.0
        assert room.perimeter == 70.0
        assert room.area == 300.0

    def test_room_default_values(self, test_session):
        """Test room default values"""
        user = User(
            id="user_room_def",
            email="roomdef@test.com",
            name="User",
            api_key="pk_room_def"
        )
        test_session.add(user)

        project = Project(
            id="proj_room_def",
            name="Project",
            owner_id=user.id
        )
        test_session.add(project)

        room = Room(
            id="room_def",
            project_id=project.id,
            name="Default Room"
        )

        test_session.add(room)
        test_session.commit()

        assert room.total_area == 0.0
        assert room.wall_area == 0.0
        assert room.ceiling_area == 0.0
        assert room.trim_area == 0.0
        assert room.primer_gallons == 0.0
        assert room.finish_gallons == 0.0
        assert room.total_gallons == 0.0
        assert room.labor_hours == 0.0
        assert room.material_cost == 0.0
        assert room.labor_cost == 0.0
        assert room.total_cost == 0.0
        assert room.manual_override is False

    def test_room_surfaces_json_field(self, test_session):
        """Test room surfaces JSON field"""
        user = User(
            id="user_surf",
            email="surf@test.com",
            name="User",
            api_key="pk_surf"
        )
        test_session.add(user)

        project = Project(
            id="proj_surf",
            name="Project",
            owner_id=user.id
        )
        test_session.add(project)

        surfaces = {
            "walls": {"area": 500.0, "type": "wall"},
            "ceiling": {"area": 300.0, "type": "ceiling"}
        }

        room = Room(
            id="room_surf",
            project_id=project.id,
            name="Surface Room",
            surfaces=surfaces
        )

        test_session.add(room)
        test_session.commit()

        assert room.surfaces is not None
        assert "walls" in room.surfaces
        assert room.surfaces["walls"]["area"] == 500.0

    def test_room_paint_requirements(self, test_session):
        """Test room paint requirement fields"""
        user = User(
            id="user_paint",
            email="paint@test.com",
            name="User",
            api_key="pk_paint"
        )
        test_session.add(user)

        project = Project(
            id="proj_paint",
            name="Project",
            owner_id=user.id
        )
        test_session.add(project)

        room = Room(
            id="room_paint",
            project_id=project.id,
            name="Paint Room",
            primer_gallons=3.5,
            finish_gallons=5.0,
            total_gallons=8.5
        )

        test_session.add(room)
        test_session.commit()

        assert room.primer_gallons == 3.5
        assert room.finish_gallons == 5.0
        assert room.total_gallons == 8.5


# ============================================================================
# Drawing Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestDrawingModel:
    """Test Drawing model"""

    def test_create_drawing(self, test_session):
        """Test creating drawing"""
        user = User(
            id="user_draw",
            email="draw@test.com",
            name="User",
            api_key="pk_draw"
        )
        test_session.add(user)

        project = Project(
            id="proj_draw",
            name="Drawing Project",
            owner_id=user.id
        )
        test_session.add(project)

        drawing = Drawing(
            id="draw_123",
            project_id=project.id,
            filename="floor_plan.pdf",
            original_filename="Floor Plan Level 1.pdf"
        )

        test_session.add(drawing)
        test_session.commit()

        assert drawing.id == "draw_123"
        assert drawing.project_id == project.id
        assert drawing.filename == "floor_plan.pdf"

    def test_drawing_default_status(self, test_session):
        """Test drawing default status"""
        user = User(
            id="user_draw_st",
            email="drawst@test.com",
            name="User",
            api_key="pk_draw_st"
        )
        test_session.add(user)

        project = Project(
            id="proj_draw_st",
            name="Project",
            owner_id=user.id
        )
        test_session.add(project)

        drawing = Drawing(
            id="draw_st",
            project_id=project.id,
            filename="test.pdf"
        )

        test_session.add(drawing)
        test_session.commit()

        assert drawing.status == "pending"
        assert drawing.rooms_detected == 0

    def test_drawing_processing_fields(self, test_session):
        """Test drawing processing-related fields"""
        user = User(
            id="user_proc",
            email="proc@test.com",
            name="User",
            api_key="pk_proc"
        )
        test_session.add(user)

        project = Project(
            id="proj_proc",
            name="Project",
            owner_id=user.id
        )
        test_session.add(project)

        drawing = Drawing(
            id="draw_proc",
            project_id=project.id,
            filename="process.pdf",
            status="complete",
            rooms_detected=5,
            ai_confidence=0.92,
            processing_time=15.7
        )

        test_session.add(drawing)
        test_session.commit()

        assert drawing.status == "complete"
        assert drawing.rooms_detected == 5
        assert drawing.ai_confidence == 0.92
        assert drawing.processing_time == 15.7


# ============================================================================
# MaterialItem Model Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestMaterialItemModel:
    """Test MaterialItem model"""

    def test_create_material_item(self, test_session):
        """Test creating material item"""
        user = User(
            id="user_mat",
            email="mat@test.com",
            name="User",
            api_key="pk_mat"
        )
        test_session.add(user)

        project = Project(
            id="proj_mat",
            name="Material Project",
            owner_id=user.id
        )
        test_session.add(project)

        material = MaterialItem(
            id="mat_123",
            project_id=project.id,
            category="paint",
            name="ProMar 400 Interior",
            quantity=10.0,
            unit="gallons",
            unit_price=65.99,
            total_price=659.90
        )

        test_session.add(material)
        test_session.commit()

        assert material.id == "mat_123"
        assert material.category == "paint"
        assert material.name == "ProMar 400 Interior"
        assert material.quantity == 10.0
        assert material.unit_price == 65.99
        assert material.total_price == 659.90


# ============================================================================
# Relationship Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestModelRelationships:
    """Test relationships between models"""

    def test_user_projects_relationship(self, test_session):
        """Test User-Project relationship"""
        user = User(
            id="user_rel",
            email="rel@test.com",
            name="User",
            api_key="pk_rel"
        )
        test_session.add(user)

        proj1 = Project(
            id="proj_rel1",
            name="Project 1",
            owner_id=user.id
        )
        proj2 = Project(
            id="proj_rel2",
            name="Project 2",
            owner_id=user.id
        )

        test_session.add_all([proj1, proj2])
        test_session.commit()

        # Access projects through relationship
        assert len(user.projects) == 2
        assert proj1 in user.projects
        assert proj2 in user.projects

    def test_project_rooms_relationship(self, test_session):
        """Test Project-Room relationship"""
        user = User(
            id="user_proj_room",
            email="projroom@test.com",
            name="User",
            api_key="pk_projroom"
        )
        test_session.add(user)

        project = Project(
            id="proj_rooms",
            name="Rooms Project",
            owner_id=user.id
        )
        test_session.add(project)

        room1 = Room(id="room1", project_id=project.id, name="Room 1")
        room2 = Room(id="room2", project_id=project.id, name="Room 2")

        test_session.add_all([room1, room2])
        test_session.commit()

        # Access rooms through relationship
        assert len(project.rooms) == 2
        assert room1 in project.rooms
        assert room2 in project.rooms


# ============================================================================
# Enum Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.database
class TestEnums:
    """Test enum values"""

    def test_user_role_enum_values(self):
        """Test UserRole enum values"""
        assert UserRole.OWNER.value == "owner"
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.ESTIMATOR.value == "estimator"
        assert UserRole.VIEWER.value == "viewer"

    def test_project_status_enum_values(self):
        """Test ProjectStatus enum values"""
        assert ProjectStatus.DRAFT.value == "draft"
        assert ProjectStatus.PROCESSING.value == "processing"
        assert ProjectStatus.COMPLETE.value == "complete"
        assert ProjectStatus.SUBMITTED.value == "submitted"
        assert ProjectStatus.WON.value == "won"
        assert ProjectStatus.LOST.value == "lost"
        assert ProjectStatus.ARCHIVED.value == "archived"
