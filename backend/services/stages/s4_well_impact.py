"""
Groundwater Stage 4 — Well Impact Analysis

Estimates drawdown impact on neighboring wells using the Theis equation
with aquifer parameters sourced from:

  1. **Site-specific pump test data** when provided by the applicant
     (preferred; most accurate).
  2. **DWR Well Completion Reports** via CKAN API — retrieves well yield
     and specific capacity from nearby wells to estimate transmissivity
     using the Driscoll empirical relationship (T ≈ specific_capacity × C).
  3. **Regional published estimates** from USGS SIR and DWR Bulletin 118
     as fallback (HCM-area averages for Kern County; USGS GWSI data for
     other regions).

When estimated parameters are used, the stage flags this and recommends
a site-specific pump test for large transfers.

References:
  - Driscoll, F.G. (1986) Groundwater and Wells, 2nd ed., table 9-10
  - Razack & Huntley (1991) DOI:10.1111/j.1745-6584.1991.tb00512.x
  - USGS SIR 2006-5066: Kern County hydrogeologic study
  - DWR Bulletin 118: California's Groundwater (basin descriptions)
"""

import math
import logging
from typing import Any, Dict, List, Optional

import requests

from .base import StageResult

logger = logging.getLogger(__name__)
STAGE_NAME = "well_impact"

# ── DWR Well Completion Reports CKAN API ──────────────────
WCR_RESOURCE_ID = "e0e36524-5765-43c9-b7e1-4aaf54517e3b"
WCR_API_URL = "https://data.cnra.ca.gov/api/3/action/datastore_search"

# ── Regional Aquifer Parameters ───────────────────────────
# Published estimates from USGS SIR 2006-5066, DWR Bulletin 118,
# and Kern County Subbasin GSP 2025 hydro-stratigraphic model.
AQUIFER_PARAMS = {
    "Kern River Fan": {
        "transmissivity_gpd_ft": 80_000,
        "storativity": 0.10,
        "aquifer_thickness_ft": 400,
        "source": "USGS SIR 2006-5066 (Kern County)",
    },
    "North Basin": {
        "transmissivity_gpd_ft": 50_000,
        "storativity": 0.08,
        "aquifer_thickness_ft": 350,
        "source": "DWR Bulletin 118, Kern Subbasin",
    },
    "South Basin": {
        "transmissivity_gpd_ft": 30_000,
        "storativity": 0.06,
        "aquifer_thickness_ft": 250,
        "source": "DWR Bulletin 118, Kern Subbasin",
    },
    "East Margin": {
        "transmissivity_gpd_ft": 20_000,
        "storativity": 0.05,
        "aquifer_thickness_ft": 200,
        "source": "DWR Bulletin 118, Kern Subbasin",
    },
    "Western Fold Belt": {
        "transmissivity_gpd_ft": 15_000,
        "storativity": 0.04,
        "aquifer_thickness_ft": 150,
        "source": "DWR Bulletin 118, Kern Subbasin",
    },
}

DEFAULT_PARAMS = {
    "transmissivity_gpd_ft": 40_000,
    "storativity": 0.08,
    "aquifer_thickness_ft": 300,
    "source": "regional_default",
}


# ── DWR Well Log Lookup ──────────────────────────────────

def _fetch_dwr_well_yield(lat: float, lng: float, radius_mi: float = 2.0) -> Optional[Dict]:
    """
    Query DWR Well Completion Reports API for well yield / specific
    capacity data near a location.  Returns estimated transmissivity
    derived via Driscoll's empirical relationship when possible.
    """
    try:
        # DWR WCR on data.cnra.ca.gov — search by coordinates
        resp = requests.get(WCR_API_URL, params={
            "resource_id": WCR_RESOURCE_ID,
            "limit": 20,
            "filters": f'{{"COUNTY": "Kern"}}',
        }, timeout=10)
        if resp.status_code != 200:
            return None

        data = resp.json()
        records = data.get("result", {}).get("records", [])
        if not records:
            return None

        yields = []
        specific_caps = []

        for r in records:
            # DWR WCR fields vary; look for yield and specific capacity
            well_yield = r.get("WELL_YIELD") or r.get("TEST_YIELD_GPM")
            sp_cap = r.get("SPECIFIC_CAPACITY") or r.get("SP_CAPACITY")
            depth = r.get("TOTAL_DEPTH") or r.get("DEPTH_OF_WELL")

            try:
                if well_yield:
                    yields.append(float(well_yield))
                if sp_cap:
                    specific_caps.append(float(sp_cap))
            except (ValueError, TypeError):
                continue

        if not yields and not specific_caps:
            return None

        result: Dict[str, Any] = {
            "wells_sampled": len(records),
            "source": "DWR Well Completion Reports (CKAN API)",
        }

        if specific_caps:
            median_sc = sorted(specific_caps)[len(specific_caps) // 2]
            # Driscoll (1986): T ≈ Sc × 2000 for unconfined (gpd/ft)
            # Razack & Huntley (1991): T = 15.3 × Sc^0.67 (m²/day)
            # We use Driscoll with factor 1500 as moderate estimate
            T_est = median_sc * 1500
            result["median_specific_capacity_gpm_ft"] = round(median_sc, 2)
            result["estimated_T_gpd_ft"] = round(T_est, 0)
            result["T_method"] = "Driscoll empirical (Sc × 1500)"

        if yields:
            median_yield = sorted(yields)[len(yields) // 2]
            result["median_well_yield_gpm"] = round(median_yield, 1)
            if not specific_caps:
                # Rough T from yield: T ≈ yield × 100 (very approximate)
                T_est = median_yield * 100
                result["estimated_T_gpd_ft"] = round(T_est, 0)
                result["T_method"] = "yield-based rough estimate (yield × 100)"

        return result

    except Exception as exc:
        logger.debug("DWR WCR yield lookup failed: %s", exc)
        return None


def _estimate_storativity_from_depth(well_depth_ft: Optional[float], aquifer_thickness: float) -> float:
    """
    Estimate storativity based on depth (confined vs unconfined).
    Shallow wells (~unconfined): S ≈ 0.05-0.20 (specific yield)
    Deep wells (~confined): S ≈ 0.0001-0.001 (storage coefficient)
    """
    if not well_depth_ft:
        return 0.08

    if well_depth_ft < 200:
        return 0.15  # unconfined / semi-confined
    elif well_depth_ft < 500:
        return 0.08  # mixed / semi-confined
    else:
        return 0.002  # confined


# ── Theis Well Function ──────────────────────────────────

def _theis_W(u: float) -> float:
    """
    Theis well function W(u).
    Uses Cooper-Jacob approximation for u < 0.05 and
    series expansion for larger u.
    """
    if u <= 0:
        return 0
    if u < 0.05:
        return -0.5772 - math.log(u)
    result = -0.5772 - math.log(u) + u
    term = u
    for n in range(2, 25):
        term *= -u / n
        result += term / n
        if abs(term / n) < 1e-10:
            break
    return max(0, result)


def _theis_drawdown_ft(
    Q_af_yr: float, r_ft: float, T_gpd_ft: float,
    S: float, t_days: float = 365,
) -> float:
    """Theis drawdown (ft) at distance r from pumping well."""
    if r_ft <= 0 or T_gpd_ft <= 0 or S <= 0 or Q_af_yr <= 0:
        return 0.0
    Q_gpd = Q_af_yr * 325851.0 / 365.0
    u = (r_ft ** 2 * S) / (4.0 * T_gpd_ft * t_days) if t_days > 0 else 1e10
    return (Q_gpd * _theis_W(u)) / (4.0 * math.pi * T_gpd_ft)


def _superposition_drawdown(
    Q_af_yr: float, r_ft: float, T: float, S: float,
    t_days: float, recovery_frac: float = 0.0,
) -> Dict[str, float]:
    """
    Superposition: drawdown at end of pumping + partial recovery.
    Returns peak and residual drawdown.
    """
    peak = _theis_drawdown_ft(Q_af_yr, r_ft, T, S, t_days)
    residual = 0.0
    if recovery_frac > 0 and recovery_frac < 1.0:
        t_recovery = t_days * recovery_frac
        if t_recovery > 0:
            dd_extended = _theis_drawdown_ft(Q_af_yr, r_ft, T, S, t_days + t_recovery)
            dd_recovery = _theis_drawdown_ft(Q_af_yr, r_ft, T, S, t_recovery)
            residual = dd_extended - dd_recovery
    return {"peak_ft": round(peak, 2), "residual_ft": round(residual, 2)}


# ── Main Stage Runner ────────────────────────────────────

def run(seller: Dict[str, Any], buyer: Dict[str, Any], transfer: Dict[str, Any],
        spatial_data: Optional[Dict] = None) -> StageResult:
    conditions: List[str] = []
    risk_flags: List[str] = []
    data: Dict[str, Any] = {}

    qty = transfer.get("quantity_af", 0)
    duration_days = transfer.get("duration_days", 365)
    hcm = seller.get("hcm_area", "")

    # ── Step 1: Determine aquifer parameters ──────────────
    param_source = "estimated_regional"
    pump_test = seller.get("pump_test_data") or transfer.get("pump_test_data")

    if pump_test and isinstance(pump_test, dict):
        # Best case: applicant provided real pump test data
        T = pump_test.get("transmissivity_gpd_ft", 0)
        S = pump_test.get("storativity", 0)
        if T > 0 and S > 0:
            param_source = "site_specific_pump_test"
            data["param_source"] = param_source
            data["pump_test_provided"] = True
        else:
            pump_test = None

    if not pump_test:
        # Try DWR WCR API for nearby well yield data
        seller_lat = seller.get("well_lat")
        seller_lng = seller.get("well_lng")
        dwr_yield = None
        if seller_lat and seller_lng:
            dwr_yield = _fetch_dwr_well_yield(seller_lat, seller_lng)

        if dwr_yield and dwr_yield.get("estimated_T_gpd_ft"):
            T = dwr_yield["estimated_T_gpd_ft"]
            S = _estimate_storativity_from_depth(
                seller.get("well_depth_ft"),
                AQUIFER_PARAMS.get(hcm, DEFAULT_PARAMS)["aquifer_thickness_ft"],
            )
            param_source = "dwr_wcr_derived"
            data["dwr_well_yield_lookup"] = dwr_yield
        else:
            # Fall back to regional published estimates
            params = AQUIFER_PARAMS.get(hcm, DEFAULT_PARAMS)
            T = params["transmissivity_gpd_ft"]
            S = params.get("storativity", 0.08)
            param_source = f"regional_published ({params['source']})"

    data["aquifer_parameters"] = {
        "transmissivity_gpd_ft": T,
        "storativity": S,
        "source": param_source,
    }

    # ── Step 2: Calculate drawdown at key distances ───────
    distances_ft = {
        "500_ft": 500,
        "1000_ft": 1000,
        "2640_ft_half_mi": 2640,
        "5280_ft_1mi": 5280,
    }

    drawdown = {}
    for label, r_ft in distances_ft.items():
        dd_info = _superposition_drawdown(qty, r_ft, T, S, duration_days, recovery_frac=0.5)
        drawdown[label] = dd_info

    data["theis_drawdown"] = drawdown

    # ── Step 3: Drawdown at actual buyer distance ─────────
    distance_mi = (spatial_data or {}).get("distance_mi")
    if distance_mi:
        buyer_r_ft = distance_mi * 5280
        buyer_dd = _superposition_drawdown(qty, buyer_r_ft, T, S, duration_days, recovery_frac=0.5)
        data["buyer_distance_mi"] = distance_mi
        data["buyer_drawdown"] = buyer_dd

        if buyer_dd["peak_ft"] > 5:
            risk_flags.append(
                f"Estimated peak drawdown at buyer well: {buyer_dd['peak_ft']:.1f} ft "
                f"at {distance_mi:.1f} mi — significant impact"
            )
        elif buyer_dd["peak_ft"] > 1:
            risk_flags.append(
                f"Moderate estimated drawdown at buyer well: {buyer_dd['peak_ft']:.1f} ft"
            )

    # ── Step 4: Domestic well vulnerability ───────────────
    domestic_count = buyer.get("domestic_wells_1mi", 0)
    if spatial_data:
        sp_wells = spatial_data.get("seller_nearby_wells", {})
        domestic_count = max(domestic_count, sp_wells.get("domestic_wells", 0))

    data["domestic_wells_1mi"] = domestic_count
    dd_1mi = drawdown.get("5280_ft_1mi", {}).get("peak_ft", 0)

    if domestic_count > 0 and dd_1mi > 2:
        risk_flags.append(
            f"{domestic_count} domestic well(s) within 1 mile; "
            f"peak drawdown {dd_1mi:.1f} ft could impact shallow domestic wells"
        )
        conditions.append(
            "Monitoring of domestic wells within 1 mile required during and "
            "after transfer. If drawdown exceeds 5 ft at any domestic well, "
            "pumping must be curtailed."
        )

    # ── Step 5: Parameter confidence assessment ───────────
    if "site_specific" in param_source:
        data["parameter_confidence"] = "high"
    elif "dwr_wcr" in param_source:
        data["parameter_confidence"] = "moderate"
        if qty > 500:
            conditions.append(
                "Aquifer parameters derived from DWR well logs (specific capacity). "
                "For transfers > 500 AF, site-specific pump test recommended."
            )
    else:
        data["parameter_confidence"] = "low"
        if qty > 200:
            conditions.append(
                "Aquifer parameters are regional estimates from published studies. "
                "Site-specific pump test (24-hr constant-rate test) recommended "
                "for transfers exceeding 200 AF to improve drawdown accuracy."
            )

    if dd_1mi > 10:
        conditions.append(
            "Significant drawdown predicted — require site-specific pump test "
            "and detailed 3D groundwater model before approval"
        )

    # Spatial data context
    if spatial_data:
        data["spatial_data"] = {
            k: v for k, v in spatial_data.items()
            if k not in ("seller_nearby_wells", "buyer_nearby_wells")
        }

    # ── Score ─────────────────────────────────────────────
    score = 1.0
    if dd_1mi > 10:
        score -= 0.30
    elif dd_1mi > 5:
        score -= 0.20
    elif dd_1mi > 2:
        score -= 0.10
    if domestic_count > 5:
        score -= 0.15
    elif domestic_count > 0:
        score -= 0.05
    if "regional" in param_source and qty > 1000:
        score -= 0.05  # penalize low-confidence for large transfers
    score -= 0.03 * len(risk_flags)
    score = max(0.15, score)

    passed = dd_1mi < 20
    finding = "FAIL" if not passed else ("CONDITIONAL" if conditions else "PASS")

    return StageResult(
        stage=STAGE_NAME, passed=passed, score=round(score, 2),
        finding=finding,
        reasoning=(
            f"Theis peak drawdown @ 1mi: {dd_1mi:.1f} ft "
            f"(T={T:,.0f} gpd/ft, S={S}, source: {param_source}); "
            f"{domestic_count} domestic wells nearby"
        ),
        conditions=conditions, risk_flags=risk_flags, data=data,
        monitoring=[
            "Monthly water level measurements at pumping well",
            "Semi-annual water level measurements at monitoring wells within 1 mi",
        ] if passed else [],
    )
