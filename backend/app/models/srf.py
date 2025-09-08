from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, AuditMixin
import enum

class SRFStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"  
    ACCEPTED = "accepted"
    INWARD_COMPLETED = "inward_completed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class SRF(Base, TimestampMixin, AuditMixin):
    __tablename__ = "srf"
    
    id = Column(Integer, primary_key=True, index=True)
    srf_no = Column(String(100), nullable=False, unique=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    contact_person = Column(String(255))
    date_received = Column(Date, nullable=False)
    status = Column(SQLEnum(SRFStatus), default=SRFStatus.SUBMITTED)
    priority = Column(String(50), default='normal')  # normal, urgent, critical
    special_instructions = Column(Text)
    nextage_contract_reference = Column(String(255))
    calibration_frequency = Column(String(100), default='as_per_standard')
    
    # Relationships
    customer = relationship("Customer", back_populates="srfs")
    items = relationship("SRFItem", back_populates="srf", cascade="all, delete-orphan")

class SRFItem(Base, TimestampMixin):
    __tablename__ = "srf_items"
    
    id = Column(Integer, primary_key=True, index=True)
    srf_id = Column(Integer, ForeignKey("srf.id"), nullable=False)
    sl_no = Column(Integer, nullable=False)
    
    # Equipment Details (from SRF Excel analysis)
    equip_desc = Column(String(500), nullable=False)  # Instrument Nomenclature
    make = Column(String(255))                        # Model
    model = Column(String(255))   
    serial_no = Column(String(255))                   # Serial No/ID
    range_text = Column(String(255))                  # Range
    unit = Column(String(50))                         # Unit of Measurement
    calibration_points = Column(String(255))          # No. of calibration points
    calibration_mode = Column(String(255))            # Mode of calibration
    quantity = Column(Integer, default=1)
    remarks = Column(Text)
    
    # Relationships
    srf = relationship("SRF", back_populates="items")
    inward = relationship("Inward", back_populates="srf_item", uselist=False)