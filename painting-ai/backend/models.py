"""
PostgreSQL Database Models
Migration from JSON to production-ready database
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    ESTIMATOR = "estimator"
    VIEWER = "viewer"


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETE = "complete"
    SUBMITTED = "submitted"
    WON = "won"
    LOST = "lost"
    ARCHIVED = "archived"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    company = Column(String)
    phone = Column(String)
    api_key = Column(String, unique=True, nullable=False, index=True)

    # Subscription
    plan = Column(String, default="trial")  # trial, starter, pro, enterprise
    stripe_customer_id = Column(String)
    stripe_subscription_id = Column(String)
    subscription_status = Column(String)  # active, canceled, past_due
    trial_ends_at = Column(DateTime)

    # Settings
    settings = Column(JSON, default={})
    default_paint_price = Column(Float, default=55.0)
    default_labor_rate = Column(Float, default=50.0)
    default_surface_type = Column(String, default="smooth_drywall")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    team_members = relationship("TeamMember", back_populates="user")


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    owner_id = Column(String, ForeignKey("users.id"))

    # Settings
    settings = Column(JSON, default={})
    logo_url = Column(String)

    # Subscription
    plan = Column(String, default="starter")
    seats = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team_members = relationship("TeamMember", back_populates="organization")
    projects = relationship("Project", back_populates="organization")


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"))
    user_id = Column(String, ForeignKey("users.id"))
    role = Column(Enum(UserRole), default=UserRole.ESTIMATOR)

    invited_at = Column(DateTime, default=datetime.utcnow)
    joined_at = Column(DateTime)

    # Relationships
    organization = relationship("Organization", back_populates="team_members")
    user = relationship("User", back_populates="team_members")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    customer = Column(String)
    customer_email = Column(String)
    customer_phone = Column(String)

    # Owner
    owner_id = Column(String, ForeignKey("users.id"))
    organization_id = Column(String, ForeignKey("organizations.id"))

    # Status
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)

    # Location
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)

    # Project details
    project_type = Column(String)  # residential, commercial, industrial
    building_type = Column(String)  # office, retail, hospital, etc.
    floors = Column(Integer)

    # Estimate details
    total_rooms = Column(Integer, default=0)
    total_sqft = Column(Float, default=0.0)
    total_gallons = Column(Float, default=0.0)
    total_labor_hours = Column(Float, default=0.0)

    # Pricing
    material_cost = Column(Float, default=0.0)
    labor_cost = Column(Float, default=0.0)
    markup_percentage = Column(Float, default=30.0)
    estimated_cost = Column(Float, default=0.0)
    bid_amount = Column(Float, default=0.0)

    # Dates
    estimate_date = Column(DateTime)
    bid_due_date = Column(DateTime)
    project_start_date = Column(DateTime)
    project_end_date = Column(DateTime)

    # Win/Loss tracking
    submitted_at = Column(DateTime)
    decision_date = Column(DateTime)
    won_amount = Column(Float)
    lost_reason = Column(String)
    competitor_won = Column(String)

    # Notes
    notes = Column(Text)
    scope_of_work = Column(Text)
    exclusions = Column(Text)
    assumptions = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Tags
    tags = Column(JSON, default=[])

    # Relationships
    owner = relationship("User", back_populates="projects")
    organization = relationship("Organization", back_populates="projects")
    rooms = relationship("Room", back_populates="project", cascade="all, delete-orphan")
    drawings = relationship("Drawing", back_populates="project", cascade="all, delete-orphan")
    materials = relationship("MaterialItem", back_populates="project", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="project", cascade="all, delete-orphan")


class Drawing(Base):
    __tablename__ = "drawings"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"))

    filename = Column(String, nullable=False)
    original_filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    file_type = Column(String)  # pdf, png, jpg

    # Drawing info
    drawing_type = Column(String)  # floor_plan, elevation, section, detail
    drawing_number = Column(String)
    sheet_number = Column(String)
    title = Column(String)
    scale = Column(String)
    floor_level = Column(Integer)

    # Processing
    status = Column(String, default="pending")  # pending, processing, complete, failed
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    processing_time = Column(Float)
    error_message = Column(Text)

    # Results
    rooms_detected = Column(Integer, default=0)
    ai_confidence = Column(Float)

    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="drawings")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"))
    drawing_id = Column(String, ForeignKey("drawings.id"))

    name = Column(String, nullable=False)
    number = Column(String)
    floor = Column(Integer)

    # Dimensions
    length = Column(Float)
    width = Column(Float)
    height = Column(Float)
    perimeter = Column(Float)
    area = Column(Float)

    # Surfaces (stored as JSON for flexibility)
    surfaces = Column(JSON, default={})

    # Totals
    total_area = Column(Float, default=0.0)
    wall_area = Column(Float, default=0.0)
    ceiling_area = Column(Float, default=0.0)
    trim_area = Column(Float, default=0.0)

    # Paint requirements
    primer_gallons = Column(Float, default=0.0)
    finish_gallons = Column(Float, default=0.0)
    total_gallons = Column(Float, default=0.0)

    # Labor
    labor_hours = Column(Float, default=0.0)

    # Cost
    material_cost = Column(Float, default=0.0)
    labor_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)

    # Room details
    ceiling_type = Column(String)  # flat, vaulted, cathedral
    wall_finish = Column(String)  # smooth, textured, rough
    paint_quality = Column(String)  # economy, standard, premium

    # Custom adjustments
    custom_notes = Column(Text)
    manual_override = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="rooms")


class MaterialItem(Base):
    __tablename__ = "material_items"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"))

    # Item details
    category = Column(String)  # paint, primer, supplies, equipment
    name = Column(String, nullable=False)
    manufacturer = Column(String)
    product_code = Column(String)

    # Quantity
    quantity = Column(Float, nullable=False)
    unit = Column(String)  # gallons, sqft, linear_ft, each

    # Pricing
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    # Supplier
    supplier = Column(String)
    supplier_sku = Column(String)

    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="materials")


class Template(Base):
    __tablename__ = "templates"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))

    name = Column(String, nullable=False)
    description = Column(Text)

    # Template type
    template_type = Column(String)  # room, assembly, project

    # Template data (JSON)
    data = Column(JSON, nullable=False)

    # Usage
    is_public = Column(Boolean, default=False)
    times_used = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Assembly(Base):
    """Pre-built assemblies (e.g., 'Standard Office Room' with typical finishes)"""
    __tablename__ = "assemblies"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))

    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)

    # Assembly components
    components = Column(JSON, nullable=False)

    # Default quantities
    default_quantity = Column(Float)
    default_unit = Column(String)

    # Pricing
    unit_cost = Column(Float)
    labor_hours_per_unit = Column(Float)

    is_public = Column(Boolean, default=False)
    times_used = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)


class PricingData(Base):
    """Historical pricing data for materials and labor"""
    __tablename__ = "pricing_data"

    id = Column(String, primary_key=True)

    # Item
    category = Column(String, nullable=False)
    item_name = Column(String, nullable=False)
    manufacturer = Column(String)

    # Location
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)

    # Pricing
    price = Column(Float, nullable=False)
    unit = Column(String)

    # Source
    source = Column(String)  # user_submitted, supplier_api, web_scraping
    supplier = Column(String)

    # Validity
    effective_date = Column(DateTime, nullable=False)
    expires_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)


class Activity(Base):
    """Activity log for projects"""
    __tablename__ = "activities"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"))
    user_id = Column(String, ForeignKey("users.id"))

    action = Column(String, nullable=False)  # created, updated, exported, submitted, etc.
    description = Column(Text)

    # Metadata
    metadata = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="activities")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))

    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)

    # Type
    notification_type = Column(String)  # project_complete, payment_due, team_invite, etc.

    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)

    # Action link
    action_url = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)


class Integration(Base):
    """Third-party integrations"""
    __tablename__ = "integrations"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))

    # Integration details
    provider = Column(String, nullable=False)  # quickbooks, sage, procore, etc.
    status = Column(String, default="pending")  # pending, active, disconnected, error

    # Credentials (encrypted)
    credentials = Column(JSON)

    # Settings
    settings = Column(JSON, default={})
    sync_enabled = Column(Boolean, default=True)
    last_sync = Column(DateTime)

    connected_at = Column(DateTime, default=datetime.utcnow)


class Webhook(Base):
    """Webhook endpoints for API integrations"""
    __tablename__ = "webhooks"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))

    url = Column(String, nullable=False)
    events = Column(JSON, nullable=False)  # List of event types to subscribe to

    # Security
    secret = Column(String, nullable=False)

    # Status
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    failure_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)


class APIUsage(Base):
    """Track API usage for billing and analytics"""
    __tablename__ = "api_usage"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))

    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)

    # Request details
    request_size = Column(Integer)
    response_size = Column(Integer)
    response_time = Column(Float)
    status_code = Column(Integer)

    # Rate limiting
    rate_limit_remaining = Column(Integer)

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
