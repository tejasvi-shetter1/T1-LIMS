# app/models/calculations.py
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON, DateTime, Date, Numeric
from sqlalchemy.types import DECIMAL as Decimal
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin
import enum
from datetime import datetime


class CalculationStage(int, enum.Enum):
    NEW_RD = 1
    UN_RESOLUTION = 2 
    UNCERTAINTY_BUDGET = 3


class CalculationStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    STAGE1_COMPLETE = "stage1_complete"
    STAGE2_COMPLETE = "stage2_complete" 
    STAGE3_COMPLETE = "stage3_complete"
    COMPLETED = "completed"
    COMPLETED_WITH_DEVIATIONS = "completed_with_deviations"
    FAILED = "failed"


class ValidationStatus(str, enum.Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


class FormulaLookupTable(Base, TimestampMixin):
    """
    Lookup tables for Excel-equivalent formulas and interpolation
    Stores data like INTERPOLATION tables, Master Transducer Uncertainty, etc.
    """
    __tablename__ = "formula_lookup_tables"
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(100), nullable=False)
    equipment_type_id = Column(Integer, ForeignKey("equipment_types.id"))
    lookup_type = Column(String(50), nullable=False)  # "interpolation", "uncertainty", "cmc"
    category = Column(String(50), nullable=False)  # "torque_transducer", "pressure_gauge"
    range_column = Column(String(50))  # Column used for range matching
    data_structure = Column(JSON, nullable=False)  # Structure definition
    lookup_data = Column(JSON, nullable=False)  # Actual lookup data
    validity_period = Column(String(100))  # Certificate validity info
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    equipment_type = relationship("EquipmentType", back_populates="formula_lookups")


class CalculationMethod(Base, TimestampMixin):
    """
    Defines calculation methods for each stage and equipment type
    Maps to Excel calculation sequences
    """
    __tablename__ = "calculation_methods"
    
    id = Column(Integer, primary_key=True, index=True)
    method_name = Column(String(100), nullable=False)
    equipment_type_id = Column(Integer, ForeignKey("equipment_types.id"))
    calculation_stage = Column(Integer, nullable=False)  # 1=New RD, 2=UN_Resolution, 3=Uncertainty
    calculation_order = Column(Integer, nullable=False)  # Order within stage
    calculation_type = Column(String(50), nullable=False)  # "repeatability", "reproducibility", etc.
    formula_expression = Column(Text, nullable=False)  # Actual formula
    input_requirements = Column(JSON, nullable=False)  # Required input fields
    output_fields = Column(JSON, nullable=False)  # Expected output fields
    validation_rules = Column(JSON)  # Validation criteria
    tolerance_limits = Column(JSON)  # Acceptable limits
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships  
    equipment_type = relationship("EquipmentType", back_populates="calculation_methods")


class JobCalculationResult(Base, TimestampMixin):
    """
    Stores results from each calculation stage for audit and tracking
    """
    __tablename__ = "job_calculation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    calculation_stage = Column(Integer, nullable=False)
    calculation_type = Column(String(50), nullable=False)
    calculation_order = Column(Integer, default=0)
    
    # Input/Output Data
    input_data = Column(JSON, nullable=False)
    measurement_readings = Column(JSON)
    calculated_values = Column(JSON, nullable=False)
    intermediate_steps = Column(JSON)
    
    # References Used
    formulas_used = Column(JSON)
    constants_used = Column(JSON)
    lookup_tables_used = Column(JSON)
    standards_referenced = Column(JSON)
    
    # Validation Results
    validation_status = Column(String(20), nullable=False, default="pending")
    validation_details = Column(JSON)
    error_details = Column(Text)
    
    # Deviation Detection
    exceeds_tolerance = Column(Boolean, nullable=False, default=False)
    tolerance_value = Column(Numeric(10, 6))
    deviation_percentage = Column(Numeric(10, 6))
    auto_deviation_triggered = Column(Boolean, nullable=False, default=False)
    
    # Audit Information
    calculated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    calculated_by = Column(String(255))
    calculation_engine_version = Column(String(10), nullable=False, default="1.0")
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="calculation_results")


class StandardsCertificateData(Base, TimestampMixin):
    """
    Stores detailed certificate data for standards used in calculations
    Maps to Excel certificate validity tables
    """
    __tablename__ = "standards_certificate_data"
    
    id = Column(Integer, primary_key=True, index=True)
    standard_id = Column(Integer, ForeignKey("standards.id"), nullable=False)
    certificate_validity_start = Column(Date)
    certificate_validity_end = Column(Date, nullable=False)
    calibration_points = Column(JSON, nullable=False)  # Applied/Indicated/Error data
    certificate_reference = Column(String(255))
    traceability_chain = Column(Text)
    measurement_conditions = Column(JSON)  # Temp, humidity, etc.
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    standard = relationship("Standard", back_populates="certificate_data")


class CalculationEngineConfig(Base, TimestampMixin):
    """
    Configuration for calculation engine behavior per equipment type
    Defines which methods to use for each stage
    """
    __tablename__ = "calculation_engine_config"
    
    id = Column(Integer, primary_key=True, index=True)
    config_name = Column(String(100), nullable=False, unique=True)
    equipment_type = Column(String(50))  # "torque", "pressure", etc.
    
    # Stage Configurations
    stage1_methods = Column(JSON)  # New RD methods config
    stage2_methods = Column(JSON)  # UN_Resolution methods config  
    stage3_methods = Column(JSON)  # Uncertainty budget methods config
    
    # Automation Settings
    auto_deviation_enabled = Column(Boolean, nullable=False, default=True)
    tolerance_config = Column(JSON)  # Tolerance limits per calculation type
    notification_config = Column(JSON)  # When to notify users
    
    # Calculation Constants
    formula_constants = Column(JSON)  # Constants like coverage factors
    interpolation_tables = Column(JSON)  # Reference to lookup table names
    
    is_active = Column(Boolean, nullable=False, default=True)


class CalculationFormulaTemplate(Base, TimestampMixin):
    """
    Template storage for reusable calculation formulas
    Stores Excel formula expressions with parameter mapping
    """
    __tablename__ = "calculation_formula_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), nullable=False)
    equipment_category_id = Column(Integer, ForeignKey("equipment_categories.id"))
    formula_category = Column(String(50), nullable=False)  # "uncertainty", "deviation", "interpolation"
    
    # Formula Definition
    formula_expression = Column(Text, nullable=False)  # Actual formula
    excel_reference = Column(Text)  # Original Excel formula for reference
    
    # Parameters
    input_parameters = Column(JSON, nullable=False)  # Required input parameters with types
    output_parameters = Column(JSON, nullable=False)  # Output parameters with types
    constants_required = Column(JSON)  # Required calculation constants
    lookup_tables_required = Column(JSON)  # Required lookup tables
    
    # Validation
    validation_rules = Column(JSON)  # Validation rules for inputs/outputs
    tolerance_limits = Column(JSON)  # Tolerance limits for deviation detection
    deviation_thresholds = Column(JSON)  # Thresholds for auto-deviation triggers
    
    # Documentation
    calculation_steps = Column(JSON)  # Step-by-step calculation documentation
    example_data = Column(JSON)  # Example input/output for testing
    
    # Metadata
    version = Column(String(10), default="1.0")
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    equipment_category = relationship("EquipmentCategory", back_populates="formula_templates")
    

# Update existing models to add the missing relationships
# These would be added to existing model files:

# In app/models/equipment.py - add to EquipmentType class:
# formula_lookups = relationship("FormulaLookupTable", back_populates="equipment_type")
# calculation_methods = relationship("CalculationMethod", back_populates="equipment_type")

# In app/models/equipment.py - add to EquipmentCategory class:  
# formula_templates = relationship("CalculationFormulaTemplate", back_populates="equipment_category")

# In app/models/jobs.py - add to Job class:
# calculation_results = relationship("JobCalculationResult", back_populates="job", cascade="all, delete-orphan")

# In app/models/standards.py - add to Standard class:
# certificate_data = relationship("StandardsCertificateData", back_populates="standard", cascade="all, delete-orphan")
