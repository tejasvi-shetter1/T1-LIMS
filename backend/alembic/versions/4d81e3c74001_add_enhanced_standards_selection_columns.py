"""add enhanced standards selection columns

Revision ID: 4d81e3c74001
Revises: 3f2b470fccbd
Create Date: 2025-09-08 16:59:47.871417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d81e3c74001'
down_revision: Union[str, None] = '3f2b470fccbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Just add a few new columns to existing tables (no new tables needed)
    
    try:
        # Add JSON columns to equipment_types if they don't exist
        op.add_column('equipment_types', sa.Column('measurement_points', sa.JSON(), nullable=True))
    except Exception as e:
        print(f"Column measurement_points might already exist: {e}")
    
    try:
        op.add_column('equipment_types', sa.Column('required_standards_config', sa.JSON(), nullable=True))
    except Exception as e:
        print(f"Column required_standards_config might already exist: {e}")
    
    try:
        # Add rule_name to standards_selection_rules if it doesn't exist
        op.add_column('standards_selection_rules', sa.Column('rule_name', sa.String(255), nullable=True))
    except Exception as e:
        print(f"Column rule_name might already exist: {e}")
    
    try:
        # Add selection_reason to job_standards if it doesn't exist
        op.add_column('job_standards', sa.Column('selection_reason', sa.Text(), nullable=True))
    except Exception as e:
        print(f"Column selection_reason might already exist: {e}")

def downgrade():
    # Remove added columns
    try:
        op.drop_column('job_standards', 'selection_reason')
        op.drop_column('standards_selection_rules', 'rule_name')
        op.drop_column('equipment_types', 'required_standards_config')
        op.drop_column('equipment_types', 'measurement_points')
    except Exception as e:
        print(f"Error in downgrade: {e}")
