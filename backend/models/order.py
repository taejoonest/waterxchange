"""
Order model for buy/sell water orders
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from core.database import Base

class OrderType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, enum.Enum):
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Order details
    order_type = Column(Enum(OrderType), nullable=False)
    quantity_af = Column(Float, nullable=False)  # Acre-feet
    filled_quantity_af = Column(Float, default=0.0)
    price_per_af = Column(Float, nullable=False)  # USD per acre-foot
    
    # Location/basin for matching
    basin = Column(String, nullable=False)
    
    # Status
    status = Column(Enum(OrderStatus), default=OrderStatus.OPEN)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    filled_at = Column(DateTime(timezone=True))
    
    @property
    def remaining_quantity(self) -> float:
        return self.quantity_af - self.filled_quantity_af
