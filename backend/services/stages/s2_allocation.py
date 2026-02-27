"""
Groundwater Stage 2 — Allocation Check

Verifies seller has sufficient allocation/balance for the transfer.
"""

from typing import Any, Dict
from .base import StageResult

STAGE_NAME = "allocation_check"


def run(seller: Dict[str, Any], buyer: Dict[str, Any], transfer: Dict[str, Any]) -> StageResult:
    conditions = []
    risk_flags = []
    data = {}

    qty = transfer.get("quantity_af", 0)
    ttype = transfer.get("transfer_type", "direct")

    alloc = seller.get("allocation_af", 0)
    used = seller.get("used_af", 0)
    banked = seller.get("banked_balance_af", 0)

    data["allocation_af"] = alloc
    data["used_af"] = used
    data["banked_balance_af"] = banked

    if ttype == "banked":
        available = banked
        data["available_af"] = available
        data["source"] = "banked_balance"
    elif ttype == "in_lieu":
        available = alloc - used
        data["available_af"] = max(0, available)
        data["source"] = "unused_allocation_in_lieu"
    else:
        available = alloc - used
        data["available_af"] = max(0, available)
        data["source"] = "unused_allocation"

    data["requested_af"] = qty

    if available <= 0:
        return StageResult(
            stage=STAGE_NAME, passed=False, score=0.0, finding="FAIL",
            reasoning=f"No available water: alloc={alloc}, used={used}, banked={banked}",
            data=data,
        )

    if qty > available:
        overage_pct = ((qty - available) / available * 100) if available > 0 else 100
        risk_flags.append(
            f"Requested {qty:,.0f} AF exceeds available {available:,.0f} AF "
            f"(overage: {overage_pct:.0f}%)"
        )
        data["overage_pct"] = round(overage_pct, 1)

    utilization = used / alloc if alloc > 0 else 0
    data["utilization_pct"] = round(utilization * 100, 1)

    if utilization > 0.90:
        risk_flags.append(
            f"High utilization ({utilization:.0%}) — seller is using most of allocation"
        )

    # Seller entity-specific checks
    seller_type = seller.get("entity_type", "")
    if seller_type == "water_bank":
        conditions.append(
            "Water bank must provide current accounting statement "
            "verified by independent auditor"
        )
    elif seller_type == "municipality":
        conditions.append(
            "Municipal seller must demonstrate transfer will not "
            "impact public water supply reliability"
        )

    score = 1.0
    if qty > available:
        score = max(0.2, available / qty) if qty > 0 else 0.2
    score -= 0.05 * len(risk_flags)
    score = max(0.1, score)

    passed = available > 0
    finding = "FAIL" if not passed else ("CONDITIONAL" if conditions or risk_flags else "PASS")

    return StageResult(
        stage=STAGE_NAME, passed=passed, score=round(score, 2),
        finding=finding,
        reasoning=f"Available: {available:,.0f} AF, Requested: {qty:,.0f} AF ({data['source']})",
        conditions=conditions, risk_flags=risk_flags, data=data,
    )
