"""
WaterXchange Compliance Engine
The core intelligence: generates compliance questions from policies,
retrieves relevant policy text, and uses the LLM to reason through
each question using farmer data + hydrology data.
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from services.policy_engine import PolicyEngine, PolicyChunk


# ─────────────────────────────────────────────────────────────────
# COMPLIANCE QUESTIONS
# These are generated from the actual policy categories.
# In production, the LLM would generate these dynamically.
# Here we define them based on real GSP/SGMA requirements.
# ─────────────────────────────────────────────────────────────────

COMPLIANCE_QUESTIONS = [
    {
        "id": "Q1",
        "question": "Does the seller have a verified surplus above their allocation that can legally be transferred?",
        "category": "transfer",
        "data_needed": ["seller.annual_gsa_allocation_af", "seller.total_available_af", 
                        "seller.crop_water_demand_af", "seller.surplus_af", "seller.transfer_quantity_af"],
        "policy_categories": ["transfer", "water_budget"],
        "severity": "critical",  # Must pass
    },
    {
        "id": "Q2",
        "question": "Will this transfer cause the seller's extraction to exceed their GSA allocation?",
        "category": "sustainability_criteria",
        "data_needed": ["seller.total_annual_extraction_af", "seller.annual_gsa_allocation_af", 
                        "seller.transfer_quantity_af"],
        "policy_categories": ["sustainability_criteria", "wells"],
        "severity": "critical",
    },
    {
        "id": "Q3",
        "question": "Will the buyer's total extraction (allocation + transferred water) push groundwater levels below the Minimum Threshold at their location?",
        "category": "groundwater_levels",
        "data_needed": ["buyer.hcm_gw_level_decline_ft_per_yr", "buyer.hcm_area",
                        "buyer.total_annual_extraction_af", "buyer.additional_requested_af",
                        "hydrology.groundwater_levels_by_hcm"],
        "policy_categories": ["groundwater_levels", "sustainability_criteria"],
        "severity": "critical",
    },
    {
        "id": "Q4",
        "question": "Is the buyer's area experiencing subsidence that could be worsened by additional extraction?",
        "category": "subsidence",
        "data_needed": ["buyer.hcm_subsidence_rate_ft_per_yr", "buyer.hcm_subsidence_rate_mt_ft_per_yr",
                        "buyer.hcm_subsidence_extent_mt_ft", "buyer.hcm_area",
                        "hydrology.subsidence_by_hcm"],
        "policy_categories": ["subsidence", "sustainability_criteria"],
        "severity": "high",
    },
    {
        "id": "Q5",
        "question": "Are there water quality concerns (nitrate, arsenic, TDS) at either party's wells that could be exacerbated by changed pumping patterns?",
        "category": "water_quality",
        "data_needed": ["buyer.groundwater_quality_nitrate_mg_l",
                        "hydrology.water_quality"],
        "policy_categories": ["water_quality", "sustainability_criteria"],
        "severity": "high",
    },
    {
        "id": "Q6",
        "question": "Could increased extraction by the buyer cause well interference with nearby domestic wells?",
        "category": "wells",
        "data_needed": ["buyer.domestic_wells_within_1mi",
                        "buyer.wells", "buyer.additional_requested_af"],
        "policy_categories": ["wells", "sustainability_criteria"],
        "severity": "high",
    },
    {
        "id": "Q7",
        "question": "Are both parties' wells properly metered and reporting extraction data as required by the GSP?",
        "category": "monitoring",
        "data_needed": ["seller.has_metered_wells", "buyer.has_metered_wells",
                        "seller.wells", "buyer.wells"],
        "policy_categories": ["monitoring", "wells"],
        "severity": "critical",
    },
    {
        "id": "Q8",
        "question": "Given that the Kern County Subbasin is Critically Overdrafted, does this transfer comply with the basin's overdraft reduction timeline?",
        "category": "water_budget",
        "data_needed": ["hydrology.water_budget", "hydrology.basin_priority",
                        "seller.surplus_af", "buyer.deficit_af"],
        "policy_categories": ["water_budget", "sustainability_criteria", "projects_actions"],
        "severity": "critical",
    },
    {
        "id": "Q9",
        "question": "Does the buyer have a history of over-extraction or compliance violations that should affect approval?",
        "category": "gsa_governance",
        "data_needed": ["buyer.past_violations", "buyer.extraction_within_allocation",
                        "buyer.gsa_membership_status"],
        "policy_categories": ["gsa_governance", "monitoring"],
        "severity": "medium",
    },
    {
        "id": "Q10",
        "question": "Are there interconnected surface water or groundwater-dependent ecosystem impacts to consider?",
        "category": "sustainability_criteria",
        "data_needed": ["seller.gde_within_1000ft", "buyer.gde_within_1000ft"],
        "policy_categories": ["sustainability_criteria"],
        "severity": "medium",
    },
    {
        "id": "Q11",
        "question": "Do both parties belong to GSAs within the same basin, and do those GSAs have a coordination agreement that permits inter-GSA transfers?",
        "category": "gsa_governance",
        "data_needed": ["seller.gsa", "buyer.gsa", "seller.basin", "buyer.basin"],
        "policy_categories": ["gsa_governance", "transfer"],
        "severity": "critical",
    },
    {
        "id": "Q12",
        "question": "Under current drought conditions and SWP allocation levels, should additional transfer restrictions apply?",
        "category": "water_budget",
        "data_needed": ["hydrology.climate"],
        "policy_categories": ["water_budget", "sustainability_criteria"],
        "severity": "medium",
    },
]


def get_data_for_question(question: Dict, seller: Dict, buyer: Dict, hydrology: Dict) -> str:
    """Extract the specific data needed for a compliance question."""
    lines = []
    for field in question["data_needed"]:
        parts = field.split(".")
        if parts[0] == "seller":
            value = seller
            label = f"Seller ({seller['name']})"
        elif parts[0] == "buyer":
            value = buyer
            label = f"Buyer ({buyer['name']})"
        elif parts[0] == "hydrology":
            value = hydrology
            label = "Basin Hydrology"
        else:
            continue

        # Navigate nested dict
        for key in parts[1:]:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                value = "N/A"
                break

        # Format the value
        if isinstance(value, dict):
            lines.append(f"  {label} — {parts[-1]}:")
            for k, v in value.items():
                lines.append(f"    {k}: {v}")
        elif isinstance(value, list):
            lines.append(f"  {label} — {parts[-1]}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"    • {json.dumps(item, default=str)}")
                else:
                    lines.append(f"    • {item}")
        else:
            lines.append(f"  {label} — {parts[-1]}: {value}")

    return "\n".join(lines) if lines else "  No specific data available."


def build_compliance_prompt(
    question: Dict,
    data_context: str,
    policy_text: str,
    seller: Dict,
    buyer: Dict,
) -> str:
    """
    Build the full prompt for the LLM to reason through a compliance question.
    This is the core of the RAG pipeline.
    """
    prompt = f"""You are a SGMA compliance analyst for the WaterXchange platform.

TRANSFER UNDER REVIEW:
  Transfer ID: WXT-2026-0042
  Seller: {seller['name']} ({seller['farm_name']}) — {seller['gsa']}
  Buyer: {buyer['name']} ({buyer['farm_name']}) — {buyer['gsa']}
  Quantity: 150 AF (acre-feet)
  Basin: Kern County Subbasin (Critically Overdrafted)
  Type: Intra-basin groundwater credit transfer

COMPLIANCE QUESTION:
  {question['question']}

RELEVANT DATA:
{data_context}

APPLICABLE POLICY TEXT (from Kern County GSP 2025 and CA Water Rights Law):
{policy_text}

INSTRUCTIONS:
1. Analyze the data against the policy requirements
2. State your finding: PASS, CONDITIONAL PASS, or FAIL
3. Explain your reasoning with specific citations to the policy text (cite source document and page number)
4. If CONDITIONAL PASS, state what conditions must be met
5. Note any risks or concerns even if passing
6. Be specific — use actual numbers from the data

Respond in this format:
FINDING: [PASS / CONDITIONAL PASS / FAIL]
REASONING: [Your detailed analysis with policy citations]
CONDITIONS: [If conditional, list conditions. Otherwise "None"]
RISKS: [Any concerns worth noting]"""
    return prompt


def build_verdict_prompt(
    question_results: List[Dict],
    seller: Dict,
    buyer: Dict,
    hydrology: Dict,
) -> str:
    """Build the prompt for the final verdict after all questions are answered."""
    results_text = ""
    for qr in question_results:
        results_text += f"\n{qr['id']}: {qr['question']}\n"
        results_text += f"  Finding: {qr['finding']}\n"
        results_text += f"  Severity: {qr['severity']}\n"
        results_text += f"  Summary: {qr['summary'][:200]}\n"

    prompt = f"""You are the chief compliance officer for WaterXchange.

TRANSFER UNDER REVIEW:
  Transfer ID: WXT-2026-0042
  Seller: {seller['name']} ({seller['farm_name']}) → Buyer: {buyer['name']} ({buyer['farm_name']})
  Quantity: 150 AF | Price: $415/AF | Total: $62,250
  Basin: Kern County Subbasin (Critically Overdrafted)

COMPLIANCE ANALYSIS RESULTS:
{results_text}

BASIN STATUS:  [All data from Kern County GSP 2025]
  Change in Storage (baseline): {hydrology['water_budget']['change_in_storage_baseline_afy']:,} AFY  [GSP p.54]
  Sustainable Yield: {hydrology['sustainable_yield']['total_afy']:,} AFY  [GSP p.595]
  Total GW Pumping: {hydrology['water_budget']['total_groundwater_pumping_afy']:,} AFY  [GSP p.595]
  Projected Deficit (2030 CC): {hydrology['water_budget']['projected_deficit_2030_climate_afy']:,} AFY  [GSP p.776]

Based on the above analysis of all 12 compliance questions:
1. Issue your FINAL VERDICT: APPROVED, CONDITIONALLY APPROVED, or DENIED
2. Summarize the key findings
3. List ALL conditions that must be met (if conditionally approved)
4. Specify monitoring requirements
5. Note the policy basis for your decision (cite specific GSP sections and SGMA statute)

Format your response clearly with headers."""
    return prompt
