"""
Centralized California water regulatory data.

Contains real data from:
  - DWR Bulletin 118 (basin prioritization)
  - DWR adjudicated basins GeoJSON
  - California Water Code (CWC) sections
  - SWRCB Water Transfer Decision Tree

Defines 10+ regulatory pathways and implements the decision tree
to route transfers to the correct pathway.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"

# ══════════════════════════════════════════════════════════════
#  DWR Critically Overdrafted Basins (Bulletin 118, 2019)
# ══════════════════════════════════════════════════════════════

CRITICALLY_OVERDRAFTED_BASINS = [
    "Chowchilla Subbasin", "Delta-Mendota Subbasin",
    "Eastern San Joaquin Subbasin", "Indian Wells Valley",
    "Kaweah Subbasin", "Kern County Subbasin", "Kings Subbasin",
    "Merced Subbasin", "Paso Robles Area", "Pleasant Valley",
    "Tule Subbasin", "Tulare Lake Subbasin", "Cuyama Valley",
    "Kettleman Plain", "Los Osos Valley", "Madera Subbasin",
    "Oxnard", "Santa Cruz Mid-County",
    "180/400-Foot Aquifer Subbasin", "Salinas Valley",
    "Tracy Subbasin",
]

# ══════════════════════════════════════════════════════════════
#  Protected River Systems (CWC §1215-1220)
# ══════════════════════════════════════════════════════════════

PROTECTED_RIVER_SYSTEMS = {
    "wild_scenic_federal": [
        "Eel River", "Smith River", "Klamath River", "Trinity River",
        "American River (North Fork)", "Merced River (South Fork)",
        "Tuolumne River (above Hetch Hetchy)", "Kings River (Middle Fork)",
        "Kern River (North Fork)",
    ],
    "fully_appropriated": [
        "Sacramento River", "San Joaquin River",
        "Sacramento-San Joaquin Delta",
    ],
    "cwc_1215_protected": [
        "American River (below Nimbus Dam)",
        "Sacramento River",
        "Delta",
    ],
}

# ══════════════════════════════════════════════════════════════
#  California Water Code sections relevant to transfers
# ══════════════════════════════════════════════════════════════

WATER_CODE = {
    "CWC §1011": "Conservation and transfer — saved water from conservation may be transferred",
    "CWC §1020-1030": "Temporary urgency changes in water rights",
    "CWC §1435-1442": "Temporary change in point of diversion, place of use, or purpose of use",
    "CWC §1700-1707": "Long-term transfers — petition to SWRCB for change in water right",
    "CWC §1702": "No-injury rule — transfer cannot injure other legal users",
    "CWC §1725-1732": "Temporary water transfers — up to 1 year",
    "CWC §1810-1814": "Wheeling — fair compensation for use of conveyance facilities",
    "CWC §10505-10505.5": "Area of origin protections",
    "CWC §10726.4": "GSA authority to regulate groundwater extraction and transfers",
    "CWC §10726.4(a)(2)": "GSA may restrict transfers to prevent adverse impacts",
    "CWC §1215-1220": "Protected waterways — restrictions on new appropriations",
    "SGMA §10720-10737.8": "Sustainable Groundwater Management Act",
}

# ══════════════════════════════════════════════════════════════
#  Regulatory Pathways
# ══════════════════════════════════════════════════════════════

class RegulatoryPathway:
    GW_SGMA = "gw_sgma"
    GW_ADJUDICATED = "gw_adjudicated"
    GW_BANKED = "gw_banked"
    GW_IN_LIEU = "gw_in_lieu"
    GW_PROTECTED_EXPORT = "gw_protected_export"
    PRE1914_PRIVATE = "pre1914_private"
    CONTRACT_CVP_SWP = "contract_cvp_swp"
    POST1914_SHORT = "post1914_short"
    POST1914_LONG = "post1914_long"
    IMPORTED_WATER = "imported_water"


PATHWAY_DESCRIPTIONS = {
    RegulatoryPathway.GW_SGMA: (
        "Groundwater transfer under SGMA jurisdiction. GSA approval "
        "and GSP consistency required (CWC §10726.4)."
    ),
    RegulatoryPathway.GW_ADJUDICATED: (
        "Transfer within adjudicated basin. Watermaster approval "
        "required; court decree governs pumping rights."
    ),
    RegulatoryPathway.GW_BANKED: (
        "Withdrawal of previously banked/stored groundwater. "
        "Banking agreement governs withdrawal rights."
    ),
    RegulatoryPathway.GW_IN_LIEU: (
        "In-lieu transfer: seller reduces pumping and makes "
        "surface water available. Metering verification required."
    ),
    RegulatoryPathway.GW_PROTECTED_EXPORT: (
        "Groundwater export from protected area. Subject to "
        "CWC §1215-1220 restrictions."
    ),
    RegulatoryPathway.PRE1914_PRIVATE: (
        "Pre-1914 appropriative right transfer. No SWRCB approval "
        "needed but no-injury rule still applies in court."
    ),
    RegulatoryPathway.CONTRACT_CVP_SWP: (
        "Federal/state contract water transfer (CVP or SWP). "
        "Bureau of Reclamation or DWR approval required."
    ),
    RegulatoryPathway.POST1914_SHORT: (
        "Post-1914 temporary transfer (≤1 year). SWRCB temporary "
        "change petition with 30-day public notice (CWC §1725)."
    ),
    RegulatoryPathway.POST1914_LONG: (
        "Post-1914 long-term transfer (>1 year). SWRCB long-term "
        "change petition with full hearing process (CWC §1700)."
    ),
    RegulatoryPathway.IMPORTED_WATER: (
        "Transfer of imported water — water brought into a basin "
        "from outside. Generally fewer restrictions."
    ),
}


def get_pathway_description(pathway: str) -> str:
    return PATHWAY_DESCRIPTIONS.get(pathway, "Unknown regulatory pathway")


# ══════════════════════════════════════════════════════════════
#  Adjudicated Basins (DWR GeoJSON)
# ══════════════════════════════════════════════════════════════

_adjudicated_basins_cache = None


def _load_adjudicated_basins() -> List[Dict]:
    global _adjudicated_basins_cache
    if _adjudicated_basins_cache is not None:
        return _adjudicated_basins_cache

    geojson_path = DATA_DIR / "adjudicated_basins.geojson"
    if not geojson_path.exists():
        logger.warning("Adjudicated basins GeoJSON not found at %s", geojson_path)
        _adjudicated_basins_cache = []
        return []

    try:
        with open(geojson_path) as f:
            data = json.load(f)
        features = data.get("features", [])
        _adjudicated_basins_cache = features
        logger.info("Loaded %d adjudicated basin features", len(features))
        return features
    except Exception as exc:
        logger.warning("Failed to load adjudicated basins: %s", exc)
        _adjudicated_basins_cache = []
        return []


def is_adjudicated_basin(basin_name: str) -> bool:
    """Check if a basin is adjudicated based on DWR data."""
    features = _load_adjudicated_basins()
    basin_lower = basin_name.lower()
    for f in features:
        props = f.get("properties", {})
        adj_name = (props.get("AdjBasinName") or props.get("Basin_Name") or "").lower()
        if adj_name and (adj_name in basin_lower or basin_lower in adj_name):
            return True
    return False


def get_watermaster(basin_name: str) -> Optional[str]:
    """Get the watermaster for an adjudicated basin."""
    features = _load_adjudicated_basins()
    basin_lower = basin_name.lower()
    for f in features:
        props = f.get("properties", {})
        adj_name = (props.get("AdjBasinName") or props.get("Basin_Name") or "").lower()
        if adj_name and (adj_name in basin_lower or basin_lower in adj_name):
            return props.get("Watermaster") or props.get("watermaster")
    return None


# ══════════════════════════════════════════════════════════════
#  SWRCB Decision Tree — determine regulatory pathway
# ══════════════════════════════════════════════════════════════

def determine_pathway(seller: dict, buyer: dict, transfer: dict) -> str:
    """
    Implement the SWRCB Water Transfer Decision Tree to route
    a transfer to the correct regulatory pathway.
    """
    source = transfer.get("source_type", "").lower()
    ttype = transfer.get("transfer_type", "").lower()
    right_type = seller.get("water_right_type", "").lower()
    basin = seller.get("basin", "")
    duration = transfer.get("duration_days", 365)

    # ── Groundwater paths ──
    if source == "groundwater" or ttype in ("direct", "in_lieu", "banked"):
        if ttype == "banked":
            return RegulatoryPathway.GW_BANKED
        if ttype == "in_lieu":
            return RegulatoryPathway.GW_IN_LIEU

        # Check if adjudicated basin
        if is_adjudicated_basin(basin):
            return RegulatoryPathway.GW_ADJUDICATED

        # Check if export from protected area
        src_basin = transfer.get("source_basin", seller.get("basin", ""))
        dst_basin = transfer.get("destination_basin", buyer.get("basin", ""))
        if src_basin and dst_basin and src_basin.lower() != dst_basin.lower():
            return RegulatoryPathway.GW_PROTECTED_EXPORT

        return RegulatoryPathway.GW_SGMA

    # ── Surface water paths ──
    if right_type in ("cvp_contract", "swp_contract") or ttype in ("cvp_transfer", "swp_transfer"):
        return RegulatoryPathway.CONTRACT_CVP_SWP

    if right_type == "appropriative_pre1914" or ttype == "water_sale":
        return RegulatoryPathway.PRE1914_PRIVATE

    if right_type == "imported" or ttype == "imported":
        return RegulatoryPathway.IMPORTED_WATER

    # Post-1914 appropriative
    if duration > 365:
        return RegulatoryPathway.POST1914_LONG
    return RegulatoryPathway.POST1914_SHORT
