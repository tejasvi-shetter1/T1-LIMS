from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin

class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    recipient_user_id = Column(Integer, ForeignKey("users.id"))
    recipient_email = Column(String(255))
    
    # Related entities
    deviation_id = Column(Integer, ForeignKey("deviation_reports.id"))
    srf_id = Column(Integer, ForeignKey("srf.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    
    # Status
    is_read = Column(Boolean, nullable=False, default=False)
    is_email_sent = Column(Boolean, nullable=False, default=False)
    email_sent_at = Column(DateTime)
    
    # Relationships
    deviation = relationship("DeviationReport")
    srf = relationship("SRF") 
    job = relationship("Job")
    recipient_user = relationship("User")