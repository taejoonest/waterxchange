"""
Groundwater Stage 7 — Decision Synthesis

Aggregates all stage results into a final decision with weighted scoring.
"""

from typing import Any, Dict, List, Optional
from .base import StageResult

STAGE_NAME = "decision"

DEFAULT_WEIGHTS = {
    "intake_validation":  0.10,
    "allocation_check":   0.15,
    "gsp_compliance":     0.20,
    "well_impact":        0.20,
    "basin_health":       0.15,
    "cross_gsa":          0.10,
    "sw_intake_validation": 0.10,
    "sw_rights_verification": 0.20,
    "sw_no_injury":       0.25,
    "sw_environmental":   0.20,
    "sw_conveyance":      0.15,
}


def run(
    stage_results: List[StageResult],
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Synthesize a final decision from stage results."""
    w = weights or DEFAULT_WEIGHTS

    all_conditions = []
    all_risk_flags = []
    all_monitoring = []
    all_data = {}

    any_failed = False
    weighted_sum = 0.0
    weight_total = 0.0

    stage_dicts = []
    for sr in stage_results:
        d = sr.__dict__ if hasattr(sr, "__dict__") else sr
        stage_dicts.append(d)

        stage_name = d.get("stage", "")
        score = d.get("score", 0)
        passed = d.get("passed", True)

        stage_weight = w.get(stage_name, 0.10)
        weighted_sum += score * stage_weight
        weight_total += stage_weight

        if not passed:
            any_failed = True

        all_conditions.extend(d.get("conditions", []))
        all_risk_flags.extend(d.get("risk_flags", []))
        all_monitoring.extend(d.get("monitoring", []))

    composite = weighted_sum / weight_total if weight_total > 0 else 0.0

    # Decision logic
    if any_failed:
        decision = "DENIED"
    elif composite >= 0.75 and not all_conditions:
        decision = "APPROVED"
    elif composite >= 0.50:
        decision = "CONDITIONALLY_APPROVED"
    else:
        decision = "DENIED"

    # Deduplicate
    conditions = list(dict.fromkeys(all_conditions))
    risk_flags = list(dict.fromkeys(all_risk_flags))
    monitoring = list(dict.fromkeys(all_monitoring))

    return {
        "decision": decision,
        "composite_score": round(composite, 3),
        "stage_results": stage_dicts,
        "conditions": conditions,
        "risk_flags": risk_flags,
        "monitoring_requirements": monitoring,
    }
