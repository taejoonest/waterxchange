"""
Seed script for demo data
Run this to populate the database with sample users, orders, and transactions
"""

import sys
sys.path.insert(0, '.')

from sqlalchemy.orm import Session
from core.database import SessionLocal, create_tables
from core.security import get_password_hash
from models.user import User
from models.order import Order, OrderType, OrderStatus
from models.transaction import Transaction
from datetime import datetime, timedelta
import random

def seed_database():
    """Seed the database with demo data"""
    
    print("Creating database tables...")
    create_tables()
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"Database already has {existing_users} users. Skipping seed.")
            return
        
        print("Seeding demo users...")
        
        # Create demo farmers
        farmers = [
            {
                "email": "john@greenvalleyfarm.com",
                "password": "demo123",
                "full_name": "John Martinez",
                "farm_name": "Green Valley Farm",
                "basin": "Kern County",
                "water_balance_af": 150,
                "annual_allocation_af": 200
            },
            {
                "email": "sarah@sunrisefarms.com",
                "password": "demo123",
                "full_name": "Sarah Chen",
                "farm_name": "Sunrise Farms",
                "basin": "Kern County",
                "water_balance_af": 85,
                "annual_allocation_af": 100
            },
            {
                "email": "mike@centralvalleyag.com",
                "password": "demo123",
                "full_name": "Mike Thompson",
                "farm_name": "Central Valley Agriculture",
                "basin": "San Joaquin Valley",
                "water_balance_af": 300,
                "annual_allocation_af": 350
            },
            {
                "email": "lisa@fresnofields.com",
                "password": "demo123",
                "full_name": "Lisa Rodriguez",
                "farm_name": "Fresno Fields",
                "basin": "Fresno County",
                "water_balance_af": 120,
                "annual_allocation_af": 150
            },
            {
                "email": "david@tularegrowers.com",
                "password": "demo123",
                "full_name": "David Kim",
                "farm_name": "Tulare Growers Co-op",
                "basin": "Tulare Lake",
                "water_balance_af": 200,
                "annual_allocation_af": 250
            },
            {
                "email": "demo@waterxchange.com",
                "password": "demo123",
                "full_name": "Demo User",
                "farm_name": "Demo Farm",
                "basin": "Kern County",
                "water_balance_af": 127,
                "annual_allocation_af": 150
            }
        ]
        
        user_objects = []
        for farmer in farmers:
            user = User(
                email=farmer["email"],
                hashed_password=get_password_hash(farmer["password"]),
                full_name=farmer["full_name"],
                farm_name=farmer["farm_name"],
                basin=farmer["basin"],
                water_balance_af=farmer["water_balance_af"],
                annual_allocation_af=farmer["annual_allocation_af"],
                is_active=True,
                is_verified=True
            )
            db.add(user)
            user_objects.append(user)
        
        db.commit()
        
        # Refresh to get IDs
        for user in user_objects:
            db.refresh(user)
        
        print(f"Created {len(user_objects)} demo users")
        
        # Create sample orders
        print("Seeding demo orders...")
        
        orders_data = [
            # Kern County orders
            {"user_idx": 0, "type": OrderType.SELL, "qty": 25, "price": 415, "basin": "Kern County"},
            {"user_idx": 0, "type": OrderType.SELL, "qty": 30, "price": 420, "basin": "Kern County"},
            {"user_idx": 1, "type": OrderType.BUY, "qty": 20, "price": 400, "basin": "Kern County"},
            {"user_idx": 5, "type": OrderType.BUY, "qty": 50, "price": 395, "basin": "Kern County"},
            
            # San Joaquin orders
            {"user_idx": 2, "type": OrderType.SELL, "qty": 50, "price": 380, "basin": "San Joaquin Valley"},
            {"user_idx": 2, "type": OrderType.SELL, "qty": 40, "price": 390, "basin": "San Joaquin Valley"},
            
            # Fresno orders
            {"user_idx": 3, "type": OrderType.BUY, "qty": 30, "price": 375, "basin": "Fresno County"},
            {"user_idx": 3, "type": OrderType.SELL, "qty": 15, "price": 400, "basin": "Fresno County"},
            
            # Tulare orders
            {"user_idx": 4, "type": OrderType.SELL, "qty": 45, "price": 425, "basin": "Tulare Lake"},
            {"user_idx": 4, "type": OrderType.BUY, "qty": 25, "price": 380, "basin": "Tulare Lake"},
        ]
        
        order_objects = []
        for order_data in orders_data:
            order = Order(
                user_id=user_objects[order_data["user_idx"]].id,
                order_type=order_data["type"],
                quantity_af=order_data["qty"],
                filled_quantity_af=0,
                price_per_af=order_data["price"],
                basin=order_data["basin"],
                status=OrderStatus.OPEN
            )
            db.add(order)
            order_objects.append(order)
        
        db.commit()
        print(f"Created {len(order_objects)} demo orders")
        
        # Create sample transactions (historical)
        print("Seeding demo transactions...")
        
        transactions_data = [
            {"buyer_idx": 1, "seller_idx": 0, "qty": 15, "price": 412, "basin": "Kern County", "days_ago": 2},
            {"buyer_idx": 5, "seller_idx": 0, "qty": 10, "price": 408, "basin": "Kern County", "days_ago": 5},
            {"buyer_idx": 3, "seller_idx": 2, "qty": 25, "price": 385, "basin": "Fresno County", "days_ago": 7},
            {"buyer_idx": 4, "seller_idx": 2, "qty": 20, "price": 390, "basin": "San Joaquin Valley", "days_ago": 10},
            {"buyer_idx": 5, "seller_idx": 4, "qty": 8, "price": 420, "basin": "Kern County", "days_ago": 12},
        ]
        
        for tx_data in transactions_data:
            transaction = Transaction(
                buyer_id=user_objects[tx_data["buyer_idx"]].id,
                seller_id=user_objects[tx_data["seller_idx"]].id,
                buy_order_id=order_objects[0].id,  # Placeholder
                sell_order_id=order_objects[1].id,  # Placeholder
                quantity_af=tx_data["qty"],
                price_per_af=tx_data["price"],
                total_value=tx_data["qty"] * tx_data["price"],
                basin=tx_data["basin"],
                compliance_verified="approved",
                executed_at=datetime.utcnow() - timedelta(days=tx_data["days_ago"])
            )
            db.add(transaction)
        
        db.commit()
        print(f"Created {len(transactions_data)} demo transactions")
        
        print("\n✅ Demo data seeded successfully!")
        print("\n📱 Demo Login Credentials:")
        print("   Email: demo@waterxchange.com")
        print("   Password: demo123")
        print("\n   Or use any other seeded user with password: demo123")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
