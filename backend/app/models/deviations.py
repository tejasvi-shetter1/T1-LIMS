from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum
from app.database import Base
from app.models.base import TimestampMixin, AuditMixin
import enum
from datetime import datetime

class DeviationType(str, enum.Enum):
    OOT = "OOT"
    DAMAGED = "DAMAGED" 
    MISSING_STANDARD = "MISSING_STANDARD"
    GB_FAILURE = "GB_FAILURE"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    EQUIPMENT_MALFUNCTION = "EQUIPMENT_MALFUNCTION"

class DeviationStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    CUSTOMER_NOTIFIED = "CUSTOMER_NOTIFIED"
    CUSTOMER_ACCEPTED = "CUSTOMER_ACCEPTED"
    CUSTOMER_REJECTED = "CUSTOMER_REJECTED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class DeviationReport(Base, TimestampMixin, AuditMixin):
    __tablename__ = "deviation_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    deviation_number = Column(String(100), unique=True, nullable=False)
    deviation_type = Column(String(100))
    severity = Column(String(50))
    description = Column(Text, nullable=False)
    root_cause_analysis = Column(Text)
    affected_measurements = Column(JSON)
    technical_impact = Column(Text)
    customer_impact = Column(Text)
    recommendations = Column(Text)
    status = Column(String(50))
    
    # Lab Staff Actions
    identified_by = Column(String(255))
    reviewed_by = Column(String(255))
    approved_by = Column(String(255))
    
    # Client Communication
    client_notified_at = Column(DateTime)
    client_notification_method = Column(String(100))
    client_decision = Column(String(50))
    client_decision_date = Column(DateTime)
    client_comments = Column(Text)
    
    # Resolution
    resolution_actions = Column(Text)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(255))
    
    # Relationships
    job = relationship("Job", back_populates="deviations")
    actions = relationship("DeviationAction", back_populates="deviation", cascade="all, delete-orphan")

class DeviationAction(Base, TimestampMixin):
    __tablename__ = "deviation_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    deviation_id = Column(Integer, ForeignKey("deviation_reports.id"), nullable=False)
    action_type = Column(String(50), nullable=False)
    action_by = Column(String(255), nullable=False)
    action_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    comments = Column(Text)
    old_status = Column(String(50))
    new_status = Column(String(50))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Relationships
    deviation = relationship("DeviationReport", back_populates="actions")