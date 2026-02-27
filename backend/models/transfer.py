"""
Transfer model for water transfer pipeline records.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON, Text
from sqlalchemy.sql import func
import enum

from core.database import Base


class EntityType(str, enum.Enum):
    FARMER = "farmer"
    WATER_DISTRICT = "water_district"
    MUNICIPALITY = "municipality"
    WATER_BANK = "water_bank"
    INDUSTRIAL = "industrial"
    GSA = "gsa"
    DEVELOPER = "developer"
    ENVIRONMENTAL = "environmental"


class TransferType(str, enum.Enum):
    DIRECT = "direct"
    IN_LIEU = "in_lieu"
    BANKED = "banked"
    TEMPORARY_CHANGE = "temporary_change"
    LONG_TERM_CHANGE = "long_term_change"
    PERMANENT = "transfer"
    WATER_SALE = "water_sale"
    CVP_TRANSFER = "cvp_transfer"
    SWP_TRANSFER = "swp_transfer"


class TransferStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    DENIED = "denied"
    IN_REVIEW = "in_review"


class TransferParty(Base):
    __tablename__ = "transfer_parties"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    basin = Column(String)
    gsa = Column(String)
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer)
    buyer_id = Column(Integer)

    transfer_type = Column(String, nullable=False)
    quantity_af = Column(Float, nullable=False)
    price_per_af = Column(Float)

    source_basin = Column(String)
    destination_basin = Column(String)
    source_gsa = Column(String)
    destination_gsa = Column(String)

    pipeline_type = Column(String)   # "groundwater", "surface_water", "auto"
    pathway = Column(String)         # regulatory pathway used

    status = Column(String, default="pending")
    decision = Column(String)
    composite_score = Column(Float)
    report = Column(Text)
    stage_results = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
