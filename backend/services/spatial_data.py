"""
Spatial data service — fetches real well, water level, and domestic well
data from DWR public APIs and local GeoJSON caches.
"""

import json
import math
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache

import requests

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
MONITORING_DIR = DATA_DIR.parent.parent / "data" / "monitoring"

DWR_WCR_URL = (
    "https://data.cnra.ca.gov/api/3/action/datastore_search"
)
WCR_RESOURCE_ID = "e0e36524-5765-43c9-b7e1-4aaf54517e3b"

DWR_CASGEM_URL = (
    "https://services.arcgis.com/cJ9YHowT8TU7DUyn/"
    "arcgis/rest/services/GW_Elevation_Points/FeatureServer/0/query"
)


def haversine_mi(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@lru_cache(maxsize=32)
def _load_kern_wells() -> List[Dict]:
    for candidate in [
        DATA_DIR / "kern_wells.json",
        MONITORING_DIR / "kern_wells.json",
    ]:
        if candidate.exists():
            with open(candidate) as f:
                data = json.load(f)
            return data if isinstance(data, list) else data.get("features", [])
    return []


def get_nearby_wells(lat: float, lng: float, radius_mi: float = 1.0) -> Dict[str, Any]:
    """Find wells within radius_mi of a point."""
    wells = _load_kern_wells()
    nearby = []
    domestic = []

    for w in wells:
        props = w.get("properties", w) if "properties" in w else w
        wlat = props.get("latitude") or props.get("lat")
        wlng = props.get("longitude") or props.get("lng") or props.get("lon")
        if wlat is None or wlng is None:
            continue
        try:
            dist = haversine_mi(lat, lng, float(wlat), float(wlng))
        except (ValueError, TypeError):
            continue
        if dist <= radius_mi:
            use = (props.get("use") or props.get("planned_use") or "").lower()
            entry = {
                "distance_mi": round(dist, 3),
                "depth_ft": props.get("total_depth") or props.get("depth"),
                "use": use,
            }
            nearby.append(entry)
            if "domestic" in use:
                domestic.append(entry)

    return {
        "total_wells_within_radius": len(nearby),
        "domestic_wells": len(domestic),
        "radius_mi": radius_mi,
        "source": "DWR Well Completion Reports (local cache)",
    }


def fetch_water_level_dwr(lat: float, lng: float, radius_m: float = 5000) -> Optional[Dict]:
    """Query DWR CASGEM/GW Elevation Points near a coordinate."""
    try:
        resp = requests.get(DWR_CASGEM_URL, params={
            "where": "1=1",
            "geometry": f"{lng},{lat}",
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "distance": radius_m,
            "units": "esriSRUnit_Meter",
            "outFields": "WELL_NAME,MEASUREMENT_DATE,GS_ELEVATION,WS_ELEVATION,RP_ELEVATION",
            "returnGeometry": "false",
            "f": "json",
            "resultRecordCount": 5,
            "orderByFields": "MEASUREMENT_DATE DESC",
        }, timeout=10)
        resp.raise_for_status()
        features = resp.json().get("features", [])
        if not features:
            return None
        latest = features[0]["attributes"]
        return {
            "well_name": latest.get("WELL_NAME"),
            "date": latest.get("MEASUREMENT_DATE"),
            "ground_surface_elev_ft": latest.get("GS_ELEVATION"),
            "water_surface_elev_ft": latest.get("WS_ELEVATION"),
            "source": "DWR GW Elevation Points FeatureServer",
        }
    except Exception as exc:
        logger.warning("DWR water level fetch failed: %s", exc)
        return None


def get_well_impact_data(
    seller_lat: Optional[float], seller_lng: Optional[float],
    buyer_lat: Optional[float], buyer_lng: Optional[float],
) -> Dict[str, Any]:
    """Gather spatial data needed for well-impact analysis."""
    result: Dict[str, Any] = {}

    if seller_lat and seller_lng:
        result["seller_nearby_wells"] = get_nearby_wells(seller_lat, seller_lng)
        wl = fetch_water_level_dwr(seller_lat, seller_lng)
        if wl:
            result["seller_dwr_water_level"] = wl

    if buyer_lat and buyer_lng:
        result["buyer_nearby_wells"] = get_nearby_wells(buyer_lat, buyer_lng)
        wl = fetch_water_level_dwr(buyer_lat, buyer_lng)
        if wl:
            result["buyer_dwr_water_level"] = wl

    if seller_lat and seller_lng and buyer_lat and buyer_lng:
        result["distance_mi"] = round(
            haversine_mi(seller_lat, seller_lng, buyer_lat, buyer_lng), 2
        )

    return result
