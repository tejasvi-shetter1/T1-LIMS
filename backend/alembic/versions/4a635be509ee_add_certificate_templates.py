"""add_certificate_templates

Revision ID: 4a635be509ee
Revises: 85cb21df2e65
Create Date: 2025-09-03 20:14:02.916283

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '4a635be509ee'
down_revision = '85cb21df2e65'
branch_labels = None
depends_on = None

def upgrade():
    # Create certificate_templates table
    op.create_table('certificate_templates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('template_name', sa.String(100), nullable=False),
        sa.Column('template_type', sa.String(20), nullable=False),  # Crt1, Crt2, Crt3
        sa.Column('equipment_types', sa.JSON(), nullable=True),
        sa.Column('template_path', sa.String(255), nullable=False),
        sa.Column('template_content', sa.Text(), nullable=True),  # HTML template content
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('version', sa.String(10), default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(255)),
        sa.Column('updated_by', sa.String(255))
    )
    
    # Add certificate generation workflow fields to existing certificates table
    op.add_column('certificates', sa.Column('template_id', sa.Integer()))
    op.add_column('certificates', sa.Column('generation_status', sa.String(50), default='pending'))
    op.add_column('certificates', sa.Column('generation_started_at', sa.DateTime(timezone=True)))
    op.add_column('certificates', sa.Column('generation_completed_at', sa.DateTime(timezone=True)))
    op.add_column('certificates', sa.Column('generation_error', sa.Text()))
    op.add_column('certificates', sa.Column('file_size_bytes', sa.Integer()))
    op.add_column('certificates', sa.Column('file_hash', sa.String(64)))
    op.add_column('certificates', sa.Column('auto_populated_fields', sa.JSON()))
    op.add_column('certificates', sa.Column('manual_override_fields', sa.JSON()))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'certificates_template_id_fkey',
        'certificates', 'certificate_templates',
        ['template_id'], ['id']
    )
    
    # Add indexes for performance
    op.create_index('idx_certificates_template_id', 'certificates', ['template_id'])
    op.create_index('idx_certificates_generation_status', 'certificates', ['generation_status'])
    op.create_index('idx_certificate_templates_type', 'certificate_templates', ['template_type'])

def downgrade():
    op.drop_index('idx_certificate_templates_type', 'certificate_templates')
    op.drop_index('idx_certificates_generation_status', 'certificates')
    op.drop_index('idx_certificates_template_id', 'certificates')
    
    op.drop_constraint('certificates_template_id_fkey', 'certificates')
    
    op.drop_column('certificates', 'manual_override_fields')
    op.drop_column('certificates', 'auto_populated_fields')
    op.drop_column('certificates', 'file_hash')
    op.drop_column('certificates', 'file_size_bytes')
    op.drop_column('certificates', 'generation_error')
    op.drop_column('certificates', 'generation_completed_at')
    op.drop_column('certificates', 'generation_started_at')
    op.drop_column('certificates', 'generation_status')
    op.drop_column('certificates', 'template_id')
    
    op.drop_table('certificate_templates')
