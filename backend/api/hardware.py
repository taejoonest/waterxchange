"""
Hardware Data Ingestion API

Receives telemetry from WX-Level and WX-Flow IoT devices.
Stores readings in the database and provides query endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


# ── Request Models ───────────────────────────────────────────

class WXLevelReading(BaseModel):
    device_id: str
    device_type: str = "wx-level"
    fw_version: str = ""
    boot_count: int = 0
    water_level_ft: float
    pressure_psi: float
    water_temp_c: Optional[float] = None
    baro_pressure_hpa: Optional[float] = None
    baro_temp_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    battery_v: float = 0
    solar_v: float = 0


class FlowData(BaseModel):
    velocity_cm_day: float = 0
    direction_deg: float = -1
    valid: bool = False
    peak_temps: list[float] = Field(default_factory=list)
    peak_times: list[float] = Field(default_factory=list)


class WXFlowReading(BaseModel):
    device_id: str
    device_type: str = "wx-flow"
    fw_version: str = ""
    boot_count: int = 0
    flow: FlowData = Field(default_factory=FlowData)
    conductivity_us: float = 0
    tds_ppm: float = 0
    water_temp_c: float = 0
    water_level_ft: float = 0
    pressure_psi: float = 0
    battery_v: float = 0
    solar_v: float = 0


# ── In-Memory Storage (swap for SQLAlchemy in production) ────

_readings: list[dict] = []
MAX_STORED = 50000


def _store(reading: dict):
    reading["timestamp"] = datetime.utcnow().isoformat()
    _readings.append(reading)
    if len(_readings) > MAX_STORED:
        _readings.pop(0)


# ── Ingest Endpoints ─────────────────────────────────────────

@router.post("/data")
async def ingest_data(payload: dict):
    """
    Universal ingest — accepts both wx-level and wx-flow payloads.
    The device_type field determines how the data is parsed.
    """
    device_type = payload.get("device_type", "")
    device_id = payload.get("device_id", "unknown")

    if device_type == "wx-level":
        reading = WXLevelReading(**payload)
        record = reading.dict()
    elif device_type == "wx-flow":
        reading = WXFlowReading(**payload)
        record = reading.dict()
    else:
        record = payload.copy()

    record["device_id"] = device_id
    record["device_type"] = device_type
    _store(record)

    return {
        "status": "ok",
        "device_id": device_id,
        "timestamp": record["timestamp"],
        "readings_stored": len(_readings),
    }


@router.post("/data/level")
async def ingest_level(reading: WXLevelReading):
    """Typed endpoint specifically for WX-Level devices."""
    record = reading.dict()
    _store(record)
    return {"status": "ok", "device_id": reading.device_id, "timestamp": record["timestamp"]}


@router.post("/data/flow")
async def ingest_flow(reading: WXFlowReading):
    """Typed endpoint specifically for WX-Flow devices."""
    record = reading.dict()
    _store(record)
    return {"status": "ok", "device_id": reading.device_id, "timestamp": record["timestamp"]}


# ── Query Endpoints ──────────────────────────────────────────

@router.get("/data")
async def get_readings(
    device_id: Optional[str] = Query(None),
    device_type: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=8760),
    limit: int = Query(100, ge=1, le=5000),
):
    """Query stored readings with optional filters."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    cutoff_str = cutoff.isoformat()

    results = _readings
    if device_id:
        results = [r for r in results if r.get("device_id") == device_id]
    if device_type:
        results = [r for r in results if r.get("device_type") == device_type]
    results = [r for r in results if r.get("timestamp", "") >= cutoff_str]

    return {
        "count": len(results[-limit:]),
        "readings": results[-limit:],
    }


@router.get("/devices")
async def list_devices():
    """List all known devices and their last reading time."""
    devices = {}
    for r in _readings:
        did = r.get("device_id", "unknown")
        devices[did] = {
            "device_id": did,
            "device_type": r.get("device_type", ""),
            "last_seen": r.get("timestamp", ""),
            "battery_v": r.get("battery_v", 0),
            "fw_version": r.get("fw_version", ""),
        }
    return {"devices": list(devices.values())}


@router.get("/data/{device_id}/latest")
async def get_latest(device_id: str):
    """Get the most recent reading for a specific device."""
    for r in reversed(_readings):
        if r.get("device_id") == device_id:
            return r
    raise HTTPException(status_code=404, detail=f"No readings for device {device_id}")
