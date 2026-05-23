"""
Database Service Layer for XBOQ Platform
Handles all database operations with connection pooling
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

from models import Base, User, Project, BOQ, Estimate

load_dotenv()
logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Database service with connection pooling and session management
    Supports both SQLite (development) and PostgreSQL (production)
    """

    def __init__(self, database_url: str = None):
        """
        Initialize database connection

        Args:
            database_url: Database connection string. If None, reads from DATABASE_URL env var
        """
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///xboq.db')

        # Configure engine based on database type
        if self.database_url.startswith('sqlite'):
            # SQLite configuration
            self.engine = create_engine(
                self.database_url,
                connect_args={'check_same_thread': False},
                poolclass=StaticPool,
                echo=False  # Set to True for SQL logging
            )
            # Enable foreign keys for SQLite
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        else:
            # PostgreSQL configuration
            self.engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
                echo=False
            )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False  # Prevent DetachedInstanceError
        )

        logger.info(f"Database initialized: {self.database_url.split(':')[0]}://...")

    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("All database tables created")

    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
        logger.info("All database tables dropped")

    @contextmanager
    def get_session(self) -> Session:
        """
        Context manager for database sessions

        Usage:
            with db.get_session() as session:
                user = session.query(User).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()

    # ========================================
    # USER OPERATIONS
    # ========================================

    def create_user(self, email: str, name: str = None, password_hash: str = None) -> User:
        """Create a new user"""
        with self.get_session() as session:
            user = User(email=email, name=name, password_hash=password_hash)
            session.add(user)
            session.flush()
            session.refresh(user)
            return user

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        with self.get_session() as session:
            return session.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        with self.get_session() as session:
            return session.query(User).filter(User.email == email).first()

    def get_all_users(self, limit: int = 100) -> List[User]:
        """Get all users"""
        with self.get_session() as session:
            return session.query(User).limit(limit).all()

    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user fields"""
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                session.flush()
                session.refresh(user)
            return user

    def delete_user(self, user_id: int) -> bool:
        """Delete user (cascades to projects)"""
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                session.delete(user)
                return True
            return False

    # ========================================
    # PROJECT OPERATIONS
    # ========================================

    def create_project(self, user_id: int, project_type: str, name: str,
                       file_url: str = None, file_name: str = None) -> Project:
        """Create a new project"""
        with self.get_session() as session:
            project = Project(
                user_id=user_id,
                type=project_type,
                name=name,
                file_url=file_url,
                file_name=file_name,
                status='pending'
            )
            session.add(project)
            session.flush()
            session.refresh(project)
            return project

    def get_project(self, project_id: int) -> Optional[Project]:
        """Get project by ID"""
        with self.get_session() as session:
            return session.query(Project).filter(Project.id == project_id).first()

    def get_user_projects(self, user_id: int, project_type: str = None, limit: int = 100) -> List[Project]:
        """Get all projects for a user"""
        with self.get_session() as session:
            query = session.query(Project).filter(Project.user_id == user_id)
            if project_type:
                query = query.filter(Project.type == project_type)
            return query.order_by(Project.created_at.desc()).limit(limit).all()

    def update_project(self, project_id: int, **kwargs) -> Optional[Project]:
        """Update project fields"""
        with self.get_session() as session:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                for key, value in kwargs.items():
                    if hasattr(project, key):
                        setattr(project, key, value)
                session.flush()
                session.refresh(project)
            return project

    def delete_project(self, project_id: int) -> bool:
        """Delete project (cascades to BOQs and Estimates)"""
        with self.get_session() as session:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                session.delete(project)
                return True
            return False

    # ========================================
    # BOQ OPERATIONS
    # ========================================

    def create_boq(self, project_id: int, project_name: str, sections: List[Dict],
                   total_items: int, extraction_time: float = None) -> BOQ:
        """Create a new BOQ"""
        with self.get_session() as session:
            boq = BOQ(
                project_id=project_id,
                project_name=project_name,
                sections=sections,
                total_items=total_items,
                extraction_time=extraction_time
            )
            session.add(boq)
            session.flush()
            session.refresh(boq)
            return boq

    def get_boq(self, boq_id: int) -> Optional[BOQ]:
        """Get BOQ by ID"""
        with self.get_session() as session:
            return session.query(BOQ).filter(BOQ.id == boq_id).first()

    def get_boq_by_project(self, project_id: int) -> Optional[BOQ]:
        """Get BOQ by project ID"""
        with self.get_session() as session:
            return session.query(BOQ).filter(BOQ.project_id == project_id).first()

    # ========================================
    # ESTIMATE OPERATIONS
    # ========================================

    def create_estimate(self, project_id: int, trade: str, rooms: List[Dict],
                        summary: Dict, project_type: str = None,
                        total_cost: float = None, total_sqft: float = None,
                        total_labor_hours: float = None, calculation_time: float = None) -> Estimate:
        """Create a new estimate"""
        with self.get_session() as session:
            estimate = Estimate(
                project_id=project_id,
                trade=trade,
                project_type=project_type,
                rooms=rooms,
                summary=summary,
                total_cost=total_cost,
                total_sqft=total_sqft,
                total_labor_hours=total_labor_hours,
                calculation_time=calculation_time
            )
            session.add(estimate)
            session.flush()
            session.refresh(estimate)
            return estimate

    def get_estimate(self, estimate_id: int) -> Optional[Estimate]:
        """Get estimate by ID"""
        with self.get_session() as session:
            return session.query(Estimate).filter(Estimate.id == estimate_id).first()

    def get_estimate_by_project(self, project_id: int) -> Optional[Estimate]:
        """Get estimate by project ID"""
        with self.get_session() as session:
            return session.query(Estimate).filter(Estimate.project_id == project_id).first()

    def get_estimates_by_trade(self, user_id: int, trade: str, limit: int = 50) -> List[Estimate]:
        """Get all estimates for a user by trade"""
        with self.get_session() as session:
            return session.query(Estimate)\
                .join(Project)\
                .filter(Project.user_id == user_id, Estimate.trade == trade)\
                .order_by(Estimate.created_at.desc())\
                .limit(limit)\
                .all()

    # ========================================
    # STATISTICS & ANALYTICS
    # ========================================

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        with self.get_session() as session:
            total_projects = session.query(Project).filter(Project.user_id == user_id).count()
            boq_projects = session.query(Project).filter(
                Project.user_id == user_id, Project.type == 'boq'
            ).count()
            estimate_projects = session.query(Project).filter(
                Project.user_id == user_id, Project.type == 'estimate'
            ).count()

            return {
                'total_projects': total_projects,
                'boq_projects': boq_projects,
                'estimate_projects': estimate_projects
            }

    # ========================================
    # UTILITY METHODS
    # ========================================

    def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Singleton instance
_db_instance: Optional[DatabaseService] = None


def get_database() -> DatabaseService:
    """Get singleton database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseService()
        # Create tables if they don't exist
        _db_instance.create_tables()
    return _db_instance


if __name__ == '__main__':
    # Test database connection
    logger.info("Testing database connection...")

    db = get_database()

    # Create tables
    db.create_tables()
    logger.info("✅ Tables created")

    # Health check
    if db.health_check():
        logger.info("✅ Database connection healthy")
    else:
        logger.error("❌ Database connection failed")

    # Create test user
    user = db.create_user(email="test@xboq.ai", name="Test User")
    logger.info(f"✅ Created user: {user}")

    # Create test project
    project = db.create_project(
        user_id=user.id,
        project_type='estimate',
        name='Test Project'
    )
    logger.info(f"✅ Created project: {project}")

    # Get user's projects
    projects = db.get_user_projects(user.id)
    logger.info(f"✅ User has {len(projects)} project(s)")

    # Cleanup
    db.delete_user(user.id)
    logger.info("✅ Cleaned up test data")

    logger.info("🎉 Database test complete!")
