"""add_deviation_management_tables

Revision ID: 85cb21df2e65
Revises: ea15c69740c6
Create Date: 2025-09-03 08:41:14.029801

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '85cb21df2e65'
down_revision = 'ea15c69740c6'
branch_labels = None
depends_on = None


def create_enum_safe(connection, enum_name, enum_values):
    """Create ENUM only if it doesn't exist"""
    result = connection.execute(
        sa.text(f"SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}')")
    ).scalar()
    
    if not result:
        # Create enum using raw SQL to avoid SQLAlchemy auto-creation issues
        values_str = "', '".join(enum_values)
        connection.execute(sa.text(f"CREATE TYPE {enum_name} AS ENUM ('{values_str}')"))
        return True
    return False


def upgrade():
    connection = op.get_bind()
    
    # Create ENUMs safely (only if they don't exist)
    create_enum_safe(connection, 'deviation_status', [
        'OPEN', 'IN_REVIEW', 'CUSTOMER_NOTIFIED', 'CUSTOMER_ACCEPTED', 
        'CUSTOMER_REJECTED', 'RESOLVED', 'CLOSED'
    ])
    
    create_enum_safe(connection, 'deviation_type', [
        'OOT', 'DAMAGED', 'MISSING_STANDARD', 'GB_FAILURE', 
        'ENVIRONMENTAL', 'EQUIPMENT_MALFUNCTION'
    ])
    
    create_enum_safe(connection, 'notification_type', [
        'DEVIATION_CREATED', 'DEVIATION_RESPONSE_REQUIRED', 'CUSTOMER_RESPONSE_RECEIVED',
        'DEVIATION_RESOLVED', 'DEVIATION_CLOSED'
    ])
    
    create_enum_safe(connection, 'user_role', [
        'ADMIN', 'LAB_MANAGER', 'TECHNICIAN', 'QA_MANAGER', 
        'CUSTOMER_ADMIN', 'CUSTOMER_USER'
    ])

    # Check existing tables
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()
    
    # Create users table (skip if exists)
    if 'users' not in existing_tables:
        op.create_table('users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(length=100), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('password_hash', sa.String(length=255), nullable=False),
            sa.Column('full_name', sa.String(length=255), nullable=True),
            sa.Column('role', sa.String(length=50), nullable=False),  # Use String, enforce with constraint
            sa.Column('customer_id', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
            sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email'),
            sa.UniqueConstraint('username')
        )
        op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
        
        # Add enum constraint manually after table creation
        op.execute(sa.text("""
            ALTER TABLE users 
            ADD CONSTRAINT users_role_enum_check 
            CHECK (role::text = ANY (ARRAY['ADMIN'::character varying, 'LAB_MANAGER'::character varying, 'TECHNICIAN'::character varying, 'QA_MANAGER'::character varying, 'CUSTOMER_ADMIN'::character varying, 'CUSTOMER_USER'::character varying]::text[]))
        """))

    # Create deviation_reports table
    if 'deviation_reports' not in existing_tables:
        op.create_table('deviation_reports',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deviation_number', sa.String(length=100), nullable=False),
            sa.Column('srf_id', sa.Integer(), nullable=False),
            sa.Column('srf_item_id', sa.Integer(), nullable=False),
            sa.Column('job_id', sa.Integer(), nullable=True),
            sa.Column('deviation_type', sa.String(length=50), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('severity', sa.String(length=20), server_default=sa.text("'medium'"), nullable=False),
            sa.Column('status', sa.String(length=50), server_default=sa.text("'OPEN'"), nullable=False),
            sa.Column('raised_by', sa.String(length=255), nullable=False),
            sa.Column('raised_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('reviewed_by', sa.String(length=255), nullable=True),
            sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('resolved_by', sa.String(length=255), nullable=True),
            sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('closed_by', sa.String(length=255), nullable=True),
            sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('customer_response', sa.String(length=50), nullable=True),
            sa.Column('customer_response_note', sa.Text(), nullable=True),
            sa.Column('customer_response_by', sa.String(length=255), nullable=True),
            sa.Column('customer_response_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('root_cause_analysis', sa.Text(), nullable=True),
            sa.Column('corrective_actions', sa.Text(), nullable=True),
            sa.Column('preventive_actions', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_by', sa.String(length=255), nullable=True),
            sa.Column('updated_by', sa.String(length=255), nullable=True),
            sa.ForeignKeyConstraint(['job_id'], ['jobs.id']),
            sa.ForeignKeyConstraint(['srf_id'], ['srf.id']),
            sa.ForeignKeyConstraint(['srf_item_id'], ['srf_items.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('deviation_number')
        )
        op.create_index(op.f('ix_deviation_reports_id'), 'deviation_reports', ['id'], unique=False)
        op.create_index('idx_deviations_srf_id', 'deviation_reports', ['srf_id'], unique=False)
        op.create_index('idx_deviations_status', 'deviation_reports', ['status'], unique=False)
        
        # Add enum constraints manually
        op.execute(sa.text("""
            ALTER TABLE deviation_reports 
            ADD CONSTRAINT deviation_reports_deviation_type_enum_check 
            CHECK (deviation_type::text = ANY (ARRAY['OOT'::character varying, 'DAMAGED'::character varying, 'MISSING_STANDARD'::character varying, 'GB_FAILURE'::character varying, 'ENVIRONMENTAL'::character varying, 'EQUIPMENT_MALFUNCTION'::character varying]::text[]))
        """))
        
        op.execute(sa.text("""
            ALTER TABLE deviation_reports 
            ADD CONSTRAINT deviation_reports_status_enum_check 
            CHECK (status::text = ANY (ARRAY['OPEN'::character varying, 'IN_REVIEW'::character varying, 'CUSTOMER_NOTIFIED'::character varying, 'CUSTOMER_ACCEPTED'::character varying, 'CUSTOMER_REJECTED'::character varying, 'RESOLVED'::character varying, 'CLOSED'::character varying]::text[]))
        """))

    # Create deviation_actions table
    if 'deviation_actions' not in existing_tables:
        op.create_table('deviation_actions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('deviation_id', sa.Integer(), nullable=False),
            sa.Column('action_type', sa.String(length=50), nullable=False),
            sa.Column('action_by', sa.String(length=255), nullable=False),
            sa.Column('action_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('comments', sa.Text(), nullable=True),
            sa.Column('old_status', sa.String(length=50), nullable=True),
            sa.Column('new_status', sa.String(length=50), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['deviation_id'], ['deviation_reports.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_deviation_actions_deviation_id', 'deviation_actions', ['deviation_id'], unique=False)
        
        # Add enum constraints
        op.execute(sa.text("""
            ALTER TABLE deviation_actions 
            ADD CONSTRAINT deviation_actions_old_status_enum_check 
            CHECK (old_status IS NULL OR old_status::text = ANY (ARRAY['OPEN'::character varying, 'IN_REVIEW'::character varying, 'CUSTOMER_NOTIFIED'::character varying, 'CUSTOMER_ACCEPTED'::character varying, 'CUSTOMER_REJECTED'::character varying, 'RESOLVED'::character varying, 'CLOSED'::character varying]::text[]))
        """))
        
        op.execute(sa.text("""
            ALTER TABLE deviation_actions 
            ADD CONSTRAINT deviation_actions_new_status_enum_check 
            CHECK (new_status IS NULL OR new_status::text = ANY (ARRAY['OPEN'::character varying, 'IN_REVIEW'::character varying, 'CUSTOMER_NOTIFIED'::character varying, 'CUSTOMER_ACCEPTED'::character varying, 'CUSTOMER_REJECTED'::character varying, 'RESOLVED'::character varying, 'CLOSED'::character varying]::text[]))
        """))

    # Create notifications table
    if 'notifications' not in existing_tables:
        op.create_table('notifications',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('notification_type', sa.String(length=50), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('recipient_user_id', sa.Integer(), nullable=True),
            sa.Column('recipient_email', sa.String(length=255), nullable=True),
            sa.Column('deviation_id', sa.Integer(), nullable=True),
            sa.Column('srf_id', sa.Integer(), nullable=True),
            sa.Column('job_id', sa.Integer(), nullable=True),
            sa.Column('is_read', sa.Boolean(), server_default=sa.text('false'), nullable=False),
            sa.Column('is_email_sent', sa.Boolean(), server_default=sa.text('false'), nullable=False),
            sa.Column('email_sent_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('created_by', sa.String(length=255), nullable=True),
            sa.ForeignKeyConstraint(['deviation_id'], ['deviation_reports.id']),
            sa.ForeignKeyConstraint(['job_id'], ['jobs.id']),
            sa.ForeignKeyConstraint(['recipient_user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['srf_id'], ['srf.id']),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Add enum constraint
        op.execute(sa.text("""
            ALTER TABLE notifications 
            ADD CONSTRAINT notifications_notification_type_enum_check 
            CHECK (notification_type::text = ANY (ARRAY['DEVIATION_CREATED'::character varying, 'DEVIATION_RESPONSE_REQUIRED'::character varying, 'CUSTOMER_RESPONSE_RECEIVED'::character varying, 'DEVIATION_RESOLVED'::character varying, 'DEVIATION_CLOSED'::character varying]::text[]))
        """))

    # Add columns to existing tables safely
    jobs_columns = [col['name'] for col in inspector.get_columns('jobs')]
    if 'deviation_required' not in jobs_columns:
        op.add_column('jobs', sa.Column('deviation_required', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    if 'deviation_resolved' not in jobs_columns:
        op.add_column('jobs', sa.Column('deviation_resolved', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    if 'can_generate_certificate' not in jobs_columns:
        op.add_column('jobs', sa.Column('can_generate_certificate', sa.Boolean(), server_default=sa.text('true'), nullable=False))

    customers_columns = [col['name'] for col in inspector.get_columns('customers')]
    if 'notification_email' not in customers_columns:
        op.add_column('customers', sa.Column('notification_email', sa.String(length=255), nullable=True))
    if 'notification_phone' not in customers_columns:
        op.add_column('customers', sa.Column('notification_phone', sa.String(length=50), nullable=True))
    if 'preferred_notification_method' not in customers_columns:
        op.add_column('customers', sa.Column('preferred_notification_method', sa.String(length=50), server_default=sa.text("'email'"), nullable=False))


def downgrade():
    # Remove added columns
    op.drop_column('customers', 'preferred_notification_method')
    op.drop_column('customers', 'notification_phone')
    op.drop_column('customers', 'notification_email')
    op.drop_column('jobs', 'can_generate_certificate')
    op.drop_column('jobs', 'deviation_resolved')
    op.drop_column('jobs', 'deviation_required')
    
    # Drop tables
    op.drop_table('notifications')
    op.drop_table('deviation_actions')
    op.drop_table('deviation_reports')
    op.drop_table('users')
    
    # Drop enums with CASCADE (only the new ones)
    op.execute('DROP TYPE IF EXISTS notification_type CASCADE')
    op.execute('DROP TYPE IF EXISTS deviation_type CASCADE')
    op.execute('DROP TYPE IF EXISTS deviation_status CASCADE')
    # Skip user_role if it existed before this migration
