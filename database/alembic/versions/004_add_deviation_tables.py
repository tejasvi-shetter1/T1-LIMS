"""Add deviation management tables

Revision ID: 004_add_deviation_tables
Revises: 003_previous_migration
Create Date: 2025-09-02 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '004_add_deviation_tables'
down_revision = '003_previous_migration'  # Update with your latest migration
branch_labels = None
depends_on = None

def upgrade():
    # Create enums
    deviation_type_enum = postgresql.ENUM(
        'OOT', 'DAMAGED', 'MISSING_STANDARD', 'GB_FAILURE', 
        'ENVIRONMENTAL', 'EQUIPMENT_MALFUNCTION',
        name='deviation_type'
    )
    deviation_type_enum.create(op.get_bind())
    
    deviation_status_enum = postgresql.ENUM(
        'OPEN', 'IN_REVIEW', 'CUSTOMER_NOTIFIED', 'CUSTOMER_ACCEPTED', 
        'CUSTOMER_REJECTED', 'RESOLVED', 'CLOSED',
        name='deviation_status'
    )
    deviation_status_enum.create(op.get_bind())
    
    user_role_enum = postgresql.ENUM(
        'ADMIN', 'LAB_MANAGER', 'TECHNICIAN', 'QA_MANAGER', 
        'CUSTOMER_ADMIN', 'CUSTOMER_USER',
        name='user_role'
    )
    user_role_enum.create(op.get_bind())
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('role', user_role_enum, nullable=False),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id')),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_login', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True))
    )
    
    # Create deviation_reports table
    op.create_table('deviation_reports',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('deviation_number', sa.String(100), unique=True, nullable=False),
        sa.Column('srf_id', sa.Integer(), sa.ForeignKey('srf.id'), nullable=False),
        sa.Column('srf_item_id', sa.Integer(), sa.ForeignKey('srf_items.id'), nullable=False),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('jobs.id')),
        
        # Deviation Details
        sa.Column('deviation_type', deviation_type_enum, nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('severity', sa.String(20), default='medium'),
        
        # Status Management
        sa.Column('status', deviation_status_enum, default='OPEN'),
        
        # Audit Trail
        sa.Column('raised_by', sa.String(255), nullable=False),
        sa.Column('raised_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('reviewed_by', sa.String(255)),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_by', sa.String(255)),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('closed_by', sa.String(255)),
        sa.Column('closed_at', sa.DateTime(timezone=True)),
        
        # Customer Response
        sa.Column('customer_response', sa.String(50)),
        sa.Column('customer_response_note', sa.Text()),
        sa.Column('customer_response_by', sa.String(255)),
        sa.Column('customer_response_at', sa.DateTime(timezone=True)),
        
        # Resolution
        sa.Column('root_cause_analysis', sa.Text()),
        sa.Column('corrective_actions', sa.Text()),
        sa.Column('preventive_actions', sa.Text()),
        
        # Standard audit fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('created_by', sa.String(255)),
        sa.Column('updated_by', sa.String(255))
    )
    
    # Create deviation_actions table (audit trail)
    op.create_table('deviation_actions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('deviation_id', sa.Integer(), sa.ForeignKey('deviation_reports.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('action_by', sa.String(255), nullable=False),
        sa.Column('action_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('comments', sa.Text()),
        sa.Column('old_status', deviation_status_enum),
        sa.Column('new_status', deviation_status_enum),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text())
    )
    
    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('recipient_user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('recipient_email', sa.String(255)),
        
        # Related entities
        sa.Column('deviation_id', sa.Integer(), sa.ForeignKey('deviation_reports.id')),
        sa.Column('srf_id', sa.Integer(), sa.ForeignKey('srf.id')),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('jobs.id')),
        
        # Delivery status
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('is_email_sent', sa.Boolean(), default=False),
        sa.Column('email_sent_at', sa.DateTime(timezone=True)),
        
        # Standard fields
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(255))
    )
    
    # Add missing fields to existing tables
    op.add_column('customers', sa.Column('notification_email', sa.String(255)))
    op.add_column('customers', sa.Column('notification_phone', sa.String(50)))
    op.add_column('jobs', sa.Column('deviation_required', sa.Boolean(), default=False))
    op.add_column('jobs', sa.Column('deviation_resolved', sa.Boolean(), default=False))
    op.add_column('jobs', sa.Column('can_generate_certificate', sa.Boolean(), default=True))
    
    # Create indexes for performance
    op.create_index('idx_deviation_reports_srf_id', 'deviation_reports', ['srf_id'])
    op.create_index('idx_deviation_reports_status', 'deviation_reports', ['status'])
    op.create_index('idx_deviation_reports_raised_by', 'deviation_reports', ['raised_by'])
    op.create_index('idx_deviation_actions_deviation_id', 'deviation_actions', ['deviation_id'])
    op.create_index('idx_notifications_recipient_user_id', 'notifications', ['recipient_user_id'])
    op.create_index('idx_users_customer_id', 'users', ['customer_id'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_users_customer_id')
    op.drop_index('idx_notifications_recipient_user_id')
    op.drop_index('idx_deviation_actions_deviation_id')
    op.drop_index('idx_deviation_reports_raised_by')
    op.drop_index('idx_deviation_reports_status')
    op.drop_index('idx_deviation_reports_srf_id')
    
    # Drop columns
    op.drop_column('jobs', 'can_generate_certificate')
    op.drop_column('jobs', 'deviation_resolved')
    op.drop_column('jobs', 'deviation_required')
    op.drop_column('customers', 'notification_phone')
    op.drop_column('customers', 'notification_email')
    
    # Drop tables
    op.drop_table('notifications')
    op.drop_table('deviation_actions')
    op.drop_table('deviation_reports')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS user_role')
    op.execute('DROP TYPE IF EXISTS deviation_status')
    op.execute('DROP TYPE IF EXISTS deviation_type')
