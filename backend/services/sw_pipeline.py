"""
Surface Water Transfer Pipeline — orchestrates all SW stages.

Stages:
  1. Intake Validation
  2. Rights Verification (eWRIMS API)
  3. No-Injury Analysis (USGS + eWRIMS + consumptive use)
  4. Environmental Compliance (CEQA, ESA, W&S, Delta)
  5. Conveyance & Infrastructure
"""

from typing import Any, Dict

from services.stages import (
    sw1_intake, sw2_rights_verification, sw3_no_injury,
    sw4_environmental, sw5_conveyance, s7_decision,
)
from services.transfer_llm import analyze_transfer, generate_report


def run_surface_water_pipeline(
    seller: Dict[str, Any],
    buyer: Dict[str, Any],
    transfer: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute the full surface water transfer approval pipeline."""

    # Stage 1: Intake Validation
    r1 = sw1_intake.run(seller, buyer, transfer)
    if not r1.passed:
        return _early_deny(r1)

    # Stage 2: Rights Verification
    r2 = sw2_rights_verification.run(seller, buyer, transfer)
    if not r2.passed:
        return _early_deny(r2)

    # Stage 3: No-Injury Analysis
    r3 = sw3_no_injury.run(seller, buyer, transfer)

    # Stage 4: Environmental Compliance
    r4 = sw4_environmental.run(seller, buyer, transfer)

    # Stage 5: Conveyance
    r5 = sw5_conveyance.run(seller, buyer, transfer)

    # Decision
    all_stages = [r1, r2, r3, r4, r5]
    result = s7_decision.run(all_stages)

    # LLM analysis
    tier = "complex" if _needs_complex_review(seller, transfer) else "routine"
    llm = analyze_transfer(seller, buyer, transfer, all_stages, tier=tier)
    result["llm_analysis"] = llm

    result["llm_report"] = generate_report(
        seller, buyer, transfer,
        result["decision"], result["composite_score"],
        all_stages, result["conditions"], result["risk_flags"],
    )

    result["pipeline_type"] = "surface_water"
    return result


def _early_deny(stage_result) -> Dict:
    d = stage_result.__dict__
    return {
        "decision": "DENIED",
        "composite_score": 0.0,
        "stage_results": [d],
        "conditions": d.get("conditions", []),
        "risk_flags": d.get("risk_flags", []),
        "monitoring_requirements": [],
        "llm_analysis": {},
        "llm_report": f"DENIED at {d['stage']}: {d['reasoning']}",
        "pipeline_type": "surface_water",
    }


def _needs_complex_review(seller, transfer) -> bool:
    right_type = seller.get("water_right_type", "")
    if right_type == "appropriative_post1914":
        return True
    if transfer.get("quantity_af", 0) > 5000:
        return True
    if transfer.get("through_delta", False):
        return True
    return False
