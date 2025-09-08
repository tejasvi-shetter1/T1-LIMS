from sqlalchemy import Column, Integer, DateTime, Boolean, String, func
from app.database import Base

class TimestampMixin:
    """Mixin to add timestamp fields to models"""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SoftDeleteMixin:
    """Mixin to add soft delete functionality"""
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))

class AuditMixin:
    """Mixin to add audit fields"""
    created_by = Column(String(255))
    updated_by = Column(String(255))