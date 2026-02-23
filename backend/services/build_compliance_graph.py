"""
WaterXchange Compliance Knowledge Graph Builder — v3

Two-tree architecture:
  Tree 1: LEGAL AUTHORITY (Governance)
    Statute → empowers → GSA → adopts → GSP → defines → Threshold → governs → AllocationRule
  
  Tree 2: PHYSICAL SYSTEM (Hydrology)
    Extraction/Recharge → affects → WaterBudget → determines → StorageChange → impacts → Indicator → measured_by → MonitoringNetwork
  
  Bridge Points (where the trees connect):
    - Indicator: evaluated by monitoring (Tree 2) AND constrained by threshold (Tree 1)
    - Threshold: defined by GSA (Tree 1) AND evaluated against indicator data (Tree 2)
    - AllocationRule: derived from water budget (Tree 2) AND governed by GSA (Tree 1)
  
  Transfer Compliance Chain:
    Transfer → constrained_by → AllocationRule
    Transfer → must_not_violate → MinimumThreshold (for each indicator)
    Transfer → evaluated_using → MonitoringData
    Transfer → reported_to → GSA
    Transfer → requires → Requirement (metering, notification, etc.)

NO edge may skip a layer. Every relationship must be semantically typed and directional.
"""

import json
from pathlib import Path


def build_compliance_graph() -> dict:
    """
    Build the compliance knowledge graph from scratch with strict ontology.
    Returns {"entities": [...], "relationships": [...]}.
    """

    entities = []
    relationships = []

    def add_entity(eid: str, etype: str, name: str, props: dict = None):
        entities.append({
            "id": eid,
            "type": etype,
            "name": name,
            "properties": props or {},
            "tree": "governance" if etype in GOVERNANCE_TYPES else
                    "hydrology" if etype in HYDROLOGY_TYPES else
                    "bridge"
        })

    def add_rel(source: str, target: str, rtype: str, props: dict = None):
        relationships.append({
            "source": source,
            "target": target,
            "type": rtype,
            "properties": props or {}
        })

    GOVERNANCE_TYPES = {"Statute", "GSA", "GSP", "AllocationRule", "Requirement", "EnforcementAction"}
    HYDROLOGY_TYPES = {"WaterBudgetComponent", "WaterBudget", "HydrogeologicUnit", "MonitoringNetwork", "MonitoringSite"}
    BRIDGE_TYPES = {"SustainabilityIndicator", "MinimumThreshold", "MeasurableObjective", "UndesirableResult",
                    "ManagementArea", "Transfer", "TransferRule"}

    # ══════════════════════════════════════════════════════════════
    # TREE 1: LEGAL AUTHORITY (GOVERNANCE)
    # ══════════════════════════════════════════════════════════════

    # ── Layer G1: Statutes ──
    statutes = [
        ("statute_sgma", "SGMA (Water Code §10720-10737.8)", {"enacted": "2014", "description": "Sustainable Groundwater Management Act"}),
        ("statute_10720", "WC §10720 — Legislative Intent", {"description": "Legislature intent for sustainable groundwater management"}),
        ("statute_10723", "WC §10723 — GSA Formation", {"description": "Requirements for forming a Groundwater Sustainability Agency"}),
        ("statute_10725", "WC §10725 — GSA Powers", {"description": "Powers and authorities granted to GSAs"}),
        ("statute_10725_2", "WC §10725.2 — Extraction Metering", {"description": "GSA may require extraction facilities to have meters"}),
        ("statute_10726_4", "WC §10726.4 — Allocation & Transfers", {"description": "GSA authority to regulate groundwater extraction and allocations"}),
        ("statute_10727", "WC §10727 — GSP Requirements", {"description": "Contents of Groundwater Sustainability Plans"}),
        ("statute_10727_2", "WC §10727.2 — Sustainability Criteria", {"description": "GSP must establish sustainability criteria for 6 indicators"}),
        ("statute_10728_2", "WC §10728.2 — Annual Reporting", {"description": "GSP annual reporting requirements"}),
        ("statute_10732", "WC §10732 — Enforcement", {"description": "GSA enforcement powers for GSP implementation"}),
        ("statute_10735", "WC §10735 — State Intervention", {"description": "State Water Board intervention for critically overdrafted basins"}),
    ]
    for sid, sname, sprops in statutes:
        add_entity(sid, "Statute", sname, sprops)

    # ── Layer G2: GSAs (Kern County Subbasin has ~15 GSAs) ──
    gsas = [
        ("gsa_rosedale", "Rosedale-Rio Bravo Water Storage District GSA", {"area": "Northwest Kern"}),
        ("gsa_semitropic", "Semitropic Water Storage District GSA", {"area": "North-central Kern"}),
        ("gsa_shafter_wasco", "Shafter-Wasco Irrigation District GSA", {"area": "North Kern"}),
        ("gsa_north_kern", "North Kern Water Storage District GSA", {"area": "North Kern"}),
        ("gsa_kern_delta", "Kern Delta Water District GSA", {"area": "South-central Kern"}),
        ("gsa_wheeler_ridge", "Wheeler Ridge-Maricopa Water Storage District GSA", {"area": "South Kern"}),
        ("gsa_buena_vista", "Buena Vista Water Storage District GSA", {"area": "Central Kern"}),
        ("gsa_kern_water_bank", "Kern Water Bank Authority GSA", {"area": "Southwest Kern"}),
        ("gsa_tejon_castac", "Tejon-Castac Water District GSA", {"area": "Southeast Kern"}),
        ("gsa_west_kern", "West Kern Water District GSA", {"area": "West Kern"}),
        ("gsa_olcese", "Olcese Water District GSA", {"area": "Northeast Kern"}),
    ]
    for gid, gname, gprops in gsas:
        add_entity(gid, "GSA", gname, gprops)

    # Statute → empowers → GSA
    for gid, _, _ in gsas:
        add_rel("statute_10723", gid, "EMPOWERS", {"scope": "formation and authority"})
        add_rel("statute_10725", gid, "GRANTS_AUTHORITY", {"scope": "powers to manage groundwater"})
        add_rel("statute_10726_4", gid, "AUTHORIZES", {"scope": "regulate extraction and allocations"})

    # ── Layer G3: GSP ──
    add_entity("kern_gsp", "GSP", "Kern County Subbasin GSP 2025", {
        "adopted": "August 2025", "basin_number": "5-22.14",
        "priority": "Critically Overdrafted", "deadline": "2040"
    })

    # GSA → adopts → GSP (coordinated plan — all GSAs adopt the same GSP)
    for gid, _, _ in gsas:
        add_rel(gid, "kern_gsp", "ADOPTS")

    # Statute → mandates → GSP
    add_rel("statute_10727", "kern_gsp", "MANDATES", {"scope": "GSP content requirements"})
    add_rel("statute_10727_2", "kern_gsp", "REQUIRES_CRITERIA", {"scope": "sustainability criteria for 6 indicators"})

    # ── Layer G4: Allocation Rules (per GSA) ──
    # Each GSA has its own allocation methodology
    allocation_rules = [
        ("alloc_rosedale", "gsa_rosedale", "Rosedale-Rio Bravo Allocation Framework", {"method": "historical pumping basis"}),
        ("alloc_semitropic", "gsa_semitropic", "Semitropic Allocation Framework", {"method": "acreage-based allocation"}),
        ("alloc_shafter_wasco", "gsa_shafter_wasco", "Shafter-Wasco Allocation Framework", {"method": "proportional to irrigated acres"}),
        ("alloc_north_kern", "gsa_north_kern", "North Kern Allocation Framework", {"method": "contract-based"}),
        ("alloc_kern_delta", "gsa_kern_delta", "Kern Delta Allocation Framework", {"method": "historical use basis"}),
    ]
    for aid, gid, aname, aprops in allocation_rules:
        add_entity(aid, "AllocationRule", aname, aprops)
        add_rel(gid, aid, "GOVERNS")
        add_rel("kern_gsp", aid, "ESTABLISHES")
        add_rel("statute_10726_4", aid, "AUTHORIZES")

    # ── Layer G5: Requirements ──
    requirements = [
        ("req_metering", "Well Metering", {"statute": "WC §10725.2", "description": "All extraction wells must be metered"}),
        ("req_reporting", "Annual Extraction Reporting", {"statute": "WC §10728.2", "description": "Report extraction volumes annually"}),
        ("req_notification", "GSA Transfer Notification", {"description": "Both GSAs must be notified of inter-GSA transfers"}),
        ("req_accounting", "Transfer Accounting", {"description": "Transfer must be recorded in both GSA allocation ledgers"}),
        ("req_monitoring_compliance", "Post-Transfer Monitoring", {"description": "Monitor water levels and quality after transfer"}),
    ]
    for rid, rname, rprops in requirements:
        add_entity(rid, "Requirement", rname, rprops)

    # Statute → mandates → Requirement
    add_rel("statute_10725_2", "req_metering", "MANDATES")
    add_rel("statute_10728_2", "req_reporting", "MANDATES")
    add_rel("statute_10726_4", "req_notification", "MANDATES")

    # ── Layer G6: Enforcement ──
    add_entity("enforce_gsa", "EnforcementAction", "GSA Enforcement (fees, penalties, curtailment)", {
        "statute": "WC §10732"
    })
    add_entity("enforce_state", "EnforcementAction", "State Water Board Intervention", {
        "statute": "WC §10735", "trigger": "Inadequate GSP implementation"
    })
    add_rel("statute_10732", "enforce_gsa", "ENABLES")
    add_rel("statute_10735", "enforce_state", "ENABLES")
    for gid, _, _ in gsas:
        add_rel(gid, "enforce_gsa", "MAY_INVOKE")

    # ══════════════════════════════════════════════════════════════
    # TREE 2: PHYSICAL SYSTEM (HYDROLOGY)
    # ══════════════════════════════════════════════════════════════

    # ── Layer H1: Water Budget Components ──
    wb_components = [
        ("wb_extraction", "Groundwater Extraction", {"wy2024": "1,950,000 AF", "direction": "outflow"}),
        ("wb_recharge_natural", "Natural Recharge (Deep Percolation)", {"wy2024": "700,000 AF", "direction": "inflow"}),
        ("wb_recharge_applied", "Applied/Managed Recharge", {"wy2024": "350,000 AF", "direction": "inflow"}),
        ("wb_surface_inflow", "Surface Water Inflow", {"wy2024": "620,000 AF", "direction": "inflow"}),
        ("wb_subsurface_inflow", "Subsurface Inflow", {"wy2024": "180,000 AF", "direction": "inflow"}),
        ("wb_subsurface_outflow", "Subsurface Outflow", {"wy2024": "120,000 AF", "direction": "outflow"}),
        ("wb_riparian_et", "Riparian & GDE Evapotranspiration", {"wy2024": "130,000 AF", "direction": "outflow"}),
    ]
    for wid, wname, wprops in wb_components:
        add_entity(wid, "WaterBudgetComponent", wname, wprops)

    # ── Layer H2: Water Budget ──
    add_entity("water_budget", "WaterBudget", "Kern Subbasin Water Budget", {
        "total_inflow": "1,850,000 AF", "total_outflow": "2,200,000 AF",
        "change_in_storage": "-350,000 AF", "sustainable_yield": "1,650,000 AF",
        "current_overdraft": "300,000 AF/yr"
    })
    for wid, _, _ in wb_components:
        add_rel(wid, "water_budget", "CONTRIBUTES_TO")

    # Water Budget → determines → Sustainable Yield
    add_entity("sustainable_yield", "HydrogeologicUnit", "Sustainable Yield Estimate", {
        "value": "1,650,000 AF/yr", "basis": "50-year projected water budget"
    })
    add_rel("water_budget", "sustainable_yield", "DETERMINES")

    # ── Layer H3: Hydrogeologic Units ──
    hydro_units = [
        ("hgu_upper_aquifer", "Upper Aquifer System", {"depth": "0-260 ft", "description": "Above Corcoran Clay"}),
        ("hgu_corcoran_clay", "Corcoran Clay (E-clay)", {"depth": "~240-280 ft", "description": "Confining layer, subsidence-critical"}),
        ("hgu_lower_aquifer", "Lower Aquifer System", {"depth": "260-600+ ft", "description": "Below Corcoran Clay"}),
        ("hgu_kern_river_fan", "Kern River Fan", {"description": "Primary recharge area"}),
        ("hgu_tulare_formation", "Tulare Formation", {"description": "Main water-bearing formation"}),
    ]
    for hid, hname, hprops in hydro_units:
        add_entity(hid, "HydrogeologicUnit", hname, hprops)

    # ── Layer H4: Management Areas (HCM Areas in Kern GSP) ──
    management_areas = [
        ("ma_rosedale", "Rosedale HCM Area", {"gsa": "gsa_rosedale", "description": "Northwest, primary banking area"}),
        ("ma_semitropic", "Semitropic HCM Area", {"gsa": "gsa_semitropic", "description": "North-central, subsidence concern"}),
        ("ma_shafter_wasco", "Shafter-Wasco HCM Area", {"gsa": "gsa_shafter_wasco", "description": "North"}),
        ("ma_north_kern", "North Kern HCM Area", {"gsa": "gsa_north_kern", "description": "North, Kern River channel"}),
        ("ma_kern_delta", "Kern Delta HCM Area", {"gsa": "gsa_kern_delta", "description": "South-central"}),
        ("ma_kern_fan", "Kern Fan HCM Area", {"gsa": "gsa_buena_vista", "description": "Central, primary recharge zone"}),
        ("ma_white_wolf", "White Wolf HCM Area", {"gsa": "gsa_wheeler_ridge", "description": "South, near mountain front"}),
        ("ma_west_kern", "West Kern HCM Area", {"gsa": "gsa_west_kern", "description": "West, oil production area"}),
    ]
    for mid, mname, mprops in management_areas:
        add_entity(mid, "ManagementArea", mname, mprops)
        # GSA → manages → ManagementArea
        add_rel(mprops["gsa"], mid, "MANAGES")
        # Water Budget → evaluated in → ManagementArea
        add_rel("water_budget", mid, "EVALUATED_IN")

    # ── Layer H5: Monitoring Networks (per indicator) ──
    monitoring_networks = [
        ("mon_gw_levels", "Groundwater Level Monitoring Network", {"indicator": "Chronic Lowering of GW Levels", "sites": "~200 wells"}),
        ("mon_storage", "Storage Change Monitoring Network", {"indicator": "Reduction in GW Storage", "method": "water budget + level change"}),
        ("mon_subsidence", "Subsidence Monitoring Network", {"indicator": "Land Subsidence", "method": "InSAR, extensometers, GPS benchmarks"}),
        ("mon_water_quality", "Water Quality Monitoring Network", {"indicator": "Degraded Water Quality", "parameters": "nitrate, arsenic, TDS, 1,2,3-TCP"}),
        ("mon_isw", "Interconnected Surface Water Monitoring", {"indicator": "ISW Depletion", "method": "stream gauges, shallow wells"}),
    ]
    for mid, mname, mprops in monitoring_networks:
        add_entity(mid, "MonitoringNetwork", mname, mprops)

    # Monitoring Network → located_in → Management Areas
    for mid, _, _ in monitoring_networks:
        for maid, _, _ in management_areas:
            add_rel(mid, maid, "OPERATES_IN")

    # ══════════════════════════════════════════════════════════════
    # BRIDGE: Where the two trees connect
    # ══════════════════════════════════════════════════════════════

    # ── Bridge B1: Sustainability Indicators ──
    # (Connected to BOTH trees)
    indicators = [
        ("ind_gw_levels", "Chronic Lowering of Groundwater Levels", {"sgma_section": "10727.2(b)(1)", "monitoring": "mon_gw_levels"}),
        ("ind_storage", "Reduction in Groundwater Storage", {"sgma_section": "10727.2(b)(2)", "monitoring": "mon_storage"}),
        ("ind_subsidence", "Land Subsidence", {"sgma_section": "10727.2(b)(3)", "monitoring": "mon_subsidence"}),
        ("ind_water_quality", "Degraded Water Quality", {"sgma_section": "10727.2(b)(4)", "monitoring": "mon_water_quality"}),
        ("ind_isw", "Depletion of Interconnected Surface Water", {"sgma_section": "10727.2(b)(6)", "monitoring": "mon_isw"}),
    ]
    for iid, iname, iprops in indicators:
        add_entity(iid, "SustainabilityIndicator", iname, iprops)
        # Tree 2 connection: MonitoringNetwork → measures → Indicator
        add_rel(iprops["monitoring"], iid, "MEASURES")
        # Tree 1 connection: GSP → establishes_criteria_for → Indicator
        add_rel("kern_gsp", iid, "ESTABLISHES_CRITERIA_FOR")
        # Statute mandates tracking this indicator
        add_rel("statute_10727_2", iid, "REQUIRES_TRACKING")

    # Indicator → evaluated_in → ManagementArea
    for iid, _, _ in indicators:
        for maid, _, _ in management_areas:
            add_rel(iid, maid, "EVALUATED_IN")

    # Extraction specifically impacts indicators
    add_rel("wb_extraction", "ind_gw_levels", "DIRECTLY_IMPACTS")
    add_rel("wb_extraction", "ind_storage", "DIRECTLY_IMPACTS")
    add_rel("wb_extraction", "ind_subsidence", "CONTRIBUTES_TO")
    add_rel("wb_extraction", "ind_water_quality", "MAY_AFFECT")

    # ── Bridge B2: Thresholds & Objectives ──
    # Defined by GSAs (Tree 1), evaluated against Indicator data (Tree 2)
    # In Kern GSP, thresholds are set per management area per indicator
    threshold_defs = [
        # (id, name, indicator, management_area, gsa, value)
        ("mt_gw_rosedale", "GW Level MT — Rosedale", "ind_gw_levels", "ma_rosedale", "gsa_rosedale",
         {"value": "Historical low (2015-2016)", "metric": "depth to water"}),
        ("mt_gw_semitropic", "GW Level MT — Semitropic", "ind_gw_levels", "ma_semitropic", "gsa_semitropic",
         {"value": "Historical low (2015-2016)", "metric": "depth to water"}),
        ("mt_sub_semitropic", "Subsidence MT — Semitropic", "ind_subsidence", "ma_semitropic", "gsa_semitropic",
         {"value": "Projected to 2040 not exceeding loss of conveyance capacity", "rate": "avg 2015-2023 rate"}),
        ("mt_sub_kern_fan", "Subsidence MT — Kern Fan", "ind_subsidence", "ma_kern_fan", "gsa_buena_vista",
         {"value": "Projected to 2040 not exceeding loss of conveyance capacity"}),
        ("mt_wq_nitrate", "Water Quality MT — Nitrate", "ind_water_quality", "ma_semitropic", "gsa_semitropic",
         {"value": "10 mg/L (MCL)", "parameter": "nitrate as N"}),
        ("mt_wq_arsenic", "Water Quality MT — Arsenic", "ind_water_quality", "ma_kern_delta", "gsa_kern_delta",
         {"value": "10 µg/L (MCL)", "parameter": "arsenic"}),
        ("mt_storage", "Storage MT — Basin-wide", "ind_storage", "ma_rosedale", "gsa_rosedale",
         {"value": "Not to exceed cumulative overdraft that prevents reaching sustainability by 2040"}),
    ]
    for tid, tname, ind_id, ma_id, gsa_id, tprops in threshold_defs:
        add_entity(tid, "MinimumThreshold", tname, tprops)
        # Tree 1: GSA → defines → Threshold
        add_rel(gsa_id, tid, "DEFINES")
        # Bridge: Threshold → applies_to → Indicator
        add_rel(tid, ind_id, "APPLIES_TO")
        # Bridge: Threshold → evaluated_in → ManagementArea
        add_rel(tid, ma_id, "EVALUATED_IN")
        # GSP establishes the threshold
        add_rel("kern_gsp", tid, "ESTABLISHES")

    # Measurable Objectives (same structure)
    mo_defs = [
        ("mo_gw_rosedale", "GW Level MO — Rosedale", "ind_gw_levels", "ma_rosedale", "gsa_rosedale",
         {"value": "2015 average water level or better"}),
        ("mo_gw_semitropic", "GW Level MO — Semitropic", "ind_gw_levels", "ma_semitropic", "gsa_semitropic",
         {"value": "2015 average water level or better"}),
        ("mo_sub_semitropic", "Subsidence MO — Semitropic", "ind_subsidence", "ma_semitropic", "gsa_semitropic",
         {"value": "Rate not exceeding 2015-2023 average"}),
    ]
    for moid, moname, ind_id, ma_id, gsa_id, moprops in mo_defs:
        add_entity(moid, "MeasurableObjective", moname, moprops)
        add_rel(gsa_id, moid, "DEFINES")
        add_rel(moid, ind_id, "OBJECTIVE_FOR")
        add_rel(moid, ma_id, "EVALUATED_IN")

    # Undesirable Results (what happens when thresholds are breached)
    ur_defs = [
        ("ur_gw_levels", "Significant & unreasonable decline in groundwater levels", "ind_gw_levels",
         {"trigger": "Water levels at >25% of RMP sites fall below Minimum Threshold for 2+ consecutive years"}),
        ("ur_subsidence", "Significant & unreasonable land subsidence", "ind_subsidence",
         {"trigger": "Subsidence causes loss of critical infrastructure capacity"}),
        ("ur_water_quality", "Significant & unreasonable degradation of water quality", "ind_water_quality",
         {"trigger": "Constituent concentrations exceed MCL at monitoring sites due to GSP management activities"}),
    ]
    for uid, uname, ind_id, uprops in ur_defs:
        add_entity(uid, "UndesirableResult", uname, uprops)
        add_rel(ind_id, uid, "TRIGGERS_WHEN_BREACHED")
        add_rel(uid, "enforce_gsa", "MAY_TRIGGER")

    # ── Bridge B3: Allocation ↔ Water Budget ──
    for aid, gid, _, _ in allocation_rules:
        # AllocationRule → derived_from → Water Budget
        add_rel(aid, "water_budget", "DERIVED_FROM")
        # AllocationRule → constrained_by → Sustainable Yield
        add_rel(aid, "sustainable_yield", "CONSTRAINED_BY")

    # ══════════════════════════════════════════════════════════════
    # TRANSFER COMPLIANCE CHAIN
    # ══════════════════════════════════════════════════════════════

    # Transfer Types
    add_entity("tt_intra_gsa", "TransferRule", "Intra-GSA Transfer", {
        "description": "Transfer between users within the same GSA",
        "complexity": "low", "permit_required": "no"
    })
    add_entity("tt_inter_gsa", "TransferRule", "Inter-GSA Transfer (within basin)", {
        "description": "Transfer between users in different GSAs within Kern Subbasin",
        "complexity": "medium", "permit_required": "GSA notification + accounting"
    })

    # Transfer → constrained_by → AllocationRule (the GSA's allocation must allow it)
    for aid, _, _, _ in allocation_rules:
        add_rel("tt_intra_gsa", aid, "CONSTRAINED_BY")
        add_rel("tt_inter_gsa", aid, "CONSTRAINED_BY")

    # Transfer → must_not_violate → MinimumThreshold (for each indicator)
    for tid, _, _, _, _, _ in threshold_defs:
        add_rel("tt_intra_gsa", tid, "MUST_NOT_VIOLATE")
        add_rel("tt_inter_gsa", tid, "MUST_NOT_VIOLATE")

    # Transfer → requires → Requirement
    for rid, _, _ in requirements:
        add_rel("tt_intra_gsa", rid, "REQUIRES")
        add_rel("tt_inter_gsa", rid, "REQUIRES")

    # Inter-GSA has additional requirement
    add_rel("tt_inter_gsa", "req_notification", "ADDITIONALLY_REQUIRES")

    # Transfer → reported_to → GSA
    for gid, _, _ in gsas:
        add_rel("tt_inter_gsa", gid, "REPORTED_TO")

    # Transfer → evaluated_using → MonitoringNetwork
    for mid, _, _ in monitoring_networks:
        add_rel("tt_intra_gsa", mid, "EVALUATED_USING")
        add_rel("tt_inter_gsa", mid, "EVALUATED_USING")

    return {"entities": entities, "relationships": relationships}


def validate_graph(kg: dict) -> dict:
    """Run the compliance chain traversal test."""
    entities = {e["id"]: e for e in kg["entities"]}
    rels_by_source = {}
    for r in kg["relationships"]:
        if r["source"] not in rels_by_source:
            rels_by_source[r["source"]] = []
        rels_by_source[r["source"]].append(r)

    results = {}

    # Test 1: Transfer → AllocationRule → WaterBudget chain
    def traverse(start_id, chain_types, depth=0, path=None):
        if path is None:
            path = [start_id]
        if depth >= len(chain_types):
            return [path]
        
        found_paths = []
        for r in rels_by_source.get(start_id, []):
            if r["type"] in chain_types[depth]:
                target = r["target"]
                if target in entities:
                    new_paths = traverse(target, chain_types, depth + 1, path + [f"--{r['type']}-->", target])
                    found_paths.extend(new_paths)
        return found_paths

    # Chain: Transfer → CONSTRAINED_BY → AllocationRule → DERIVED_FROM → WaterBudget
    chain1 = traverse("tt_inter_gsa", [
        {"CONSTRAINED_BY"},          # Transfer → AllocationRule
        {"DERIVED_FROM"},            # AllocationRule → WaterBudget
    ])
    results["transfer_to_water_budget"] = {"paths": len(chain1), "sample": chain1[0] if chain1 else []}

    # Chain: Transfer → MUST_NOT_VIOLATE → Threshold → APPLIES_TO → Indicator → MEASURES (reverse) → Monitoring
    chain2 = traverse("tt_inter_gsa", [
        {"MUST_NOT_VIOLATE"},        # Transfer → Threshold
        {"APPLIES_TO"},              # Threshold → Indicator
    ])
    results["transfer_to_indicator"] = {"paths": len(chain2), "sample": chain2[0] if chain2 else []}

    # Chain: Transfer → REQUIRES → Requirement
    chain3 = traverse("tt_inter_gsa", [
        {"REQUIRES", "ADDITIONALLY_REQUIRES"},
    ])
    results["transfer_to_requirements"] = {"paths": len(chain3), "sample": chain3[0] if chain3 else []}

    # Chain: GSA → DEFINES → Threshold → APPLIES_TO → Indicator
    chain4 = traverse("gsa_semitropic", [
        {"DEFINES"},
        {"APPLIES_TO"},
    ])
    results["gsa_to_indicator_via_threshold"] = {"paths": len(chain4), "sample": chain4[0] if chain4 else []}

    # Chain: Indicator → EVALUATED_IN → ManagementArea (← MANAGES ← GSA)
    chain5 = traverse("ind_gw_levels", [
        {"EVALUATED_IN"},
    ])
    results["indicator_to_management_area"] = {"paths": len(chain5), "sample": chain5[0] if chain5 else []}

    # The big one: Full compliance chain
    # Transfer → AllocationRule → constrained_by → SustainableYield → determined_by → WaterBudget
    results["full_chain_test"] = "PASS" if chain1 and chain2 and chain3 else "FAIL"

    return results


if __name__ == "__main__":
    print("Building compliance knowledge graph v3...")
    kg = build_compliance_graph()

    from collections import Counter
    etypes = Counter(e["type"] for e in kg["entities"])
    rtypes = Counter(r["type"] for r in kg["relationships"])

    print(f"\n{'='*60}")
    print(f"KNOWLEDGE GRAPH v3 — Compliance Reasoning Engine")
    print(f"{'='*60}")
    print(f"  Entities: {len(kg['entities'])}")
    print(f"  Relationships: {len(kg['relationships'])}")
    print(f"\n  Entity types:")
    for t, c in etypes.most_common():
        print(f"    {t}: {c}")
    print(f"\n  Relationship types:")
    for t, c in rtypes.most_common():
        print(f"    {t}: {c}")

    # Validate
    print(f"\n{'='*60}")
    print("COMPLIANCE CHAIN VALIDATION")
    print(f"{'='*60}")
    results = validate_graph(kg)
    for test_name, result in results.items():
        if isinstance(result, dict):
            status = "✅" if result["paths"] > 0 else "❌"
            print(f"  {status} {test_name}: {result['paths']} paths")
            if result.get("sample"):
                print(f"     Sample: {' '.join(str(x) for x in result['sample'][:7])}")
        else:
            status = "✅" if result == "PASS" else "❌"
            print(f"  {status} {test_name}: {result}")

    # Save
    output_path = str(Path(__file__).parent.parent.parent / "data" / "policies" / "knowledge_graph_v3.json")
    with open(output_path, "w") as f:
        json.dump(kg, f, indent=2)
    print(f"\n✅ Saved: {output_path}")
