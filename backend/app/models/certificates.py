from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, LargeBinary, Date, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, AuditMixin
import enum
from datetime import datetime

class CertificateStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    APPROVED = "approved"
    DELIVERED = "delivered"

class CertificateType(str, enum.Enum):
    CRT1 = "Crt1"
    CRT2 = "Crt2"
    CRT3 = "Crt3"

class GenerationStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class CertificateTemplate(Base, TimestampMixin, AuditMixin):
    __tablename__ = "certificate_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), nullable=False)
    template_type = Column(String(20), nullable=False)  # Crt1, Crt2, Crt3
    equipment_types = Column(JSON)  # List of applicable equipment types
    template_path = Column(String(255), nullable=False)
    template_content = Column(Text)  # HTML template content
    is_active = Column(Boolean, default=True)
    version = Column(String(10), default="1.0")
    
    # Relationships
    certificates = relationship("Certificate", back_populates="template")

class Certificate(Base, TimestampMixin, AuditMixin):
    __tablename__ = "certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("certificate_templates.id"))
    
    # Certificate Identification
    certificate_number = Column(String(255), unique=True, nullable=False)
    ulr_number = Column(String(255))
    revision_number = Column(Integer, default=0)
    certificate_type = Column(String(20))  # Crt1, Crt2, Crt3
    
    # Certificate Dates
    issue_date = Column(Date, nullable=False)
    calibration_date = Column(Date, nullable=False)
    recommended_due_date = Column(Date)
    
    # Generation Workflow
    generation_status = Column(String(50), default="pending")
    generation_started_at = Column(DateTime(timezone=True))
    generation_completed_at = Column(DateTime(timezone=True))
    generation_error = Column(Text)
    
    # Template and Data
    template_used = Column(String(255))
    certificate_data = Column(JSON)  # All data used for generation
    auto_populated_fields = Column(JSON)  # Fields auto-populated from data
    manual_override_fields = Column(JSON)  # Manual overrides
    
    # File Details
    pdf_content = Column(LargeBinary)
    file_size_bytes = Column(Integer)
    file_hash = Column(String(64))
    
    # Security Features
    password_protected = Column(Boolean, default=False)
    password_hash = Column(String(255))
    digital_signature = Column(Text)
    watermark_applied = Column(Boolean, default=True)
    
    # Workflow Status
    status = Column(String(50), default="draft")
    reviewed_by = Column(String(255))
    approved_by = Column(String(255))
    
    # Delivery Tracking
    delivery_method = Column(String(100))
    delivered_at = Column(Date)
    delivery_confirmation = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    
    # Relationships
    job = relationship("Job", back_populates="certificates")
    template = relationship("CertificateTemplate", back_populates="certificates")
