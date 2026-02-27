"""
Groundwater Stage 3 — GSP Compliance Check

Checks transfer against Groundwater Sustainability Plan thresholds
using **real DWR GSP data** for all California basins.

Data sources:
  - gsp_smc_thresholds.csv: Sustainable Management Criteria from DWR's
    GSP Data Portal. Contains Minimum Thresholds and Measurable Objectives
    for 3,100+ monitoring sites across 101 basins.
  - gsp_monitoring_sites.csv: Site metadata linking EWM_IDs to basins,
    GSAs, coordinates, and sustainability indicators.

When a transfer is submitted, the stage:
  1. Looks up the basin from seller data
  2. Finds all monitoring sites in that basin
  3. Loads the real MT/MO for those sites
  4. Compares seller's water level against nearest site threshold
  5. Evaluates compliance and flags violations

This replaces the previous Kern-County-only hardcoded thresholds.
"""

import csv
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache

from .base import StageResult

logger = logging.getLogger(__name__)
STAGE_NAME = "gsp_compliance"

DATA_DIR = Path(__file__).parent.parent.parent / "data"


# ══════════════════════════════════════════════════════════════
#  Load real DWR GSP monitoring sites and thresholds
# ══════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def _load_monitoring_sites() -> Dict[str, Dict]:
    """Load all monitoring sites keyed by EWM_ID."""
    path = DATA_DIR / "gsp_monitoring_sites.csv"
    if not path.exists():
        logger.warning("GSP monitoring sites CSV not found: %s", path)
        return {}

    sites = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ewm = row.get("EWM_ID", "").strip()
                if not ewm:
                    continue
                sites[ewm] = {
                    "ewm_id": ewm,
                    "site_name": row.get("LOCAL_SITE_NAME", ""),
                    "basin_name": row.get("BASIN_NAME", ""),
                    "subbasin": row.get("SUBBASIN_N", ""),
                    "basin_number": row.get("BASIN_SUBB", "") or row.get("BASIN_ID", ""),
                    "gsa_name": row.get("AGENCY_NAME", ""),
                    "gsp_name": row.get("GSP_NAME", ""),
                    "lat": _safe_float(row.get("LATITUDE")),
                    "lng": _safe_float(row.get("LONGITUDE")),
                    "depth_ft": _safe_float(row.get("DEPTH")),
                    "gs_elevation_ft": _safe_float(row.get("GS_ELEVATION")),
                    "county": row.get("COUNTY", ""),
                    "indicators": {
                        "gw_levels": row.get("SUS_GROUNDWATER_LEVEL", "") == "Yes",
                        "gw_storage": row.get("SUS_GROUNDWATER_STORAGE", "") == "Yes",
                        "seawater": row.get("SUS_SEAWATER_INTRUSION", "") == "Yes",
                        "water_quality": row.get("SUS_WATER_QUALITY", "") == "Yes",
                        "subsidence": row.get("SUS_LAND_SUBSIDENCE", "") == "Yes",
                        "isw": row.get("SUS_INTER_SURFACE_WATER", "") == "Yes",
                    },
                }
        logger.info("Loaded %d GSP monitoring sites", len(sites))
    except Exception as exc:
        logger.warning("Failed to load monitoring sites: %s", exc)
    return sites


@lru_cache(maxsize=1)
def _load_thresholds() -> Dict[str, Dict[str, float]]:
    """
    Load SMC thresholds keyed by EWM_ID.
    Returns {ewm_id: {"minimum_threshold": val, "measurable_objective": val, ...}}
    """
    path = DATA_DIR / "gsp_smc_thresholds.csv"
    if not path.exists():
        logger.warning("GSP SMC thresholds CSV not found: %s", path)
        return {}

    result: Dict[str, Dict[str, float]] = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ewm = row.get("EWM_ID", "").strip()
                if not ewm:
                    continue
                mtype = (row.get("MEASUREMENT_TYPE") or "").strip().lower().replace(" ", "_")
                val = _safe_float(row.get("DATA_VALUE"))
                if val is None:
                    continue
                if ewm not in result:
                    result[ewm] = {}
                result[ewm][mtype] = val
        logger.info("Loaded SMC thresholds for %d sites", len(result))
    except Exception as exc:
        logger.warning("Failed to load SMC thresholds: %s", exc)
    return result


def _safe_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _haversine_mi(lat1, lon1, lat2, lon2):
    R = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ══════════════════════════════════════════════════════════════
#  Find monitoring sites for a basin/location
# ══════════════════════════════════════════════════════════════

def _find_basin_sites(
    basin: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
) -> List[Dict]:
    """Find GSP monitoring sites matching a basin name, sorted by proximity."""
    sites = _load_monitoring_sites()
    basin_lower = basin.lower()

    matches = []
    for ewm_id, site in sites.items():
        site_basin = (site.get("basin_name", "") + " " + site.get("subbasin", "")).lower()
        if basin_lower in site_basin or any(
            word in site_basin for word in basin_lower.split() if len(word) > 3
        ):
            if lat and lng and site.get("lat") and site.get("lng"):
                dist = _haversine_mi(lat, lng, site["lat"], site["lng"])
                site = {**site, "distance_mi": round(dist, 2)}
            matches.append(site)

    if lat and lng:
        matches.sort(key=lambda s: s.get("distance_mi", 9999))

    return matches


def _get_thresholds_for_sites(site_ewm_ids: List[str]) -> List[Dict]:
    """Get SMC thresholds for a list of site EWM_IDs."""
    all_thresh = _load_thresholds()
    result = []
    for ewm in site_ewm_ids:
        t = all_thresh.get(ewm)
        if t:
            result.append({"ewm_id": ewm, **t})
    return result


# ══════════════════════════════════════════════════════════════
#  Main stage runner
# ══════════════════════════════════════════════════════════════

def run(seller: Dict[str, Any], buyer: Dict[str, Any], transfer: Dict[str, Any],
        knowledge_graph=None) -> StageResult:
    conditions: List[str] = []
    risk_flags: List[str] = []
    data: Dict[str, Any] = {}

    basin = seller.get("basin", "")
    seller_lat = seller.get("well_lat")
    seller_lng = seller.get("well_lng")
    seller_wl = seller.get("water_level_ft")
    data["basin"] = basin

    # ── Find real GSP monitoring sites for this basin ─────
    basin_sites = _find_basin_sites(basin, seller_lat, seller_lng)
    data["gsp_sites_found"] = len(basin_sites)

    if basin_sites:
        nearest = basin_sites[0]
        data["nearest_gsp_site"] = {
            "ewm_id": nearest["ewm_id"],
            "name": nearest.get("site_name", ""),
            "distance_mi": nearest.get("distance_mi"),
            "gsa": nearest.get("gsa_name", ""),
            "gsp": nearest.get("gsp_name", ""),
            "depth_ft": nearest.get("depth_ft"),
        }

        # Get thresholds for nearby sites (up to 5 nearest)
        nearby_ewm_ids = [s["ewm_id"] for s in basin_sites[:5]]
        thresh_list = _get_thresholds_for_sites(nearby_ewm_ids)

        if thresh_list:
            # Use nearest site's thresholds, or average of nearby
            mt_values = [t.get("minimum_threshold") for t in thresh_list if t.get("minimum_threshold") is not None]
            mo_values = [t.get("measurable_objective") for t in thresh_list if t.get("measurable_objective") is not None]

            mt = sum(mt_values) / len(mt_values) if mt_values else None
            mo = sum(mo_values) / len(mo_values) if mo_values else None

            data["gsp_thresholds"] = {
                "minimum_threshold_ft": round(mt, 1) if mt is not None else None,
                "measurable_objective_ft": round(mo, 1) if mo is not None else None,
                "sites_averaged": len(thresh_list),
                "source": f"DWR GSP Data Portal ({len(thresh_list)} monitoring sites)",
            }

            # Compare seller water level against real thresholds.
            # DWR thresholds may be in different reference frames:
            #   - Negative values = depth below ground surface (ft BGS)
            #   - Positive values = water surface elevation (ft MSL)
            # Seller water_level_ft is typically depth BGS (negative).
            if seller_wl is not None and mt is not None:
                data["seller_water_level_ft"] = seller_wl

                # Determine reference frame
                mt_is_elevation = mt > 0 and (mo is None or mo > 0)
                seller_is_depth = seller_wl < 0

                if mt_is_elevation and seller_is_depth:
                    gs_elev = nearest.get("gs_elevation_ft")
                    if gs_elev and gs_elev > 0:
                        seller_elev = gs_elev + seller_wl  # e.g., 350 + (-120) = 230 ft MSL
                        compare_wl = seller_elev
                        data["reference_frame"] = "converted_to_elevation"
                        data["ground_surface_elev_ft"] = gs_elev
                        data["seller_water_elev_ft"] = round(seller_elev, 1)
                    else:
                        compare_wl = seller_wl
                        data["reference_frame"] = "mixed_warning"
                        risk_flags.append(
                            "GSP thresholds are in elevation (ft MSL) but seller "
                            "water level is depth (ft BGS) — cannot convert without "
                            "ground surface elevation. Manual verification recommended."
                        )
                elif not mt_is_elevation and seller_is_depth:
                    compare_wl = seller_wl
                    data["reference_frame"] = "depth_bgs"
                else:
                    compare_wl = seller_wl
                    data["reference_frame"] = "elevation_msl" if mt_is_elevation else "depth_bgs"

                data["compliance_check"] = {
                    "water_level_compared": round(compare_wl, 1),
                    "minimum_threshold": round(mt, 1),
                    "measurable_objective": round(mo, 1) if mo else None,
                    "reference_frame": data.get("reference_frame", "unknown"),
                }

                if "mixed_warning" not in data.get("reference_frame", ""):
                    if compare_wl < mt:
                        risk_flags.append(
                            f"Water level ({compare_wl:.1f} ft) is BELOW the "
                            f"Minimum Threshold ({mt:.1f} ft) per GSP — "
                            f"sustainability indicator violated"
                        )
                        conditions.append(
                            "Transfer may not proceed until water levels recover above "
                            f"Minimum Threshold ({mt:.1f} ft) per SGMA §10727.2(b)(1). "
                            f"Based on {len(mt_values)} monitoring site(s) from DWR GSP data."
                        )
                    elif mo is not None and compare_wl < mo:
                        risk_flags.append(
                            f"Water level ({compare_wl:.1f} ft) is below "
                            f"Measurable Objective ({mo:.1f} ft) but above "
                            f"Minimum Threshold ({mt:.1f} ft)"
                        )
                        conditions.append(
                            "Post-transfer monitoring required to ensure water levels "
                            f"do not fall below Minimum Threshold ({mt:.1f} ft)"
                        )
                    else:
                        data["compliance_check"]["status"] = "ABOVE_MO"
        else:
            data["gsp_thresholds"] = {
                "note": "No SMC thresholds found for nearby monitoring sites",
                "source": "DWR GSP Data Portal (no match)",
            }
    else:
        data["gsp_thresholds"] = {
            "note": f"No GSP monitoring sites found for basin '{basin}'",
            "source": "DWR GSP Data Portal (no match)",
        }

    # ── Water quality check (if nitrate provided) ─────────
    nitrate = seller.get("nitrate_mg_l")
    if nitrate is not None:
        data["seller_nitrate_mg_l"] = nitrate
        # Federal MCL for nitrate
        if nitrate > 45.0:
            risk_flags.append(
                f"Nitrate ({nitrate} mg/L) exceeds federal MCL (45 mg/L as NO3)"
            )
        elif nitrate > 10.0:
            risk_flags.append(
                f"Nitrate ({nitrate} mg/L) exceeds EPA standard (10 mg/L as N)"
            )

    # ── Subsidence (flagged based on basin indicators) ────
    if basin_sites:
        any_subsidence = any(s.get("indicators", {}).get("subsidence") for s in basin_sites[:5])
        data["subsidence_monitoring_active"] = any_subsidence
        if any_subsidence:
            conditions.append(
                "Basin has active subsidence monitoring — transfer must not "
                "exacerbate land subsidence per GSP §10727.2(b)(3)"
            )

    # ── Knowledge graph context ───────────────────────────
    if knowledge_graph:
        try:
            kg_results = knowledge_graph.query(f"transfer compliance {basin}")
            if kg_results:
                data["kg_entities_found"] = len(kg_results)
                data["kg_top_entity"] = kg_results[0].get("data", {}).get("name", "")
        except Exception:
            pass

    # ── Scoring ───────────────────────────────────────────
    score = 1.0
    if any("violated" in f.lower() for f in risk_flags):
        score -= 0.35
    score -= 0.08 * len(risk_flags)
    score -= 0.03 * len(conditions)
    if not basin_sites:
        score -= 0.05  # penalty for no GSP data
    score = max(0.10, score)

    passed = not any("may not proceed" in c.lower() for c in conditions)
    finding = "FAIL" if not passed else ("CONDITIONAL" if conditions else "PASS")

    src = "DWR GSP Data Portal" if basin_sites else "no basin match"

    return StageResult(
        stage=STAGE_NAME, passed=passed, score=round(score, 2),
        finding=finding,
        reasoning=(
            f"Basin: {basin}; {len(basin_sites)} GSP site(s) ({src}); "
            f"{len(risk_flags)} risk flags"
        ),
        conditions=conditions, risk_flags=risk_flags, data=data,
        monitoring=[
            "Semi-annual water level monitoring per GSP requirements",
            "Annual subsidence monitoring via InSAR (if applicable)",
        ] if passed else [],
    )
