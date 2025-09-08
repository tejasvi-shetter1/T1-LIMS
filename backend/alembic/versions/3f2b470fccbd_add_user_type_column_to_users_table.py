
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f2b470fccbd'
down_revision: Union[str, None] = '8d2ed0018108'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

"""fix humidity column precision in measurements table

Revision ID: [auto-generated]
Revises: [previous-revision]
Create Date: [auto-generated]
"""

def upgrade():
    # Fix humidity columns to support percentage values (0-100%)
    # Change from DECIMAL(5,4) to DECIMAL(7,4) to support values like 60.5000
    op.alter_column('measurements', 'humidity_before',
                   existing_type=sa.DECIMAL(precision=5, scale=4),
                   type_=sa.DECIMAL(precision=7, scale=4),
                   existing_nullable=True)
    
    op.alter_column('measurements', 'humidity_after',
                   existing_type=sa.DECIMAL(precision=5, scale=4),
                   type_=sa.DECIMAL(precision=7, scale=4),
                   existing_nullable=True)

def downgrade():
    # Revert back to original schema (WARNING: May lose data)
    op.alter_column('measurements', 'humidity_before',
                   existing_type=sa.DECIMAL(precision=7, scale=4),
                   type_=sa.DECIMAL(precision=5, scale=4),
                   existing_nullable=True)
    
    op.alter_column('measurements', 'humidity_after',
                   existing_type=sa.DECIMAL(precision=7, scale=4),
                   type_=sa.DECIMAL(precision=5, scale=4),
                   existing_nullable=True)
