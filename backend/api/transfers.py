"""
Transfer pipeline API endpoints.

Provides:
  - POST /transfers/run           — run GW pipeline
  - POST /transfers/run/surface-water  — run SW pipeline
  - POST /transfers/run/auto      — auto-route to correct pipeline
  - GET  /transfers/demo/scenarios       — GW demo scenarios
  - GET  /transfers/demo/sw-scenarios    — SW demo scenarios
  - GET  /transfers/demo/all-scenarios   — all pathway scenarios
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Any, Dict, Optional

router = APIRouter()


class QuickRunRequest(BaseModel):
    seller: Dict[str, Any]
    buyer: Dict[str, Any]
    transfer: Dict[str, Any]


@router.post("/run")
async def run_transfer_pipeline(request: Request, req: QuickRunRequest):
    """Run the groundwater pipeline."""
    from services.pipeline import run_groundwater_pipeline
    sgma_graph = getattr(request.app.state, 'sgma_graph', None)
    result = run_groundwater_pipeline(
        seller=req.seller, buyer=req.buyer, transfer=req.transfer,
        knowledge_graph=sgma_graph,
    )
    return result


@router.post("/run/surface-water")
async def run_sw_pipeline(req: QuickRunRequest):
    """Run the surface water pipeline."""
    from services.sw_pipeline import run_surface_water_pipeline
    result = run_surface_water_pipeline(
        seller=req.seller, buyer=req.buyer, transfer=req.transfer,
    )
    return result


@router.post("/run/auto")
async def run_auto_routed_pipeline(request: Request, req: QuickRunRequest):
    """Auto-route to the correct pipeline based on transfer characteristics."""
    from services.pipeline_router import run_routed_pipeline
    sgma_graph = getattr(request.app.state, 'sgma_graph', None)
    result = run_routed_pipeline(
        seller=req.seller, buyer=req.buyer, transfer=req.transfer,
        knowledge_graph=sgma_graph,
    )
    return result


@router.get("/demo/scenarios")
async def get_demo_scenarios():
    """Return GW demo scenarios."""
    return {"scenarios": _gw_scenarios()}


@router.get("/demo/sw-scenarios")
async def get_sw_demo_scenarios():
    """Return SW demo scenarios."""
    return {"scenarios": _sw_scenarios()}


@router.get("/demo/all-scenarios")
async def get_all_pathway_scenarios():
    """Return scenarios covering all 10+ regulatory pathways."""
    return {"scenarios": _gw_scenarios() + _sw_scenarios() + _special_scenarios()}


def _gw_scenarios():
    return [
        {
            "name": "Kern County Intra-GSA",
            "description": "Farmer-to-farmer within Rosedale-Rio Bravo GSA",
            "seller": {
                "entity_type": "farmer", "name": "Grimmway Farms",
                "gsa": "Rosedale-Rio Bravo WSD GSA", "basin": "Kern County",
                "allocation_af": 800, "used_af": 500, "extraction_method": "metered",
                "well_lat": 35.38, "well_lng": -119.18, "well_depth_ft": 350,
                "water_level_ft": -120, "nitrate_mg_l": 8.5, "hcm_area": "Kern River Fan",
            },
            "buyer": {
                "entity_type": "farmer", "name": "Bolthouse Farms",
                "gsa": "Rosedale-Rio Bravo WSD GSA", "basin": "Kern County",
                "allocation_af": 600, "used_af": 550, "extraction_method": "metered",
                "well_lat": 35.40, "well_lng": -119.20, "well_depth_ft": 400,
                "water_level_ft": -140, "nitrate_mg_l": 6.0, "domestic_wells_1mi": 3,
                "hcm_area": "Kern River Fan",
            },
            "transfer": {
                "transfer_type": "direct", "quantity_af": 200, "price_per_af": 450,
                "source_gsa": "Rosedale-Rio Bravo WSD GSA",
                "destination_gsa": "Rosedale-Rio Bravo WSD GSA",
                "source_basin": "Kern County", "destination_basin": "Kern County",
                "duration_days": 365,
            },
        },
        {
            "name": "Cross-GSA Transfer",
            "description": "Water district to municipality across GSA boundaries",
            "seller": {
                "entity_type": "water_district", "name": "Semitropic WSD",
                "gsa": "Semitropic WSD GSA", "basin": "Kern County",
                "allocation_af": 5000, "used_af": 3000, "extraction_method": "metered",
                "well_lat": 35.50, "well_lng": -119.60, "well_depth_ft": 500,
                "water_level_ft": -180, "nitrate_mg_l": 12.0, "hcm_area": "North Basin",
            },
            "buyer": {
                "entity_type": "municipality", "name": "City of Bakersfield",
                "gsa": "Kern County Water Agency GSA", "basin": "Kern County",
                "allocation_af": 10000, "used_af": 8500, "service_population": 400000,
                "extraction_method": "metered",
                "well_lat": 35.37, "well_lng": -119.02, "well_depth_ft": 450,
                "water_level_ft": -160, "nitrate_mg_l": 5.0, "domestic_wells_1mi": 15,
                "hcm_area": "Kern River Fan",
            },
            "transfer": {
                "transfer_type": "direct", "quantity_af": 1500, "price_per_af": 600,
                "source_gsa": "Semitropic WSD GSA",
                "destination_gsa": "Kern County Water Agency GSA",
                "source_basin": "Kern County", "destination_basin": "Kern County",
                "duration_days": 365,
            },
        },
        {
            "name": "Water Bank Withdrawal",
            "description": "Water bank to municipality (banked water)",
            "seller": {
                "entity_type": "water_bank", "name": "Kern Water Bank",
                "gsa": "Kern County Water Agency GSA", "basin": "Kern County",
                "allocation_af": 0, "used_af": 0, "banked_balance_af": 50000,
                "extraction_method": "metered",
                "well_lat": 35.30, "well_lng": -119.10, "well_depth_ft": 300,
                "water_level_ft": -80, "nitrate_mg_l": 4.0, "hcm_area": "Kern River Fan",
            },
            "buyer": {
                "entity_type": "municipality", "name": "City of Bakersfield",
                "gsa": "Kern County Water Agency GSA", "basin": "Kern County",
                "allocation_af": 10000, "used_af": 9000, "service_population": 400000,
                "extraction_method": "metered",
                "well_lat": 35.37, "well_lng": -119.02, "well_depth_ft": 450,
                "water_level_ft": -160, "domestic_wells_1mi": 15,
                "hcm_area": "Kern River Fan",
            },
            "transfer": {
                "transfer_type": "banked", "quantity_af": 5000, "price_per_af": 350,
                "source_gsa": "Kern County Water Agency GSA",
                "destination_gsa": "Kern County Water Agency GSA",
                "source_basin": "Kern County", "destination_basin": "Kern County",
                "duration_days": 180,
            },
        },
    ]


def _sw_scenarios():
    return [
        {
            "name": "Post-1914 Temporary Transfer",
            "description": "Short-term surface water sale on Kern River",
            "seller": {
                "entity_type": "water_district", "name": "North Kern WSD",
                "water_right_type": "appropriative_post1914",
                "water_right_id": "S014901", "ewrims_status": "active",
                "face_value_af": 10000, "priority_date": "1952-03-15",
                "beneficial_use_af": 8000, "historical_diversion_af": 9000,
                "consumptive_use_af": 6000,
            },
            "buyer": {
                "entity_type": "farmer", "name": "Harris Ranch",
                "basin": "Kings Subbasin",
            },
            "transfer": {
                "transfer_type": "temporary_change", "quantity_af": 2000,
                "price_per_af": 500, "duration_days": 180,
                "source_stream": "Kern River", "point_of_diversion": "Kern River at Isabella",
                "place_of_use": "Harris Ranch, Coalinga",
                "downstream_rights_count": 4, "conveyance_method": "canal_lined",
                "has_environmental_flow_requirement": True,
                "anadromous_fish_present": False,
                "is_area_of_origin_export": True,
            },
        },
        {
            "name": "Pre-1914 Water Sale",
            "description": "Private sale of pre-1914 right — no SWRCB needed",
            "seller": {
                "entity_type": "farmer", "name": "Historic Ranch LLC",
                "water_right_type": "appropriative_pre1914",
                "water_right_id": "", "face_value_af": 5000,
                "beneficial_use_af": 3000, "historical_diversion_af": 4000,
                "consumptive_use_af": 2500,
            },
            "buyer": {
                "entity_type": "water_district", "name": "Westlands WD",
                "basin": "Westside Subbasin",
            },
            "transfer": {
                "transfer_type": "water_sale", "quantity_af": 1000,
                "price_per_af": 800, "duration_days": 365,
                "source_stream": "Kings River",
                "conveyance_method": "canal_lined",
            },
        },
        {
            "name": "CVP Contract Transfer",
            "description": "CVP allocation transfer between districts",
            "seller": {
                "entity_type": "water_district", "name": "Arvin-Edison WSD",
                "water_right_type": "cvp_contract",
                "contract_allocation_af": 40000, "contract_used_af": 25000,
            },
            "buyer": {
                "entity_type": "water_district", "name": "Kern-Tulare WD",
                "basin": "Tulare Lake Subbasin",
            },
            "transfer": {
                "transfer_type": "cvp_transfer", "quantity_af": 5000,
                "price_per_af": 200, "duration_days": 365,
                "source_stream": "Friant-Kern Canal",
                "conveyance_method": "canal_lined",
            },
        },
    ]


def _special_scenarios():
    return [
        {
            "name": "GW Export (Protected Area)",
            "description": "Groundwater export across basin — triggers CWC §1220",
            "seller": {
                "entity_type": "farmer", "name": "East Side Farms",
                "gsa": "Eastern Kern GSA", "basin": "Indian Wells Valley",
                "allocation_af": 500, "used_af": 200, "extraction_method": "metered",
                "well_lat": 35.62, "well_lng": -117.80, "well_depth_ft": 600,
                "water_level_ft": -250, "hcm_area": "",
            },
            "buyer": {
                "entity_type": "developer", "name": "Mojave Development Corp",
                "basin": "Fremont Valley",
                "well_lat": 35.10, "well_lng": -117.90, "well_depth_ft": 400,
            },
            "transfer": {
                "transfer_type": "direct", "quantity_af": 200, "price_per_af": 900,
                "source_gsa": "Eastern Kern GSA", "destination_gsa": "",
                "source_basin": "Indian Wells Valley", "destination_basin": "Fremont Valley",
                "duration_days": 365,
            },
        },
        {
            "name": "In-Lieu Transfer",
            "description": "Farmer reduces pumping, frees surface water for buyer",
            "seller": {
                "entity_type": "farmer", "name": "Wonderful Orchards",
                "gsa": "Semitropic WSD GSA", "basin": "Kern County",
                "allocation_af": 2000, "used_af": 800, "extraction_method": "metered",
                "well_lat": 35.52, "well_lng": -119.55, "well_depth_ft": 450,
                "water_level_ft": -160, "hcm_area": "North Basin",
            },
            "buyer": {
                "entity_type": "municipality", "name": "City of Wasco",
                "gsa": "Semitropic WSD GSA", "basin": "Kern County",
                "allocation_af": 1000, "used_af": 950, "service_population": 28000,
                "well_lat": 35.59, "well_lng": -119.34, "well_depth_ft": 350,
                "water_level_ft": -130, "domestic_wells_1mi": 8,
                "hcm_area": "North Basin",
            },
            "transfer": {
                "transfer_type": "in_lieu", "quantity_af": 500, "price_per_af": 400,
                "source_gsa": "Semitropic WSD GSA",
                "destination_gsa": "Semitropic WSD GSA",
                "source_basin": "Kern County", "destination_basin": "Kern County",
                "duration_days": 365,
            },
        },
    ]
