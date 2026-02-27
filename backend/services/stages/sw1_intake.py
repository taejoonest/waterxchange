"""
Surface Water Stage 1 — Intake Validation

Validates surface water transfer basics: right type, seller identity,
and required documentation. CVP/SWP contract transfers are exempt
from eWRIMS permit ID requirement.
"""

from typing import Any, Dict
from .base import StageResult

STAGE_NAME = "sw_intake_validation"

VALID_RIGHT_TYPES = [
    "appropriative_pre1914", "appropriative_post1914",
    "cvp_contract", "swp_contract", "riparian",
]


def run(seller: Dict[str, Any], buyer: Dict[str, Any], transfer: Dict[str, Any]) -> StageResult:
    conditions = []
    risk_flags = []
    data = {}

    seller_type = seller.get("entity_type", "")
    right_type = seller.get("water_right_type", "")
    right_id = seller.get("water_right_id", "")

    data["seller_type"] = seller_type
    data["water_right_type"] = right_type
    data["water_right_id"] = right_id

    # Validate right type
    if right_type not in VALID_RIGHT_TYPES:
        return StageResult(
            stage=STAGE_NAME, passed=False, score=0.0, finding="FAIL",
            reasoning=f"Unknown water right type: '{right_type}'",
            data=data,
        )

    # CVP/SWP contracts and pre-1914 rights don't need eWRIMS permit ID
    is_contract = right_type in ("cvp_contract", "swp_contract")
    is_pre1914 = right_type == "appropriative_pre1914"
    data["is_contract_transfer"] = is_contract
    data["is_pre1914"] = is_pre1914

    if not is_contract and not is_pre1914 and not right_id:
        return StageResult(
            stage=STAGE_NAME, passed=False, score=0.0, finding="FAIL",
            reasoning="eWRIMS permit/license ID required for non-contract transfers",
            data=data,
        )

    # Validate quantity
    qty = transfer.get("quantity_af", 0)
    if qty <= 0:
        return StageResult(
            stage=STAGE_NAME, passed=False, score=0.0, finding="FAIL",
            reasoning="Transfer quantity must be > 0 AF",
        )
    data["quantity_af"] = qty

    # Transfer type
    ttype = transfer.get("transfer_type", "")
    data["transfer_type"] = ttype

    # Contract-specific checks
    if is_contract:
        contract_alloc = seller.get("contract_allocation_af", 0)
        contract_used = seller.get("contract_used_af", 0)
        available = contract_alloc - contract_used
        data["contract_allocation_af"] = contract_alloc
        data["contract_used_af"] = contract_used
        data["contract_available_af"] = max(0, available)

        if qty > available:
            risk_flags.append(
                f"Requested {qty:,.0f} AF exceeds available contract water "
                f"({available:,.0f} AF)"
            )
        conditions.append(
            f"{'Bureau of Reclamation' if right_type == 'cvp_contract' else 'DWR'} "
            f"approval required for {'CVP' if right_type == 'cvp_contract' else 'SWP'} "
            f"contract water transfer"
        )

    # Face value check for appropriative rights
    if not is_contract:
        face_value = seller.get("face_value_af", 0)
        data["face_value_af"] = face_value
        if face_value > 0 and qty > face_value:
            risk_flags.append(
                f"Transfer qty ({qty:,.0f} AF) exceeds face value ({face_value:,.0f} AF)"
            )

    # Duration check
    duration = transfer.get("duration_days", 365)
    data["duration_days"] = duration
    if duration > 365:
        data["long_term"] = True
        conditions.append(
            "Long-term transfer (>1 year) requires SWRCB long-term change petition"
        )

    score = 1.0
    score -= 0.05 * len(risk_flags)
    score = max(0.3, score)

    return StageResult(
        stage=STAGE_NAME, passed=True, score=round(score, 2),
        finding="CONDITIONAL" if conditions else "PASS",
        reasoning=f"{right_type} transfer, {qty:,.0f} AF, seller: {seller.get('name', 'Unknown')}",
        conditions=conditions, risk_flags=risk_flags, data=data,
    )
