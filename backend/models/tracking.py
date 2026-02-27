"""
Post-approval tracking: conditions and monitoring reports.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
import enum

from core.database import Base


class ConditionStatus(str, enum.Enum):
    PENDING = "pending"
    MET = "met"
    PARTIALLY_MET = "partially_met"
    VIOLATED = "violated"


class TransferCondition(Base):
    __tablename__ = "transfer_conditions"

    id = Column(Integer, primary_key=True, index=True)
    transfer_id = Column(Integer, ForeignKey("transfers.id"), nullable=False)
    condition_text = Column(Text, nullable=False)
    status = Column(String, default="pending")
    due_date = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MonitoringReport(Base):
    __tablename__ = "monitoring_reports"

    id = Column(Integer, primary_key=True, index=True)
    transfer_id = Column(Integer, ForeignKey("transfers.id"), nullable=False)
    report_type = Column(String, nullable=False)
    data = Column(Text)
    submitted_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
