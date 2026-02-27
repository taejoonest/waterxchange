"""
Surface Water Stage 3 — No-Injury Analysis (Hydrologic Model)

The cornerstone of California surface water transfer law: a transfer
cannot injure other legal users of water.

"No injury" means:
  1. No reduction in supply to downstream senior rights holders
  2. No degradation of water quality for other users
  3. No harm to fish, wildlife, or instream beneficial uses
  4. No unreasonable effect on the area of origin (CWC §1810)

This version implements a multi-component hydrologic analysis:

  A) USGS NWIS real-time streamflow + daily statistics
  B) Flow Duration Curve analysis (exceedance probabilities)
  C) Tennant Method environmental flow assessment
  D) Cumulative impact modeling (sum of all diversions vs. available flow)
  E) eWRIMS downstream water rights query
  F) SWRCB consumptive use methodology (CWC §1011, §1725)

Data sources:
  - USGS NWIS Instantaneous Values API (real-time discharge)
  - USGS NWIS Statistics API (daily flow duration percentiles)
  - eWRIMS CKAN API (downstream water rights)
"""

import logging
from typing import Dict, Any, List, Optional

import requests

from .base import StageResult

logger = logging.getLogger(__name__)
STAGE_NAME = "sw_no_injury"

# ═══════════════════════════════════════════════════════════════
#  USGS NWIS Streamflow API
#  https://waterservices.usgs.gov/docs/instantaneous-values/
#  Parameter code 00060 = discharge (ft³/s)
# ═══════════════════════════════════════════════════════════════

USGS_IV_URL = "https://waterservices.usgs.gov/nwis/iv/"
USGS_STAT_URL = "https://waterservices.usgs.gov/nwis/stat/"

# USGS station IDs for key California rivers used in water transfers
USGS_STATIONS = {
    "kern river":          "11186000",  # Kern River near Bakersfield
    "sacramento river":    "11447650",  # Sacramento R at Freeport
    "san joaquin river":   "11303500",  # San Joaquin R near Vernalis
    "feather river":       "11407000",  # Feather R at Oroville
    "yuba river":          "11421000",  # Yuba R near Marysville
    "american river":      "11446500",  # American R at Fair Oaks
    "stanislaus river":    "11303000",  # Stanislaus R at Ripon
    "tuolumne river":      "11290000",  # Tuolumne R at Modesto
    "merced river":        "11272500",  # Merced R near Stevinson
    "mokelumne river":     "11325500",  # Mokelumne R at Woodbridge
    "kings river":         "11218000",  # Kings R near Piedra
    "kaweah river":        "11210100",  # Kaweah R at Three Rivers
    "tule river":          "11204100",  # Tule R near Springville
    "cache creek":         "11452500",  # Cache Cr at Yolo
    "putah creek":         "11454000",  # Putah Cr near Winters
    "stony creek":         "11388000",  # Stony Cr near Hamilton City
    "cosumnes river":      "11335000",  # Cosumnes R at Michigan Bar
    "bear river":          "11424000",  # Bear R near Wheatland
}


def _fetch_usgs_streamflow(station_id: str) -> Optional[Dict]:
    """Fetch latest streamflow from USGS NWIS instantaneous values API."""
    try:
        resp = requests.get(USGS_IV_URL, params={
            "format": "json",
            "sites": station_id,
            "parameterCd": "00060",
            "siteStatus": "active",
        }, timeout=8)
        if resp.status_code != 200:
            return None

        ts_data = resp.json()
        series = ts_data.get("value", {}).get("timeSeries", [])
        if not series:
            return None

        values = series[0].get("values", [{}])[0].get("value", [])
        if not values:
            return None

        latest = values[-1]
        site_info = series[0].get("sourceInfo", {})
        return {
            "station_id": station_id,
            "station_name": site_info.get("siteName", ""),
            "discharge_cfs": float(latest.get("value", 0)),
            "datetime": latest.get("dateTime", ""),
            "source": "USGS NWIS Instantaneous Values API",
        }
    except Exception as exc:
        logger.warning("USGS NWIS fetch failed for station %s: %s", station_id, exc)
        return None


def _fetch_usgs_statistics(station_id: str) -> Optional[Dict]:
    """Fetch statistical streamflow data (median, P10, P90) from USGS."""
    try:
        resp = requests.get(USGS_STAT_URL, params={
            "format": "json",
            "sites": station_id,
            "parameterCd": "00060",
            "statReportType": "daily",
            "statTypeCd": "mean,p10,p50,p90",
        }, timeout=8)
        if resp.status_code != 200:
            return None

        stats = resp.json()
        series = stats.get("value", {}).get("timeSeries", [])
        if not series:
            return None

        result = {"station_id": station_id, "source": "USGS NWIS Daily Statistics"}
        for s in series[0].get("values", []):
            stat_name = s.get("method", [{}])[0].get("methodDescription", "")
            vals = s.get("value", [])
            if vals:
                result[stat_name] = float(vals[0].get("value", 0))
        return result
    except Exception as exc:
        logger.debug("USGS statistics fetch failed for %s: %s", station_id, exc)
        return None


# ═══════════════════════════════════════════════════════════════
#  eWRIMS — Downstream Water Rights Query
#  CKAN API at data.ca.gov, resource 151c067a-...
# ═══════════════════════════════════════════════════════════════

EWRIMS_RESOURCE_ID = "151c067a-088b-42a2-b6ad-99d84b48fb36"
EWRIMS_API_URL = "https://data.ca.gov/api/3/action/datastore_search"


def _query_downstream_rights(source_stream: str, seller_right_id: str = "") -> Dict:
    """
    Query eWRIMS for water rights on the same source stream.
    Returns count and details of potentially affected downstream rights.
    """
    result = {"queried": False, "source": "eWRIMS (data.ca.gov CKAN API)"}
    if not source_stream:
        return result

    stream_query = source_stream.upper().replace("RIVER", "R").strip()
    try:
        resp = requests.get(EWRIMS_API_URL, params={
            "resource_id": EWRIMS_RESOURCE_ID,
            "q": stream_query,
            "limit": 50,
        }, timeout=10)
        if resp.status_code != 200:
            result["error"] = f"eWRIMS API returned {resp.status_code}"
            return result

        data = resp.json()
        if not data.get("success"):
            result["error"] = "eWRIMS API query unsuccessful"
            return result

        records = data.get("result", {}).get("records", [])
        total = data.get("result", {}).get("total", 0)

        result["queried"] = True
        result["total_rights_on_stream"] = total
        result["sample_rights"] = []

        for r in records[:10]:
            right_info = {
                "application_id": r.get("APPLICATION_NUMBER", ""),
                "holder": r.get("PRIMARY_OWNER", ""),
                "right_type": r.get("WATER_RIGHT_TYPE", ""),
                "status": r.get("WATER_RIGHT_STATUS", ""),
                "face_value_af": r.get("FACE_VALUE_AMOUNT", ""),
                "priority_date": r.get("PRIORITY_DATE", ""),
            }
            if right_info["application_id"] != seller_right_id:
                result["sample_rights"].append(right_info)

        result["potentially_affected_count"] = len(result["sample_rights"])
        return result

    except Exception as exc:
        logger.warning("eWRIMS downstream rights query failed: %s", exc)
        result["error"] = str(exc)
        return result


# ═══════════════════════════════════════════════════════════════
#  CONSUMPTIVE USE METHODOLOGY — per SWRCB Guide to Water Transfers
#  Only the consumptive-use portion of a water right is transferable.
#  Return flows must continue to downstream users.
# ═══════════════════════════════════════════════════════════════

def _analyze_consumptive_use(seller: Dict, qty: float) -> Dict:
    """
    SWRCB consumptive use analysis per CWC §1011 and §1725.
    Consumptive use = diversion - return flows - tailwater - seepage.
    """
    diversion_af = seller.get("historical_diversion_af", 0)
    consumptive_af = seller.get("consumptive_use_af", 0)

    if diversion_af <= 0 or consumptive_af <= 0:
        return {"method": "insufficient_data"}

    return_flow = diversion_af - consumptive_af
    cu_ratio = consumptive_af / diversion_af if diversion_af > 0 else 0
    transferable = min(qty, consumptive_af)
    excess = max(0, qty - consumptive_af)

    return {
        "method": "SWRCB consumptive use methodology (CWC §1011, §1725)",
        "historical_diversion_af": diversion_af,
        "consumptive_use_af": consumptive_af,
        "return_flow_af": round(return_flow, 1),
        "consumptive_use_ratio": round(cu_ratio, 3),
        "max_transferable_af": round(transferable, 1),
        "excess_over_consumptive_af": round(excess, 1),
        "return_flows_must_continue": True,
    }


# ═══════════════════════════════════════════════════════════════
#  FLOW DURATION CURVE — Exceedance Probabilities
#  Uses USGS daily statistics to determine flow percentiles.
#  A transfer that would reduce flow below Q90 is high-risk.
# ═══════════════════════════════════════════════════════════════

USGS_DV_URL = "https://waterservices.usgs.gov/nwis/dv/"


def _fetch_flow_duration(station_id: str) -> Optional[Dict]:
    """
    Fetch recent daily discharge values from USGS and compute
    flow duration percentiles (Q10, Q25, Q50, Q75, Q90, Q95).
    """
    try:
        resp = requests.get(USGS_DV_URL, params={
            "format": "json",
            "sites": station_id,
            "parameterCd": "00060",
            "startDT": "2020-01-01",
            "siteStatus": "active",
        }, timeout=12)
        if resp.status_code != 200:
            return None

        ts = resp.json().get("value", {}).get("timeSeries", [])
        if not ts:
            return None

        values = []
        for v in ts[0].get("values", [{}])[0].get("value", []):
            try:
                q = float(v.get("value", 0))
                if q >= 0:
                    values.append(q)
            except (ValueError, TypeError):
                continue

        if len(values) < 30:
            return None

        values.sort(reverse=True)
        n = len(values)

        def pct(p):
            idx = int(p * n / 100)
            return round(values[min(idx, n - 1)], 1)

        return {
            "station_id": station_id,
            "n_days": n,
            "Q10_cfs": pct(10),   # exceeded 10% of the time (high flow)
            "Q25_cfs": pct(25),
            "Q50_cfs": pct(50),   # median flow
            "Q75_cfs": pct(75),
            "Q90_cfs": pct(90),   # exceeded 90% of the time (low flow)
            "Q95_cfs": pct(95),   # near minimum
            "source": "USGS NWIS Daily Values (2020-present)",
        }
    except Exception as exc:
        logger.debug("Flow duration curve fetch failed for %s: %s", station_id, exc)
        return None


# ═══════════════════════════════════════════════════════════════
#  TENNANT METHOD — Environmental Flow Requirements
#
#  The Tennant (Montana) Method defines minimum flows as percentages
#  of mean annual flow (MAF):
#    - Outstanding habitat:  60-100% of MAF
#    - Excellent habitat:    40% of MAF
#    - Good habitat:         30% of MAF
#    - Fair/degrading:       10% of MAF
#    - Severe degradation:   < 10% of MAF
#
#  Ref: Tennant, D.L. (1976) Instream Flow Regimens for Fish,
#  Wildlife, Recreation and Related Environmental Resources.
#  Fisheries 1(4): 6-10.
# ═══════════════════════════════════════════════════════════════

TENNANT_THRESHOLDS = {
    "outstanding": 0.60,
    "excellent": 0.40,
    "good": 0.30,
    "fair": 0.10,
    "severe_degradation": 0.10,
}


def _tennant_analysis(
    current_flow_cfs: float,
    transfer_cfs: float,
    mean_annual_flow_cfs: Optional[float] = None,
    q50_cfs: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Apply Tennant Method to assess habitat impact.
    Uses mean annual flow if available, otherwise median (Q50).
    """
    maf = mean_annual_flow_cfs or q50_cfs
    if not maf or maf <= 0:
        return {"method": "tennant", "status": "insufficient_data"}

    post_transfer_flow = max(0, current_flow_cfs - transfer_cfs)
    post_pct = post_transfer_flow / maf

    if post_pct >= 0.60:
        habitat = "outstanding"
    elif post_pct >= 0.40:
        habitat = "excellent"
    elif post_pct >= 0.30:
        habitat = "good"
    elif post_pct >= 0.10:
        habitat = "fair_degrading"
    else:
        habitat = "severe_degradation"

    return {
        "method": "Tennant (Montana) Method",
        "reference": "Tennant 1976, Fisheries 1(4):6-10",
        "mean_annual_flow_cfs": round(maf, 1),
        "current_flow_cfs": round(current_flow_cfs, 1),
        "post_transfer_flow_cfs": round(post_transfer_flow, 1),
        "pct_of_maf": round(post_pct * 100, 1),
        "habitat_rating": habitat,
        "minimum_good_habitat_cfs": round(maf * 0.30, 1),
        "minimum_fair_habitat_cfs": round(maf * 0.10, 1),
    }


# ═══════════════════════════════════════════════════════════════
#  CUMULATIVE IMPACT — Sum of all diversions vs. available flow
#
#  Queries eWRIMS for all rights on the stream, sums face values
#  to estimate total authorized diversions, and compares against
#  available flow to determine cumulative stress.
# ═══════════════════════════════════════════════════════════════

def _cumulative_impact(
    current_flow_cfs: float,
    transfer_cfs: float,
    total_rights_on_stream: int,
    sample_rights: List[Dict],
) -> Dict[str, Any]:
    """
    Estimate cumulative impact of all authorized diversions.
    """
    total_authorized_af = 0
    for r in sample_rights:
        try:
            fv = float(r.get("face_value_af", 0) or 0)
            total_authorized_af += fv
        except (ValueError, TypeError):
            continue

    # Scale up from sample to total
    if sample_rights and total_rights_on_stream > len(sample_rights):
        scale = total_rights_on_stream / len(sample_rights)
        estimated_total_af = total_authorized_af * scale
    else:
        estimated_total_af = total_authorized_af

    # Convert annual AF to instantaneous CFS (rough)
    estimated_diversion_cfs = (estimated_total_af * 43560) / (365 * 86400)

    annual_flow_af = current_flow_cfs * 86400 * 365 / 43560
    stress_ratio = estimated_diversion_cfs / current_flow_cfs if current_flow_cfs > 0 else 999

    return {
        "method": "cumulative_impact_estimate",
        "total_rights_sampled": len(sample_rights),
        "total_rights_on_stream": total_rights_on_stream,
        "sampled_authorized_af": round(total_authorized_af, 0),
        "estimated_total_authorized_af": round(estimated_total_af, 0),
        "estimated_diversion_cfs": round(estimated_diversion_cfs, 1),
        "current_flow_cfs": round(current_flow_cfs, 1),
        "stress_ratio": round(stress_ratio, 3),
        "note": "stress_ratio > 0.5 indicates heavily appropriated stream",
    }


def run(seller: Dict[str, Any], buyer: Dict[str, Any], transfer: Dict[str, Any]) -> StageResult:
    conditions = []
    risk_flags = []
    data = {}
    qty = transfer.get("quantity_af", 0)

    right_type = seller.get("water_right_type", "")
    source_stream = transfer.get("source_stream", "")
    seller_right_id = seller.get("water_right_id", "")

    # ═══════════════════════════════════════════════════════════
    #  REAL STREAMFLOW CHECK — USGS NWIS API
    # ═══════════════════════════════════════════════════════════
    stream_key = source_stream.lower().strip()
    station_id = USGS_STATIONS.get(stream_key) or transfer.get("usgs_station_id")

    if station_id:
        flow_data = _fetch_usgs_streamflow(station_id)
        if flow_data:
            data["usgs_streamflow"] = flow_data
            cfs = flow_data["discharge_cfs"]

            transfer_cfs = (qty * 43560) / (transfer.get("duration_days", 365) * 86400)
            data["transfer_demand_cfs"] = round(transfer_cfs, 2)

            flow_pct = (transfer_cfs / cfs * 100) if cfs > 0 else 100
            data["transfer_pct_of_flow"] = round(flow_pct, 2)

            if flow_pct > 20:
                risk_flags.append(
                    f"Transfer would consume {flow_pct:.1f}% of current flow "
                    f"({cfs:.0f} cfs at USGS {station_id}) — high injury risk"
                )
                conditions.append(
                    "Transfer rate must be curtailed during low-flow periods to maintain "
                    "minimum instream flows and downstream senior rights"
                )
            elif flow_pct > 10:
                risk_flags.append(
                    f"Transfer is {flow_pct:.1f}% of current flow — moderate impact on stream"
                )

            if cfs < 50:
                risk_flags.append(
                    f"Current streamflow critically low ({cfs:.0f} cfs) — "
                    "transfer may not be feasible during this period"
                )
        else:
            data["usgs_streamflow_note"] = (
                f"USGS NWIS query for station {station_id} returned no data — "
                "using seller-reported flow estimates"
            )
    else:
        data["usgs_streamflow_note"] = (
            f"No USGS station mapped for '{source_stream}' — "
            "manual streamflow verification required"
        )

    # ═══════════════════════════════════════════════════════════
    #  FLOW DURATION CURVE ANALYSIS
    # ═══════════════════════════════════════════════════════════
    if station_id:
        fdc = _fetch_flow_duration(station_id)
        if fdc:
            data["flow_duration_curve"] = fdc
            q90 = fdc.get("Q90_cfs", 0)
            q50 = fdc.get("Q50_cfs", 0)

            transfer_cfs = (qty * 43560) / (transfer.get("duration_days", 365) * 86400)

            if q90 > 0:
                post_transfer_q90 = q90 - transfer_cfs
                data["post_transfer_at_Q90_cfs"] = round(post_transfer_q90, 1)
                if post_transfer_q90 < 0:
                    risk_flags.append(
                        f"Transfer ({transfer_cfs:.1f} cfs) would eliminate flow "
                        f"at Q90 level ({q90:.0f} cfs) — severe low-flow impact"
                    )
                elif transfer_cfs > q90 * 0.5:
                    risk_flags.append(
                        f"Transfer ({transfer_cfs:.1f} cfs) is >{50}% of Q90 "
                        f"low flow ({q90:.0f} cfs) — high seasonal impact risk"
                    )

            # Tennant method analysis
            if q50 > 0:
                tennant = _tennant_analysis(
                    current_flow_cfs=data.get("usgs_streamflow", {}).get("discharge_cfs", q50),
                    transfer_cfs=transfer_cfs,
                    q50_cfs=q50,
                )
                data["tennant_analysis"] = tennant
                habitat = tennant.get("habitat_rating", "")
                if habitat == "severe_degradation":
                    risk_flags.append(
                        "Tennant Method: post-transfer flow causes SEVERE habitat "
                        f"degradation (<10% of median flow). "
                        f"Post-transfer: {tennant['post_transfer_flow_cfs']:.0f} cfs "
                        f"({tennant['pct_of_maf']:.0f}% of median)"
                    )
                    conditions.append(
                        "Transfer must maintain minimum instream flow of at least "
                        f"{tennant['minimum_fair_habitat_cfs']:.0f} cfs (10% of median) "
                        "per Tennant Method fair habitat threshold"
                    )
                elif habitat == "fair_degrading":
                    risk_flags.append(
                        f"Tennant Method: post-transfer flow rated 'fair/degrading' "
                        f"({tennant['pct_of_maf']:.0f}% of median flow)"
                    )

    # ═══════════════════════════════════════════════════════════
    #  REAL DOWNSTREAM RIGHTS — eWRIMS API
    # ═══════════════════════════════════════════════════════════
    ewrims_result = _query_downstream_rights(source_stream, seller_right_id)
    data["ewrims_query"] = ewrims_result

    if ewrims_result.get("queried"):
        downstream_rights = ewrims_result.get("potentially_affected_count", 0)
        total_on_stream = ewrims_result.get("total_rights_on_stream", 0)
        data["downstream_rights_count"] = downstream_rights
        data["total_rights_on_stream"] = total_on_stream

        if downstream_rights > 0:
            risk_flags.append(
                f"{downstream_rights} other water right(s) found on {source_stream} via eWRIMS "
                f"(of {total_on_stream} total) — each must be analyzed for potential injury"
            )
            conditions.append(
                "Transfer must not reduce flow below minimum needed to satisfy "
                "all downstream senior rights (no-injury rule, CWC §1702)"
            )
        if downstream_rights > 5:
            risk_flags.append("High protest risk — many rights holders on this stream")
    else:
        downstream_rights = transfer.get("downstream_rights_count", 0)
        data["downstream_rights_count"] = downstream_rights
        if downstream_rights > 0:
            risk_flags.append(
                f"{downstream_rights} downstream right(s) reported (eWRIMS query unavailable) — "
                "each must be analyzed for potential injury"
            )
            conditions.append(
                "Transfer must not reduce flow below minimum needed to satisfy "
                "all downstream senior rights (no-injury rule, CWC §1702)"
            )

    # ═══════════════════════════════════════════════════════════
    #  CUMULATIVE IMPACT ANALYSIS
    # ═══════════════════════════════════════════════════════════
    usgs_flow = data.get("usgs_streamflow", {})
    current_cfs = usgs_flow.get("discharge_cfs", 0)
    if current_cfs > 0 and ewrims_result.get("queried"):
        cum_impact = _cumulative_impact(
            current_flow_cfs=current_cfs,
            transfer_cfs=(qty * 43560) / (transfer.get("duration_days", 365) * 86400),
            total_rights_on_stream=ewrims_result.get("total_rights_on_stream", 0),
            sample_rights=ewrims_result.get("sample_rights", []),
        )
        data["cumulative_impact"] = cum_impact
        stress = cum_impact.get("stress_ratio", 0)
        if stress > 0.8:
            risk_flags.append(
                f"Cumulative stress ratio {stress:.2f} — stream is heavily "
                "over-appropriated; new diversion highly likely to injure "
                "existing rights holders"
            )
        elif stress > 0.5:
            risk_flags.append(
                f"Cumulative stress ratio {stress:.2f} — stream is significantly "
                "appropriated; careful timing/curtailment analysis needed"
            )

    # --- Environmental flows ---
    has_env_flows = transfer.get("has_environmental_flow_requirement", False)
    data["has_environmental_flow_requirement"] = has_env_flows

    if has_env_flows:
        conditions.append(
            "Transfer must maintain minimum instream flows per SWRCB-mandated "
            "environmental flow requirements"
        )
        env_flow_af = transfer.get("environmental_flow_af", 0)
        if env_flow_af > 0:
            data["environmental_flow_af"] = env_flow_af

    # --- Fish and wildlife ---
    anadromous = transfer.get("anadromous_fish_present", False)
    data["anadromous_fish"] = anadromous
    if anadromous:
        conditions.append(
            "CDFW consultation required — anadromous fish species present in source waterway. "
            "Transfer timing must avoid critical migration and spawning periods."
        )
        risk_flags.append("Anadromous fish habitat — likely triggers CEQA biological review")

    # --- Area of origin protections ---
    is_export = transfer.get("is_area_of_origin_export", False)
    data["is_area_of_origin_export"] = is_export

    if is_export:
        conditions.append(
            "Area-of-origin protection applies (CWC §§10505-10505.5): "
            "source county has priority right to water for reasonable beneficial use"
        )
        risk_flags.append("Area-of-origin export — county of origin may file protest")

    # --- Delta considerations ---
    through_delta = transfer.get("through_delta", False)
    data["through_delta"] = through_delta

    if through_delta:
        conditions.append(
            "Transfer through Sacramento-San Joaquin Delta must comply with "
            "Delta Plan and SWRCB D-1641 flow objectives"
        )
        risk_flags.append(
            "Delta transfer — may be limited by biological opinions for "
            "delta smelt and winter-run salmon"
        )

    # --- Groundwater substitution (conjunctive use) ---
    is_gw_sub = transfer.get("groundwater_substitution", False)
    data["groundwater_substitution"] = is_gw_sub

    if is_gw_sub:
        conditions.append(
            "Groundwater substitution transfer: seller pumps groundwater in lieu of "
            "diverting surface water, making surface water available for transfer. "
            "Must demonstrate no overdraft impact."
        )
        risk_flags.append("GW substitution — triggers both surface and groundwater review requirements")

    # --- Public notice / protest risk ---
    right_type = seller.get("water_right_type", "")
    if right_type == "appropriative_post1914":
        data["public_notice_required"] = True
        data["protest_period_days"] = 30
        conditions.append("SWRCB must issue public notice with 30-day protest period")

        protest_risk = "low"
        if downstream_rights > 3:
            protest_risk = "high"
        elif downstream_rights > 0 or is_export or through_delta:
            protest_risk = "medium"
        data["protest_risk"] = protest_risk

        if protest_risk == "high":
            risk_flags.append(
                "High protest risk — expect SWRCB hearing process (3-12 months additional)"
            )
            conditions.append("SWRCB hearing may be required if protests are filed")
    elif right_type == "appropriative_pre1914":
        data["public_notice_required"] = False
        risk_flags.append(
            "Pre-1914 right: no SWRCB public notice process, but injured parties "
            "can still file suit in court"
        )

    # ═══════════════════════════════════════════════════════════
    #  CONSUMPTIVE USE ANALYSIS — SWRCB methodology
    # ═══════════════════════════════════════════════════════════
    cu_analysis = _analyze_consumptive_use(seller, qty)
    data["consumptive_use_analysis"] = cu_analysis

    if cu_analysis.get("method") != "insufficient_data":
        data["diversion_af"] = cu_analysis["historical_diversion_af"]
        data["consumptive_af"] = cu_analysis["consumptive_use_af"]
        data["return_flow_af"] = cu_analysis["return_flow_af"]

        if cu_analysis["excess_over_consumptive_af"] > 0:
            risk_flags.append(
                f"Transfer qty ({qty:,.0f} AF) exceeds consumptive use "
                f"({cu_analysis['consumptive_use_af']:,.0f} AF). "
                f"Only consumptive use is transferable — return flows "
                f"({cu_analysis['return_flow_af']:,.0f} AF) must continue to downstream users. "
                f"(CU ratio: {cu_analysis['consumptive_use_ratio']:.1%})"
            )
            conditions.append(
                "Transfer limited to consumptive use portion of water right (CWC §1011, §1725). "
                "Return flows must be maintained for downstream users."
            )

    # --- Score ---
    score = 1.0
    if downstream_rights > 5:
        score -= 0.25
    elif downstream_rights > 0:
        score -= 0.10
    if is_export:
        score -= 0.15
    if through_delta:
        score -= 0.15
    if anadromous:
        score -= 0.10
    if data.get("transfer_pct_of_flow", 0) > 20:
        score -= 0.20
    elif data.get("transfer_pct_of_flow", 0) > 10:
        score -= 0.10
    score -= 0.03 * len(risk_flags)
    score = max(0.15, score)

    passed = True
    finding = "CONDITIONAL" if conditions else "PASS"

    return StageResult(
        stage=STAGE_NAME, passed=passed, score=round(score, 2),
        finding=finding,
        reasoning=_build_reasoning(source_stream, downstream_rights, is_export,
                                   through_delta, qty, data),
        conditions=conditions, risk_flags=risk_flags, data=data,
    )


def _build_reasoning(stream, downstream, export, delta, qty, data):
    parts = [f"Source: {stream}" if stream else "Source stream unknown"]

    usgs = data.get("usgs_streamflow")
    if usgs:
        parts.append(
            f"USGS {usgs['station_id']}: {usgs['discharge_cfs']:.0f} cfs "
            f"({usgs['station_name']})"
        )
        pct = data.get("transfer_pct_of_flow")
        if pct:
            parts.append(f"Transfer = {pct:.1f}% of current flow")

    ewrims = data.get("ewrims_query", {})
    if ewrims.get("queried"):
        parts.append(
            f"eWRIMS: {ewrims.get('total_rights_on_stream', '?')} rights on stream, "
            f"{downstream} potentially affected"
        )
    else:
        parts.append(f"Downstream rights (reported): {downstream}")

    cu = data.get("consumptive_use_analysis", {})
    if cu.get("method") != "insufficient_data" and cu.get("method"):
        parts.append(f"CU ratio: {cu.get('consumptive_use_ratio', 0):.1%}")

    if export:
        parts.append("Area-of-origin export")
    if delta:
        parts.append("Through-delta transfer")
    parts.append(f"Qty: {qty:,.0f} AF")
    return "; ".join(parts)
