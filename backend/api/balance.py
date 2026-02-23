"""
Balance API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.transaction import Transaction

router = APIRouter()

class BalanceResponse(BaseModel):
    water_balance_af: float
    annual_allocation_af: float
    used_this_year_af: float
    available_to_sell_af: float
    basin: str

class TransactionHistoryItem(BaseModel):
    id: int
    type: str  # "bought" or "sold"
    quantity_af: float
    price_per_af: float
    total_value: float
    counterparty_basin: str
    executed_at: datetime

class TransactionHistoryResponse(BaseModel):
    transactions: List[TransactionHistoryItem]
    total_bought_af: float
    total_sold_af: float
    net_flow_af: float

@router.get("/", response_model=BalanceResponse)
async def get_balance(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's water balance"""
    
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    
    if not user:
        return BalanceResponse(
            water_balance_af=0,
            annual_allocation_af=0,
            used_this_year_af=0,
            available_to_sell_af=0,
            basin="Unknown"
        )
    
    # Calculate used this year (sold - bought)
    from datetime import datetime
    year_start = datetime(datetime.now().year, 1, 1)
    
    sold = db.query(Transaction).filter(
        Transaction.seller_id == user.id,
        Transaction.executed_at >= year_start
    ).all()
    
    bought = db.query(Transaction).filter(
        Transaction.buyer_id == user.id,
        Transaction.executed_at >= year_start
    ).all()
    
    total_sold = sum(t.quantity_af for t in sold)
    total_bought = sum(t.quantity_af for t in bought)
    used_this_year = total_sold - total_bought
    
    return BalanceResponse(
        water_balance_af=user.water_balance_af,
        annual_allocation_af=user.annual_allocation_af,
        used_this_year_af=max(0, used_this_year),
        available_to_sell_af=user.water_balance_af,
        basin=user.basin
    )

@router.get("/history", response_model=TransactionHistoryResponse)
async def get_transaction_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's transaction history"""
    
    user_id = current_user["user_id"]
    
    # Get all transactions where user is buyer or seller
    transactions = db.query(Transaction).filter(
        (Transaction.buyer_id == user_id) | (Transaction.seller_id == user_id)
    ).order_by(Transaction.executed_at.desc()).limit(50).all()
    
    history = []
    total_bought = 0.0
    total_sold = 0.0
    
    for t in transactions:
        is_buyer = t.buyer_id == user_id
        
        history.append(TransactionHistoryItem(
            id=t.id,
            type="bought" if is_buyer else "sold",
            quantity_af=t.quantity_af,
            price_per_af=t.price_per_af,
            total_value=t.total_value,
            counterparty_basin=t.basin,
            executed_at=t.executed_at
        ))
        
        if is_buyer:
            total_bought += t.quantity_af
        else:
            total_sold += t.quantity_af
    
    return TransactionHistoryResponse(
        transactions=history,
        total_bought_af=total_bought,
        total_sold_af=total_sold,
        net_flow_af=total_bought - total_sold
    )
