"""
Order management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.order import Order, OrderType, OrderStatus
from services.matching_engine import MatchingEngine

router = APIRouter()

# Request/Response schemas
class CreateOrderRequest(BaseModel):
    order_type: str  # "buy" or "sell"
    quantity_af: float
    price_per_af: float

class OrderResponse(BaseModel):
    id: int
    order_type: str
    quantity_af: float
    filled_quantity_af: float
    price_per_af: float
    basin: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int

@router.post("/", response_model=OrderResponse)
async def create_order(
    request: CreateOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new buy or sell order"""
    
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate order type
    try:
        order_type = OrderType(request.order_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid order type. Must be 'buy' or 'sell'"
        )
    
    # Validate sell order has sufficient balance
    if order_type == OrderType.SELL:
        if request.quantity_af > user.water_balance_af:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient water balance. You have {user.water_balance_af} AF available."
            )
    
    # Validate positive values
    if request.quantity_af <= 0 or request.price_per_af <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity and price must be positive"
        )
    
    # Create order
    order = Order(
        user_id=user.id,
        order_type=order_type,
        quantity_af=request.quantity_af,
        price_per_af=request.price_per_af,
        basin=user.basin,
        status=OrderStatus.OPEN
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Run matching engine
    matching_engine = MatchingEngine(db)
    matches = matching_engine.match_orders()
    
    # Refresh order to get updated status
    db.refresh(order)
    
    return OrderResponse(
        id=order.id,
        order_type=order.order_type.value,
        quantity_af=order.quantity_af,
        filled_quantity_af=order.filled_quantity_af,
        price_per_af=order.price_per_af,
        basin=order.basin,
        status=order.status.value,
        created_at=order.created_at
    )

@router.get("/", response_model=OrderListResponse)
async def list_orders(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's orders"""
    
    query = db.query(Order).filter(Order.user_id == current_user["user_id"])
    
    if status_filter:
        try:
            status_enum = OrderStatus(status_filter.lower())
            query = query.filter(Order.status == status_enum)
        except ValueError:
            pass
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    return OrderListResponse(
        orders=[
            OrderResponse(
                id=o.id,
                order_type=o.order_type.value,
                quantity_af=o.quantity_af,
                filled_quantity_af=o.filled_quantity_af,
                price_per_af=o.price_per_af,
                basin=o.basin,
                status=o.status.value,
                created_at=o.created_at
            ) for o in orders
        ],
        total=len(orders)
    )

@router.delete("/{order_id}")
async def cancel_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel an open order"""
    
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user["user_id"]
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status not in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel order with status: " + order.status.value
        )
    
    order.status = OrderStatus.CANCELLED
    db.commit()
    
    return {"message": "Order cancelled successfully", "order_id": order_id}
