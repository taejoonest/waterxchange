#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║           WaterXchange — Compliance Engine Demo                  ║
║                                                                  ║
║  Demonstrates how our AI reads real SGMA policies,              ║
║  ingests farmer + hydrology data, generates compliance          ║
║  questions, and produces a legally-grounded transfer verdict.   ║
╚══════════════════════════════════════════════════════════════════╝

Run:
  cd backend
  source venv/bin/activate
  python demo_compliance.py

Requires: OPENAI_API_KEY or ANTHROPIC_API_KEY in .env or environment
"""

import os
import sys
import json
import time
import asyncio
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from services.policy_engine import PolicyEngine
from services.farmer_data import (
    get_farmer_a_seller, get_farmer_b_buyer,
    get_transfer_details, get_hydrology_data,
    format_farmer_profile
)
from services.compliance_engine import (
    COMPLIANCE_QUESTIONS, get_data_for_question,
    build_compliance_prompt, build_verdict_prompt
)


# ─────────────────────────────────────────────────────────────
# ANSI Colors for terminal output
# ─────────────────────────────────────────────────────────────
class C:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'


def slow_print(text: str, delay: float = 0.01):
    """Print text character by character for dramatic effect."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        if delay > 0 and char in ['\n', '.', ',']:
            time.sleep(delay)
    print()


def print_header(title: str):
    width = 70
    print(f"\n{C.BOLD}{C.CYAN}{'═'*width}{C.END}")
    print(f"{C.BOLD}{C.CYAN}  {title}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'═'*width}{C.END}\n")


def print_subheader(title: str):
    print(f"\n{C.BOLD}{C.BLUE}── {title} ──{C.END}\n")


INTERACTIVE = True  # Set to False to auto-advance

def wait_for_enter(prompt: str = "Press ENTER to continue..."):
    if INTERACTIVE:
        print(f"\n{C.DIM}{prompt}{C.END}")
        try:
            input()
        except EOFError:
            pass
    else:
        print(f"\n{C.DIM}─── advancing ───{C.END}\n")
        time.sleep(1)


# ─────────────────────────────────────────────────────────────
# LLM CLIENT
# ─────────────────────────────────────────────────────────────

class LLMClient:
    """Unified LLM client for the demo. Supports Gemini, OpenAI, and Anthropic."""

    def __init__(self):
        self.provider = None
        self.client = None
        self._init()

    def _init(self):
        # Try Gemini first (Google AI)
        api_key = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel("gemini-2.0-flash")
                self.provider = "gemini"
                return
            except ImportError:
                pass

        # Try OpenAI
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
                self.provider = "openai"
                return
            except ImportError:
                pass

        # Try Anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=api_key)
                self.provider = "anthropic"
                return
            except ImportError:
                pass

        self.provider = None

    def call(self, system_prompt: str, user_prompt: str) -> str:
        """Call the LLM and return the response text."""
        if self.provider == "gemini":
            full_prompt = f"{system_prompt}\n\n---\n\n{user_prompt}"
            response = self.client.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 1200,
                }
            )
            return response.text

        elif self.provider == "openai":
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
            )
            return response.choices[0].message.content

        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=1000,
            )
            return response.content[0].text

        else:
            return None


# ─────────────────────────────────────────────────────────────
# DEMO SCRIPT
# ─────────────────────────────────────────────────────────────

async def run_demo():
    """Main demo flow."""

    os.system('clear' if os.name != 'nt' else 'cls')

    print(f"""{C.BOLD}{C.CYAN}
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║         🌊  W A T E R X C H A N G E  🌊                    ║
    ║                                                              ║
    ║         SGMA Compliance Engine — Live Demo                   ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    {C.END}""")

    print(f"""
    {C.DIM}This demo shows exactly how WaterXchange uses AI to evaluate
    a groundwater transfer for SGMA compliance — step by step.

    We will:
    1. Ingest real policy text from the Kern County GSP & SGMA statute
    2. Load detailed farmer profiles and hydrologic data
    3. Generate compliance questions derived from the policies
    4. Use the LLM to reason through each question with real data
    5. Produce a legally-grounded verdict with policy citations{C.END}
    """)

    wait_for_enter()

    # ─────────────────────────────────────────────
    # ACT 1: Policy Ingestion
    # ─────────────────────────────────────────────
    print_header("ACT 1: POLICY INGESTION")
    print(f"  {C.YELLOW}Loading real policy documents...{C.END}\n")

    policy_engine = PolicyEngine()
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "policies")
    stats = policy_engine.load_policies(data_dir)

    time.sleep(0.5)
    print(f"  {C.GREEN}✓{C.END} Kern County Subbasin GSP 2025 (3,155 pages / 280 MB)")
    print(f"    → Extracted {stats['gsp_chunks']} relevant policy sections")
    time.sleep(0.3)
    print(f"  {C.GREEN}✓{C.END} CA Statutory Water Rights Law / SGMA (461 pages)")
    print(f"    → Extracted {stats['sgma_chunks']} relevant statute sections")
    time.sleep(0.3)
    print(f"\n  {C.BOLD}Total: {stats['total_chunks']} policy chunks indexed{C.END}")
    print(f"\n  {C.DIM}Policy Categories:{C.END}")
    for cat, count in sorted(stats['categories'].items(), key=lambda x: -x[1]):
        bar = '█' * min(count, 40)
        print(f"    {cat:30s} {C.CYAN}{bar}{C.END} ({count})")

    print(f"\n  {C.DIM}Sample policy text (from GSP page {policy_engine.gsp_chunks[0].page}):{C.END}")
    sample = policy_engine.gsp_chunks[0].text[:400]
    for line in sample.split('\n'):
        print(f"    {C.DIM}│{C.END} {line}")

    wait_for_enter()

    # ─────────────────────────────────────────────
    # ACT 2: Farmer Profiles & Hydrology Data
    # ─────────────────────────────────────────────
    print_header("ACT 2: TRANSFER REQUEST & DATA PROFILES")

    seller = get_farmer_a_seller()
    buyer = get_farmer_b_buyer()
    transfer = get_transfer_details()
    hydrology = get_hydrology_data()

    print(f"  {C.YELLOW}Transfer Request:{C.END}")
    print(f"    ID: {transfer['transfer_id']}")
    print(f"    {seller['name']} ({seller['farm_name']}) → {buyer['name']} ({buyer['farm_name']})")
    print(f"    Quantity: {transfer['quantity_af']} AF")
    print(f"    Price: ${transfer['price_per_af']}/AF  (Total: ${transfer['total_value_usd']:,.2f})")
    print(f"    Basin: {transfer['basin']}")
    print(f"    Type: {transfer['transfer_type']}")

    wait_for_enter("Press ENTER to view Seller profile...")

    print(format_farmer_profile(seller))

    wait_for_enter("Press ENTER to view Buyer profile...")

    print(format_farmer_profile(buyer))

    wait_for_enter("Press ENTER to view Basin Hydrology...")

    print_subheader("Basin Hydrology — Kern County Subbasin")
    wb = hydrology['water_budget']
    print(f"  ⚠️  Basin Priority: {C.RED}{C.BOLD}{hydrology['basin_priority']}{C.END}")
    print(f"  📊 Water Budget (WY 2024-2025):")
    print(f"     Total Inflow:      {wb['total_inflow_af']:>12,} AF")
    print(f"     Total Outflow:     {wb['total_outflow_af']:>12,} AF")
    print(f"     {C.RED}Change in Storage: {wb['change_in_storage_af']:>12,} AF (OVERDRAFT){C.END}")
    print(f"     Sustainable Yield: {wb['sustainable_yield_estimate_af']:>12,} AF")
    print(f"     Current Overdraft: {wb['current_overdraft_af']:>12,} AF/yr")
    gl = hydrology['groundwater_levels']
    print(f"\n  💧 Groundwater Levels:")
    print(f"     Seller's area (Rosedale): {gl['rosedale_area_avg_ft']} ft depth")
    print(f"     Buyer's area (Semitropic): {gl['semitropic_area_avg_ft']} ft depth")
    print(f"     Min Threshold: {gl['basin_minimum_threshold_ft']} ft")
    print(f"     5-yr decline rate: {gl['5yr_avg_decline_ft_per_yr']} ft/yr")
    sub = hydrology['subsidence']
    print(f"\n  📉 Subsidence:")
    print(f"     Basin avg: {sub['basin_avg_rate_ft_per_yr']} ft/yr")
    print(f"     Max area: {sub['max_subsidence_area']} @ {sub['max_rate_ft_per_yr']} ft/yr")
    print(f"     Cumulative: {sub['cumulative_subsidence_ft']} ft (threshold: {sub['minimum_threshold_ft_total']} ft)")
    cl = hydrology['climate']
    print(f"\n  🌤  Climate:")
    print(f"     Water Year Type: {cl['current_water_year_type']}")
    print(f"     Drought Status: {cl['drought_status']}")
    print(f"     SWP Allocation: {cl['swp_allocation_pct']}%")

    wait_for_enter()

    # ─────────────────────────────────────────────
    # ACT 3: Compliance Question Generation
    # ─────────────────────────────────────────────
    print_header("ACT 3: AI COMPLIANCE ANALYSIS")

    print(f"  The AI has generated {C.BOLD}{len(COMPLIANCE_QUESTIONS)}{C.END} compliance questions")
    print(f"  derived from Kern County GSP and SGMA statute requirements.\n")

    for q in COMPLIANCE_QUESTIONS:
        sev_color = C.RED if q['severity'] == 'critical' else C.YELLOW if q['severity'] == 'high' else C.CYAN
        print(f"  {C.BOLD}{q['id']}{C.END} [{sev_color}{q['severity'].upper()}{C.END}] {q['question']}")
    
    print(f"\n  {C.DIM}Severity: CRITICAL = must pass | HIGH = strong weight | MEDIUM = advisory{C.END}")

    wait_for_enter("Press ENTER to begin AI analysis (each question will be sent to the LLM)...")

    # ─────────────────────────────────────────────
    # ACT 4: LLM Reasoning per Question
    # ─────────────────────────────────────────────
    
    # Initialize LLM
    llm = LLMClient()
    if llm.provider:
        print(f"\n  {C.GREEN}✓ LLM connected: {llm.provider.upper()}{C.END}\n")
    else:
        print(f"\n  {C.YELLOW}⚠ No LLM API key found. Using simulated AI responses.{C.END}")
        print(f"  {C.DIM}Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY for live AI.{C.END}\n")

    system_prompt = """You are a SGMA compliance analyst for the WaterXchange platform.
You analyze groundwater transfers for compliance with California's Sustainable Groundwater Management Act
and the Kern County Subbasin Groundwater Sustainability Plan (2025).
Be precise, cite specific policy sections and page numbers when available, and use actual data values in your analysis.
Your analysis directly determines whether water transfers are approved or denied."""

    question_results = []

    for i, q in enumerate(COMPLIANCE_QUESTIONS):
        sev_color = C.RED if q['severity'] == 'critical' else C.YELLOW if q['severity'] == 'high' else C.CYAN

        print(f"\n{'─'*70}")
        print(f"  {C.BOLD}Question {q['id']}{C.END} [{sev_color}{q['severity'].upper()}{C.END}]")
        print(f"  {C.BOLD}{q['question']}{C.END}")
        print(f"{'─'*70}")

        # Step A: Gather relevant data
        print(f"\n  {C.DIM}[1/3] Gathering farmer + hydrology data...{C.END}")
        data_context = get_data_for_question(q, seller, buyer, hydrology)
        print(f"  {C.GREEN}✓{C.END} Data retrieved:")
        for line in data_context.split('\n')[:8]:
            print(f"    {line}")
        if data_context.count('\n') > 8:
            print(f"    {C.DIM}... ({data_context.count(chr(10)) - 8} more lines){C.END}")

        # Step B: Retrieve relevant policy text
        print(f"\n  {C.DIM}[2/3] Retrieving relevant policy sections...{C.END}")
        policy_chunks = policy_engine.retrieve_for_question(q['question'], top_k=4)
        # Also get by category
        cat_chunks = policy_engine.retrieve_by_categories(q['policy_categories'], max_per_cat=2)
        # Deduplicate
        seen_pages = set()
        all_policy = []
        for ch in policy_chunks + cat_chunks:
            key = (ch.source, ch.page)
            if key not in seen_pages:
                seen_pages.add(key)
                all_policy.append(ch)

        policy_text = ""
        for ch in all_policy[:5]:
            policy_text += f"\n--- {ch.source}, Page {ch.page} ({ch.category}) ---\n"
            policy_text += ch.text[:800] + "\n"
            print(f"  {C.GREEN}✓{C.END} {ch.source}, p.{ch.page} ({ch.category})")

        # Step C: Send to LLM
        print(f"\n  {C.DIM}[3/3] Sending to AI for analysis...{C.END}")

        user_prompt = build_compliance_prompt(q, data_context, policy_text, seller, buyer)

        if llm.provider:
            try:
                response = llm.call(system_prompt, user_prompt)
                time.sleep(0.3)  # Brief pause for readability
            except Exception as e:
                print(f"  {C.RED}LLM Error: {e}{C.END}")
                response = generate_simulated_response(q, seller, buyer, hydrology)
        else:
            response = generate_simulated_response(q, seller, buyer, hydrology)
            time.sleep(0.5)  # Simulate thinking

        # Parse finding from response
        finding = "PASS"
        if "FINDING: FAIL" in response or "FINDING:FAIL" in response:
            finding = "FAIL"
        elif "CONDITIONAL PASS" in response:
            finding = "CONDITIONAL PASS"
        elif "FINDING: PASS" in response or "FINDING:PASS" in response:
            finding = "PASS"

        finding_color = C.GREEN if finding == "PASS" else C.YELLOW if finding == "CONDITIONAL PASS" else C.RED
        
        print(f"\n  {C.BOLD}AI Analysis:{C.END}")
        print(f"  ┌{'─'*66}┐")
        for line in response.split('\n'):
            # Colorize findings
            if line.strip().startswith("FINDING:"):
                print(f"  │ {finding_color}{C.BOLD}{line.strip()[:64]:64s}{C.END} │")
            elif line.strip().startswith("RISKS:") or line.strip().startswith("CONDITIONS:"):
                print(f"  │ {C.YELLOW}{line.strip()[:64]:64s}{C.END} │")
            else:
                print(f"  │ {line.strip()[:64]:64s} │")
        print(f"  └{'─'*66}┘")

        question_results.append({
            "id": q['id'],
            "question": q['question'],
            "severity": q['severity'],
            "finding": finding,
            "summary": response[:500],
            "full_response": response,
        })

        if i < len(COMPLIANCE_QUESTIONS) - 1:
            wait_for_enter(f"Press ENTER for next question ({i+2}/{len(COMPLIANCE_QUESTIONS)})...")

    # ─────────────────────────────────────────────
    # ACT 5: Final Verdict
    # ─────────────────────────────────────────────
    wait_for_enter("Press ENTER for FINAL VERDICT...")

    print_header("ACT 5: FINAL VERDICT")

    # Summary of findings
    passes = sum(1 for r in question_results if r['finding'] == 'PASS')
    conditionals = sum(1 for r in question_results if r['finding'] == 'CONDITIONAL PASS')
    fails = sum(1 for r in question_results if r['finding'] == 'FAIL')

    print(f"  📊 Analysis Summary:")
    print(f"     {C.GREEN}PASS: {passes}{C.END}  |  {C.YELLOW}CONDITIONAL: {conditionals}{C.END}  |  {C.RED}FAIL: {fails}{C.END}")
    print()

    for r in question_results:
        fc = C.GREEN if r['finding'] == 'PASS' else C.YELLOW if r['finding'] == 'CONDITIONAL PASS' else C.RED
        icon = '✅' if r['finding'] == 'PASS' else '⚠️' if r['finding'] == 'CONDITIONAL PASS' else '❌'
        sev_color = C.RED if r['severity'] == 'critical' else C.YELLOW if r['severity'] == 'high' else C.CYAN
        print(f"  {icon} {r['id']} [{sev_color}{r['severity']:8s}{C.END}] {fc}{r['finding']:18s}{C.END} {r['question'][:50]}...")

    print(f"\n{'═'*70}")

    # Get final verdict from LLM
    verdict_prompt = build_verdict_prompt(question_results, seller, buyer, hydrology)

    if llm.provider:
        print(f"\n  {C.DIM}Generating final verdict via {llm.provider.upper()}...{C.END}\n")
        try:
            verdict = llm.call(system_prompt, verdict_prompt)
        except Exception as e:
            print(f"  {C.RED}LLM Error: {e}{C.END}")
            verdict = generate_simulated_verdict(question_results, seller, buyer, hydrology)
    else:
        verdict = generate_simulated_verdict(question_results, seller, buyer, hydrology)

    # Determine overall result
    if fails > 0 and any(r['finding'] == 'FAIL' and r['severity'] == 'critical' for r in question_results):
        overall = "DENIED"
        overall_color = C.RED
    elif conditionals > 0 or fails > 0:
        overall = "CONDITIONALLY APPROVED"
        overall_color = C.YELLOW
    else:
        overall = "APPROVED"
        overall_color = C.GREEN

    print(f"""
  {overall_color}{C.BOLD}
  ╔══════════════════════════════════════════════════════════════╗
  ║                                                              ║
  ║   TRANSFER WXT-2026-0042:  {overall:^20s}              ║
  ║                                                              ║
  ╚══════════════════════════════════════════════════════════════╝
  {C.END}""")

    print(f"  {C.BOLD}AI Verdict:{C.END}\n")
    for line in verdict.split('\n'):
        print(f"  {line}")

    print(f"\n{'═'*70}")
    print(f"\n  {C.DIM}This analysis was powered by:{C.END}")
    print(f"  • Kern County Subbasin GSP 2025 ({stats['gsp_chunks']} policy sections)")
    print(f"  • CA Statutory Water Rights Law / SGMA ({stats['sgma_chunks']} statute sections)")
    print(f"  • {len(COMPLIANCE_QUESTIONS)} compliance questions")
    if llm.provider:
        print(f"  • {llm.provider.upper()} LLM for reasoning")
    else:
        print(f"  • Simulated AI (set OPENAI_API_KEY for live LLM)")
    print(f"\n  {C.BOLD}{C.CYAN}WaterXchange — Making water transfers transparent, compliant, and fair.{C.END}\n")


# ─────────────────────────────────────────────────────────────
# SIMULATED RESPONSES (when no API key available)
# ─────────────────────────────────────────────────────────────

def generate_simulated_response(q: Dict, seller: Dict, buyer: Dict, hydrology: Dict) -> str:
    """Generate a realistic simulated response for demo without API key."""
    responses = {
        "Q1": f"""FINDING: PASS
REASONING: The seller ({seller['name']}) has a total available supply of {seller['total_available_af']} AF against a crop water demand of {seller['crop_water_demand_af']} AF, yielding a surplus of {seller['surplus_af']} AF. The requested transfer of {seller['transfer_quantity_af']} AF is within this surplus. Per the Kern County GSP Chapter 11 (Sustainable Management Criteria), transfers of surplus allocation are permitted when the seller demonstrates adequate supply for their own beneficial use.
CONDITIONS: None
RISKS: Seller's surplus depends on surface water delivery of {seller['surface_water_received_af']} AF which may decrease further under drought conditions.""",

        "Q2": f"""FINDING: PASS
REASONING: The seller's total annual extraction is {seller['total_annual_extraction_af']} AF against a GSA allocation of {seller['annual_gsa_allocation_af']} AF. Even after transferring {seller['transfer_quantity_af']} AF of extraction credits, the seller's extraction ({seller['total_annual_extraction_af']} AF) remains within allocation. Per Kern County GSP Section 13, extraction must not exceed allocated amounts. The transfer is a credit transfer, not additional extraction. Ref: SGMA §10726.4 — GSAs may regulate extraction and transfers within their jurisdiction.
CONDITIONS: None
RISKS: None identified.""",

        "Q3": f"""FINDING: CONDITIONAL PASS
REASONING: The buyer's area (Semitropic) has current water levels at {buyer['wells'][0]['current_water_level_ft']} ft depth, with {buyer['water_level_vs_minimum_threshold']}. The 5-year decline rate of {buyer['water_level_trend_5yr']} is concerning. Adding 150 AF of extraction rights brings the buyer's total to {buyer['total_annual_extraction_af'] + 150} AF. Per Kern County GSP Section 13.1 (Chronic Lowering of Groundwater Levels), extraction must not cause water levels to fall below the Minimum Threshold of {hydrology['groundwater_levels']['basin_minimum_threshold_ft']} ft. Current projections show the buyer's area has a buffer of 18 ft above threshold.
CONDITIONS: Buyer must demonstrate quarterly water level monitoring at wells SF-1 and SF-2. If water levels decline more than 5 ft below current levels, extraction must be curtailed.
RISKS: At the current decline rate of 3.8 ft/yr, the buffer could be exhausted within 5 years without corrective action.""",

        "Q4": f"""FINDING: CONDITIONAL PASS
REASONING: The buyer's area shows a subsidence rate of {buyer['subsidence_rate_ft_per_year']} ft/yr, which is above the basin average of {hydrology['subsidence']['basin_avg_rate_ft_per_yr']} ft/yr. The cumulative subsidence in the basin is {hydrology['subsidence']['cumulative_subsidence_ft']} ft against a threshold of {hydrology['subsidence']['minimum_threshold_ft_total']} ft (65% consumed). Per Kern County GSP Section 13.4 (Land Subsidence), the buyer's area ({hydrology['subsidence']['max_subsidence_area']}) is identified as a subsidence concern area. Additional extraction could exacerbate irreversible compaction of the Corcoran Clay (present at {buyer['depth_to_corcoran_clay_ft']} ft).
CONDITIONS: Transfer approved contingent on buyer maintaining extraction below allocation + transfer amount. Subsidence monitoring at benchmark {buyer['nearest_subsidence_benchmark']} must continue semi-annually.
RISKS: Subsidence is irreversible. The buyer's area is approaching the measurable objective threshold.""",

        "Q5": f"""FINDING: CONDITIONAL PASS
REASONING: The buyer's well SF-1 shows nitrate at {buyer['groundwater_quality_nitrate_mg_l']} mg/L, which EXCEEDS the MCL of {hydrology['water_quality']['minimum_threshold_nitrate_mg_l']} mg/L. Per Kern County GSP Section 13.3 (Degraded Water Quality), pumping pattern changes should not worsen existing water quality degradation. Increased extraction at the buyer's location could draw contaminated water from agricultural areas. The seller's water quality is acceptable (nitrate: {seller['groundwater_quality_nitrate_mg_l']} mg/L, TDS: {seller['groundwater_quality_tds_mg_l']} mg/L). Per SGMA §10727.2, GSPs must address degraded water quality as an undesirable result.
CONDITIONS: Buyer must conduct water quality sampling at SF-1 before and 6 months after initiating additional extraction. If nitrate increases by >2 mg/L, extraction adjustment may be required.
RISKS: Existing nitrate exceedance at buyer's well is a pre-existing concern independent of this transfer.""",

        "Q6": f"""FINDING: CONDITIONAL PASS
REASONING: The buyer has {buyer['domestic_wells_within_1mi']} domestic wells within 1 mile, with the nearest at {buyer['nearest_domestic_well_depth_ft']} ft depth. The buyer's production wells are at {buyer['wells'][0]['depth_ft']}-{buyer['wells'][1]['depth_ft']} ft. Per Kern County GSP and SGMA §10726.4, transfers must not cause unreasonable impacts to beneficial uses including domestic wells. With additional extraction of 150 AF, the cone of depression around buyer's wells could expand, potentially lowering water levels at nearby domestic wells.
CONDITIONS: A well interference analysis should be conducted for the 7 domestic wells within 1 mile. If any domestic well shows >10 ft of additional drawdown attributable to the buyer's increased extraction, mitigation measures must be implemented.
RISKS: Domestic well at 220 ft depth is relatively shallow compared to buyer's production wells. Monitoring recommended.""",

        "Q7": f"""FINDING: PASS
REASONING: Both the seller and buyer have metered wells. Seller wells GVF-1 and GVF-2 were calibrated on {seller['wells'][0]['meter_calibration_date']}. Buyer wells SF-1 and SF-2 were calibrated on {buyer['wells'][0]['meter_calibration_date']}. Per Kern County GSP monitoring requirements and SGMA §10725.8, accurate extraction measurement is required for all groundwater users. Both parties meet this requirement.
CONDITIONS: None
RISKS: None — both parties demonstrate good metering practices.""",

        "Q8": f"""FINDING: PASS
REASONING: While the Kern County Subbasin is Critically Overdrafted with a current overdraft of {hydrology['water_budget']['current_overdraft_af']:,} AF/yr, this transfer does not increase total basin extraction. It merely reallocates existing extraction rights from the seller to the buyer. The seller has a genuine surplus (producing less than allocated), and the buyer has a demonstrated need (deficit of {buyer['deficit_af']} AF). Per SGMA §10720.7, the GSP must achieve sustainability by 2040. This transfer is consistent with that goal because it optimizes allocation efficiency without increasing net extraction. Ref: Kern County GSP Section 14 (Projects and Management Actions) supports water markets as a management tool.
CONDITIONS: None
RISKS: Basin remains in overdraft. All transfers must be tracked to ensure aggregate extraction stays within GSP targets.""",

        "Q9": f"""FINDING: CONDITIONAL PASS
REASONING: The buyer has a compliance history that includes: {buyer['past_violations'][0]}. The buyer is currently at {buyer['total_annual_extraction_af']} AF extraction against {buyer['annual_gsa_allocation_af']} AF allocation (111% — over-extracting). Per GSA governance rules, past violations and current over-extraction status are relevant to transfer approval. The buyer's GSA fees are current and annual reports are filed. The corrective action plan from 2023 should be reviewed.
CONDITIONS: Buyer must demonstrate that the over-extraction corrective action plan from 2023 has been implemented. The transferred 150 AF must be explicitly added to the buyer's allocation ledger by the GSA before additional extraction occurs.
RISKS: Pattern of over-extraction is a governance concern. GSA should impose enhanced monitoring for this water year.""",

        "Q10": f"""FINDING: PASS
REASONING: The seller is {seller['nearest_interconnected_sw_ft']:,} ft (2.3 mi) from the nearest interconnected surface water, and the buyer is {buyer['nearest_interconnected_sw_ft']:,} ft (1.6 mi) from the nearest ISW. Neither party has groundwater-dependent ecosystems within 1,000 ft. Per Kern County GSP Section 13.5 (Interconnected Surface Water) and SGMA §10727.2(b)(4), depletions of interconnected surface water must not cause undesirable results. Given the distances involved, impacts to ISW and GDEs are not expected from this transfer.
CONDITIONS: None
RISKS: Minimal — distances are sufficient to avoid ISW impacts.""",

        "Q11": f"""FINDING: CONDITIONAL PASS
REASONING: The seller belongs to the {seller['gsa']} and the buyer to the {buyer['gsa']}. Both are within the Kern County Subbasin but under DIFFERENT GSAs. Per the Kern County GSP Chapter 5 (Plan Area), the Kern Subbasin has 15 GSAs coordinated under a single GSP. Inter-GSA transfers within the same subbasin are governed by the GSP's coordination agreement (Ref: Kern County GSP Section 5.3). Per SGMA §10726.2, GSAs within the same basin must coordinate on transfers.
CONDITIONS: Both GSAs (Rosedale-Rio Bravo and Semitropic) must acknowledge and record the transfer in their respective accounting ledgers. Formal notification to the GSP coordinating committee is required.
RISKS: Inter-GSA accounting discrepancies have occurred historically. Both GSAs must reconcile the transfer in their annual reports.""",

        "Q12": f"""FINDING: PASS
REASONING: Current conditions show a Below Normal water year with Moderate (D1) drought status and SWP allocation at {hydrology['climate']['swp_allocation_pct']}%. While conditions are dry, they do not trigger emergency drought restrictions per SGMA §10609.60 or the Kern County GSP's drought contingency provisions. The transfer is for a single water year and will expire automatically. Sierra snowpack is at {hydrology['climate']['sierra_snowpack_pct_of_normal']}% of normal, suggesting continued tight supply.
CONDITIONS: None — current conditions do not trigger additional restrictions.
RISKS: If drought conditions worsen to Severe (D2) or Extreme (D3), the GSA may impose additional transfer restrictions under emergency provisions.""",
    }
    return responses.get(q['id'], f"FINDING: PASS\nREASONING: Analysis complete.\nCONDITIONS: None\nRISKS: None identified.")


def generate_simulated_verdict(results: List[Dict], seller: Dict, buyer: Dict, hydrology: Dict) -> str:
    """Generate a realistic simulated final verdict."""
    passes = sum(1 for r in results if r['finding'] == 'PASS')
    conditionals = sum(1 for r in results if r['finding'] == 'CONDITIONAL PASS')
    fails = sum(1 for r in results if r['finding'] == 'FAIL')

    return f"""VERDICT: CONDITIONALLY APPROVED

SUMMARY:
Transfer WXT-2026-0042 from {seller['name']} to {buyer['name']} for 150 AF of 
groundwater extraction credits within the Kern County Subbasin has been evaluated 
against 12 compliance criteria derived from the Kern County GSP 2025 and SGMA statute.

Results: {passes} PASS | {conditionals} CONDITIONAL | {fails} FAIL

KEY FINDINGS:
✅ Seller has verified surplus ({seller['surplus_af']} AF) exceeding transfer amount
✅ No increase in basin-wide extraction (credit transfer only)
✅ Both parties have metered, calibrated wells
✅ No impacts to interconnected surface water or GDEs
✅ Current drought conditions do not trigger emergency restrictions

⚠️  AREAS REQUIRING ATTENTION:
• Buyer's area shows elevated subsidence (0.08 ft/yr) approaching measurable objective
• Buyer's well SF-1 has nitrate above MCL (12.5 mg/L vs 10 mg/L threshold)
• Buyer has history of over-extraction (2023 violation, currently at 111% of allocation)
• Transfer is inter-GSA (Rosedale-Rio Bravo → Semitropic) requiring coordination

CONDITIONS FOR APPROVAL:
1. Both GSAs must formally acknowledge and record the transfer (GSP §5.3)
2. Buyer must maintain quarterly water level monitoring at SF-1 and SF-2
3. Buyer must conduct water quality sampling before and 6 months after initiation
4. Well interference analysis for 7 domestic wells within 1 mile of buyer
5. Buyer's 2023 corrective action plan compliance must be verified by GSA
6. Subsidence monitoring at benchmark SMTP-07 must continue semi-annually
7. Transferred 150 AF must be recorded in buyer's allocation ledger before extraction

MONITORING REQUIREMENTS:
• Quarterly extraction reporting by both parties
• Semi-annual water level and subsidence monitoring
• Water quality sampling at buyer's wells (baseline + 6-month follow-up)
• Annual reconciliation by both GSAs

POLICY BASIS:
• Kern County GSP 2025, Sections 5.3, 11, 13.1-13.5, 14
• SGMA §10720.7, §10725.8, §10726.2, §10726.4, §10727.2
• CA Water Code §1018 (transfer provisions)

VALIDITY: This approval is valid for Water Year 2025-2026 only (expires Sep 30, 2026).
Transfer does not create permanent water rights. Subject to GSA annual review."""


if __name__ == "__main__":
    if "--auto" in sys.argv:
        INTERACTIVE = False
    asyncio.run(run_demo())
