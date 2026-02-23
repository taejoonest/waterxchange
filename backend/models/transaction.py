"""
Transaction model for completed water trades
"""

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.sql import func

from core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Parties
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Orders that created this transaction
    buy_order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    sell_order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Trade details
    quantity_af = Column(Float, nullable=False)
    price_per_af = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    
    # Basin info
    basin = Column(String, nullable=False)
    
    # SGMA compliance
    compliance_verified = Column(String, default="pending")  # pending, approved, flagged
    compliance_notes = Column(String)
    
    # Timestamps
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
