"""add_user_type_column_to_users_table

Revision ID: 8d2ed0018108
Revises: 56c6cad1d7e1
Create Date: 2025-09-07 08:45:33.734064

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d2ed0018108'
down_revision: Union[str, None] = '56c6cad1d7e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add user_type column with default value
    op.add_column('users', 
        sa.Column('user_type', sa.String(50), 
                 server_default='internal', 
                 nullable=False))
    
    # Update existing records to have a default user_type
    op.execute("UPDATE users SET user_type = 'internal' WHERE user_type IS NULL")

def downgrade():
    # Remove user_type column
    op.drop_column('users', 'user_type')
