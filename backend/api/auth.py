"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from core.database import get_db
from core.security import get_password_hash, verify_password, create_access_token
from models.user import User

router = APIRouter()

# Request/Response schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    farm_name: Optional[str] = None
    basin: str
    gsa: Optional[str] = None
    water_balance_af: float = 100.0  # Default starting balance for demo

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    farm_name: Optional[str]
    basin: str
    gsa: Optional[str]
    water_balance_af: float
    annual_allocation_af: float

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new farmer account"""
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        farm_name=request.farm_name,
        basin=request.basin,
        gsa=request.gsa,
        water_balance_af=request.water_balance_af,
        annual_allocation_af=request.water_balance_af
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate token
    token = create_access_token({"sub": str(user.id), "email": user.email})
    
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "farm_name": user.farm_name,
            "basin": user.basin,
            "water_balance_af": user.water_balance_af
        }
    )

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password"""
    
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Generate token
    token = create_access_token({"sub": str(user.id), "email": user.email})
    
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "farm_name": user.farm_name,
            "basin": user.basin,
            "water_balance_af": user.water_balance_af
        }
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(__import__('core.security', fromlist=['get_current_user']).get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user profile"""
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        farm_name=user.farm_name,
        basin=user.basin,
        gsa=user.gsa,
        water_balance_af=user.water_balance_af,
        annual_allocation_af=user.annual_allocation_af
    )
