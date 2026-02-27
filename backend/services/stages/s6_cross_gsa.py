"""
Groundwater Stage 6 — Cross-GSA Coordination Check

When a transfer crosses GSA boundaries within the same basin,
SGMA §10726.4 requires coordination between the GSAs.
"""

from typing import Any, Dict
from .base import StageResult

STAGE_NAME = "cross_gsa"


def run(seller: Dict[str, Any], buyer: Dict[str, Any], transfer: Dict[str, Any]) -> StageResult:
    conditions = []
    risk_flags = []
    data = {}

    src_gsa = transfer.get("source_gsa", seller.get("gsa", ""))
    dst_gsa = transfer.get("destination_gsa", buyer.get("gsa", ""))

    data["source_gsa"] = src_gsa
    data["destination_gsa"] = dst_gsa

    if not src_gsa or not dst_gsa:
        risk_flags.append("GSA information incomplete — cannot verify cross-GSA status")
        return StageResult(
            stage=STAGE_NAME, passed=True, score=0.70, finding="CONDITIONAL",
            reasoning="GSA info missing; assuming potential cross-GSA transfer",
            conditions=["Verify GSA jurisdictions before finalizing"],
            risk_flags=risk_flags, data=data,
        )

    is_cross_gsa = src_gsa.lower().strip() != dst_gsa.lower().strip()
    data["is_cross_gsa"] = is_cross_gsa

    if is_cross_gsa:
        risk_flags.append(
            f"Cross-GSA transfer: {src_gsa} → {dst_gsa}"
        )
        conditions.append(
            "Coordination agreement between GSAs required per SGMA §10726.4"
        )
        conditions.append(
            "Both GSAs must verify transfer is consistent with their respective GSPs"
        )

        # Check for known coordination agreements (Kern County)
        kern_coord_gsas = {
            "rosedale-rio bravo", "semitropic", "kern county water agency",
            "olcese", "north kern", "buena vista",
        }
        src_known = any(k in src_gsa.lower() for k in kern_coord_gsas)
        dst_known = any(k in dst_gsa.lower() for k in kern_coord_gsas)

        if src_known and dst_known:
            data["coordination_agreement"] = "Kern County Subbasin Coordination Agreement"
            data["agreement_status"] = "Active — 2020 Coordination Agreement"
        else:
            conditions.append(
                "No known coordination agreement on file — "
                "GSAs must execute agreement before transfer"
            )

        score = 0.70
    else:
        data["note"] = "Intra-GSA transfer — no cross-GSA coordination needed"
        score = 1.0

    passed = True
    finding = "CONDITIONAL" if conditions else "PASS"

    return StageResult(
        stage=STAGE_NAME, passed=passed, score=round(score, 2),
        finding=finding,
        reasoning=(
            f"{'Cross-GSA' if is_cross_gsa else 'Intra-GSA'}: "
            f"{src_gsa} → {dst_gsa}"
        ),
        conditions=conditions, risk_flags=risk_flags, data=data,
    )
