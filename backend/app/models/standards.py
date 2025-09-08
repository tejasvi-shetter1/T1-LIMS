from sqlalchemy import Column, Integer, String, Text, Date, Boolean, ForeignKey, Float
from sqlalchemy.types import DECIMAL as Decimal
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin


class Standard(Base, TimestampMixin):
    __tablename__ = "standards"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # From Standards sheet analysis
    nomenclature = Column(String(500), nullable=False)  # e.g., "TORQUE TRANSDUCER ( 1000 - 40000 Nm)"
    manufacturer = Column(String(255))                   # e.g., "NORBAR, UK"
    model_serial_no = Column(String(255))               # e.g., "50781.LOG / 201062 / 148577"
    
    # Uncertainty and Accuracy
    uncertainty = Column(Decimal(15, 10), nullable=False)  # e.g., 0.0016
    accuracy = Column(String(100))                          # e.g., "0.005"
    resolution = Column(Decimal(15, 10))                   # e.g., 1
    unit = Column(String(50))                               # e.g., "Nm"
    
    # Measurement Range
    range_min = Column(Decimal(15, 4))                     # e.g., 1000
    range_max = Column(Decimal(15, 4))                     # e.g., 40000
    
    # NEW: Equipment Category Association for Dynamic Logic
    equipment_category_id = Column(Integer, ForeignKey("equipment_categories.id"))
    applicable_range_min = Column(Float)
    applicable_range_max = Column(Float)
    discipline = Column(String(50))  # "Torque", "Pressure", "Electrical"
    
    # Traceability Information
    certificate_no = Column(String(255))                   # e.g., "SCPL/CC/3685/03/2023-2024"
    calibration_valid_upto = Column(Date, nullable=False)  # e.g., "2026-03-13"
    traceable_to_lab = Column(Text)                        # e.g., "Traceable to NABL Accredited Lab No. CC 2874"
    
    # Status
    is_active = Column(Boolean, default=True)
    is_expired = Column(Boolean, default=False)  # Auto-calculated
    
    # Relationships
    job_standards = relationship("JobStandard", back_populates="standard")
    
    # NEW: Equipment Dynamic Selection Rules Relationship
    selection_rules = relationship("StandardsSelectionRule", back_populates="standard")


class JobStandard(Base, TimestampMixin):
    __tablename__ = "job_standards"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    standard_id = Column(Integer, ForeignKey("standards.id"), nullable=False)
    
    # Standard Usage
    standard_sequence = Column(Integer, nullable=False)  # 1, 2, 3 (Standard-1, Standard-2, etc.)
    is_primary = Column(Boolean, default=False)
    usage_notes = Column(Text)
    
    # Relationships
    job = relationship("Job", back_populates="standards")
    standard = relationship("Standard", back_populates="job_standards")
