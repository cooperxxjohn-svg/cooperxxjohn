"""
Database Models for XBOQ Platform
SQLAlchemy ORM models for PostgreSQL/SQLite
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User model - stores user accounts"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    password_hash = Column(String(255))  # Future: JWT authentication
    api_key = Column(String(255), unique=True, index=True)  # Future: API access

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    projects = relationship('Project', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Project(Base):
    """Project model - stores BOQ and Estimate projects"""
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Project info
    type = Column(String(50), nullable=False, index=True)  # 'boq' or 'estimate'
    name = Column(String(255), nullable=False)
    status = Column(String(50), default='pending', index=True)  # pending, processing, complete, error

    # File info
    file_url = Column(Text)  # Path or URL to uploaded file
    file_name = Column(String(255))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship('User', back_populates='projects')
    boqs = relationship('BOQ', back_populates='project', cascade='all, delete-orphan')
    estimates = relationship('Estimate', back_populates='project', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Project(id={self.id}, type='{self.type}', name='{self.name}', status='{self.status}')>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'name': self.name,
            'status': self.status,
            'file_url': self.file_url,
            'file_name': self.file_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BOQ(Base):
    """BOQ model - stores Bill of Quantities extraction results"""
    __tablename__ = 'boqs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)

    # BOQ data
    project_name = Column(String(255))
    sections = Column(JSON, nullable=False)  # Store full BOQ sections as JSON
    total_items = Column(Integer, default=0)

    # Metadata
    extraction_time = Column(Numeric(10, 2))  # Time in seconds

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project = relationship('Project', back_populates='boqs')

    def __repr__(self):
        return f"<BOQ(id={self.id}, project_id={self.project_id}, project_name='{self.project_name}', items={self.total_items})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_name': self.project_name,
            'sections': self.sections,
            'total_items': self.total_items,
            'extraction_time': float(self.extraction_time) if self.extraction_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Estimate(Base):
    """Estimate model - stores construction estimates (drywall, painting, etc.)"""
    __tablename__ = 'estimates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)

    # Estimate data
    trade = Column(String(50), nullable=False, index=True)  # 'drywall', 'painting', 'concrete'
    project_type = Column(String(50))  # 'residential', 'commercial', 'industrial'
    rooms = Column(JSON, nullable=False)  # Store rooms array as JSON
    summary = Column(JSON, nullable=False)  # Store summary as JSON

    # Calculated totals
    total_cost = Column(Numeric(10, 2))
    total_sqft = Column(Numeric(10, 2))
    total_labor_hours = Column(Numeric(10, 2))

    # Metadata
    calculation_time = Column(Numeric(10, 2))  # Time in seconds

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    project = relationship('Project', back_populates='estimates')

    def __repr__(self):
        return f"<Estimate(id={self.id}, project_id={self.project_id}, trade='{self.trade}', cost=${self.total_cost})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'trade': self.trade,
            'project_type': self.project_type,
            'rooms': self.rooms,
            'summary': self.summary,
            'total_cost': float(self.total_cost) if self.total_cost else None,
            'total_sqft': float(self.total_sqft) if self.total_sqft else None,
            'total_labor_hours': float(self.total_labor_hours) if self.total_labor_hours else None,
            'calculation_time': float(self.calculation_time) if self.calculation_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Future models (placeholders for upcoming features)

class APIKey(Base):
    """API Key model - for programmatic API access"""
    __tablename__ = 'api_keys'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    key = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))  # Friendly name for the key
    is_active = Column(Integer, default=1)  # SQLite doesn't have boolean

    # Usage tracking
    last_used_at = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<APIKey(id={self.id}, user_id={self.user_id}, name='{self.name}')>"


class Subscription(Base):
    """Subscription model - for Stripe payments (future)"""
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Stripe info
    stripe_customer_id = Column(String(255), unique=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True, index=True)

    # Plan info
    plan = Column(String(50), nullable=False)  # 'starter', 'pro', 'enterprise'
    status = Column(String(50), default='active')  # active, canceled, past_due, trialing

    # Billing
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    cancel_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan='{self.plan}', status='{self.status}')>"
