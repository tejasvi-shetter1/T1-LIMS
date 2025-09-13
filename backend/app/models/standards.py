# app/models/standards.py (ADD THIS MODEL)
from sqlalchemy import Column, Integer, String, Text, Date, Boolean, ForeignKey, Float, JSON
from sqlalchemy.types import DECIMAL as Decimal
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin
from datetime import date

class Standard(Base, TimestampMixin):
    __tablename__ = "standards"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    nomenclature = Column(String(500), nullable=False)
    manufacturer = Column(String(255))
    model_serial_no = Column(String(255))
    uncertainty = Column(Decimal(15, 10), nullable=False)
    accuracy = Column(String(100))
    resolution = Column(Decimal(15, 10))
    unit = Column(String(50))
    range_min = Column(Decimal(15, 4))
    range_max = Column(Decimal(15, 4))
    
    # Enhanced fields for dynamic selection
    equipment_category_id = Column(Integer, ForeignKey("equipment_categories.id"))
    applicable_range_min = Column(Float)
    applicable_range_max = Column(Float)
    discipline = Column(String(50))  # "Torque", "Pressure", etc.
    
    # Traceability
    certificate_no = Column(String(255))
    calibration_valid_upto = Column(Date, nullable=False)
    traceable_to_lab = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_expired = Column(Boolean, default=False)
    
    # Relationships
    job_standards = relationship("JobStandard", back_populates="standard")
    selection_rules = relationship("StandardsSelectionRule", back_populates="standard")
    certificate_data = relationship("StandardsCertificateData", back_populates="standard", cascade="all, delete-orphan")

# ADD THIS MISSING MODEL
class StandardsSelectionRule(Base, TimestampMixin):
    __tablename__ = "standards_selection_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_type_id = Column(Integer, ForeignKey("equipment_types.id"))
    standard_id = Column(Integer, ForeignKey("standards.id"))
    
    # Selection criteria
    priority = Column(Integer, default=1)
    range_min = Column(Float)
    range_max = Column(Float)
    is_active = Column(Boolean, default=True)
    rule_name = Column(String(255))
    
    # Relationships
    equipment_type = relationship("EquipmentType", back_populates="standards_rules")
    standard = relationship("Standard", back_populates="selection_rules")

class JobStandard(Base, TimestampMixin):
    __tablename__ = "job_standards"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    standard_id = Column(Integer, ForeignKey("standards.id"), nullable=False)
    
    # Usage details
    standard_sequence = Column(Integer, nullable=False)
    is_primary = Column(Boolean, default=False)
    usage_notes = Column(Text)
    selection_reason = Column(Text)
    
    # Enhanced auto-selection fields
    auto_selected = Column(Boolean, default=True)
    selection_timestamp = Column(Date, default=date.today)
    interpolation_data = Column(JSON)
    
    # Relationships
    job = relationship("Job", back_populates="standards")
    standard = relationship("Standard", back_populates="job_standards")
