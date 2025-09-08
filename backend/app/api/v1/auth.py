from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import AuthService
from app.models.users import UserRole, UserType
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
security = HTTPBearer()

class LoginRequest(BaseModel):
    username: str
    password: str
    user_type: UserType  # "staff" or "customer" selection

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: UserRole
    user_type: UserType
    customer_id: Optional[int] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_info: dict

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Unified login for both staff and customers"""
    
    user = AuthService.authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify user type matches request
    if user.user_type != login_data.user_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user type for this portal"
        )
    
    # Create access token
    access_token = AuthService.create_access_token(user)
    
    # Return user info
    user_info = {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value,
        "user_type": user.user_type.value,
        "customer_id": user.customer_id,
        "customer_name": user.customer.name if user.customer else None
    }
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_info=user_info
    )

@router.post("/register")
async def register(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register new user"""
    
    try:
        user = AuthService.create_user(
            db=db,
            username=register_data.username,
            email=register_data.email,
            password=register_data.password,
            full_name=register_data.full_name,
            role=register_data.role,
            user_type=register_data.user_type,
            customer_id=register_data.customer_id
        )
        
        return {"message": "User registered successfully", "user_id": user.id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Dependency to get current user from token"""
    
    user = AuthService.get_current_user(db, credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return user
