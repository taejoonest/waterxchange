"""
Groundwater Stage 1 — Intake Validation

Validates entity types, basin info, allocation data, and extraction methods.
"""

from typing import Any, Dict
from .base import StageResult, ENTITY_TYPES, ALLOWED_TRANSFER_TYPES

STAGE_NAME = "intake_validation"


def run(seller: Dict[str, Any], buyer: Dict[str, Any], transfer: Dict[str, Any]) -> StageResult:
    conditions = []
    risk_flags = []
    data = {}

    seller_type = seller.get("entity_type", "")
    buyer_type = buyer.get("entity_type", "")
    ttype = transfer.get("transfer_type", "direct")

    # Validate entity types
    if seller_type not in ENTITY_TYPES:
        return StageResult(
            stage=STAGE_NAME, passed=False, score=0.0, finding="FAIL",
            reasoning=f"Unknown seller entity type: '{seller_type}'",
        )
    if buyer_type not in ENTITY_TYPES:
        return StageResult(
            stage=STAGE_NAME, passed=False, score=0.0, finding="FAIL",
            reasoning=f"Unknown buyer entity type: '{buyer_type}'",
        )

    # Validate transfer type allowed for these entities
    allowed = ALLOWED_TRANSFER_TYPES.get(ttype, set())
    if buyer_type not in allowed:
        return StageResult(
            stage=STAGE_NAME, passed=False, score=0.0, finding="FAIL",
            reasoning=f"Transfer type '{ttype}' not allowed for buyer type '{buyer_type}'",
        )

    # Validate basic data
    qty = transfer.get("quantity_af", 0)
    if qty <= 0:
        return StageResult(
            stage=STAGE_NAME, passed=False, score=0.0, finding="FAIL",
            reasoning="Transfer quantity must be > 0 AF",
        )

    data["seller_type"] = seller_type
    data["buyer_type"] = buyer_type
    data["transfer_type"] = ttype
    data["quantity_af"] = qty

    # Check basin info
    seller_basin = seller.get("basin", "")
    buyer_basin = buyer.get("basin", "")
    if not seller_basin:
        risk_flags.append("Seller basin not specified")
    if not buyer_basin:
        risk_flags.append("Buyer basin not specified")

    data["seller_basin"] = seller_basin
    data["buyer_basin"] = buyer_basin
    data["same_basin"] = seller_basin.lower() == buyer_basin.lower() if seller_basin and buyer_basin else None

    # Check GSA info
    seller_gsa = seller.get("gsa", "")
    buyer_gsa = buyer.get("gsa", "")
    data["seller_gsa"] = seller_gsa
    data["buyer_gsa"] = buyer_gsa

    # Extraction method
    method = seller.get("extraction_method", "")
    if method == "self_reported":
        risk_flags.append("Seller uses self-reported extraction — metering recommended")
        conditions.append("Install totalizing flow meter within 90 days (GSP requirement)")

    # Check allocation > 0
    alloc = seller.get("allocation_af", 0)
    if alloc <= 0 and ttype == "direct":
        risk_flags.append("Seller has no allocation on record")

    # Banked water checks
    if ttype == "banked":
        banked = seller.get("banked_balance_af", 0)
        if banked <= 0:
            return StageResult(
                stage=STAGE_NAME, passed=False, score=0.0, finding="FAIL",
                reasoning="Banked transfer requested but seller has no banked balance",
            )
        if qty > banked:
            risk_flags.append(
                f"Transfer qty ({qty} AF) exceeds banked balance ({banked} AF)"
            )
        data["banked_balance_af"] = banked

    score = 1.0
    score -= 0.05 * len(risk_flags)
    score = max(0.3, score)

    return StageResult(
        stage=STAGE_NAME, passed=True, score=round(score, 2),
        finding="CONDITIONAL" if conditions else "PASS",
        reasoning=f"{seller_type} → {buyer_type}, {qty:,.0f} AF {ttype}, basin: {seller_basin}",
        conditions=conditions, risk_flags=risk_flags, data=data,
    )
