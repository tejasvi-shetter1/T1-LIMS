"""enhanced_calculation_engine

Revision ID: a3a36bf00ef7
Revises: d68465a911dc
Create Date: 2025-09-11 17:41:01.069824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3a36bf00ef7'
down_revision: Union[str, None] = 'd68465a911dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Create enhanced calculation engine tables"""
    
    print("🏗️  Creating enhanced calculation engine schema...")
    
    # 1. FORMULA LOOKUP TABLES (X-Lookup functionality from Excel)
    op.create_table(
        'formula_lookup_tables',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('table_name', sa.String(100), nullable=False, unique=True),
        sa.Column('calibration_method', sa.String(100), nullable=False),
        sa.Column('equipment_category_id', sa.Integer(), sa.ForeignKey('equipment_categories.id')),
        sa.Column('description', sa.Text()),
        
        # Core X-Lookup Data (from your Excel Formulae sheet)
        sa.Column('lookup_data', sa.JSON(), nullable=False, comment='X-lookup table data with ranges and errors'),
        sa.Column('interpolation_config', sa.JSON(), comment='Interpolation rules and parameters'),
        
        # Range Configuration
        sa.Column('lower_ranges', sa.JSON(), comment='Lower range values for lookup'),
        sa.Column('higher_ranges', sa.JSON(), comment='Higher range values for lookup'),
        sa.Column('error_lower', sa.JSON(), comment='Lower error values'),
        sa.Column('error_higher', sa.JSON(), comment='Higher error values'),
        sa.Column('interpolation_points', sa.JSON(), comment='Calculated interpolation points'),
        
        # Metadata
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('version', sa.String(10), default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(255)),
        sa.Column('updated_by', sa.String(255)),
        
        # Indexes for performance
        sa.Index('idx_formula_lookup_method', 'calibration_method', 'equipment_category_id'),
        sa.Index('idx_formula_lookup_active', 'is_active')
    )
    print("    Created formula_lookup_tables")
    
    # 2. CALCULATION CONSTANTS (UN_resolution, repeatability constants)
    op.create_table(
        'calculation_constants',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('constant_name', sa.String(100), nullable=False),
        sa.Column('calibration_method', sa.String(100), nullable=False),
        sa.Column('equipment_category_id', sa.Integer(), sa.ForeignKey('equipment_categories.id')),
        
        # Constant Values
        sa.Column('constant_value', sa.Numeric(20, 15), comment='Single numeric constant'),
        sa.Column('constant_data', sa.JSON(), comment='Complex constant data structures'),
        sa.Column('constant_matrix', sa.JSON(), comment='Matrix data for repeatability calculations'),
        
        # Configuration
        sa.Column('data_type', sa.String(50), comment='Type: scalar, array, matrix, lookup_table'),
        sa.Column('unit', sa.String(20)),
        sa.Column('description', sa.Text()),
        sa.Column('formula_reference', sa.String(255), comment='Reference to source formula/sheet'),
        
        # Metadata
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(255)),
        sa.Column('updated_by', sa.String(255)),
        
        # Constraints
        sa.UniqueConstraint('constant_name', 'calibration_method', 'equipment_category_id', 
                          name='uk_calc_constants_name_method'),
        sa.Index('idx_calc_constants_method', 'calibration_method', 'equipment_category_id'),
        sa.Index('idx_calc_constants_name', 'constant_name')
    )
    print("   Created calculation_constants")
    
    # 3. CALCULATION FORMULA TEMPLATES
    op.create_table(
        'calculation_formula_templates',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('template_name', sa.String(200), nullable=False),
        sa.Column('calibration_method', sa.String(100), nullable=False),
        sa.Column('equipment_category_id', sa.Integer(), sa.ForeignKey('equipment_categories.id')),
        
        # Formula Definition
        sa.Column('formula_type', sa.String(50), nullable=False, 
                 comment='Type: uncertainty, repeatability, interpolation, deviation'),
        sa.Column('formula_expression', sa.Text(), nullable=False, 
                 comment='Python/SQL expression for calculation'),
        sa.Column('excel_reference', sa.Text(), comment='Original Excel formula for reference'),
        
        # Parameters
        sa.Column('input_parameters', sa.JSON(), comment='Required input parameters with types'),
        sa.Column('output_parameters', sa.JSON(), comment='Output parameters with types'),
        sa.Column('constants_required', sa.JSON(), comment='Required calculation constants'),
        sa.Column('lookup_tables_required', sa.JSON(), comment='Required lookup tables'),
        
        # Validation and Tolerance
        sa.Column('validation_rules', sa.JSON(), comment='Validation rules for inputs/outputs'),
        sa.Column('tolerance_limits', sa.JSON(), comment='Tolerance limits for deviation detection'),
        sa.Column('deviation_thresholds', sa.JSON(), comment='Thresholds for auto-deviation triggers'),
        
        # Documentation
        sa.Column('description', sa.Text()),
        sa.Column('calculation_steps', sa.JSON(), comment='Step-by-step calculation documentation'),
        sa.Column('example_data', sa.JSON(), comment='Example input/output for testing'),
        
        # Metadata
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('version', sa.String(10), default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(255)),
        sa.Column('updated_by', sa.String(255)),
        
        # Constraints
        sa.UniqueConstraint('template_name', 'calibration_method', 'version', 
                          name='uk_formula_templates_name_method_version'),
        sa.Index('idx_formula_templates_type', 'formula_type', 'calibration_method'),
        sa.Index('idx_formula_templates_active', 'is_active')
    )
    print("   Created calculation_formula_templates")
    
    # 4. ENHANCE STANDARDS TABLE
    print("🔧 Enhancing standards table...")
    op.add_column('standards', sa.Column('formula_data', sa.JSON(), 
                 comment='Standards-specific formula data and coefficients'))
    op.add_column('standards', sa.Column('interpolation_points', sa.JSON(), 
                 comment='Pre-calculated interpolation points for X-lookup'))
    op.add_column('standards', sa.Column('uncertainty_coefficients', sa.JSON(), 
                 comment='Uncertainty calculation coefficients'))
    op.add_column('standards', sa.Column('pressure_gauge_data', sa.JSON(), 
                 comment='Pressure gauge specific data from certificates'))
    op.add_column('standards', sa.Column('calibration_curve', sa.JSON(), 
                 comment='Calibration curve data points'))
    print("   Enhanced standards table")
    
    # 5. JOB CALCULATION RESULTS
    op.create_table(
        'job_calculation_results',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('jobs.id'), nullable=False),
        sa.Column('measurement_id', sa.Integer(), sa.ForeignKey('measurements.id')),
        
        # Calculation Identification
        sa.Column('calculation_type', sa.String(50), nullable=False, 
                 comment='Type: uncertainty_budget, repeatability, reproducibility, etc.'),
        sa.Column('calculation_step', sa.String(100), comment='Step in calculation workflow'),
        sa.Column('formula_template_id', sa.Integer(), sa.ForeignKey('calculation_formula_templates.id')),
        
        # Calculation Data
        sa.Column('input_data', sa.JSON(), nullable=False, comment='All input data used'),
        sa.Column('calculation_results', sa.JSON(), nullable=False, comment='Complete calculation results'),
        sa.Column('intermediate_results', sa.JSON(), comment='Intermediate calculation steps'),
        sa.Column('final_values', sa.JSON(), comment='Final calculated values'),
        
        # Tolerance and Deviation Detection
        sa.Column('tolerance_check', sa.JSON(), comment='Tolerance check results'),
        sa.Column('deviation_detected', sa.Boolean(), default=False),
        sa.Column('deviation_percentage', sa.Numeric(10, 4)),
        sa.Column('deviation_type', sa.String(50), comment='Type of deviation detected'),
        sa.Column('deviation_severity', sa.String(20), comment='Severity: low, medium, high'),
        
        # Traceability
        sa.Column('formulas_used', sa.JSON(), comment='Track which formulas were used'),
        sa.Column('constants_used', sa.JSON(), comment='Track which constants were used'),
        sa.Column('lookup_tables_used', sa.JSON(), comment='Track which lookup tables were used'),
        sa.Column('calculation_timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('calculated_by', sa.String(255)),
        
        # Validation Status
        sa.Column('validation_status', sa.String(50), default='pending', 
                 comment='Status: pending, passed, failed, requires_review'),
        sa.Column('validation_notes', sa.Text()),
        
        # Indexes
        sa.Index('idx_job_calc_results_job', 'job_id'),
        sa.Index('idx_job_calc_results_type', 'calculation_type'),
        sa.Index('idx_job_calc_results_deviation', 'deviation_detected')
    )
    print(" Created job_calculation_results")
    
    # 6. NOTIFICATION TEMPLATES
    op.create_table(
        'notification_templates',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('template_name', sa.String(100), nullable=False, unique=True),
        sa.Column('template_code', sa.String(50), nullable=False, unique=True),
        
        # Notification Configuration
        sa.Column('notification_type', sa.String(50), nullable=False, 
                 comment='Type: deviation_alert, first_inspection, final_inspection'),
        sa.Column('trigger_condition', sa.JSON(), comment='Conditions that trigger this notification'),
        sa.Column('auto_trigger', sa.Boolean(), default=False),
        
        # Email Template
        sa.Column('subject_template', sa.String(255)),
        sa.Column('body_template', sa.Text()),
        sa.Column('body_html_template', sa.Text()),
        
        # Attachment Configuration
        sa.Column('attachment_config', sa.JSON(), comment='Excel generation configuration'),
        sa.Column('attachment_templates', sa.JSON(), comment='Template files for attachments'),
        
        # Recipient Configuration
        sa.Column('recipient_config', sa.JSON(), comment='Who gets the notification'),
        sa.Column('cc_recipients', sa.JSON(), comment='CC recipients'),
        sa.Column('bcc_recipients', sa.JSON(), comment='BCC recipients'),
        
        # Delivery Settings
        sa.Column('delivery_method', sa.String(50), default='email'),
        sa.Column('priority', sa.String(20), default='normal'),
        sa.Column('retry_config', sa.JSON(), comment='Retry configuration for failed sends'),
        
        # Metadata
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(255)),
        sa.Column('updated_by', sa.String(255)),
        
        # Indexes
        sa.Index('idx_notification_templates_type', 'notification_type'),
        sa.Index('idx_notification_templates_active', 'is_active')
    )
    print("Created notification_templates")
    
    # 7. NOTIFICATION LOG (Track sent notifications)
    op.create_table(
        'notification_log',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('notification_templates.id')),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('jobs.id')),
        sa.Column('inward_id', sa.Integer(), sa.ForeignKey('inward.id')),
        
        # Notification Details
        sa.Column('recipient_email', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(255)),
        sa.Column('notification_type', sa.String(50)),
        
        # Send Status
        sa.Column('send_status', sa.String(50), default='pending', 
                 comment='Status: pending, sent, failed, retry'),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('delivery_confirmation', sa.Boolean(), default=False),
        sa.Column('error_message', sa.Text()),
        sa.Column('retry_count', sa.Integer(), default=0),
        
        # Attachment Info
        sa.Column('attachments', sa.JSON(), comment='List of attachment file paths'),
        sa.Column('attachment_generated', sa.Boolean(), default=False),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        
        # Indexes
        sa.Index('idx_notification_log_job', 'job_id'),
        sa.Index('idx_notification_log_status', 'send_status'),
        sa.Index('idx_notification_log_sent', 'sent_at')
    )
    print(" Created notification_log")
    
    # 8. ENHANCE JOBS TABLE
    print(" Enhancing jobs table...")
    op.add_column('jobs', sa.Column('calculation_engine_version', sa.String(10), default='1.0'))
    op.add_column('jobs', sa.Column('auto_deviation_enabled', sa.Boolean(), default=True,
                 comment='Enable auto-deviation detection for tolerance >±4%'))
    op.add_column('jobs', sa.Column('tolerance_limits', sa.JSON(), 
                 comment='Job-specific tolerance limits'))
    op.add_column('jobs', sa.Column('calculation_method_config', sa.JSON(), 
                 comment='Configuration for calculation method'))
    print("   Enhanced jobs table")

def downgrade():
    """Remove enhanced calculation engine tables"""
    print("🗑️  Removing enhanced calculation engine schema...")
    
    op.drop_table('notification_log')
    op.drop_table('notification_templates')
    op.drop_table('job_calculation_results')
    op.drop_table('calculation_formula_templates')
    op.drop_table('calculation_constants')
    op.drop_table('formula_lookup_tables')
    
    # Remove added columns from existing tables
    op.drop_column('jobs', 'calculation_method_config')
    op.drop_column('jobs', 'tolerance_limits')
    op.drop_column('jobs', 'auto_deviation_enabled')
    op.drop_column('jobs', 'calculation_engine_version')
    
    op.drop_column('standards', 'calibration_curve')
    op.drop_column('standards', 'pressure_gauge_data')
    op.drop_column('standards', 'uncertainty_coefficients')
    op.drop_column('standards', 'interpolation_points')
    op.drop_column('standards', 'formula_data')
    
    print(" Removed enhanced calculation engine schema")
