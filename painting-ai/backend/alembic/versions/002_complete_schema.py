"""Complete schema with all models and relationships

Revision ID: 002
Revises: 001
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to users table
    try:
        op.add_column('users', sa.Column('company', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('users', sa.Column('phone', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('users', sa.Column('stripe_subscription_id', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('users', sa.Column('trial_ends_at', sa.DateTime(), nullable=True))
    except:
        pass
    try:
        op.add_column('users', sa.Column('default_paint_price', sa.Float(), server_default='55.0'))
    except:
        pass
    try:
        op.add_column('users', sa.Column('default_labor_rate', sa.Float(), server_default='50.0'))
    except:
        pass
    try:
        op.add_column('users', sa.Column('default_surface_type', sa.String(), server_default='smooth_drywall'))
    except:
        pass
    try:
        op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))
    except:
        pass
    try:
        op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default='true'))
    except:
        pass

    # Add missing columns to organizations table
    try:
        op.add_column('organizations', sa.Column('logo_url', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('organizations', sa.Column('seats', sa.Integer(), server_default='1'))
    except:
        pass

    # Create team_members table if not exists
    try:
        op.create_table('team_members',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('organization_id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('role', sa.String(), nullable=False),
            sa.Column('invited_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('joined_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_team_members_org_id', 'team_members', ['organization_id'])
        op.create_index('ix_team_members_user_id', 'team_members', ['user_id'])
    except:
        pass

    # Add missing columns to projects table
    try:
        op.add_column('projects', sa.Column('customer_email', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('customer_phone', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('city', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('state', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('zip_code', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('building_type', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('floors', sa.Integer(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('total_gallons', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('total_labor_hours', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('material_cost', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('labor_cost', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('markup_percentage', sa.Float(), server_default='30.0'))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('estimated_cost', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('estimate_date', sa.DateTime(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('bid_due_date', sa.DateTime(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('project_start_date', sa.DateTime(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('project_end_date', sa.DateTime(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('submitted_at', sa.DateTime(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('decision_date', sa.DateTime(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('won_amount', sa.Float(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('lost_reason', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('competitor_won', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('scope_of_work', sa.Text(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('exclusions', sa.Text(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('assumptions', sa.Text(), nullable=True))
    except:
        pass
    try:
        op.add_column('projects', sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), server_default='[]'))
    except:
        pass

    # Add missing columns to rooms table
    try:
        op.add_column('rooms', sa.Column('drawing_id', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('length', sa.Float(), nullable=True))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('width', sa.Float(), nullable=True))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('height', sa.Float(), nullable=True))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('perimeter', sa.Float(), nullable=True))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('area', sa.Float(), nullable=True))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('wall_area', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('ceiling_area', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('trim_area', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('primer_gallons', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('finish_gallons', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('total_gallons', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('labor_hours', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('material_cost', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('labor_cost', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('total_cost', sa.Float(), server_default='0.0'))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('ceiling_type', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('wall_finish', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('paint_quality', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('custom_notes', sa.Text(), nullable=True))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('manual_override', sa.Boolean(), server_default='false'))
    except:
        pass
    try:
        op.add_column('rooms', sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')))
    except:
        pass

    # Add missing columns to drawings table
    try:
        op.add_column('drawings', sa.Column('original_filename', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('drawings', sa.Column('file_type', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('drawings', sa.Column('drawing_type', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('drawings', sa.Column('drawing_number', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('drawings', sa.Column('sheet_number', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('drawings', sa.Column('title', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('drawings', sa.Column('scale', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('drawings', sa.Column('floor_level', sa.Integer(), nullable=True))
    except:
        pass
    try:
        op.add_column('drawings', sa.Column('processing_started_at', sa.DateTime(), nullable=True))
    except:
        pass
    try:
        op.add_column('drawings', sa.Column('processing_completed_at', sa.DateTime(), nullable=True))
    except:
        pass
    try:
        op.add_column('drawings', sa.Column('processing_time', sa.Float(), nullable=True))
    except:
        pass
    try:
        op.add_column('drawings', sa.Column('error_message', sa.Text(), nullable=True))
    except:
        pass
    try:
        op.add_column('drawings', sa.Column('rooms_detected', sa.Integer(), server_default='0'))
    except:
        pass
    try:
        op.add_column('drawings', sa.Column('ai_confidence', sa.Float(), nullable=True))
    except:
        pass

    # Create material_items table
    try:
        op.create_table('material_items',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('project_id', sa.String(), nullable=False),
            sa.Column('category', sa.String(), nullable=True),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('manufacturer', sa.String(), nullable=True),
            sa.Column('product_code', sa.String(), nullable=True),
            sa.Column('quantity', sa.Float(), nullable=False),
            sa.Column('unit', sa.String(), nullable=True),
            sa.Column('unit_price', sa.Float(), nullable=False),
            sa.Column('total_price', sa.Float(), nullable=False),
            sa.Column('supplier', sa.String(), nullable=True),
            sa.Column('supplier_sku', sa.String(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_material_items_project_id', 'material_items', ['project_id'])
    except:
        pass

    # Update templates table
    try:
        op.add_column('templates', sa.Column('user_id', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('templates', sa.Column('template_type', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('templates', sa.Column('data', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    except:
        pass
    try:
        op.add_column('templates', sa.Column('times_used', sa.Integer(), server_default='0'))
    except:
        pass
    try:
        op.add_column('templates', sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')))
    except:
        pass

    # Update assemblies table
    try:
        op.add_column('assemblies', sa.Column('user_id', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('assemblies', sa.Column('category', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('assemblies', sa.Column('components', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    except:
        pass
    try:
        op.add_column('assemblies', sa.Column('default_quantity', sa.Float(), nullable=True))
    except:
        pass
    try:
        op.add_column('assemblies', sa.Column('default_unit', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('assemblies', sa.Column('unit_cost', sa.Float(), nullable=True))
    except:
        pass
    try:
        op.add_column('assemblies', sa.Column('labor_hours_per_unit', sa.Float(), nullable=True))
    except:
        pass
    try:
        op.add_column('assemblies', sa.Column('times_used', sa.Integer(), server_default='0'))
    except:
        pass

    # Create pricing_data table
    try:
        op.create_table('pricing_data',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('category', sa.String(), nullable=False),
            sa.Column('item_name', sa.String(), nullable=False),
            sa.Column('manufacturer', sa.String(), nullable=True),
            sa.Column('city', sa.String(), nullable=True),
            sa.Column('state', sa.String(), nullable=True),
            sa.Column('zip_code', sa.String(), nullable=True),
            sa.Column('price', sa.Float(), nullable=False),
            sa.Column('unit', sa.String(), nullable=True),
            sa.Column('source', sa.String(), nullable=True),
            sa.Column('supplier', sa.String(), nullable=True),
            sa.Column('effective_date', sa.DateTime(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_pricing_data_category', 'pricing_data', ['category'])
        op.create_index('ix_pricing_data_item_name', 'pricing_data', ['item_name'])
        op.create_index('ix_pricing_data_state', 'pricing_data', ['state'])
    except:
        pass

    # Add missing columns to notifications table
    try:
        op.add_column('notifications', sa.Column('notification_type', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('notifications', sa.Column('read_at', sa.DateTime(), nullable=True))
    except:
        pass
    try:
        op.add_column('notifications', sa.Column('action_url', sa.String(), nullable=True))
    except:
        pass

    # Update integrations table
    try:
        op.add_column('integrations', sa.Column('provider', sa.String(), nullable=True))
    except:
        pass
    try:
        op.add_column('integrations', sa.Column('status', sa.String(), server_default='pending'))
    except:
        pass
    try:
        op.add_column('integrations', sa.Column('sync_enabled', sa.Boolean(), server_default='true'))
    except:
        pass
    try:
        op.add_column('integrations', sa.Column('last_sync', sa.DateTime(), nullable=True))
    except:
        pass
    try:
        op.add_column('integrations', sa.Column('connected_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')))
    except:
        pass

    # Add missing columns to webhooks table
    try:
        op.add_column('webhooks', sa.Column('last_triggered', sa.DateTime(), nullable=True))
    except:
        pass
    try:
        op.add_column('webhooks', sa.Column('failure_count', sa.Integer(), server_default='0'))
    except:
        pass

    # Add missing columns to api_usage table
    try:
        op.add_column('api_usage', sa.Column('request_size', sa.Integer(), nullable=True))
    except:
        pass
    try:
        op.add_column('api_usage', sa.Column('response_size', sa.Integer(), nullable=True))
    except:
        pass
    try:
        op.add_column('api_usage', sa.Column('rate_limit_remaining', sa.Integer(), nullable=True))
    except:
        pass

    # Add indexes for email lookups
    try:
        op.create_index('ix_users_email', 'users', ['email'])
    except:
        pass
    try:
        op.create_index('ix_users_api_key', 'users', ['api_key'])
    except:
        pass

    # Add indexes for project status
    try:
        op.create_index('ix_projects_status', 'projects', ['status'])
    except:
        pass


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_projects_status', table_name='projects', if_exists=True)
    op.drop_index('ix_users_api_key', table_name='users', if_exists=True)
    op.drop_index('ix_users_email', table_name='users', if_exists=True)
    op.drop_index('ix_pricing_data_state', table_name='pricing_data', if_exists=True)
    op.drop_index('ix_pricing_data_item_name', table_name='pricing_data', if_exists=True)
    op.drop_index('ix_pricing_data_category', table_name='pricing_data', if_exists=True)
    op.drop_index('ix_material_items_project_id', table_name='material_items', if_exists=True)
    op.drop_index('ix_team_members_user_id', table_name='team_members', if_exists=True)
    op.drop_index('ix_team_members_org_id', table_name='team_members', if_exists=True)

    # Drop tables
    op.drop_table('pricing_data', if_exists=True)
    op.drop_table('material_items', if_exists=True)
    op.drop_table('team_members', if_exists=True)
