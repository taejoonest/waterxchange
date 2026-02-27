"""
Surface Water Stage 5 — Conveyance & Infrastructure

Evaluates the physical conveyance path: losses, capacity,
wheeling agreements, and infrastructure constraints.
"""

from typing import Any, Dict
from .base import StageResult

STAGE_NAME = "sw_conveyance"

LOSS_RATES = {
    "pipeline": 0.02,
    "canal_lined": 0.05,
    "canal_unlined": 0.15,
    "natural_channel": 0.25,
}


def run(seller: Dict[str, Any], buyer: Dict[str, Any], transfer: Dict[str, Any]) -> StageResult:
    conditions = []
    risk_flags = []
    data = {}

    qty = transfer.get("quantity_af", 0)
    method = transfer.get("conveyance_method", "canal_lined")
    requires_wheeling = transfer.get("requires_wheeling", False)
    wheeling_agency = transfer.get("wheeling_agency", "")

    loss_rate = LOSS_RATES.get(method, 0.10)
    loss_af = qty * loss_rate
    delivered = qty - loss_af

    data["conveyance_method"] = method
    data["loss_rate_pct"] = round(loss_rate * 100, 1)
    data["estimated_loss_af"] = round(loss_af, 1)
    data["estimated_delivery_af"] = round(delivered, 1)

    if method == "natural_channel":
        risk_flags.append(
            f"Natural channel conveyance has high losses (~{loss_rate:.0%}). "
            "Consider lined canal or pipeline."
        )
        conditions.append(
            "Conveyance loss monitoring required — actual losses may differ "
            "from estimates depending on channel conditions"
        )

    if method == "canal_unlined":
        risk_flags.append(
            f"Unlined canal losses estimated at {loss_rate:.0%} "
            f"({loss_af:,.0f} AF for this transfer)"
        )

    # Wheeling
    data["requires_wheeling"] = requires_wheeling
    data["wheeling_agency"] = wheeling_agency

    if requires_wheeling:
        if not wheeling_agency:
            risk_flags.append("Wheeling required but no wheeling agency specified")
            conditions.append(
                "Identify wheeling agency and execute wheeling agreement "
                "per CWC §1810-1814"
            )
        else:
            conditions.append(
                f"Wheeling agreement with {wheeling_agency} must be in place "
                "before transfer commencement (CWC §1810)"
            )
            data["wheeling_note"] = (
                "Fair compensation for wheeling per CWC §1811 — "
                "covers reasonable costs including maintenance and power"
            )

    # Point of diversion / place of use
    pod = transfer.get("point_of_diversion", "")
    pou = transfer.get("place_of_use", "")
    data["point_of_diversion"] = pod
    data["place_of_use"] = pou

    if pod and pou:
        if pod.lower() != pou.lower():
            conditions.append(
                "Change in point of diversion and/or place of use requires "
                "SWRCB temporary change / long-term change petition"
            )

    # Capacity check (rough)
    if qty > 10000:
        risk_flags.append(
            f"Large transfer volume ({qty:,.0f} AF) — verify conveyance capacity"
        )

    score = 1.0
    if loss_rate > 0.15:
        score -= 0.15
    elif loss_rate > 0.10:
        score -= 0.08
    if requires_wheeling and not wheeling_agency:
        score -= 0.10
    score -= 0.03 * len(risk_flags)
    score = max(0.2, score)

    return StageResult(
        stage=STAGE_NAME, passed=True, score=round(score, 2),
        finding="CONDITIONAL" if conditions else "PASS",
        reasoning=(
            f"Conveyance: {method}, loss: {loss_rate:.0%} ({loss_af:,.0f} AF), "
            f"delivered: {delivered:,.0f} AF"
            + (f", wheeling: {wheeling_agency}" if wheeling_agency else "")
        ),
        conditions=conditions, risk_flags=risk_flags, data=data,
    )
