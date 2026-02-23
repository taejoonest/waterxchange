"""
User model for farmer accounts
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Farmer profile
    full_name = Column(String, nullable=False)
    farm_name = Column(String)
    basin = Column(String, nullable=False)  # e.g., "Kern County", "San Joaquin Valley"
    gsa = Column(String)  # Groundwater Sustainability Agency
    
    # Water allocation
    water_balance_af = Column(Float, default=0.0)  # Acre-feet
    annual_allocation_af = Column(Float, default=0.0)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
