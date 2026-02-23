"""
Water Transfer Matching Engine
Algorithmic matching of buy and sell orders within compatible basins
"""

from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models.order import Order, OrderType, OrderStatus
from models.transaction import Transaction
from models.user import User

class MatchingEngine:
    """
    Continuous double auction matching engine for water transfers.
    
    Matching Rules:
    1. Orders must be in the same basin (or compatible basins)
    2. Buy price >= Sell price (price overlap)
    3. Execution at midpoint price
    4. Partial fills allowed
    5. Time priority for orders at same price
    """
    
    # Basin compatibility matrix - defines which basins can trade
    COMPATIBLE_BASINS = {
        "Kern County": ["Kern County", "Tulare Lake", "Kings County"],
        "San Joaquin Valley": ["San Joaquin Valley", "Fresno County", "Madera County"],
        "Tulare Lake": ["Tulare Lake", "Kern County", "Kings County"],
        "Kings County": ["Kings County", "Kern County", "Tulare Lake", "Fresno County"],
        "Fresno County": ["Fresno County", "San Joaquin Valley", "Kings County", "Madera County"],
        "Madera County": ["Madera County", "San Joaquin Valley", "Fresno County"]
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.matches: List[Transaction] = []
    
    def match_orders(self) -> List[Transaction]:
        """
        Run the matching algorithm on all open orders.
        Returns list of executed transactions.
        """
        self.matches = []
        
        # Get all open buy orders (sorted by price desc, then time asc)
        buy_orders = self.db.query(Order).filter(
            Order.order_type == OrderType.BUY,
            Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED])
        ).order_by(Order.price_per_af.desc(), Order.created_at.asc()).all()
        
        # Get all open sell orders (sorted by price asc, then time asc)
        sell_orders = self.db.query(Order).filter(
            Order.order_type == OrderType.SELL,
            Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED])
        ).order_by(Order.price_per_af.asc(), Order.created_at.asc()).all()
        
        # Match orders
        for buy_order in buy_orders:
            for sell_order in sell_orders:
                # Skip if already filled
                if buy_order.status == OrderStatus.FILLED:
                    break
                if sell_order.status == OrderStatus.FILLED:
                    continue
                
                # Skip same user
                if buy_order.user_id == sell_order.user_id:
                    continue
                
                # Check basin compatibility
                if not self._basins_compatible(buy_order.basin, sell_order.basin):
                    continue
                
                # Check price overlap
                if buy_order.price_per_af < sell_order.price_per_af:
                    continue
                
                # Execute match
                transaction = self._execute_match(buy_order, sell_order)
                if transaction:
                    self.matches.append(transaction)
        
        self.db.commit()
        return self.matches
    
    def _basins_compatible(self, basin1: str, basin2: str) -> bool:
        """Check if two basins can trade water"""
        compatible = self.COMPATIBLE_BASINS.get(basin1, [basin1])
        return basin2 in compatible
    
    def _execute_match(self, buy_order: Order, sell_order: Order) -> Optional[Transaction]:
        """Execute a match between buy and sell orders"""
        
        # Calculate match quantity (minimum of remaining quantities)
        buy_remaining = buy_order.quantity_af - buy_order.filled_quantity_af
        sell_remaining = sell_order.quantity_af - sell_order.filled_quantity_af
        match_quantity = min(buy_remaining, sell_remaining)
        
        if match_quantity <= 0:
            return None
        
        # Calculate execution price (midpoint)
        execution_price = (buy_order.price_per_af + sell_order.price_per_af) / 2
        total_value = match_quantity * execution_price
        
        # Update orders
        buy_order.filled_quantity_af += match_quantity
        sell_order.filled_quantity_af += match_quantity
        
        # Update order statuses
        if buy_order.filled_quantity_af >= buy_order.quantity_af:
            buy_order.status = OrderStatus.FILLED
            buy_order.filled_at = datetime.utcnow()
        else:
            buy_order.status = OrderStatus.PARTIALLY_FILLED
        
        if sell_order.filled_quantity_af >= sell_order.quantity_af:
            sell_order.status = OrderStatus.FILLED
            sell_order.filled_at = datetime.utcnow()
        else:
            sell_order.status = OrderStatus.PARTIALLY_FILLED
        
        # Update user balances
        buyer = self.db.query(User).filter(User.id == buy_order.user_id).first()
        seller = self.db.query(User).filter(User.id == sell_order.user_id).first()
        
        if buyer and seller:
            buyer.water_balance_af += match_quantity
            seller.water_balance_af -= match_quantity
        
        # Create transaction record
        transaction = Transaction(
            buyer_id=buy_order.user_id,
            seller_id=sell_order.user_id,
            buy_order_id=buy_order.id,
            sell_order_id=sell_order.id,
            quantity_af=match_quantity,
            price_per_af=execution_price,
            total_value=total_value,
            basin=buy_order.basin,
            compliance_verified="approved"  # Auto-approved for same/compatible basins
        )
        
        self.db.add(transaction)
        
        return transaction
    
    def get_best_bid(self, basin: str) -> Optional[float]:
        """Get the highest buy price for a basin"""
        order = self.db.query(Order).filter(
            Order.order_type == OrderType.BUY,
            Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]),
            Order.basin == basin
        ).order_by(Order.price_per_af.desc()).first()
        
        return order.price_per_af if order else None
    
    def get_best_ask(self, basin: str) -> Optional[float]:
        """Get the lowest sell price for a basin"""
        order = self.db.query(Order).filter(
            Order.order_type == OrderType.SELL,
            Order.status.in_([OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]),
            Order.basin == basin
        ).order_by(Order.price_per_af.asc()).first()
        
        return order.price_per_af if order else None
