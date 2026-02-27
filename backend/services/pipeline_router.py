"""
Pipeline Router — master dispatcher for all transfer types.

Uses regulatory_data.determine_pathway() to select the correct
sub-pipeline, then runs the appropriate stages and produces
a unified result with pathway metadata.
"""

from typing import Any, Dict, Optional

from services.regulatory_data import (
    RegulatoryPathway, determine_pathway, get_pathway_description,
    is_adjudicated_basin, get_watermaster, WATER_CODE,
)
from services.stages import (
    s1_intake, s2_allocation, s3_gsp_compliance,
    s4_well_impact, s5_basin_health, s6_cross_gsa,
    s7_decision,
    sw1_intake, sw2_rights_verification, sw3_no_injury,
    sw4_environmental, sw5_conveyance,
)
from services.spatial_data import get_well_impact_data
from services.transfer_llm import analyze_transfer, generate_report


PATHWAY_WEIGHTS = {
    RegulatoryPathway.GW_SGMA: {
        "intake_validation": 0.10, "allocation_check": 0.15,
        "gsp_compliance": 0.25, "well_impact": 0.20,
        "basin_health": 0.15, "cross_gsa": 0.15,
    },
    RegulatoryPathway.GW_ADJUDICATED: {
        "intake_validation": 0.10, "allocation_check": 0.20,
        "well_impact": 0.25, "basin_health": 0.15,
    },
    RegulatoryPathway.GW_BANKED: {
        "intake_validation": 0.15, "allocation_check": 0.35,
        "basin_health": 0.20, "well_impact": 0.15,
    },
    RegulatoryPathway.GW_IN_LIEU: {
        "intake_validation": 0.10, "allocation_check": 0.25,
        "gsp_compliance": 0.20, "well_impact": 0.20,
        "basin_health": 0.15, "cross_gsa": 0.10,
    },
    RegulatoryPathway.GW_PROTECTED_EXPORT: {
        "intake_validation": 0.10, "allocation_check": 0.15,
        "gsp_compliance": 0.20, "well_impact": 0.15,
        "basin_health": 0.25, "cross_gsa": 0.15,
    },
    RegulatoryPathway.PRE1914_PRIVATE: {
        "sw_intake_validation": 0.15, "sw_no_injury": 0.35,
        "sw_environmental": 0.25, "sw_conveyance": 0.25,
    },
    RegulatoryPathway.CONTRACT_CVP_SWP: {
        "sw_intake_validation": 0.15, "sw_rights_verification": 0.20,
        "sw_environmental": 0.30, "sw_conveyance": 0.20,
    },
    RegulatoryPathway.POST1914_SHORT: {
        "sw_intake_validation": 0.10, "sw_rights_verification": 0.20,
        "sw_no_injury": 0.25, "sw_environmental": 0.20,
        "sw_conveyance": 0.15,
    },
    RegulatoryPathway.POST1914_LONG: {
        "sw_intake_validation": 0.10, "sw_rights_verification": 0.20,
        "sw_no_injury": 0.25, "sw_environmental": 0.25,
        "sw_conveyance": 0.15,
    },
    RegulatoryPathway.IMPORTED_WATER: {
        "sw_intake_validation": 0.15, "sw_environmental": 0.35,
        "sw_conveyance": 0.30,
    },
}


def run_routed_pipeline(
    seller: Dict[str, Any],
    buyer: Dict[str, Any],
    transfer: Dict[str, Any],
    knowledge_graph=None,
) -> Dict[str, Any]:
    """Route transfer to appropriate pipeline and execute it."""

    pathway = determine_pathway(seller, buyer, transfer)
    weights = PATHWAY_WEIGHTS.get(pathway)

    # Select and run the right sub-pipeline
    if pathway in (
        RegulatoryPathway.GW_SGMA,
        RegulatoryPathway.GW_IN_LIEU,
    ):
        stages = _run_gw_sgma(seller, buyer, transfer, knowledge_graph)
    elif pathway == RegulatoryPathway.GW_ADJUDICATED:
        stages = _run_gw_adjudicated(seller, buyer, transfer, knowledge_graph)
    elif pathway == RegulatoryPathway.GW_BANKED:
        stages = _run_gw_banked(seller, buyer, transfer, knowledge_graph)
    elif pathway == RegulatoryPathway.GW_PROTECTED_EXPORT:
        stages = _run_gw_protected_export(seller, buyer, transfer, knowledge_graph)
    elif pathway == RegulatoryPathway.PRE1914_PRIVATE:
        stages = _run_pre1914(seller, buyer, transfer)
    elif pathway == RegulatoryPathway.CONTRACT_CVP_SWP:
        stages = _run_contract(seller, buyer, transfer)
    elif pathway in (RegulatoryPathway.POST1914_SHORT, RegulatoryPathway.POST1914_LONG):
        stages = _run_post1914(seller, buyer, transfer)
    elif pathway == RegulatoryPathway.IMPORTED_WATER:
        stages = _run_imported(seller, buyer, transfer)
    else:
        stages = _run_gw_sgma(seller, buyer, transfer, knowledge_graph)

    result = s7_decision.run(stages, weights=weights)

    # LLM analysis
    tier = "complex" if _needs_complex(pathway, transfer) else "routine"
    llm = analyze_transfer(seller, buyer, transfer, stages, tier=tier)
    result["llm_analysis"] = llm

    result["llm_report"] = generate_report(
        seller, buyer, transfer,
        result["decision"], result["composite_score"],
        stages, result["conditions"], result["risk_flags"],
    )

    # Attach pathway metadata
    result["pathway"] = pathway
    result["pathway_info"] = {
        "pathway": pathway,
        "description": get_pathway_description(pathway),
        "legal_basis": _get_legal_basis(pathway),
    }
    result["pipeline_type"] = "auto_routed"

    return result


def _get_legal_basis(pathway: str) -> list:
    mapping = {
        RegulatoryPathway.GW_SGMA: ["CWC §10726.4", "SGMA §10720-10737.8"],
        RegulatoryPathway.GW_ADJUDICATED: ["Court decree", "CWC §10726.4"],
        RegulatoryPathway.GW_BANKED: ["Banking agreement", "CWC §10726.4"],
        RegulatoryPathway.GW_IN_LIEU: ["CWC §10726.4", "SGMA §10720-10737.8"],
        RegulatoryPathway.GW_PROTECTED_EXPORT: ["CWC §1215-1220", "CWC §10726.4(a)(2)"],
        RegulatoryPathway.PRE1914_PRIVATE: ["Pre-1914 common law", "CWC §1702 (no injury)"],
        RegulatoryPathway.CONTRACT_CVP_SWP: ["Reclamation Act", "Burns-Porter Act", "CWC §1810"],
        RegulatoryPathway.POST1914_SHORT: ["CWC §1725-1732", "CWC §1702"],
        RegulatoryPathway.POST1914_LONG: ["CWC §1700-1707", "CWC §1702"],
        RegulatoryPathway.IMPORTED_WATER: ["CWC §1011"],
    }
    codes = mapping.get(pathway, [])
    return [{"code": c, "description": WATER_CODE.get(c, c)} for c in codes]


def _needs_complex(pathway, transfer):
    if pathway in (RegulatoryPathway.POST1914_LONG, RegulatoryPathway.GW_PROTECTED_EXPORT):
        return True
    if transfer.get("quantity_af", 0) > 5000:
        return True
    return False


# ── Sub-pipeline runners ────────────────────────────────────

def _run_gw_sgma(seller, buyer, transfer, kg=None):
    r1 = s1_intake.run(seller, buyer, transfer)
    r2 = s2_allocation.run(seller, buyer, transfer)
    r3 = s3_gsp_compliance.run(seller, buyer, transfer, knowledge_graph=kg)
    spatial = get_well_impact_data(
        seller.get("well_lat"), seller.get("well_lng"),
        buyer.get("well_lat"), buyer.get("well_lng"),
    )
    r4 = s4_well_impact.run(seller, buyer, transfer, spatial_data=spatial)
    r5 = s5_basin_health.run(seller, buyer, transfer)
    r6 = s6_cross_gsa.run(seller, buyer, transfer)
    return [r1, r2, r3, r4, r5, r6]


def _run_gw_adjudicated(seller, buyer, transfer, kg=None):
    r1 = s1_intake.run(seller, buyer, transfer)
    r2 = s2_allocation.run(seller, buyer, transfer)
    spatial = get_well_impact_data(
        seller.get("well_lat"), seller.get("well_lng"),
        buyer.get("well_lat"), buyer.get("well_lng"),
    )
    r4 = s4_well_impact.run(seller, buyer, transfer, spatial_data=spatial)
    r5 = s5_basin_health.run(seller, buyer, transfer)

    wm = get_watermaster(seller.get("basin", ""))
    from services.stages.base import StageResult
    adj_stage = StageResult(
        stage="adjudicated_basin",
        passed=True,
        score=0.85,
        finding="CONDITIONAL",
        reasoning=f"Adjudicated basin — watermaster: {wm or 'unknown'}",
        conditions=[
            f"Watermaster approval required{' from ' + wm if wm else ''}",
            "Transfer must comply with court decree pumping rights",
        ],
        data={"watermaster": wm, "adjudicated": True},
    )
    return [r1, r2, adj_stage, r4, r5]


def _run_gw_banked(seller, buyer, transfer, kg=None):
    r1 = s1_intake.run(seller, buyer, transfer)
    r2 = s2_allocation.run(seller, buyer, transfer)
    spatial = get_well_impact_data(
        seller.get("well_lat"), seller.get("well_lng"),
        buyer.get("well_lat"), buyer.get("well_lng"),
    )
    r4 = s4_well_impact.run(seller, buyer, transfer, spatial_data=spatial)
    r5 = s5_basin_health.run(seller, buyer, transfer)
    return [r1, r2, r4, r5]


def _run_gw_protected_export(seller, buyer, transfer, kg=None):
    r1 = s1_intake.run(seller, buyer, transfer)
    r2 = s2_allocation.run(seller, buyer, transfer)
    r3 = s3_gsp_compliance.run(seller, buyer, transfer, knowledge_graph=kg)
    spatial = get_well_impact_data(
        seller.get("well_lat"), seller.get("well_lng"),
        buyer.get("well_lat"), buyer.get("well_lng"),
    )
    r4 = s4_well_impact.run(seller, buyer, transfer, spatial_data=spatial)
    r5 = s5_basin_health.run(seller, buyer, transfer)
    r6 = s6_cross_gsa.run(seller, buyer, transfer)

    from services.stages.base import StageResult
    export_stage = StageResult(
        stage="protected_export_review",
        passed=False,
        score=0.20,
        finding="FAIL",
        reasoning="Groundwater export from protected area restricted (CWC §1220)",
        conditions=[
            "County of origin must consent to export",
            "Demonstrate no adverse impact on basin sustainability",
        ],
        risk_flags=[
            "CWC §1215-1220: Protected area groundwater export restrictions",
            "May require legislative approval for large-volume exports",
        ],
        data={"legal_basis": "CWC §1215-1220"},
    )
    return [r1, r2, r3, r4, r5, r6, export_stage]


def _run_pre1914(seller, buyer, transfer):
    r1 = sw1_intake.run(seller, buyer, transfer)
    r3 = sw3_no_injury.run(seller, buyer, transfer)
    r4 = sw4_environmental.run(seller, buyer, transfer)
    r5 = sw5_conveyance.run(seller, buyer, transfer)

    from services.stages.base import StageResult
    pre1914_stage = StageResult(
        stage="pre1914_verification",
        passed=True,
        score=0.90,
        finding="PASS",
        reasoning="Pre-1914 right: no SWRCB petition needed, private transfer",
        conditions=[
            "Seller must provide documentary proof of pre-1914 right",
            "No-injury rule still applies — injured parties may file court action",
        ],
        data={"swrcb_approval_needed": False, "legal_basis": "Pre-1914 common law"},
    )
    return [r1, pre1914_stage, r3, r4, r5]


def _run_contract(seller, buyer, transfer):
    r1 = sw1_intake.run(seller, buyer, transfer)
    r2 = sw2_rights_verification.run(seller, buyer, transfer)
    r4 = sw4_environmental.run(seller, buyer, transfer)
    r5 = sw5_conveyance.run(seller, buyer, transfer)
    return [r1, r2, r4, r5]


def _run_post1914(seller, buyer, transfer):
    r1 = sw1_intake.run(seller, buyer, transfer)
    r2 = sw2_rights_verification.run(seller, buyer, transfer)
    r3 = sw3_no_injury.run(seller, buyer, transfer)
    r4 = sw4_environmental.run(seller, buyer, transfer)
    r5 = sw5_conveyance.run(seller, buyer, transfer)
    return [r1, r2, r3, r4, r5]


def _run_imported(seller, buyer, transfer):
    r1 = sw1_intake.run(seller, buyer, transfer)
    r4 = sw4_environmental.run(seller, buyer, transfer)
    r5 = sw5_conveyance.run(seller, buyer, transfer)

    from services.stages.base import StageResult
    imported_stage = StageResult(
        stage="imported_water_review",
        passed=True,
        score=0.90,
        finding="PASS",
        reasoning="Imported water generally faces fewer restrictions (CWC §1011)",
        conditions=["Verify water was legally imported and stored"],
        data={"legal_basis": "CWC §1011"},
    )
    return [r1, imported_stage, r4, r5]
