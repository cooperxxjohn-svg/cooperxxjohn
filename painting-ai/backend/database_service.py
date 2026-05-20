"""
Database service layer - SQLAlchemy ORM
Replaces simple JSON storage with production PostgreSQL
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from models import Base, User, Project, Room, Drawing, Organization, TeamMember
from typing import Optional, List
import uuid
from datetime import datetime


class DatabaseService:
    """Production database service using SQLAlchemy"""

    def __init__(self, database_url: Optional[str] = None):
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://paintingai:changeme123@localhost:5432/paintingai"
            )

        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)

    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # User operations
    def create_user(self, email: str, name: str, **kwargs) -> User:
        """Create a new user"""
        with self.get_session() as session:
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                name=name,
                api_key=f"pk_{uuid.uuid4().hex}",
                **kwargs
            )
            session.add(user)
            session.flush()
            return user

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        with self.get_session() as session:
            return session.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        with self.get_session() as session:
            return session.query(User).filter(User.email == email).first()

    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key"""
        with self.get_session() as session:
            return session.query(User).filter(User.api_key == api_key).first()

    # Project operations
    def create_project(self, owner_id: str, name: str, **kwargs) -> Project:
        """Create a new project"""
        with self.get_session() as session:
            project = Project(
                id=str(uuid.uuid4()),
                owner_id=owner_id,
                name=name,
                **kwargs
            )
            session.add(project)
            session.flush()
            return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        with self.get_session() as session:
            return session.query(Project).filter(Project.id == project_id).first()

    def get_user_projects(self, user_id: str, limit: int = 100) -> List[Project]:
        """Get all projects for a user"""
        with self.get_session() as session:
            return (
                session.query(Project)
                .filter(Project.owner_id == user_id)
                .order_by(Project.created_at.desc())
                .limit(limit)
                .all()
            )

    def update_project(self, project_id: str, **updates):
        """Update project"""
        with self.get_session() as session:
            session.query(Project).filter(Project.id == project_id).update(updates)

    def delete_project(self, project_id: str):
        """Delete project and all related data"""
        with self.get_session() as session:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                session.delete(project)

    # Room operations
    def create_room(self, project_id: str, name: str, **kwargs) -> Room:
        """Create a new room"""
        with self.get_session() as session:
            room = Room(
                id=str(uuid.uuid4()),
                project_id=project_id,
                name=name,
                **kwargs
            )
            session.add(room)
            session.flush()
            return room

    def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID"""
        with self.get_session() as session:
            return session.query(Room).filter(Room.id == room_id).first()

    def get_project_rooms(self, project_id: str) -> List[Room]:
        """Get all rooms for a project"""
        with self.get_session() as session:
            return (
                session.query(Room)
                .filter(Room.project_id == project_id)
                .all()
            )

    def update_room(self, room_id: str, **updates):
        """Update room"""
        with self.get_session() as session:
            session.query(Room).filter(Room.id == room_id).update(updates)

    # Drawing operations
    def create_drawing(self, project_id: str, filename: str, **kwargs) -> Drawing:
        """Create a new drawing"""
        with self.get_session() as session:
            drawing = Drawing(
                id=str(uuid.uuid4()),
                project_id=project_id,
                filename=filename,
                **kwargs
            )
            session.add(drawing)
            session.flush()
            return drawing

    def get_drawing(self, drawing_id: str) -> Optional[Drawing]:
        """Get drawing by ID"""
        with self.get_session() as session:
            return session.query(Drawing).filter(Drawing.id == drawing_id).first()

    def get_project_drawings(self, project_id: str) -> List[Drawing]:
        """Get all drawings for a project"""
        with self.get_session() as session:
            return (
                session.query(Drawing)
                .filter(Drawing.project_id == project_id)
                .order_by(Drawing.uploaded_at.desc())
                .all()
            )

    def update_drawing(self, drawing_id: str, **updates):
        """Update drawing"""
        with self.get_session() as session:
            session.query(Drawing).filter(Drawing.id == drawing_id).update(updates)

    # Organization operations
    def create_organization(self, owner_id: str, name: str) -> Organization:
        """Create a new organization"""
        with self.get_session() as session:
            org = Organization(
                id=str(uuid.uuid4()),
                owner_id=owner_id,
                name=name
            )
            session.add(org)
            session.flush()
            return org

    def add_team_member(self, org_id: str, user_id: str, role: str) -> TeamMember:
        """Add member to organization"""
        with self.get_session() as session:
            member = TeamMember(
                id=str(uuid.uuid4()),
                organization_id=org_id,
                user_id=user_id,
                role=role
            )
            session.add(member)
            session.flush()
            return member


# Global database instance
db = DatabaseService()


if __name__ == "__main__":
    # Test database
    db.create_tables()
    print("✓ Database tables created")

    # Create test user
    user = db.create_user(
        email="test@paintingai.com",
        name="Test User",
        company="Test Company"
    )
    print(f"✓ User created: {user.email} (API key: {user.api_key})")

    # Create test project
    project = db.create_project(
        owner_id=user.id,
        name="Test Office Building",
        customer="ABC Construction"
    )
    print(f"✓ Project created: {project.name} ({project.id})")

    # Create test room
    room = db.create_room(
        project_id=project.id,
        name="Conference Room",
        length=20.0,
        width=15.0,
        height=9.0
    )
    print(f"✓ Room created: {room.name} ({room.id})")

    print("\n✓ Database service working correctly!")
