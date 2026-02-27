"""
Groundwater Transfer Pipeline — orchestrates all GW stages.

Stages:
  1. Intake Validation
  2. Allocation Check
  3. GSP Compliance
  4. Well Impact (Theis drawdown)
  5. Basin Health
  6. Cross-GSA Coordination
  7. Decision Synthesis
"""

from typing import Any, Dict, Optional

from services.stages import (
    s1_intake, s2_allocation, s3_gsp_compliance,
    s4_well_impact, s5_basin_health, s6_cross_gsa, s7_decision,
)
from services.spatial_data import get_well_impact_data
from services.transfer_llm import analyze_transfer, generate_report


def run_groundwater_pipeline(
    seller: Dict[str, Any],
    buyer: Dict[str, Any],
    transfer: Dict[str, Any],
    knowledge_graph=None,
) -> Dict[str, Any]:
    """Execute the full groundwater transfer approval pipeline."""

    # Stage 1: Intake Validation
    r1 = s1_intake.run(seller, buyer, transfer)
    if not r1.passed:
        return _early_deny(r1)

    # Stage 2: Allocation Check
    r2 = s2_allocation.run(seller, buyer, transfer)

    # Stage 3: GSP Compliance
    r3 = s3_gsp_compliance.run(seller, buyer, transfer, knowledge_graph=knowledge_graph)

    # Stage 4: Well Impact (with spatial data)
    spatial = get_well_impact_data(
        seller.get("well_lat"), seller.get("well_lng"),
        buyer.get("well_lat"), buyer.get("well_lng"),
    )
    r4 = s4_well_impact.run(seller, buyer, transfer, spatial_data=spatial)

    # Stage 5: Basin Health
    r5 = s5_basin_health.run(seller, buyer, transfer)

    # Stage 6: Cross-GSA
    r6 = s6_cross_gsa.run(seller, buyer, transfer)

    # Stage 7: Decision Synthesis
    all_stages = [r1, r2, r3, r4, r5, r6]
    result = s7_decision.run(all_stages)

    # LLM analysis
    tier = "complex" if _needs_complex_review(transfer, all_stages) else "routine"
    llm = analyze_transfer(seller, buyer, transfer, all_stages, tier=tier)
    result["llm_analysis"] = llm

    # Generate report
    result["llm_report"] = generate_report(
        seller, buyer, transfer,
        result["decision"], result["composite_score"],
        all_stages, result["conditions"], result["risk_flags"],
    )

    result["pipeline_type"] = "groundwater"
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
        "pipeline_type": "groundwater",
    }


def _needs_complex_review(transfer, stages) -> bool:
    if transfer.get("quantity_af", 0) > 5000:
        return True
    src = transfer.get("source_gsa", "")
    dst = transfer.get("destination_gsa", "")
    if src and dst and src.lower() != dst.lower():
        return True
    for s in stages:
        if not s.passed:
            return True
    return False
