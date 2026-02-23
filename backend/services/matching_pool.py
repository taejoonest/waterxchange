"""
WaterXchange — Weekly Spot Market Order Pool
==============================================

10 farmers across 5 GSAs in the Kern County Subbasin.
Orders represent a SINGLE WEEK's surplus/deficit — enabling
high-frequency trading (multiple matches per day/week).

DESIGN RATIONALE:
  A 200-acre almond block uses ~14 AF/week during peak irrigation.
  A farmer who skips one irrigation set frees up 5-15 AF.
  A farmer whose pump is down for 3 days needs 8-12 AF immediately.
  → Trade sizes: 5–50 AF (weekly spot), not 200-400 AF (annual bulk)

ECONOMIC DATA SOURCES:
  - Crop revenue:       UC Davis Cost & Return Studies (2023-2024)
  - Water duty:         DWR Bulletin 118 / ITRC crop coefficients
  - Marginal value:     (Revenue - Variable Cost) / Water duty = $/AF
  - Kern County prices: PPIC California Water Market ($150-$800/AF)

ENVIRONMENTAL DATA SOURCES:
  - Subsidence rates:   GSP Table 13-3 (p.681)
  - GW decline rates:   GSP Table 13-3 (p.681)
  - Water quality:      GSP Section 8 (p.16) — nitrate, arsenic, TDS
"""

from typing import Dict, Any, List


# ═══════════════════════════════════════════════════════════════
#  CROP ECONOMICS TABLE — real figures from UC Davis / USDA
# ═══════════════════════════════════════════════════════════════

CROP_ECONOMICS = {
    # crop_name: {revenue_per_acre, water_duty_af_per_acre, marginal_value_per_af, variable_cost_per_acre}
    "Almonds":              {"revenue_per_acre": 4200, "water_duty": 3.5, "var_cost": 2800, "marginal_value_af": 400},
    "Pistachios":           {"revenue_per_acre": 5800, "water_duty": 3.0, "var_cost": 3200, "marginal_value_af": 867},
    "Table Grapes":         {"revenue_per_acre": 8500, "water_duty": 2.5, "var_cost": 5500, "marginal_value_af": 1200},
    "Wine Grapes":          {"revenue_per_acre": 3200, "water_duty": 2.0, "var_cost": 2100, "marginal_value_af": 550},
    "Citrus (Oranges)":     {"revenue_per_acre": 4800, "water_duty": 3.0, "var_cost": 3000, "marginal_value_af": 600},
    "Citrus (Mandarins)":   {"revenue_per_acre": 9000, "water_duty": 3.0, "var_cost": 5000, "marginal_value_af": 1333},
    "Processing Tomatoes":  {"revenue_per_acre": 2800, "water_duty": 2.8, "var_cost": 1800, "marginal_value_af": 357},
    "Alfalfa":              {"revenue_per_acre":  800, "water_duty": 5.0, "var_cost":  500, "marginal_value_af":  60},
    "Cotton":               {"revenue_per_acre": 1200, "water_duty": 3.0, "var_cost":  800, "marginal_value_af": 133},
    "Carrots":              {"revenue_per_acre": 6500, "water_duty": 2.2, "var_cost": 3800, "marginal_value_af": 1227},
    "Potatoes":             {"revenue_per_acre": 5000, "water_duty": 2.5, "var_cost": 2800, "marginal_value_af":  880},
    "Pomegranates":         {"revenue_per_acre": 6000, "water_duty": 3.0, "var_cost": 3500, "marginal_value_af":  833},
    "Walnuts":              {"revenue_per_acre": 3500, "water_duty": 3.5, "var_cost": 2400, "marginal_value_af":  314},
    "Fallowed":             {"revenue_per_acre":    0, "water_duty": 0.0, "var_cost":    0, "marginal_value_af":    0},
}


# ═══════════════════════════════════════════════════════════════
#  GSA HCM AREA ENVIRONMENTAL RISK BASELINES — real GSP values
# ═══════════════════════════════════════════════════════════════

HCM_RISK_DATA = {
    # From GSP Table 13-3, p.681
    "Kern River Fan":     {"subsidence_rate": 0.022, "gw_decline": -3.7, "subsidence_mt": 0.27},
    "North Basin":        {"subsidence_rate": 0.059, "gw_decline": -5.2, "subsidence_mt": 0.85},
    "South Basin":        {"subsidence_rate": 0.037, "gw_decline": -4.9, "subsidence_mt": 0.48},
    "East Margin":        {"subsidence_rate": 0.006, "gw_decline": -6.5, "subsidence_mt": 0.14},
    "Western Fold Belt":  {"subsidence_rate": 0.008, "gw_decline": -4.1, "subsidence_mt": 0.10},
}


# ═══════════════════════════════════════════════════════════════
#  10-FARMER WEEKLY SPOT MARKET ORDER POOL
# ═══════════════════════════════════════════════════════════════

def get_farmer_pool() -> List[Dict[str, Any]]:
    """
    Return 10 farmers: 5 sellers + 5 buyers.
    Quantities are WEEKLY spot orders (5-50 AF), not annual bulk.

    Why these sizes?
      - 1 AF = 325,851 gallons ≈ 1 acre flooded 1 foot deep
      - A 200-acre almond block uses ~14 AF/week at peak
      - Skipping 1 irrigation set on 40ac alfalfa = ~8 AF freed
      - A pump outage for 3 days = need ~10 AF from a neighbor
      → Typical spot trade: 8–35 AF
    """
    return [
        # ─── SELLERS (weekly surplus) ───────────────────────────

        {
            "id": "S1",
            "name": "John Martinez",
            "farm": "Green Valley Farm",
            "role": "SELLER",
            "gsa": "Rosedale-Rio Bravo WSD",
            "hcm_area": "Kern River Fan",
            "crops": [
                {"type": "Almonds",  "acreage": 200, "water_duty": 3.5},
                {"type": "Alfalfa",  "acreage": 300, "water_duty": 5.0},
            ],
            "allocation_af_annual": 2200,
            "selling_af": 25,           # Skipping 1 alfalfa irrigation set this week
            "selling_note": "Delaying alfalfa cut — skipping irrigation on 25 acres this cycle",
            "ask_price": 280,
            "marginal_crop_fallowed": "Alfalfa",
            "marginal_value_of_last_af": 60,
            "well_depth_ft": 450,
            "water_level_ft": 210,
            "nitrate_mg_l": 5.2,
            "domestic_wells_1mi": 3,
            "metered": True,
            "compliance_history": "Clean",
        },

        {
            "id": "S2",
            "name": "Maria Lopez",
            "farm": "Lopez Family Orchards",
            "role": "SELLER",
            "gsa": "Kern Delta WD",
            "hcm_area": "South Basin",
            "crops": [
                {"type": "Cotton",   "acreage": 400, "water_duty": 3.0},
            ],
            "allocation_af_annual": 1800,
            "selling_af": 18,           # Cotton between irrigations — 3-day surplus
            "selling_note": "Cotton between irrigation cycles, 3-day window surplus",
            "ask_price": 220,
            "marginal_crop_fallowed": "Cotton",
            "marginal_value_of_last_af": 133,
            "well_depth_ft": 380,
            "water_level_ft": 195,
            "nitrate_mg_l": 7.8,
            "domestic_wells_1mi": 5,
            "metered": True,
            "compliance_history": "Clean",
        },

        {
            "id": "S3",
            "name": "Robert Singh",
            "farm": "Singh Ranches",
            "role": "SELLER",
            "gsa": "Semitropic WSD",
            "hcm_area": "North Basin",
            "crops": [
                {"type": "Walnuts",  "acreage": 150, "water_duty": 3.5},
                {"type": "Alfalfa",  "acreage": 200, "water_duty": 5.0},
            ],
            "allocation_af_annual": 1700,
            "selling_af": 35,           # Fallowed 35 acres of alfalfa permanently this season
            "selling_note": "Permanently fallowed 35ac alfalfa this season — weekly surplus",
            "ask_price": 310,
            "marginal_crop_fallowed": "Alfalfa",
            "marginal_value_of_last_af": 60,
            "well_depth_ft": 400,
            "water_level_ft": 242,
            "nitrate_mg_l": 11.5,
            "domestic_wells_1mi": 8,
            "metered": True,
            "compliance_history": "2023 warning — over-extraction",
        },

        {
            "id": "S4",
            "name": "Amy Nguyen",
            "farm": "Central Kern Ag",
            "role": "SELLER",
            "gsa": "Buena Vista WSA",
            "hcm_area": "Kern River Fan",
            "crops": [
                {"type": "Processing Tomatoes", "acreage": 250, "water_duty": 2.8},
                {"type": "Cotton",               "acreage": 150, "water_duty": 3.0},
            ],
            "allocation_af_annual": 1450,
            "selling_af": 12,           # Drip irrigation efficiency saving this week
            "selling_note": "Drip system efficiency — 12 AF unused from this week's allocation",
            "ask_price": 350,
            "marginal_crop_fallowed": "Cotton",
            "marginal_value_of_last_af": 133,
            "well_depth_ft": 520,
            "water_level_ft": 205,
            "nitrate_mg_l": 4.1,
            "domestic_wells_1mi": 2,
            "metered": True,
            "compliance_history": "Clean",
        },

        {
            "id": "S5",
            "name": "James Wilson",
            "farm": "Wilson Ranch",
            "role": "SELLER",
            "gsa": "Arvin-Edison WSD",
            "hcm_area": "East Margin",
            "crops": [
                {"type": "Citrus (Oranges)", "acreage": 180, "water_duty": 3.0},
            ],
            "allocation_af_annual": 1100,
            "selling_af": 15,           # Post-harvest citrus — lower water need this week
            "selling_note": "Post-harvest week — citrus water demand drops, 15 AF available",
            "ask_price": 450,
            "marginal_crop_fallowed": "Citrus (Oranges)",
            "marginal_value_of_last_af": 600,
            "well_depth_ft": 600,
            "water_level_ft": 310,
            "nitrate_mg_l": 3.0,
            "domestic_wells_1mi": 1,
            "metered": True,
            "compliance_history": "Clean",
        },

        # ─── BUYERS (weekly deficit) ───────────────────────────

        {
            "id": "B1",
            "name": "Sarah Chen",
            "farm": "Sunrise Farms",
            "role": "BUYER",
            "gsa": "Semitropic WSD",
            "hcm_area": "North Basin",
            "crops": [
                {"type": "Pistachios",   "acreage": 250, "water_duty": 3.0},
                {"type": "Pomegranates", "acreage":  80, "water_duty": 3.0},
            ],
            "allocation_af_annual": 900,
            "buying_af": 20,            # Needs extra for new pistachio block this week
            "buying_note": "New 20-acre pistachio block needs first deep soak — urgent",
            "bid_price": 650,
            "marginal_crop_expanding": "Pistachios",
            "marginal_value_of_next_af": 867,
            "well_depth_ft": 380,
            "water_level_ft": 232,
            "nitrate_mg_l": 12.5,
            "domestic_wells_1mi": 7,
            "metered": True,
            "compliance_history": "2023 over-extraction warning",
        },

        {
            "id": "B2",
            "name": "David Kim",
            "farm": "Golden Harvest Orchards",
            "role": "BUYER",
            "gsa": "Rosedale-Rio Bravo WSD",
            "hcm_area": "Kern River Fan",
            "crops": [
                {"type": "Table Grapes",        "acreage": 120, "water_duty": 2.5},
                {"type": "Citrus (Mandarins)",   "acreage":  60, "water_duty": 3.0},
            ],
            "allocation_af_annual": 500,
            "buying_af": 10,            # Mandarin block needs extra mid-week irrigation
            "buying_note": "Heat wave — mandarins need emergency mid-week irrigation",
            "bid_price": 800,
            "marginal_crop_expanding": "Citrus (Mandarins)",
            "marginal_value_of_next_af": 1333,
            "well_depth_ft": 350,
            "water_level_ft": 190,
            "nitrate_mg_l": 3.5,
            "domestic_wells_1mi": 2,
            "metered": True,
            "compliance_history": "Clean",
        },

        {
            "id": "B3",
            "name": "Patricia Gomez",
            "farm": "Gomez Ag Partners",
            "role": "BUYER",
            "gsa": "Kern Delta WD",
            "hcm_area": "South Basin",
            "crops": [
                {"type": "Almonds",  "acreage": 300, "water_duty": 3.5},
                {"type": "Carrots",  "acreage":  80, "water_duty": 2.2},
            ],
            "allocation_af_annual": 1100,
            "buying_af": 30,            # Almond hull split — critical irrigation
            "buying_note": "Hull split week — almonds need precise irrigation or crop loss",
            "bid_price": 500,
            "marginal_crop_expanding": "Almonds",
            "marginal_value_of_next_af": 400,
            "well_depth_ft": 430,
            "water_level_ft": 220,
            "nitrate_mg_l": 8.5,
            "domestic_wells_1mi": 4,
            "metered": True,
            "compliance_history": "Clean",
        },

        {
            "id": "B4",
            "name": "Tom Erikson",
            "farm": "Erikson Family Farm",
            "role": "BUYER",
            "gsa": "Arvin-Edison WSD",
            "hcm_area": "East Margin",
            "crops": [
                {"type": "Potatoes",  "acreage": 200, "water_duty": 2.5},
                {"type": "Carrots",   "acreage": 100, "water_duty": 2.2},
            ],
            "allocation_af_annual": 650,
            "buying_af": 15,            # Pump broke — needs neighbor water for 3 days
            "buying_note": "Well pump failed — needs 15 AF while awaiting repair (3 days)",
            "bid_price": 580,
            "marginal_crop_expanding": "Potatoes",
            "marginal_value_of_next_af": 880,
            "well_depth_ft": 550,
            "water_level_ft": 295,
            "nitrate_mg_l": 6.0,
            "domestic_wells_1mi": 3,
            "metered": True,
            "compliance_history": "Clean",
        },

        {
            "id": "B5",
            "name": "Wei Zhang",
            "farm": "Pacific Ag Holdings",
            "role": "BUYER",
            "gsa": "Buena Vista WSA",
            "hcm_area": "Kern River Fan",
            "crops": [
                {"type": "Wine Grapes",  "acreage": 160, "water_duty": 2.0},
                {"type": "Pomegranates", "acreage": 120, "water_duty": 3.0},
            ],
            "allocation_af_annual": 600,
            "buying_af": 22,            # Pomegranate fruit fill — needs extra this week
            "buying_note": "Pomegranate fruit fill stage — critical 22 AF needed this week",
            "bid_price": 520,
            "marginal_crop_expanding": "Pomegranates",
            "marginal_value_of_next_af": 833,
            "well_depth_ft": 480,
            "water_level_ft": 215,
            "nitrate_mg_l": 3.8,
            "domestic_wells_1mi": 1,
            "metered": True,
            "compliance_history": "Clean",
        },
    ]


def format_order_book(pool: List[Dict]) -> str:
    """Pretty-print the order book."""
    sellers = sorted([f for f in pool if f['role'] == 'SELLER'], key=lambda x: x['ask_price'])
    buyers  = sorted([f for f in pool if f['role'] == 'BUYER'],  key=lambda x: -x['bid_price'])

    lines = []
    lines.append(f"{'─'*90}")
    lines.append(f"  {'ID':<4} {'Farmer':<22} {'GSA':<22} {'Crop (marginal)':<22} {'Qty':>5}  {'Price':>8}")
    lines.append(f"{'─'*90}")
    lines.append(f"  SELL ORDERS (sorted by ask ↑)")
    for s in sellers:
        lines.append(
            f"  {s['id']:<4} {s['name']:<22} {s['gsa']:<22} "
            f"{s['marginal_crop_fallowed']:<22} {s['selling_af']:>5} AF  ${s['ask_price']:>6}/AF"
        )
    lines.append(f"")
    lines.append(f"  BUY ORDERS (sorted by bid ↓)")
    for b in buyers:
        crop_key = b.get('marginal_crop_expanding', '?')
        lines.append(
            f"  {b['id']:<4} {b['name']:<22} {b['gsa']:<22} "
            f"{crop_key:<22} {b['buying_af']:>5} AF  ${b['bid_price']:>6}/AF"
        )
    lines.append(f"{'─'*90}")
    return "\n".join(lines)
