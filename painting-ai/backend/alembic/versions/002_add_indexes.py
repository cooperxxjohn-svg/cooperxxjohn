"""Add performance indexes for production

Revision ID: 002
Revises: 001
Create Date: 2026-05-21 00:00:00.000000

Indexes for frequently queried fields:
- User: email (unique), api_key (unique already in 001)
- Project: user_id, status, created_at
- Room: project_id
- Drawing: project_id, status
- Organization: owner_id

Composite indexes for common query patterns
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes for performance optimization"""

    # User indexes (email and api_key unique indexes already exist from 001)
    # These are implicitly created by unique constraints

    # Project indexes
    op.create_index('ix_projects_status', 'projects', ['status'])
    op.create_index('ix_projects_created_at', 'projects', ['created_at'])

    # Composite index for common query: get user's projects by status
    op.create_index(
        'ix_projects_owner_status',
        'projects',
        ['owner_id', 'status']
    )

    # Composite index for project listing with date ordering
    op.create_index(
        'ix_projects_owner_created',
        'projects',
        ['owner_id', 'created_at']
    )

    # Drawing indexes
    op.create_index('ix_drawings_status', 'drawings', ['status'])

    # Composite index for project drawings by status
    op.create_index(
        'ix_drawings_project_status',
        'drawings',
        ['project_id', 'status']
    )

    # Organization indexes
    op.create_index('ix_organizations_owner_id', 'organizations', ['owner_id'])

    # Team member indexes for faster lookups
    op.create_index('ix_team_members_organization_id', 'team_members', ['organization_id'])
    op.create_index('ix_team_members_user_id', 'team_members', ['user_id'])

    # Composite index for team member role queries
    op.create_index(
        'ix_team_members_org_role',
        'team_members',
        ['organization_id', 'role']
    )

    # Material items index
    op.create_index('ix_material_items_project_id', 'material_items', ['project_id'])
    op.create_index('ix_material_items_category', 'material_items', ['category'])

    # Notification indexes
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])

    # Composite for unread notifications
    op.create_index(
        'ix_notifications_user_unread',
        'notifications',
        ['user_id', 'is_read']
    )

    # Integration indexes
    op.create_index('ix_integrations_user_id', 'integrations', ['user_id'])
    op.create_index('ix_integrations_provider', 'integrations', ['provider'])

    # Webhook indexes
    op.create_index('ix_webhooks_user_id', 'webhooks', ['user_id'])
    op.create_index('ix_webhooks_is_active', 'webhooks', ['is_active'])

    # Template indexes
    op.create_index('ix_templates_user_id', 'templates', ['user_id'])
    op.create_index('ix_templates_template_type', 'templates', ['template_type'])
    op.create_index('ix_templates_is_public', 'templates', ['is_public'])

    # Assembly indexes
    op.create_index('ix_assemblies_user_id', 'assemblies', ['user_id'])
    op.create_index('ix_assemblies_category', 'assemblies', ['category'])
    op.create_index('ix_assemblies_is_public', 'assemblies', ['is_public'])

    # Pricing data indexes
    op.create_index('ix_pricing_data_category', 'pricing_data', ['category'])
    op.create_index('ix_pricing_data_state', 'pricing_data', ['state'])
    op.create_index('ix_pricing_data_effective_date', 'pricing_data', ['effective_date'])

    # Composite index for location-based pricing lookup
    op.create_index(
        'ix_pricing_data_location_category',
        'pricing_data',
        ['state', 'category', 'effective_date']
    )


def downgrade() -> None:
    """Remove all performance indexes"""

    # Drop composite indexes
    op.drop_index('ix_pricing_data_location_category', table_name='pricing_data')
    op.drop_index('ix_notifications_user_unread', table_name='notifications')
    op.drop_index('ix_team_members_org_role', table_name='team_members')
    op.drop_index('ix_drawings_project_status', table_name='drawings')
    op.drop_index('ix_projects_owner_created', table_name='projects')
    op.drop_index('ix_projects_owner_status', table_name='projects')

    # Drop single-column indexes
    op.drop_index('ix_pricing_data_effective_date', table_name='pricing_data')
    op.drop_index('ix_pricing_data_state', table_name='pricing_data')
    op.drop_index('ix_pricing_data_category', table_name='pricing_data')

    op.drop_index('ix_assemblies_is_public', table_name='assemblies')
    op.drop_index('ix_assemblies_category', table_name='assemblies')
    op.drop_index('ix_assemblies_user_id', table_name='assemblies')

    op.drop_index('ix_templates_is_public', table_name='templates')
    op.drop_index('ix_templates_template_type', table_name='templates')
    op.drop_index('ix_templates_user_id', table_name='templates')

    op.drop_index('ix_webhooks_is_active', table_name='webhooks')
    op.drop_index('ix_webhooks_user_id', table_name='webhooks')

    op.drop_index('ix_integrations_provider', table_name='integrations')
    op.drop_index('ix_integrations_user_id', table_name='integrations')

    op.drop_index('ix_notifications_is_read', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')

    op.drop_index('ix_material_items_category', table_name='material_items')
    op.drop_index('ix_material_items_project_id', table_name='material_items')

    op.drop_index('ix_team_members_user_id', table_name='team_members')
    op.drop_index('ix_team_members_organization_id', table_name='team_members')

    op.drop_index('ix_organizations_owner_id', table_name='organizations')

    op.drop_index('ix_drawings_status', table_name='drawings')

    op.drop_index('ix_projects_created_at', table_name='projects')
    op.drop_index('ix_projects_status', table_name='projects')
