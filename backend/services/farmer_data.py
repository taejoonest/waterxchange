"""
WaterXchange Farmer Data Profiles — ACT 2
==========================================

DATA PROVENANCE:
Every number in this file is tagged with one of three sources:

  [GSP p.XXX]     → Directly from Kern County Subbasin GSP 2025 at that page number
  [GSP-derived]   → Calculated from GSP numbers with formula shown
  [SIMULATED]     → Simulated user input — this is what farmers would enter when
                     using WaterXchange. In production, this comes from the farmer
                     at registration or from GSA API integration.

Basin-level data uses ONLY real GSP numbers.
Farmer-level data is simulated user input, consistent with GSP constraints.
"""

from typing import Dict, Any, List


# ═══════════════════════════════════════════════════════════════════
#  DATA PROVENANCE TABLE — shown in ACT 2 output
# ═══════════════════════════════════════════════════════════════════

DATA_PROVENANCE = {
    # ── Basin-level: ALL from GSP ──
    "basin_name":                  {"source": "GSP", "page": 39,  "note": "Kern County Subbasin"},
    "dwr_basin_number":            {"source": "GSP", "page": 39,  "note": "5-22.14"},
    "basin_area":                  {"source": "GSP", "page": 39,  "note": "1.78 million acres"},
    "number_of_gsas":              {"source": "GSP", "page": 43,  "note": "20 GSAs"},
    "sustainable_yield":           {"source": "GSP", "page": 595, "note": "1,312,218 AFY (Table 9-5)"},
    "groundwater_recharge":        {"source": "GSP", "page": 595, "note": "1,399,299 AFY"},
    "subsurface_outflow":          {"source": "GSP", "page": 595, "note": "87,080 AFY (Table 9-6)"},
    "native_yield":                {"source": "GSP", "page": 596, "note": "280,754 AFY"},
    "total_gw_pumping":            {"source": "GSP", "page": 595, "note": "1,586,417 AFY"},
    "projected_deficit":           {"source": "GSP", "page": 776, "note": "372,120 AFY (2030 Climate Change Scenario)"},
    "change_in_storage":           {"source": "GSP", "page": 54,  "note": "-274,200 AFY (baseline)"},
    "storage_with_projects":       {"source": "GSP", "page": 627, "note": "+85,578 AFY (with SGMA projects)"},
    "subsidence_north_basin":      {"source": "GSP", "page": 681, "note": "0.059 ft/yr (Table 13-3)"},
    "subsidence_kern_fan":         {"source": "GSP", "page": 681, "note": "0.022 ft/yr (Table 13-3)"},
    "subsidence_south_basin":      {"source": "GSP", "page": 681, "note": "0.037 ft/yr (Table 13-3)"},
    "gw_decline_north_basin":      {"source": "GSP", "page": 681, "note": "-5.2 ft/yr (Table 13-3)"},
    "gw_decline_kern_fan":         {"source": "GSP", "page": 681, "note": "-3.7 ft/yr (Table 13-3)"},
    "gw_decline_south_basin":      {"source": "GSP", "page": 681, "note": "-4.9 ft/yr (Table 13-3)"},
    "gw_decline_east_margin":      {"source": "GSP", "page": 681, "note": "-6.5 ft/yr (Table 13-3)"},
    "subsidence_extent_mt_north":  {"source": "GSP", "page": 681, "note": "0.85 ft total (Table 13-3)"},
    "subsidence_extent_mt_kern_fan":{"source": "GSP", "page": 681, "note": "0.27 ft total (Table 13-3)"},
    "subsidence_extent_mt_south":  {"source": "GSP", "page": 681, "note": "0.48 ft total (Table 13-3)"},
    "aquifer_systems":             {"source": "GSP", "page": 795, "note": "Primary Alluvial, Santa Margarita, Olcese"},
    "wq_constituents_of_concern":  {"source": "GSP", "page": 16,  "note": "arsenic, nitrate, TDS, 1,2,3-TCP, uranium"},

    # ── Farmer-level: SIMULATED ──
    "farmer_name":          {"source": "SIMULATED", "note": "Farmers enter this at WaterXchange registration"},
    "farm_acreage":         {"source": "SIMULATED", "note": "Farmer self-reports; verified by county parcel data"},
    "crop_types":           {"source": "SIMULATED", "note": "Farmer self-reports; Kern County grows almonds, pistachios, citrus, grapes, alfalfa, cotton, tomatoes"},
    "well_data":            {"source": "SIMULATED", "note": "From DWR well completion reports + farmer-installed meters"},
    "gsa_allocation":       {"source": "SIMULATED", "note": "Would come from GSA records via API; not public in GSP"},
    "water_levels":         {"source": "SIMULATED", "note": "Would come from CASGEM monitoring network or farmer well logs"},
    "water_quality":        {"source": "SIMULATED", "note": "Would come from GAMA database or farm-level testing"},
    "transfer_quantity":    {"source": "SIMULATED", "note": "Farmer specifies how much they want to buy/sell"},
    "transfer_price":       {"source": "SIMULATED", "note": "Market-determined; WaterXchange matching engine"},
}


def get_data_provenance() -> Dict[str, Dict]:
    """Return the full data provenance table for display in ACT 2."""
    return DATA_PROVENANCE


def get_farmer_a_seller() -> Dict[str, Any]:
    """
    Farmer A — SELLER
    SIMULATED user input representing a farmer in the Rosedale-Rio Bravo
    Water Storage District GSA area (Kern River Fan HCM Area).

    Basin-level parameters (subsidence, GW decline) use real GSP values
    for the Kern River Fan HCM Area (GSP Table 13-3, p.681).
    """
    return {
        # ── Identity & Location [SIMULATED — farmer registration] ──
        "name": "John Martinez",
        "farm_name": "Green Valley Farm",
        "role": "SELLER",
        "data_source_note": "Farmer registration input — would be entered by farmer on WaterXchange",

        # ── Location [SIMULATED — verified against county parcel maps] ──
        "county": "Kern County",
        "basin": "Kern County Subbasin",                        # [GSP p.39]
        "basin_dwr_number": "5-22.14",                          # [GSP p.39]
        "gsa": "Rosedale-Rio Bravo Water Storage District GSA",  # [GSP p.761 — real GSA name]
        "hcm_area": "Kern River Fan",                            # [GSP p.681 — real HCM area]
        "township_range_section": "T29S R25E Sec 14",            # [SIMULATED]
        "position_in_basin": "Northwest — Kern River Fan area",

        # ── Farm & Crop Details [SIMULATED — farmer self-report] ──
        "total_acreage": 640,                                    # [SIMULATED]
        "irrigated_acreage": 580,                                # [SIMULATED]
        "crops": [
            # Kern County is #1 in CA for almond and pistachio production
            {"type": "Almonds", "acreage": 320, "water_duty_af_per_acre": 3.5},   # [SIMULATED]
            {"type": "Pistachios", "acreage": 200, "water_duty_af_per_acre": 3.0}, # [SIMULATED]
            {"type": "Fallowed (rotational)", "acreage": 60, "water_duty_af_per_acre": 0},
        ],
        "irrigation_method": "Micro-drip with soil moisture sensors",  # [SIMULATED]
        "irrigation_efficiency": 0.92,                                  # [SIMULATED]
        "crop_water_demand_af": 1720,                                   # [SIMULATED: 320*3.5 + 200*3.0]

        # ── Water Supply [SIMULATED — would come from GSA records API] ──
        "annual_gsa_allocation_af": 1850,    # [SIMULATED — GSA-specific, not published in GSP]
        "surface_water_entitlement_af": 400, # [SIMULATED]
        "surface_water_received_af": 280,    # [SIMULATED]
        "carryover_balance_af": 220,         # [SIMULATED]
        "total_available_af": 2350,          # [SIMULATED: 1850 + 280 + 220]
        "total_demand_af": 1720,
        "surplus_af": 630,                   # [SIMULATED: 2350 - 1720]

        # ── Transfer Request [SIMULATED — farmer specifies] ──
        "transfer_quantity_af": 150,
        "transfer_price_per_af": 415.00,
        "has_metered_wells": True,

        # ── Well Data [SIMULATED — from DWR well completion reports + meter readings] ──
        "wells": [
            {
                "well_id": "GVF-1",
                "type": "Agricultural production",
                "depth_ft": 450,                    # [SIMULATED]
                "pump_capacity_gpm": 1800,           # [SIMULATED]
                "current_water_level_ft": 210,       # [SIMULATED]
                "annual_extraction_af": 650,         # [SIMULATED]
                "metered": True,
                "aquifer": "Primary Alluvial Principal Aquifer",  # [GSP p.795]
            },
            {
                "well_id": "GVF-2",
                "type": "Agricultural production",
                "depth_ft": 520,                    # [SIMULATED]
                "pump_capacity_gpm": 2200,           # [SIMULATED]
                "current_water_level_ft": 218,       # [SIMULATED]
                "annual_extraction_af": 780,         # [SIMULATED]
                "metered": True,
                "aquifer": "Primary Alluvial Principal Aquifer",  # [GSP p.795]
            },
            {
                "well_id": "GVF-MON",
                "type": "Monitoring",
                "depth_ft": 300,                    # [SIMULATED]
                "current_water_level_ft": 202,       # [SIMULATED]
                "metered": False,
                "aquifer": "Primary Alluvial Principal Aquifer",  # [GSP p.795]
            }
        ],
        "total_annual_extraction_af": 1430,

        # ── Sustainability Indicators — REAL GSP values for Kern River Fan HCM area ──
        "hcm_subsidence_rate_ft_per_yr": 0.022,        # [GSP p.681 Table 13-3]
        "hcm_subsidence_extent_mt_ft": 0.27,            # [GSP p.681 Table 13-3]
        "hcm_subsidence_rate_mt_ft_per_yr": 0.029,      # [GSP p.681 Table 13-3]
        "hcm_gw_level_decline_ft_per_yr": -3.7,         # [GSP p.681 Table 13-3]

        # ── Compliance History [SIMULATED] ──
        "gsa_membership_status": "Active, in good standing",
        "past_violations": [],
        "extraction_within_allocation": True,

        # ── Environmental [SIMULATED] ──
        "domestic_wells_within_1mi": 3,
        "gde_within_1000ft": False,
    }


def get_farmer_b_buyer() -> Dict[str, Any]:
    """
    Farmer B — BUYER
    SIMULATED user input representing a farmer in the Semitropic
    Water Storage District GSA area (North Basin HCM Area).

    Basin-level parameters (subsidence, GW decline) use real GSP values
    for the North Basin HCM Area (GSP Table 13-3, p.681).
    """
    return {
        # ── Identity & Location [SIMULATED — farmer registration] ──
        "name": "Sarah Chen",
        "farm_name": "Sunrise Farms",
        "role": "BUYER",
        "data_source_note": "Farmer registration input — would be entered by farmer on WaterXchange",

        # ── Location [SIMULATED — verified against county parcel maps] ──
        "county": "Kern County",
        "basin": "Kern County Subbasin",                        # [GSP p.39]
        "basin_dwr_number": "5-22.14",                          # [GSP p.39]
        "gsa": "Semitropic Water Storage District GSA",          # [GSP p.761 — real GSA name]
        "hcm_area": "North Basin",                               # [GSP p.681 — real HCM area]
        "township_range_section": "T30S R24E Sec 22",            # [SIMULATED]
        "position_in_basin": "North — North Basin HCM area",

        # ── Farm & Crop Details [SIMULATED — farmer self-report] ──
        "total_acreage": 320,
        "irrigated_acreage": 300,
        "crops": [
            {"type": "Alfalfa (transitioning out)", "acreage": 120, "water_duty_af_per_acre": 5.0},
            {"type": "Pistachios (new planting)", "acreage": 100, "water_duty_af_per_acre": 3.2},
            {"type": "Processing Tomatoes", "acreage": 80, "water_duty_af_per_acre": 2.8},
        ],
        "irrigation_method": "Flood (alfalfa), Drip (pistachios, tomatoes)",
        "irrigation_efficiency": 0.78,
        "crop_water_demand_af": 1144,       # [SIMULATED: 120*5.0 + 100*3.2 + 80*2.8]

        # ── Water Supply [SIMULATED — would come from GSA records API] ──
        "annual_gsa_allocation_af": 900,
        "surface_water_entitlement_af": 200,
        "surface_water_received_af": 120,
        "carryover_balance_af": 50,
        "total_available_af": 1070,          # [SIMULATED: 900 + 120 + 50]
        "total_demand_af": 1144,
        "deficit_af": 74,                    # [SIMULATED: 1144 - 1070]
        "additional_requested_af": 150,

        # ── Transfer Request [SIMULATED — farmer specifies] ──
        "transfer_quantity_af": 150,
        "transfer_price_per_af": 415.00,
        "intended_use": "Irrigation — support crop transition from alfalfa to pistachios",
        "has_metered_wells": True,

        # ── Well Data [SIMULATED — from DWR well completion reports + meter readings] ──
        "wells": [
            {
                "well_id": "SF-1",
                "type": "Agricultural production",
                "depth_ft": 380,
                "pump_capacity_gpm": 1200,
                "current_water_level_ft": 232,
                "annual_extraction_af": 520,
                "metered": True,
                "aquifer": "Primary Alluvial Principal Aquifer",  # [GSP p.795]
            },
            {
                "well_id": "SF-2",
                "type": "Agricultural production",
                "depth_ft": 410,
                "pump_capacity_gpm": 1400,
                "current_water_level_ft": 240,
                "annual_extraction_af": 480,
                "metered": True,
                "aquifer": "Primary Alluvial Principal Aquifer",  # [GSP p.795]
            }
        ],
        "total_annual_extraction_af": 1000,

        # ── Sustainability Indicators — REAL GSP values for North Basin HCM area ──
        "hcm_subsidence_rate_ft_per_yr": 0.059,        # [GSP p.681 Table 13-3]
        "hcm_subsidence_extent_mt_ft": 0.85,            # [GSP p.681 Table 13-3]
        "hcm_subsidence_rate_mt_ft_per_yr": 0.053,      # [GSP p.681 Table 13-3]
        "hcm_gw_level_decline_ft_per_yr": -5.2,         # [GSP p.681 Table 13-3]

        # ── Water Quality [SIMULATED — from GAMA database or farm-level testing] ──
        "groundwater_quality_nitrate_mg_l": 12.5,        # [SIMULATED — GSP flags nitrate as constituent of concern, p.16]

        # ── Compliance History [SIMULATED] ──
        "gsa_membership_status": "Active, in good standing",
        "past_violations": [
            "2023: Over-extraction warning (107% of allocation) — corrective action plan filed"
        ],
        "extraction_within_allocation": False,   # Currently at 111% of allocation

        # ── Environmental [SIMULATED] ──
        "domestic_wells_within_1mi": 7,
        "gde_within_1000ft": False,
    }


def get_transfer_details() -> Dict[str, Any]:
    """
    Combined transfer record.
    The transfer itself is SIMULATED — this is what WaterXchange would generate
    when a buyer and seller are matched.
    """
    return {
        "transfer_id": "WXT-2026-0042",
        "date": "2026-02-17",
        "water_year": "WY 2025-2026",
        "seller": get_farmer_a_seller(),
        "buyer": get_farmer_b_buyer(),
        "quantity_af": 150,
        "price_per_af": 415.00,
        "total_value_usd": 62250.00,
        "transfer_type": "Intra-basin groundwater credit transfer",
        "basin": "Kern County Subbasin (DWR Basin 5-22.14)",    # [GSP p.39]
        "mechanism": "GSA accounting ledger transfer (extraction credits)",
        "conveyance": "No physical conveyance — paper transfer of extraction rights",
        "duration": "Single water year (expires Sep 30, 2026)",
        "conditions": [
            "Both parties must maintain metered wells",
            "Buyer extraction must not exceed allocation + transferred amount",
            "Transfer subject to GSA annual review",
            "Transfer does not create permanent water right"
        ]
    }


def get_hydrology_data() -> Dict[str, Any]:
    """
    Basin-wide hydrologic data for the Kern County Subbasin.
    ALL numbers are directly from the Kern County Subbasin GSP 2025.
    Every value includes the GSP page number for verification.
    """
    return {
        "basin_name": "Kern County Subbasin",                   # [GSP p.39]
        "dwr_basin_number": "5-22.14",                           # [GSP p.39]
        "basin_priority": "Critically Overdrafted",              # [GSP p.43 — designated by DWR]
        "basin_area_acres": 1_780_000,                           # [GSP p.39 — 1.78 million acres]
        "number_of_gsas": 20,                                    # [GSP p.43]

        # ── Sustainable Yield [GSP Section 9.4, p.595-596] ──
        "sustainable_yield": {
            "total_afy": 1_312_218,                              # [GSP p.595, Table 9-5]
            "method_1_from_pumping": 1_312_218,                  # [GSP p.595 — pumping minus storage decline]
            "method_2_from_recharge": 1_312_219,                 # [GSP p.595 — recharge minus outflow]
            "groundwater_recharge_afy": 1_399_299,               # [GSP p.595]
            "subsurface_outflow_afy": 87_080,                    # [GSP p.595, Table 9-6]
            "native_yield_afy": 280_754,                         # [GSP p.596]
            "citation": "GSP Table 9-5 & 9-6, pages 595-596",
        },

        # ── Water Budget [GSP Section 9, various pages] ──
        "water_budget": {
            "total_groundwater_pumping_afy": 1_586_417,          # [GSP p.595]
            "change_in_storage_baseline_afy": -274_200,          # [GSP p.54 — current baseline deficit]
            "change_in_storage_with_projects_afy": 85_578,       # [GSP p.627 — with SGMA projects]
            "projected_deficit_2030_climate_afy": 372_120,       # [GSP p.776 — 2030 Climate Change]
            "projected_deficit_2070_climate_afy": -472_336,      # [GSP p.56 — 2070 without projects]
            "projected_2070_with_projects_afy": -45_969,         # [GSP p.56 — 2070 with projects]
            "pma_improvement_baseline_afy": 43_400,              # [GSP p.637]
            "pma_improvement_2030_afy": 59_700,                  # [GSP p.637]
            "pma_improvement_2070_afy": 72_300,                  # [GSP p.637]
            "citation": "GSP Section 9, Tables in Appendix H-1",
        },

        # ── Groundwater Level Decline by HCM Area [GSP Table 13-3, p.681] ──
        "groundwater_levels_by_hcm": {
            "North Basin":       {"decline_ft_per_yr": -5.2, "decline_2015_2023_ft_per_yr": -5.7},
            "Kern River Fan":    {"decline_ft_per_yr": -3.7, "decline_2015_2023_ft_per_yr": -2.8},
            "South Basin":       {"decline_ft_per_yr": -4.9, "decline_2015_2023_ft_per_yr": -6.1},
            "Western Fold Belt": {"decline_ft_per_yr": -4.1, "decline_2015_2023_ft_per_yr": None},
            "East Margin":       {"decline_ft_per_yr": -6.5, "decline_2015_2023_ft_per_yr": -6.5},
            "citation": "GSP Table 13-3, page 681",
        },

        # ── Subsidence by HCM Area [GSP Table 13-3, p.681] ──
        "subsidence_by_hcm": {
            "North Basin":       {"rate_ft_per_yr": 0.059, "rate_mt": 0.053, "extent_mt_ft": 0.85},
            "Kern River Fan":    {"rate_ft_per_yr": 0.022, "rate_mt": 0.029, "extent_mt_ft": 0.27},
            "South Basin":       {"rate_ft_per_yr": 0.037, "rate_mt": 0.030, "extent_mt_ft": 0.48},
            "Western Fold Belt": {"rate_ft_per_yr": 0.008, "rate_mt": None,  "extent_mt_ft": 0.10},
            "East Margin":       {"rate_ft_per_yr": 0.006, "rate_mt": 0.006, "extent_mt_ft": 0.14},
            "citation": "GSP Table 13-3, page 681",
        },

        # ── Water Quality [GSP Section 8, p.16] ──
        "water_quality": {
            "constituents_of_concern": [
                "Arsenic", "Nitrate/Nitrite", "TDS",
                "1,2,3-TCP", "Uranium"
            ],                                                    # [GSP p.16]
            "nitrate_summary": "Table 8-16 — Range and Median by HCM Area",  # [GSP p.16]
            "tds_summary": "Table 8-25 — Range and Median by HCM Area",      # [GSP p.16]
            "mt_criteria": "15% of RMW-WQs exceeding MT triggers undesirable result",  # [GSP p.58]
            "citation": "GSP Section 8 / Section 13.3, pages 16, 58",
        },

        # ── Aquifer Systems [GSP p.795] ──
        "aquifer_systems": [
            "Primary Alluvial Principal Aquifer",
            "Santa Margarita Principal Aquifer",
            "Olcese Principal Aquifer",
        ],

        # ── GSP Process Context [GSP p.43] ──
        "gsp_context": {
            "designated_inadequate": "March 2023",               # [GSP p.43]
            "swrcb_intervention": True,                           # [GSP p.43]
            "plan_adopted": "December 2024",                     # [GSP p.43]
            "total_pmas": 85,                                    # [GSP p.797 — 85 implemented]
            "pma_categories": "Implemented (85, 47%), Functional (4, 2%), In-Process, As-Needed",  # [GSP p.797]
            "citation": "GSP pages 43, 797",
        },

        # ── Sustainability Management Criteria Framework [GSP Section 13] ──
        "smc_framework": {
            "sustainability_indicators": [
                "Chronic Lowering of Groundwater Levels",
                "Reduction of Groundwater Storage",
                "Land Subsidence",
                "Degraded Water Quality",
                "Interconnected Surface Water",
            ],                                                    # [GSP p.647-648]
            "mt_definition": "numeric value for each sustainability indicator used to define undesirable results (23 CCR §351(t))",  # [GSP p.648]
            "mo_definition": "specific, quantifiable goals for maintenance or improvement of groundwater conditions (23 CCR §351(s))",  # [GSP p.648]
            "exceedance_policy": "Appendix K-1 — investigation, notification, documentation",  # [GSP p.793]
            "citation": "GSP Section 13, pages 647-648, 793",
        },
    }


def format_farmer_profile(farmer: Dict[str, Any]) -> str:
    """Format a farmer profile for display, with data source tags."""
    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"  {farmer['role']}: {farmer['name']} — {farmer['farm_name']}")
    lines.append(f"{'='*60}")
    lines.append(f"  ℹ️  {farmer.get('data_source_note', 'Simulated user input')}")
    lines.append(f"")
    lines.append(f"  📍 Location: {farmer.get('township_range_section', '?')}, {farmer['county']}  [SIMULATED]")
    lines.append(f"  🏛  GSA: {farmer['gsa']}  [GSP p.761]")
    lines.append(f"  🗺  HCM Area: {farmer.get('hcm_area', '?')}  [GSP p.681]")
    lines.append(f"  🌊 Basin: {farmer['basin']} ({farmer.get('basin_dwr_number','')})  [GSP p.39]")
    lines.append(f"  📐 Total Acreage: {farmer['total_acreage']} ac ({farmer['irrigated_acreage']} irrigated)  [SIMULATED]")
    lines.append(f"\n  🌱 Crops:  [SIMULATED — farmer self-report]")
    for crop in farmer['crops']:
        lines.append(f"     • {crop['type']}: {crop['acreage']} ac @ {crop['water_duty_af_per_acre']} AF/ac")
    lines.append(f"  💧 Irrigation: {farmer['irrigation_method']}  [SIMULATED]")
    lines.append(f"  📊 Crop Water Demand: {farmer['crop_water_demand_af']} AF/yr  [SIMULATED]")
    lines.append(f"\n  💰 Water Supply:  [SIMULATED — would come from GSA records API]")
    lines.append(f"     GSA Allocation: {farmer['annual_gsa_allocation_af']} AF")
    lines.append(f"     Surface Water: {farmer.get('surface_water_received_af', 0)} AF (of {farmer.get('surface_water_entitlement_af', 0)} entitlement)")
    lines.append(f"     Carryover: {farmer.get('carryover_balance_af', 0)} AF")
    lines.append(f"     Total Available: {farmer.get('total_available_af', 0)} AF")
    surplus = farmer.get('surplus_af')
    deficit = farmer.get('deficit_af')
    if surplus:
        lines.append(f"     ✅ Surplus: {surplus} AF")
    if deficit:
        lines.append(f"     ⚠️  Deficit: {deficit} AF")
    lines.append(f"\n  🔧 Wells:  [SIMULATED — from DWR well completion reports]")
    for well in farmer['wells']:
        lines.append(f"     • {well['well_id']} ({well['type']}): {well['depth_ft']} ft deep, WL={well['current_water_level_ft']} ft")
        if well.get('annual_extraction_af'):
            lines.append(f"       Extraction: {well['annual_extraction_af']} AF/yr, Metered: {well.get('metered', False)}")
        lines.append(f"       Aquifer: {well.get('aquifer', '?')}  [GSP p.795]")

    lines.append(f"\n  📈 GSP Sustainability Indicators for {farmer.get('hcm_area', '?')} HCM Area:  [GSP p.681]")
    lines.append(f"     GW Level Decline: {farmer.get('hcm_gw_level_decline_ft_per_yr', '?')} ft/yr  [GSP Table 13-3]")
    lines.append(f"     Subsidence Rate: {farmer.get('hcm_subsidence_rate_ft_per_yr', '?')} ft/yr  [GSP Table 13-3]")
    lines.append(f"     Subsidence Extent MT: {farmer.get('hcm_subsidence_extent_mt_ft', '?')} ft  [GSP Table 13-3]")
    lines.append(f"     Subsidence Rate MT: {farmer.get('hcm_subsidence_rate_mt_ft_per_yr', '?')} ft/yr  [GSP Table 13-3]")

    if farmer.get('past_violations'):
        lines.append(f"\n  ⚠️  Past Issues:  [SIMULATED]")
        for v in farmer['past_violations']:
            lines.append(f"     • {v}")
    return "\n".join(lines)
