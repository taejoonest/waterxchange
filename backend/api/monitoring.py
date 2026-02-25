"""
Monitoring API — serves well locations, subsidence zones, and water quality data
from pre-built JSON files (sourced from DWR Well Completion Reports and Kern County GSP).
"""

import json
from pathlib import Path
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "monitoring"

_cache = {}

def _load(filename: str):
    if filename not in _cache:
        filepath = DATA_DIR / filename
        if filepath.exists():
            with open(filepath) as f:
                _cache[filename] = json.load(f)
        else:
            _cache[filename] = []
    return _cache[filename]


@router.get("/wells")
async def get_wells(
    use: str = Query(None, description="Filter by well use type (Domestic, Irrigation, Monitoring, etc.)"),
    min_depth: float = Query(None, description="Minimum well depth in feet"),
    max_depth: float = Query(None, description="Maximum well depth in feet"),
):
    wells = _load("kern_wells.json")
    filtered = wells

    if use:
        use_lower = use.lower()
        filtered = [w for w in filtered if use_lower in (w.get("use") or "").lower()]

    if min_depth is not None:
        filtered = [w for w in filtered if (w.get("depth_ft") or 0) >= min_depth]

    if max_depth is not None:
        filtered = [w for w in filtered if (w.get("depth_ft") or 0) <= max_depth]

    return {
        "total": len(filtered),
        "wells": filtered,
    }


@router.get("/subsidence")
async def get_subsidence():
    zones = _load("subsidence_zones.json")
    return {"zones": zones}


@router.get("/water-quality")
async def get_water_quality():
    zones = _load("water_quality.json")
    return {"zones": zones}


@router.get("/summary")
async def get_monitoring_summary():
    wells = _load("kern_wells.json")
    subsidence = _load("subsidence_zones.json")
    water_quality = _load("water_quality.json")

    use_counts = {}
    for w in wells:
        use = w.get("use", "Unknown")
        use_counts[use] = use_counts.get(use, 0) + 1

    depth_values = [w["depth_ft"] for w in wells if w.get("depth_ft")]

    critical_subsidence = [z for z in subsidence if z.get("risk_level") in ("critical", "high")]
    poor_quality = [z for z in water_quality if z.get("status") in ("poor", "warning")]

    return {
        "total_wells": len(wells),
        "wells_by_type": use_counts,
        "avg_well_depth_ft": round(sum(depth_values) / len(depth_values), 1) if depth_values else None,
        "max_well_depth_ft": max(depth_values) if depth_values else None,
        "subsidence_zones": len(subsidence),
        "critical_subsidence_zones": len(critical_subsidence),
        "water_quality_zones": len(water_quality),
        "poor_quality_zones": len(poor_quality),
    }
