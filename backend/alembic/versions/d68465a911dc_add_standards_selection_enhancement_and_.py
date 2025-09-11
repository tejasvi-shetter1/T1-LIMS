"""add standards selection enhancement and fix missing columns

Revision ID: d68465a911dc
Revises: 4d81e3c74001
Create Date: 2025-09-08 19:39:14.233332

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = 'd68465a911dc'
down_revision: Union[str, None] = '4d81e3c74001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Add missing timestamp columns and enhance standards selection"""
    
    # Fix standards_selection_rules table - add missing TimestampMixin columns
    try:
        op.add_column('standards_selection_rules', 
                     sa.Column('created_at', sa.DateTime(timezone=True), 
                              server_default=sa.func.now(), nullable=False))
        print(" Added created_at to standards_selection_rules")
    except Exception as e:
        print(f"created_at column might exist: {e}")
    
    try:
        op.add_column('standards_selection_rules', 
                     sa.Column('updated_at', sa.DateTime(timezone=True), 
                              onupdate=sa.func.now(), nullable=True))
        print("Added updated_at to standards_selection_rules")
    except Exception as e:
        print(f"updated_at column might exist: {e}")
    
    # Add auto_selected and selection_timestamp to job_standards
    try:
        op.add_column('job_standards', 
                     sa.Column('auto_selected', sa.Boolean(), default=True, nullable=True))
        print("Added auto_selected to job_standards")
    except Exception as e:
        print(f" auto_selected column might exist: {e}")
    
    try:
        op.add_column('job_standards', 
                     sa.Column('selection_timestamp', sa.Date(), 
                              default=datetime.today, nullable=True))
        print(" Added selection_timestamp to job_standards")
    except Exception as e:
        print(f" selection_timestamp column might exist: {e}")

def downgrade():
    """Remove added columns"""
    try:
        op.drop_column('job_standards', 'selection_timestamp')
        op.drop_column('job_standards', 'auto_selected')
        op.drop_column('standards_selection_rules', 'updated_at')
        op.drop_column('standards_selection_rules', 'created_at')
        print(" Removed added columns")
    except Exception as e:
        print(f"Error in downgrade: {e}")
