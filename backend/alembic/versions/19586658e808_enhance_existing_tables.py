"""enhance_existing_tables

Revision ID: 19586658e808
Revises: adcf82c4a191
Create Date: 2025-09-12 20:34:49.996176

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '19586658e808'
down_revision: Union[str, None] = 'adcf82c4a191'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def column_exists(connection, table_name, column_name):
    """Check if a column exists in a table"""
    result = connection.execute(
        sa.text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = :table_name 
            AND column_name = :column_name
        """),
        {"table_name": table_name, "column_name": column_name}
    )
    return result.scalar() > 0


def upgrade():
    # Get connection for checking existing columns
    connection = op.get_bind()
    
    # Enhance jobs table - check each column before adding
    if not column_exists(connection, 'jobs', 'calculation_engine_version'):
        op.add_column('jobs', sa.Column('calculation_engine_version', sa.String(10), nullable=True, server_default='1.0'))
    
    if not column_exists(connection, 'jobs', 'auto_deviation_enabled'):
        op.add_column('jobs', sa.Column('auto_deviation_enabled', sa.Boolean, nullable=True, server_default=sa.sql.expression.true()))
    
    if not column_exists(connection, 'jobs', 'calculation_status'):
        op.add_column('jobs', sa.Column('calculation_status', sa.String(50), nullable=True, server_default='pending'))
    
    if not column_exists(connection, 'jobs', 'calculation_started_at'):
        op.add_column('jobs', sa.Column('calculation_started_at', sa.TIMESTAMP(timezone=True), nullable=True))
    
    if not column_exists(connection, 'jobs', 'calculation_completed_at'):
        op.add_column('jobs', sa.Column('calculation_completed_at', sa.TIMESTAMP(timezone=True), nullable=True))
    
    if not column_exists(connection, 'jobs', 'calculation_error'):
        op.add_column('jobs', sa.Column('calculation_error', sa.Text, nullable=True))
    
    if not column_exists(connection, 'jobs', 'tolerance_limits'):
        op.add_column('jobs', sa.Column('tolerance_limits', sa.JSON, nullable=True))
    
    if not column_exists(connection, 'jobs', 'calculation_config'):
        op.add_column('jobs', sa.Column('calculation_config', sa.JSON, nullable=True))

    # Enhance measurements table
    if not column_exists(connection, 'measurements', 'measurement_readings'):
        op.add_column('measurements', sa.Column('measurement_readings', sa.JSON, nullable=True))
    
    if not column_exists(connection, 'measurements', 'environmental_conditions'):
        op.add_column('measurements', sa.Column('environmental_conditions', sa.JSON, nullable=True))
    
    if not column_exists(connection, 'measurements', 'standards_used'):
        op.add_column('measurements', sa.Column('standards_used', sa.JSON, nullable=True))
    
    if not column_exists(connection, 'measurements', 'calculation_results'):
        op.add_column('measurements', sa.Column('calculation_results', sa.JSON, nullable=True))
    
    if not column_exists(connection, 'measurements', 'validation_results'):
        op.add_column('measurements', sa.Column('validation_results', sa.JSON, nullable=True))

    # Enhance job_standards table
    if not column_exists(connection, 'job_standards', 'auto_selected'):
        op.add_column('job_standards', sa.Column('auto_selected', sa.Boolean, nullable=True, server_default=sa.sql.expression.true()))
    
    if not column_exists(connection, 'job_standards', 'selection_timestamp'):
        op.add_column('job_standards', sa.Column('selection_timestamp', sa.Date, nullable=True, server_default=sa.func.current_date()))
    
    if not column_exists(connection, 'job_standards', 'interpolation_data'):
        op.add_column('job_standards', sa.Column('interpolation_data', sa.JSON, nullable=True))

    # Create indexes only if they don't exist
    try:
        op.create_index('idx_job_calculation_results_job_id', 'job_calculation_results', ['job_id'], unique=False, if_not_exists=True)
    except:
        pass  # Index might already exist
    
    try:
        op.create_index('idx_job_calculation_results_stage', 'job_calculation_results', ['calculation_stage', 'calculation_type'], unique=False, if_not_exists=True)
    except:
        pass
    
    try:
        op.create_index('idx_formula_lookup_type', 'formula_lookup_tables', ['lookup_type', 'equipment_type_id'], unique=False, if_not_exists=True)
    except:
        pass
    
    try:
        op.create_index('idx_standards_certificate_active', 'standards_certificate_data', ['standard_id', 'is_active'], unique=False, if_not_exists=True)
    except:
        pass


def downgrade():
    # Drop indexes (ignore errors if they don't exist)
    try:
        op.drop_index('idx_standards_certificate_active', table_name='standards_certificate_data')
    except:
        pass
    
    try:
        op.drop_index('idx_formula_lookup_type', table_name='formula_lookup_tables')
    except:
        pass
    
    try:
        op.drop_index('idx_job_calculation_results_stage', table_name='job_calculation_results')
    except:
        pass
    
    try:
        op.drop_index('idx_job_calculation_results_job_id', table_name='job_calculation_results')
    except:
        pass

    # Drop columns (ignore errors if they don't exist)
    try:
        op.drop_column('job_standards', 'interpolation_data')
        op.drop_column('job_standards', 'selection_timestamp')
        op.drop_column('job_standards', 'auto_selected')
    except:
        pass

    try:
        op.drop_column('measurements', 'validation_results')
        op.drop_column('measurements', 'calculation_results')
        op.drop_column('measurements', 'standards_used')
        op.drop_column('measurements', 'environmental_conditions')
        op.drop_column('measurements', 'measurement_readings')
    except:
        pass

    try:
        op.drop_column('jobs', 'calculation_config')
        op.drop_column('jobs', 'tolerance_limits')
        op.drop_column('jobs', 'calculation_error')
        op.drop_column('jobs', 'calculation_completed_at')
        op.drop_column('jobs', 'calculation_started_at')
        op.drop_column('jobs', 'calculation_status')
        op.drop_column('jobs', 'auto_deviation_enabled')
        op.drop_column('jobs', 'calculation_engine_version')
    except:
        pass
