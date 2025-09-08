from sqlalchemy.orm import Session
from app.models.users import User, UserRole, UserType
from app.models.customers import Customer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-secret-key"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

class AuthService:
    
    @staticmethod
    def create_user(
        db: Session,
        username: str,
        email: str,
        password: str,
        full_name: str,
        role: UserRole,
        user_type: UserType,
        customer_id: Optional[int] = None
    ) -> User:
        """Create new user for unified portal"""
        
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            raise ValueError("Username or email already exists")
        
        # Validate customer association for customer users
        if user_type == UserType.CUSTOMER and not customer_id:
            raise ValueError("Customer users must be associated with a customer")
        
        if customer_id:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise ValueError("Customer not found")
        
        # Create user
        hashed_password = pwd_context.hash(password)
        
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            full_name=full_name,
            role=role,
            user_type=user_type,
            customer_id=customer_id,
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User created: {username} ({role.value})")
        return user
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user for login"""
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not user.is_active:
            return None
        
        if not pwd_context.verify(password, user.password_hash):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    @staticmethod
    def create_access_token(user: User) -> str:
        """Create JWT token for authenticated user"""
        
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value,
            "user_type": user.user_type.value,
            "customer_id": user.customer_id,
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        
        return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[User]:
        """Get current user from token"""
        payload = AuthService.verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return db.query(User).filter(User.id == int(user_id)).first()
