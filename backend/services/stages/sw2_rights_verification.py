"""
Surface Water Stage 2 — Water Rights Verification

Queries the real eWRIMS database (CKAN API at data.ca.gov) to verify
seller's water right status, face value, and priority date.
Falls back to seller-provided data if API is unavailable.
"""

import logging
from typing import Any, Dict, Optional

import requests

from .base import StageResult

logger = logging.getLogger(__name__)
STAGE_NAME = "sw_rights_verification"

EWRIMS_RESOURCE_ID = "151c067a-088b-42a2-b6ad-99d84b48fb36"
EWRIMS_API_URL = (
    f"https://data.ca.gov/api/3/action/datastore_search"
    f"?resource_id={EWRIMS_RESOURCE_ID}"
)


def _lookup_ewrims(right_id: str, seller: Dict) -> Optional[Dict]:
    """Look up a water right in eWRIMS via CKAN API."""
    try:
        resp = requests.get(
            EWRIMS_API_URL,
            params={"q": right_id, "limit": 5},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        records = data.get("result", {}).get("records", [])

        if not records:
            logger.info("eWRIMS: no records found for %s", right_id)
            return _from_seller(seller, "ewrims_no_match")

        rec = records[0]
        return {
            "application_id": rec.get("APPLICATION_NUMBER", ""),
            "holder": rec.get("PRIMARY_OWNER", ""),
            "right_type": rec.get("WATER_RIGHT_TYPE", ""),
            "status": rec.get("WATER_RIGHT_STATUS", ""),
            "face_value_af": rec.get("FACE_VALUE_AMOUNT", ""),
            "priority_date": rec.get("PRIORITY_DATE", ""),
            "source_name": rec.get("SOURCE_NAME", ""),
            "county": rec.get("COUNTY", ""),
            "source": "ewrims_api",
        }
    except Exception as exc:
        logger.warning("eWRIMS API lookup failed for %s: %s — using seller data", right_id, exc)
        return _from_seller(seller, "seller_provided_api_fallback")


def _from_seller(seller: Dict, source_tag: str) -> Dict:
    """Build rights record from seller-provided data."""
    return {
        "application_id": seller.get("water_right_id", ""),
        "holder": seller.get("name", ""),
        "right_type": seller.get("water_right_type", ""),
        "status": seller.get("ewrims_status", "unknown"),
        "face_value_af": seller.get("face_value_af", ""),
        "priority_date": seller.get("priority_date", ""),
        "source": source_tag,
    }


def run(seller: Dict[str, Any], buyer: Dict[str, Any], transfer: Dict[str, Any]) -> StageResult:
    conditions = []
    risk_flags = []
    data = {}

    right_id = seller.get("water_right_id", "")
    right_type = seller.get("water_right_type", "")
    qty = transfer.get("quantity_af", 0)

    # Contract transfers — no eWRIMS lookup needed
    if right_type in ("cvp_contract", "swp_contract"):
        data["verification_method"] = "contract_exempt"
        data["right_type"] = right_type
        agency = "Bureau of Reclamation" if right_type == "cvp_contract" else "DWR"
        conditions.append(f"Verify current contract status with {agency}")
        return StageResult(
            stage=STAGE_NAME, passed=True, score=0.85, finding="CONDITIONAL",
            reasoning=f"Contract water ({right_type}) — eWRIMS lookup not applicable",
            conditions=conditions, data=data,
        )

    # Pre-1914 rights — no SWRCB jurisdiction, but still verify
    if right_type == "appropriative_pre1914":
        data["verification_method"] = "pre1914_limited"
        data["note"] = "Pre-1914 rights are not tracked in eWRIMS; rely on seller documentation"
        conditions.append("Seller must provide documented proof of pre-1914 right")
        return StageResult(
            stage=STAGE_NAME, passed=True, score=0.80, finding="CONDITIONAL",
            reasoning="Pre-1914 right — not in eWRIMS, documentary proof required",
            conditions=conditions, data=data,
        )

    # Post-1914 appropriative — query eWRIMS
    rights_data = _lookup_ewrims(right_id, seller) if right_id else _from_seller(seller, "no_right_id")
    data["ewrims_record"] = rights_data
    data["verification_source"] = rights_data.get("source", "unknown")

    status = str(rights_data.get("status", "")).lower()
    data["right_status"] = status

    if "revoked" in status or "cancelled" in status:
        return StageResult(
            stage=STAGE_NAME, passed=False, score=0.0, finding="FAIL",
            reasoning=f"Water right {right_id} is {status} — cannot transfer",
            data=data,
        )

    if status not in ("active", "licensed", "permitted", "claimed"):
        risk_flags.append(f"Water right status '{status}' — may need SWRCB confirmation")

    # Face value check
    face_value = rights_data.get("face_value_af")
    try:
        face_value = float(face_value) if face_value else 0
    except (ValueError, TypeError):
        face_value = 0

    if face_value > 0:
        data["face_value_af"] = face_value
        if qty > face_value:
            risk_flags.append(
                f"Transfer ({qty:,.0f} AF) exceeds face value ({face_value:,.0f} AF)"
            )

    # Beneficial use check
    beneficial = seller.get("beneficial_use_af", 0)
    if beneficial and qty > beneficial:
        risk_flags.append(
            f"Transfer ({qty:,.0f} AF) exceeds reported beneficial use ({beneficial:,.0f} AF)"
        )

    score = 1.0
    if rights_data.get("source") != "ewrims_api":
        score -= 0.10
    score -= 0.08 * len(risk_flags)
    score = max(0.2, score)

    return StageResult(
        stage=STAGE_NAME, passed=True, score=round(score, 2),
        finding="CONDITIONAL" if risk_flags or conditions else "PASS",
        reasoning=(
            f"Right {right_id}: {status} (source: {rights_data.get('source', '?')}), "
            f"face value: {face_value:,.0f} AF"
        ),
        conditions=conditions, risk_flags=risk_flags, data=data,
    )
