"""
Market data API endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional

from core.database import get_db
from models.order import Order, OrderType, OrderStatus
from models.transaction import Transaction

router = APIRouter()

class OrderBookEntry(BaseModel):
    price_per_af: float
    total_quantity_af: float
    order_count: int

class OrderBookResponse(BaseModel):
    bids: List[OrderBookEntry]  # Buy orders (sorted high to low)
    asks: List[OrderBookEntry]  # Sell orders (sorted low to high)
    spread: Optional[float]
    basin: str

class MarketPriceResponse(BaseModel):
    basin: str
    last_price: Optional[float]
    avg_price_24h: Optional[float]
    high_24h: Optional[float]
    low_24h: Optional[float]
    volume_24h: float
    best_bid: Optional[float]
    best_ask: Optional[float]

@router.get("/book", response_model=OrderBookResponse)
async def get_order_book(
    basin: str = Query(default="Kern County", description="Filter by basin"),
    db: Session = Depends(get_db)
):
    """Get the current order book for a basin"""
    
    # Get aggregated bids (buy orders) - grouped by price
    bids_query = db.query(
        Order.price_per_af,
        func.sum(Order.quantity_af - Order.filled_quantity_af).label('total_qty'),
        func.count(Order.id).label('count')
    ).filter(
        Order.order_type == OrderType.BUY,
        Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]),
        Order.basin == basin
    ).group_by(Order.price_per_af).order_by(Order.price_per_af.desc()).limit(10).all()
    
    # Get aggregated asks (sell orders) - grouped by price
    asks_query = db.query(
        Order.price_per_af,
        func.sum(Order.quantity_af - Order.filled_quantity_af).label('total_qty'),
        func.count(Order.id).label('count')
    ).filter(
        Order.order_type == OrderType.SELL,
        Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]),
        Order.basin == basin
    ).group_by(Order.price_per_af).order_by(Order.price_per_af.asc()).limit(10).all()
    
    bids = [OrderBookEntry(price_per_af=b[0], total_quantity_af=b[1], order_count=b[2]) for b in bids_query]
    asks = [OrderBookEntry(price_per_af=a[0], total_quantity_af=a[1], order_count=a[2]) for a in asks_query]
    
    # Calculate spread
    spread = None
    if bids and asks:
        spread = asks[0].price_per_af - bids[0].price_per_af
    
    return OrderBookResponse(
        bids=bids,
        asks=asks,
        spread=spread,
        basin=basin
    )

@router.get("/price", response_model=MarketPriceResponse)
async def get_market_price(
    basin: str = Query(default="Kern County", description="Filter by basin"),
    db: Session = Depends(get_db)
):
    """Get current market price and statistics for a basin"""
    
    from datetime import datetime, timedelta
    
    # Get transactions from last 24 hours
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    recent_txns = db.query(Transaction).filter(
        Transaction.basin == basin,
        Transaction.executed_at >= cutoff
    ).all()
    
    last_price = None
    avg_price = None
    high_price = None
    low_price = None
    volume = 0.0
    
    if recent_txns:
        prices = [t.price_per_af for t in recent_txns]
        quantities = [t.quantity_af for t in recent_txns]
        
        last_price = recent_txns[-1].price_per_af
        avg_price = sum(p * q for p, q in zip(prices, quantities)) / sum(quantities)
        high_price = max(prices)
        low_price = min(prices)
        volume = sum(quantities)
    
    # Get best bid and ask
    best_bid = db.query(func.max(Order.price_per_af)).filter(
        Order.order_type == OrderType.BUY,
        Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]),
        Order.basin == basin
    ).scalar()
    
    best_ask = db.query(func.min(Order.price_per_af)).filter(
        Order.order_type == OrderType.SELL,
        Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]),
        Order.basin == basin
    ).scalar()
    
    return MarketPriceResponse(
        basin=basin,
        last_price=last_price,
        avg_price_24h=avg_price,
        high_24h=high_price,
        low_24h=low_price,
        volume_24h=volume,
        best_bid=best_bid,
        best_ask=best_ask
    )

@router.get("/basins")
async def list_basins(db: Session = Depends(get_db)):
    """List all basins with active orders"""
    
    basins = db.query(Order.basin).distinct().all()
    
    # Return predefined basins plus any in orders
    default_basins = [
        "Kern County",
        "San Joaquin Valley",
        "Tulare Lake",
        "Kings County",
        "Fresno County",
        "Madera County"
    ]
    
    active_basins = [b[0] for b in basins]
    all_basins = list(set(default_basins + active_basins))
    
    return {"basins": sorted(all_basins)}
