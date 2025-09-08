from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.types import DECIMAL as Decimal
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, AuditMixin
import enum

class InwardStatus(str, enum.Enum):
    RECEIVED = "received"
    INSPECTION_COMPLETE = "inspection_complete"
    READY_FOR_CALIBRATION = "ready_for_calibration"
    IN_CALIBRATION = "in_calibration"
    CALIBRATION_COMPLETE = "calibration_complete"
    READY_FOR_DISPATCH = "ready_for_dispatch"
    DISPATCHED = "dispatched"

class Inward(Base, TimestampMixin, AuditMixin):
    __tablename__ = "inward"
    
    id = Column(Integer, primary_key=True, index=True)
    srf_item_id = Column(Integer, ForeignKey("srf_items.id"), nullable=False)
    
    # NEPL ID Generation (from Inward Register analysis)
    nepl_id = Column(String(100), nullable=False, unique=True)  # Auto-generated: 25001, 25002
    
    # Inward Details (from Excel: DATE, CUSTOMER DC AND DATE, etc.)
    inward_date = Column(Date, nullable=False)
    customer_dc_no = Column(String(255))                        # Customer DC 
    customer_dc_date = Column(Date)
    
    # Physical Condition Assessment
    condition_on_receipt = Column(String(100), default='satisfactory')  # From "Status of item on Receipt"
    visual_inspection_notes = Column(Text)
    damage_remarks = Column(Text)
    photos = Column(JSON, default=[])                           # Store photo file paths
    
    # Tracking Information  
    received_by = Column(String(255))
    supplier = Column(String(255))                              # From Excel SUPPLIER column
    quantity_received = Column(Integer, default=1)
    
    # Status and Workflow
    status = Column(SQLEnum(InwardStatus), default=InwardStatus.RECEIVED)
    barcode = Column(String(255))                               # For barcode/QR generation
    
    # Dispatch tracking (from Excel: OUT DC, IN DC, DISPATCHING DC)
    out_dc = Column(String(255))
    in_dc = Column(String(255))  
    dispatching_dc = Column(String(255))
    dispatching_date = Column(Date)
    courier_details = Column(String(255))
    
    # Relationships
    srf_item = relationship("SRFItem", back_populates="inward")
    job = relationship("Job", back_populates="inward", uselist=False)  # One-to-one relationship