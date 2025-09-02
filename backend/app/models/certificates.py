from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, JSON, Boolean, LargeBinary
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, AuditMixin
import enum

class CertificateStatus(str, enum.Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    ISSUED = "issued"
    DELIVERED = "delivered"
    REVOKED = "revoked"

class CertificateType(str, enum.Enum):
    CRT1 = "crt1"  # Page 1 - Header and standards info
    CRT2 = "crt2"  # Page 2 - Measurement results
    CRT3 = "crt3"  # Page 3 - Uncertainties and conclusions

class Certificate(Base, TimestampMixin, AuditMixin):
    __tablename__ = "certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    
    # Certificate Identification
    certificate_number = Column(String(255), unique=True, nullable=False)  # e.g., "NEPL / C / 2025 / 98-9"
    ulr_number = Column(String(255))                                       # e.g., "CC446625000000XYZ"
    revision_number = Column(Integer, default=0)
    
    # Certificate Details
    certificate_type = Column(String(20))                                  # From CertificateType enum
    issue_date = Column(Date, nullable=False)
    calibration_date = Column(Date, nullable=False)
    recommended_due_date = Column(Date)                                     # Next calibration due
    
    # Certificate Content
    template_used = Column(String(255))                                     # Template version/name
    certificate_data = Column(JSON)                                         # All certificate data
    pdf_content = Column(LargeBinary)                                       # Generated PDF
    
    # Security Features
    password_protected = Column(Boolean, default=False)
    password_hash = Column(String(255))                                     # If password protected
    digital_signature = Column(Text)                                        # Digital signature if required
    watermark_applied = Column(Boolean, default=False)
    
    # Status and Approval
    status = Column(String(50), default=CertificateStatus.DRAFT)
    reviewed_by = Column(String(255))                                       # Calibration Engineer
    approved_by = Column(String(255))                                       # Authorized Signatory
    
    # Delivery Tracking
    delivery_method = Column(String(100))                                   # email, portal, courier
    delivered_at = Column(Date)
    delivery_confirmation = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    
    # Relationships
    job = relationship("Job", back_populates="certificates")
