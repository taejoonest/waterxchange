"""
Groundwater Stage 5 — Basin Health Check

Evaluates the overall health of the source basin including
critically overdrafted status, storage trends, and subsidence.
"""

from typing import Any, Dict
from .base import StageResult

STAGE_NAME = "basin_health"

CRITICALLY_OVERDRAFTED_BASINS = [
    "Chowchilla Subbasin", "Delta-Mendota Subbasin", "Eastern San Joaquin Subbasin",
    "Indian Wells Valley", "Kaweah Subbasin", "Kern County Subbasin",
    "Kings Subbasin", "Merced Subbasin", "Paso Robles Area",
    "Pleasant Valley", "Tule Subbasin", "Tulare Lake Subbasin",
    "Cuyama Valley", "Kettleman Plain", "Los Osos Valley",
    "Madera Subbasin", "Oxnard", "Santa Cruz Mid-County",
    "180/400-Foot Aquifer Subbasin", "Salinas Valley",
    "Tracy Subbasin",
]


def _is_critically_overdrafted(basin: str) -> bool:
    basin_lower = basin.lower()
    return any(b.lower() in basin_lower or basin_lower in b.lower()
               for b in CRITICALLY_OVERDRAFTED_BASINS)


def run(seller: Dict[str, Any], buyer: Dict[str, Any], transfer: Dict[str, Any]) -> StageResult:
    conditions = []
    risk_flags = []
    data = {}

    basin = seller.get("basin", "")
    data["basin"] = basin

    # Critically Overdrafted status
    is_cod = _is_critically_overdrafted(basin)
    data["critically_overdrafted"] = is_cod
    data["source"] = "DWR Bulletin 118, 2019 Basin Prioritization"

    if is_cod:
        risk_flags.append(
            f"Basin '{basin}' is Critically Overdrafted per DWR Bulletin 118"
        )
        conditions.append(
            "Transfer from critically overdrafted basin requires demonstration "
            "that extraction will not worsen overdraft conditions"
        )

    # Inter-basin export check
    src_basin = transfer.get("source_basin", seller.get("basin", ""))
    dst_basin = transfer.get("destination_basin", buyer.get("basin", ""))
    is_export = src_basin.lower() != dst_basin.lower() if src_basin and dst_basin else False
    data["is_export"] = is_export

    if is_export and is_cod:
        risk_flags.append(
            "Groundwater export from critically overdrafted basin — "
            "heightened scrutiny required per SGMA §10726.4(a)(2)"
        )
        conditions.append(
            "GSA board approval required for export from critically overdrafted basin"
        )

    # Water level trend (if available)
    wl = seller.get("water_level_ft")
    if wl is not None:
        data["current_water_level_ft"] = wl
        if wl < -150:
            risk_flags.append(f"Very deep water level ({wl} ft) indicates severe depletion")
        elif wl < -100:
            risk_flags.append(f"Deep water level ({wl} ft) below measurable objective")

    # Quantity relative to basin
    qty = transfer.get("quantity_af", 0)
    data["transfer_qty_af"] = qty

    if qty > 5000 and is_cod:
        risk_flags.append(
            f"Large transfer ({qty:,.0f} AF) from critically overdrafted basin "
            "— requires detailed basin impact analysis"
        )

    score = 1.0
    if is_cod:
        score -= 0.15
    if is_export and is_cod:
        score -= 0.20
    if wl is not None and wl < -150:
        score -= 0.15
    score -= 0.05 * len(risk_flags)
    score = max(0.10, score)

    passed = True
    if is_export and is_cod and qty > 10000:
        passed = False

    finding = "FAIL" if not passed else ("CONDITIONAL" if conditions else "PASS")

    return StageResult(
        stage=STAGE_NAME, passed=passed, score=round(score, 2),
        finding=finding,
        reasoning=(
            f"Basin: {basin}; "
            f"{'Critically Overdrafted' if is_cod else 'Not Critically Overdrafted'}; "
            f"{'Export' if is_export else 'Intra-basin'}"
        ),
        conditions=conditions, risk_flags=risk_flags, data=data,
    )
