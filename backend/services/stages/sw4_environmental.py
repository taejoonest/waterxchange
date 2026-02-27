"""
Surface Water Stage 4 — Environmental Compliance

Checks CEQA/NEPA requirements, ESA considerations,
Wild & Scenic Rivers, Delta Plan consistency, and
area-of-origin protections.
"""

from typing import Any, Dict
from .base import StageResult

STAGE_NAME = "sw_environmental"

WILD_SCENIC_CA = {
    "eel river", "smith river", "klamath river", "trinity river",
    "american river (north fork)", "american river (south fork)",
    "merced river (south fork)", "tuolumne river (main stem above hetch hetchy)",
    "kern river (north fork)", "kings river (middle fork)", "kings river (south fork)",
}

CRITICAL_HABITAT_STREAMS = {
    "sacramento river": ["winter-run Chinook salmon", "delta smelt"],
    "san joaquin river": ["spring-run Chinook salmon"],
    "american river": ["steelhead trout", "fall-run Chinook"],
    "feather river": ["spring-run Chinook salmon"],
    "stanislaus river": ["steelhead trout"],
    "mokelumne river": ["fall-run Chinook", "steelhead trout"],
}


def run(seller: Dict[str, Any], buyer: Dict[str, Any], transfer: Dict[str, Any]) -> StageResult:
    conditions = []
    risk_flags = []
    data = {}

    qty = transfer.get("quantity_af", 0)
    source_stream = transfer.get("source_stream", "").lower().strip()
    duration = transfer.get("duration_days", 365)
    through_delta = transfer.get("through_delta", False)
    anadromous = transfer.get("anadromous_fish_present", False)
    is_export = transfer.get("is_area_of_origin_export", False)
    gw_sub = transfer.get("groundwater_substitution", False)

    data["source_stream"] = source_stream
    data["through_delta"] = through_delta
    data["anadromous_fish_present"] = anadromous
    data["is_area_of_origin_export"] = is_export

    # CEQA determination
    if duration <= 365 and qty <= 1000:
        data["ceqa_category"] = "Categorical Exemption likely (Class 7 — small transfer)"
        conditions.append("Verify CEQA categorical exemption eligibility with lead agency")
    elif duration <= 365:
        data["ceqa_category"] = "Negative Declaration likely for temporary transfer"
        conditions.append("Prepare Initial Study / Negative Declaration")
    else:
        data["ceqa_category"] = "EIR may be required for long-term change"
        conditions.append("Prepare Environmental Impact Report (EIR)")
        risk_flags.append("Long-term transfer likely requires full EIR (6-18 months)")

    # Wild & Scenic Rivers check
    is_wild_scenic = any(ws in source_stream for ws in WILD_SCENIC_CA)
    data["wild_scenic_river"] = is_wild_scenic
    if is_wild_scenic:
        risk_flags.append(
            f"Source stream appears to be a Wild & Scenic River — "
            "additional federal review required (16 USC §1271)"
        )
        conditions.append("Wild & Scenic Rivers Act consistency determination required")

    # Critical habitat / ESA
    species = CRITICAL_HABITAT_STREAMS.get(source_stream, [])
    if anadromous or species:
        all_species = list(set(species))
        if anadromous and not species:
            all_species = ["unspecified anadromous species"]
        data["listed_species"] = all_species
        risk_flags.append(
            f"ESA-listed species on source stream: {', '.join(all_species)}"
        )
        conditions.append(
            "CDFW and/or NMFS consultation required — transfer timing "
            "must avoid critical spawning and migration periods"
        )

    # Delta transfer requirements
    if through_delta:
        data["delta_plan_applies"] = True
        conditions.append(
            "Delta Plan consistency required (Water Code §85057.5). "
            "Must comply with SWRCB D-1641 flow objectives."
        )
        risk_flags.append(
            "Through-delta transfer may be limited by biological opinions "
            "for delta smelt (BO 2019) and winter-run salmon"
        )
        conditions.append(
            "DWR and USBR must approve conveyance through Delta facilities"
        )

    # Area of origin
    if is_export:
        conditions.append(
            "Area-of-origin protections apply (CWC §§10505-10505.5): "
            "county of origin retains priority for reasonable beneficial use"
        )
        risk_flags.append("Export transfer — county of origin may file protest")

    # GW substitution
    if gw_sub:
        conditions.append(
            "Groundwater substitution transfer requires monitoring of "
            "groundwater impacts and compliance with local GSP"
        )
        risk_flags.append("Combined surface/groundwater review required")

    # NEPA (federal nexus)
    right_type = seller.get("water_right_type", "")
    if right_type in ("cvp_contract", "swp_contract"):
        data["nepa_required"] = True
        conditions.append("NEPA compliance required — federal water contract involved")

    score = 1.0
    if is_wild_scenic:
        score -= 0.20
    if through_delta:
        score -= 0.15
    if species:
        score -= 0.10
    if is_export:
        score -= 0.10
    if duration > 365:
        score -= 0.05
    score -= 0.03 * len(risk_flags)
    score = max(0.15, score)

    finding = "CONDITIONAL" if conditions else "PASS"

    return StageResult(
        stage=STAGE_NAME, passed=True, score=round(score, 2),
        finding=finding,
        reasoning=(
            f"Stream: {source_stream or 'unspecified'}; "
            f"CEQA: {data.get('ceqa_category', 'TBD')}; "
            f"{len(species)} listed species; "
            f"{'Delta' if through_delta else 'Non-delta'}"
        ),
        conditions=conditions, risk_flags=risk_flags, data=data,
    )
