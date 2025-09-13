"""add_calculation_engine_tables.py

Revision ID: adcf82c4a191
Revises: a3a36bf00ef7
Create Date: 2025-09-12 20:23:46.852062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'adcf82c4a191'
down_revision: Union[str, None] = 'a3a36bf00ef7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create formula_lookup_tables
    op.create_table('formula_lookup_tables',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('equipment_type_id', sa.Integer, sa.ForeignKey('equipment_types.id'), nullable=True),
        sa.Column('lookup_type', sa.String(50), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('range_column', sa.String(50), nullable=True),
        sa.Column('data_structure', sa.JSON, nullable=False),
        sa.Column('lookup_data', sa.JSON, nullable=False),
        sa.Column('validity_period', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.sql.expression.true()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())
    )
    
    # Create calculation_methods
    op.create_table('calculation_methods',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('method_name', sa.String(100), nullable=False),
        sa.Column('equipment_type_id', sa.Integer, sa.ForeignKey('equipment_types.id'), nullable=True),
        sa.Column('calculation_stage', sa.Integer, nullable=False),
        sa.Column('calculation_order', sa.Integer, nullable=False),
        sa.Column('calculation_type', sa.String(50), nullable=False),
        sa.Column('formula_expression', sa.Text, nullable=False),
        sa.Column('input_requirements', sa.JSON, nullable=False),
        sa.Column('output_fields', sa.JSON, nullable=False),
        sa.Column('validation_rules', sa.JSON, nullable=True),
        sa.Column('tolerance_limits', sa.JSON, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.sql.expression.true()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())
    )
    
    # Create job_calculation_results
    op.create_table('job_calculation_results',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('job_id', sa.Integer, sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('calculation_stage', sa.Integer, nullable=False),
        sa.Column('calculation_type', sa.String(50), nullable=False),
        sa.Column('calculation_order', sa.Integer, nullable=True, server_default='0'),
        sa.Column('input_data', sa.JSON, nullable=False),
        sa.Column('measurement_readings', sa.JSON, nullable=True),
        sa.Column('calculated_values', sa.JSON, nullable=False),
        sa.Column('intermediate_steps', sa.JSON, nullable=True),
        sa.Column('formulas_used', sa.JSON, nullable=True),
        sa.Column('constants_used', sa.JSON, nullable=True),
        sa.Column('lookup_tables_used', sa.JSON, nullable=True),
        sa.Column('standards_referenced', sa.JSON, nullable=True),
        sa.Column('validation_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('validation_details', sa.JSON, nullable=True),
        sa.Column('error_details', sa.Text, nullable=True),
        sa.Column('exceeds_tolerance', sa.Boolean, nullable=False, server_default=sa.sql.expression.false()),
        sa.Column('tolerance_value', sa.DECIMAL(10, 6), nullable=True),
        sa.Column('deviation_percentage', sa.DECIMAL(10, 6), nullable=True),
        sa.Column('auto_deviation_triggered', sa.Boolean, nullable=False, server_default=sa.sql.expression.false()),
        sa.Column('calculated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('calculated_by', sa.String(255), nullable=True),
        sa.Column('calculation_engine_version', sa.String(10), nullable=False, server_default='1.0')
    )
    
    # Create standards_certificate_data
    op.create_table('standards_certificate_data',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('standard_id', sa.Integer, sa.ForeignKey('standards.id'), nullable=False),
        sa.Column('certificate_validity_start', sa.Date, nullable=True),
        sa.Column('certificate_validity_end', sa.Date, nullable=False),
        sa.Column('calibration_points', sa.JSON, nullable=False),
        sa.Column('certificate_reference', sa.String(255), nullable=True),
        sa.Column('traceability_chain', sa.Text, nullable=True),
        sa.Column('measurement_conditions', sa.JSON, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.sql.expression.true()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())
    )
    
    # Create calculation_engine_config
    op.create_table('calculation_engine_config',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('config_name', sa.String(100), nullable=False, unique=True),
        sa.Column('equipment_type', sa.String(50), nullable=True),
        sa.Column('stage1_methods', sa.JSON, nullable=True),
        sa.Column('stage2_methods', sa.JSON, nullable=True),
        sa.Column('stage3_methods', sa.JSON, nullable=True),
        sa.Column('auto_deviation_enabled', sa.Boolean, nullable=False, server_default=sa.sql.expression.true()),
        sa.Column('tolerance_config', sa.JSON, nullable=True),
        sa.Column('notification_config', sa.JSON, nullable=True),
        sa.Column('formula_constants', sa.JSON, nullable=True),
        sa.Column('interpolation_tables', sa.JSON, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.sql.expression.true()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())
    )


def downgrade():
    op.drop_table('calculation_engine_config')
    op.drop_table('standards_certificate_data')
    op.drop_table('job_calculation_results')
    op.drop_table('calculation_methods')
    op.drop_table('formula_lookup_tables')
