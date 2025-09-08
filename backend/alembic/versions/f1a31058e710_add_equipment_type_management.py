"""Add Equipment Type Management

Revision ID: f1a31058e710
Revises: 4a635be509ee
Create Date: 2025-09-04 12:01:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

revision = 'f1a31058e710'
down_revision = '4a635be509ee'

def upgrade():
    # Get database connection and inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()
    
    # 1. Equipment Categories
    if 'equipment_categories' not in existing_tables:
        op.create_table('equipment_categories',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('name', sa.String(100), nullable=False, unique=True),
            sa.Column('description', sa.Text()),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
        )
    
    # 2. Equipment Types
    if 'equipment_types' not in existing_tables:
        op.create_table('equipment_types',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('category_id', sa.Integer(), sa.ForeignKey('equipment_categories.id')),
            sa.Column('nomenclature', sa.String(200), nullable=False),
            sa.Column('type_code', sa.String(50), nullable=False, unique=True),
            sa.Column('unit', sa.String(20), nullable=False),
            sa.Column('min_range', sa.Float()),
            sa.Column('max_range', sa.Float()),
            sa.Column('classification', sa.String(100)),
            sa.Column('calibration_method', sa.String(200)),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
        )
    
    # 3. Handle measurement_templates (conditionally)
    if 'measurement_templates' in existing_tables:
        # Table exists, check if we need to add equipment_type_id column
        existing_columns = [c['name'] for c in inspector.get_columns('measurement_templates')]
        if 'equipment_type_id' not in existing_columns:
            with op.batch_alter_table('measurement_templates') as batch_op:
                batch_op.add_column(sa.Column('equipment_type_id', sa.Integer(), sa.ForeignKey('equipment_types.id')))
    else:
        # Create the table
        op.create_table('measurement_templates',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('equipment_type_id', sa.Integer(), sa.ForeignKey('equipment_types.id')),
            sa.Column('template_name', sa.String(255), nullable=False),
            sa.Column('measurement_points', sa.JSON()),
            sa.Column('readings_per_point', sa.Integer(), default=5),
            sa.Column('test_types', sa.JSON()),
            sa.Column('environmental_requirements', sa.JSON()),
            sa.Column('is_default', sa.Boolean(), default=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
        )
    
    # 4. Enhance standards table (conditionally add columns)
    existing_standards_columns = [c['name'] for c in inspector.get_columns('standards')]
    
    if 'equipment_category_id' not in existing_standards_columns:
        op.add_column('standards', sa.Column('equipment_category_id', sa.Integer(), sa.ForeignKey('equipment_categories.id')))
    
    if 'applicable_range_min' not in existing_standards_columns:
        op.add_column('standards', sa.Column('applicable_range_min', sa.Float()))
    
    if 'applicable_range_max' not in existing_standards_columns:
        op.add_column('standards', sa.Column('applicable_range_max', sa.Float()))
    
    if 'discipline' not in existing_standards_columns:
        op.add_column('standards', sa.Column('discipline', sa.String(50)))
    
    # 5. Standards Selection Rules
    if 'standards_selection_rules' not in existing_tables:
        op.create_table('standards_selection_rules',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('equipment_type_id', sa.Integer(), sa.ForeignKey('equipment_types.id')),
            sa.Column('standard_id', sa.Integer(), sa.ForeignKey('standards.id')),
            sa.Column('priority', sa.Integer(), default=1),
            sa.Column('range_min', sa.Float()),
            sa.Column('range_max', sa.Float()),
            sa.Column('is_active', sa.Boolean(), default=True)
        )
    
    # 6. Calculation Formulas
    if 'calculation_formulas' not in existing_tables:
        op.create_table('calculation_formulas',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('equipment_category_id', sa.Integer(), sa.ForeignKey('equipment_categories.id')),
            sa.Column('formula_name', sa.String(100), nullable=False),
            sa.Column('formula_type', sa.String(50)),
            sa.Column('formula_expression', sa.Text()),
            sa.Column('parameters', sa.JSON()),
            sa.Column('version', sa.String(10), default="1.0"),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
        )
    
    # 7. Add equipment_type_id to jobs table (conditionally)
    existing_jobs_columns = [c['name'] for c in inspector.get_columns('jobs')]
    if 'equipment_type_id' not in existing_jobs_columns:
        op.add_column('jobs', sa.Column('equipment_type_id', sa.Integer(), sa.ForeignKey('equipment_types.id')))
    
    # 8. Create indexes (if tables were created)
    try:
        op.create_index('idx_equipment_types_category', 'equipment_types', ['category_id'])
    except:
        pass  # Index might already exist
    
    try:
        op.create_index('idx_equipment_types_nomenclature', 'equipment_types', ['nomenclature'])
    except:
        pass  # Index might already exist
    
    try:
        op.create_index('idx_standards_selection_equipment', 'standards_selection_rules', ['equipment_type_id'])
    except:
        pass  # Index might already exist

def downgrade():
    # Remove in reverse order
    try:
        op.drop_index('idx_standards_selection_equipment')
    except:
        pass
    
    try:
        op.drop_index('idx_equipment_types_nomenclature')
    except:
        pass
    
    try:
        op.drop_index('idx_equipment_types_category')
    except:
        pass
    
    # Drop columns from jobs
    try:
        op.drop_column('jobs', 'equipment_type_id')
    except:
        pass
    
    # Drop new tables
    try:
        op.drop_table('calculation_formulas')
    except:
        pass
    
    try:
        op.drop_table('standards_selection_rules')
    except:
        pass
    
    # Remove columns from standards
    try:
        op.drop_column('standards', 'discipline')
        op.drop_column('standards', 'applicable_range_max')
        op.drop_column('standards', 'applicable_range_min')
        op.drop_column('standards', 'equipment_category_id')
    except:
        pass
    
    # Handle measurement_templates
    try:
        op.drop_column('measurement_templates', 'equipment_type_id')
    except:
        pass
    
    try:
        op.drop_table('equipment_types')
    except:
        pass
    
    try:
        op.drop_table('equipment_categories')
    except:
        pass
