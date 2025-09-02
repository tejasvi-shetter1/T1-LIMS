from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, JSON, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, AuditMixin
import enum

class DeviationStatus(str, enum.Enum):
    IDENTIFIED = "identified"              # Auto-detected deviation
    UNDER_REVIEW = "under_review"         # QA/Lab Manager reviewing
    CLIENT_NOTIFIED = "client_notified"   # Customer notification sent
    AWAITING_DECISION = "awaiting_decision"  # Waiting for customer decision
    ACCEPTED = "accepted"                 # Customer accepted deviation
    REJECTED = "rejected"                 # Customer rejected - rework needed
    CLOSED = "closed"                     # Deviation resolved

class ClientDecision(str, enum.Enum):
    PROCEED = "proceed"                   # Accept as-is
    REWORK = "rework"                     # Re-calibrate
    SCRAP = "scrap"                       # Item unusable
    OOT_ACCEPTANCE = "oot_acceptance"     # Out-of-tolerance acceptance

class DeviationReport(Base, TimestampMixin, AuditMixin):
    __tablename__ = "deviation_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    
    # Deviation Identification
    deviation_number = Column(String(100), unique=True, nullable=False)  # Auto-generated
    deviation_type = Column(String(100))                                 # "measurement_out_of_tolerance", "equipment_damage"
    severity = Column(String(50), default="medium")                      # low, medium, high, critical
    
    # Deviation Details
    description = Column(Text, nullable=False)
    root_cause_analysis = Column(Text)
    affected_measurements = Column(JSON)                                 # Which measurements are affected
    
    # Impact Assessment
    technical_impact = Column(Text)
    customer_impact = Column(Text)
    recommendations = Column(Text)
    
    # Workflow Status
    status = Column(String(50), default=DeviationStatus.IDENTIFIED)
    identified_by = Column(String(255))
    reviewed_by = Column(String(255))                                    # QA Manager
    approved_by = Column(String(255))                                    # Lab Manager
    
    # Client Communication
    client_notified_at = Column(DateTime)
    client_notification_method = Column(String(100))                    # email, portal, phone
    client_decision = Column(String(50))                                # From ClientDecision enum
    client_decision_date = Column(DateTime)
    client_comments = Column(Text)
    
    # Resolution
    resolution_actions = Column(Text)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(255))
    
    # Relationships
    job = relationship("Job", back_populates="deviations")
