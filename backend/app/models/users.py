from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin
import enum

class UserRole(str, enum.Enum):
    # NEPL Staff Roles
    ADMIN = "admin"
    LAB_MANAGER = "lab_manager"
    TECHNICIAN = "technician"
    QA_MANAGER = "qa_manager"
    DISPATCH = "dispatch"
    
    # Customer Roles
    CUSTOMER_ADMIN = "customer_admin"
    CUSTOMER_USER = "customer_user"

class UserType(str, enum.Enum):
    STAFF = "staff"
    CUSTOMER = "customer"

class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    # Role and Type
    role = Column(SQLEnum(UserRole), nullable=False)
    user_type = Column(SQLEnum(UserType), nullable=False)
    
    # Customer Association (only for customer users)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    
    # Relationships
    customer = relationship("Customer", back_populates="users")
    #notifications = relationship("Notification", back_populates="recipient_user")
