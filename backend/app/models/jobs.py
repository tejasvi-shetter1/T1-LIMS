from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, JSON, Boolean, DateTime
from sqlalchemy.types import DECIMAL as Decimal
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, AuditMixin
import enum
from app.models.calculations import JobCalculationResult

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    MEASUREMENTS_COMPLETE = "measurements_complete"
    CALCULATIONS_COMPLETE = "calculations_complete"
    UNDER_REVIEW = "under_review"
    DEVIATION_PENDING = "deviation_pending"
    APPROVED = "approved"
    CERTIFICATE_GENERATED = "certificate_generated"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"

class Job(Base, TimestampMixin, AuditMixin):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    inward_id = Column(Integer, ForeignKey("inward.id"), nullable=False)
    
    # NEW: Equipment Type Association for Dynamic Logic
    equipment_type_id = Column(Integer, ForeignKey("equipment_types.id"))
    
    # Job Identification
    job_number = Column(String(100), unique=True, nullable=False)  # Auto-generated: JOB-25001, JOB-25002
    nepl_work_id = Column(String(100))                             # Links to Raw Data sheet
    
    # Calibration Planning (from BRD requirements)
    calibration_type = Column(String(100))                        # "Torque", "Pressure", "Dimension"
    calibration_method = Column(String(255))                      # "ISO 6789-1 & 2:2017", "DKD-R-6-1"
    calibration_procedure = Column(String(255))                   # "NEPL Ref: CP .No 02"
    measurement_points = Column(JSON, default=[])                 # ["20%", "60%", "100%"] 
    
    # Calibration Schedule
    planned_start_date = Column(Date)
    planned_completion_date = Column(Date)
    actual_start_date = Column(Date)
    actual_completion_date = Column(Date)
    
    # Environmental Conditions (from Raw Data sheet analysis)
    temp_before = Column(Decimal(5, 2))                          # 23.4°C (tamb before)
    temp_after = Column(Decimal(5, 2))                           # 23.6°C (tamb after)
    humidity_before = Column(Decimal(5, 4))                      # 0.605 (RH before)
    humidity_after = Column(Decimal(5, 4))                       # 0.606 (RH after)
    
    # Environmental Validation
    environmental_conditions_acceptable = Column(Boolean, default=True)
    environmental_notes = Column(Text)
    
    # Status Tracking (from Inward Register analysis)
    status = Column(String(50), default=JobStatus.PENDING.value)  # Maps to CALIBRATION STATUS
    calibration_date = Column(Date)                              # CALIBRATION DATE
    due_date = Column(Date)                                      # Service level agreement
    
    # Technical Assignment
    assigned_technician = Column(String(255))                   # Senior/Junior Technician
    reviewed_by = Column(String(255))                           # Lab Manager/QA Manager
    approved_by = Column(String(255))                           # Quality Manager
    
    # Certificate Information (from Excel: CERTIFICATE STATUS, INVOICE NO)
    certificate_status = Column(String(100), default='pending') # Maps to CERTIFICATE STATUS
    certificate_number = Column(String(255))                    # Auto-generated cert number
    invoice_no = Column(String(255))                            # INVOICE NO
    
    # Job Results Summary
    overall_result = Column(String(50))                         # "pass", "fail", "conditional"
    
    # Deviation Control Fields (Updated for deviation management)
    deviation_required = Column(Boolean, default=False)         # Auto-determined from measurements
    deviation_approved = Column(Boolean, default=False)         # Customer approval for deviation
    deviation_resolved = Column(Boolean, nullable=False, default=False)  # All deviations resolved
    can_generate_certificate = Column(Boolean, nullable=False, default=True)  # Certificate generation control
    
    # Priority and Special Instructions (from SRF)
    priority = Column(String(50), default='normal')             # normal, urgent, critical
    special_instructions = Column(Text)                         # From SRF special instructions
    customer_requirements = Column(JSON)                        # Conformity statement, decision rules
    
    # Measurement Configuration
    measurement_template_id = Column(Integer, ForeignKey("measurement_templates.id"))
    measurement_plan = Column(JSON)                             # Planned measurements
    
    # Relationships
    inward = relationship("Inward", back_populates="job")
    measurements = relationship("Measurement", back_populates="job")
    uncertainty_budgets = relationship("UncertaintyCalculation", back_populates="job", uselist=False)
    standards = relationship("JobStandard", back_populates="job")
    deviations = relationship("DeviationReport", back_populates="job")
    certificates = relationship("Certificate", back_populates="job")
    
    # NEW: Equipment Type Relationship for Dynamic Logic
    equipment_type = relationship("EquipmentType", back_populates="jobs")
        # NEW: Calculation Engine Fields
    calculation_engine_version = Column(String(10), default="1.0")
    auto_deviation_enabled = Column(Boolean, default=True)
    calculation_status = Column(String(50), default="pending")
    calculation_started_at = Column(DateTime(timezone=True))
    calculation_completed_at = Column(DateTime(timezone=True))
    calculation_error = Column(Text)
    tolerance_limits = Column(JSON)
    calculation_config = Column(JSON)
    
    # NEW: Relationships
    calculation_results = relationship("JobCalculationResult", back_populates="job", cascade="all, delete-orphan")
