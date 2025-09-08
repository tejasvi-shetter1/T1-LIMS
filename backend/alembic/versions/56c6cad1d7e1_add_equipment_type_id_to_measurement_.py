"""Add equipment_type_id to measurement_templates

Revision ID: 56c6cad1d7e1
Revises: f1a31058e710
Create Date: 2025-09-06 21:43:46.762858

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56c6cad1d7e1'
down_revision: Union[str, None] = 'f1a31058e710'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Add equipment_type_id column if it doesn't exist
    op.add_column('measurement_templates', 
                  sa.Column('equipment_type_id', sa.Integer(), nullable=False))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_measurement_templates_equipment_type_id',
        'measurement_templates', 'equipment_types',
        ['equipment_type_id'], ['id']
    )

def downgrade():
    # Drop foreign key constraint
    op.drop_constraint('fk_measurement_templates_equipment_type_id', 
                       'measurement_templates', type_='foreignkey')
    
    # Drop column
    op.drop_column('measurement_templates', 'equipment_type_id')
