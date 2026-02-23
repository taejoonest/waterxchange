#!/usr/bin/env python3
"""
WaterXchange — Live SGMA Chat
Interactive Q&A powered by Gemini + RAG over Kern County GSP & SGMA statute.

Run:
  cd backend && source venv/bin/activate
  python3 live_chat.py
"""

import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))

from services.policy_engine import PolicyEngine
from services.farmer_data import (
    get_farmer_a_seller, get_farmer_b_buyer,
    get_transfer_details, get_hydrology_data,
    format_farmer_profile
)

# ── Colors ──
class C:
    BOLD  = '\033[1m'
    DIM   = '\033[2m'
    CYAN  = '\033[96m'
    GREEN = '\033[92m'
    YELLOW= '\033[93m'
    RED   = '\033[91m'
    BLUE  = '\033[94m'
    END   = '\033[0m'

# ── Init Gemini ──
def init_llm():
    api_key = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        print(f"  {C.RED}No GEMINI_API_KEY found in environment. Set it first:{C.END}")
        print(f"  {C.DIM}export GEMINI_API_KEY=your_key_here{C.END}")
        sys.exit(1)
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    return model

# ── Boot ──
print(f"\n{C.CYAN}{C.BOLD}  WaterXchange — Live SGMA Chat{C.END}")
print(f"{C.DIM}  Loading policies & data...{C.END}\n")

policy_engine = PolicyEngine()
data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "policies")
stats = policy_engine.load_policies(data_dir)

seller   = get_farmer_a_seller()
buyer    = get_farmer_b_buyer()
transfer = get_transfer_details()
hydrology= get_hydrology_data()

model = init_llm()

print(f"  {C.GREEN}✓{C.END} {stats['total_chunks']} policy chunks loaded ({stats['gsp_chunks']} GSP + {stats['sgma_chunks']} SGMA)")
print(f"  {C.GREEN}✓{C.END} Gemini 2.0 Flash connected")
print(f"  {C.GREEN}✓{C.END} Farmer data loaded: {seller['name']} (seller) ↔ {buyer['name']} (buyer)")
print(f"  {C.GREEN}✓{C.END} Transfer: {transfer['quantity_af']} AF @ ${transfer['price_per_af']}/AF in {transfer['basin']}")

# ── Build system context ──
SYSTEM = f"""You are the WaterXchange SGMA compliance AI.

You have access to the full text of:
1. The Kern County Subbasin Groundwater Sustainability Plan (GSP) 2025
2. California Statutory Water Rights Law / SGMA statute

You also know about a pending transfer:
- SELLER: {seller['name']}, {seller['farm_name']}, GSA: {seller['gsa']}, {seller['acreage_total']} ac
  Allocation: {seller['annual_gsa_allocation_af']} AF, Surplus: {seller['surplus_af']} AF
  Wells: {len(seller['wells'])} production wells, subsidence: {seller.get('subsidence_rate_ft_per_year','N/A')} ft/yr
- BUYER: {buyer['name']}, {buyer['farm_name']}, GSA: {buyer['gsa']}, {buyer['acreage_total']} ac
  Allocation: {buyer['annual_gsa_allocation_af']} AF, Deficit: {buyer['deficit_af']} AF
  Wells: {len(buyer['wells'])} production wells, subsidence: {buyer.get('subsidence_rate_ft_per_year','N/A')} ft/yr
- TRANSFER: {transfer['quantity_af']} AF, ${transfer['price_per_af']}/AF, {transfer['transfer_type']}
  Basin: {transfer['basin']} (Critically Overdrafted)

BASIN HYDROLOGY:
- Sustainable Yield: {hydrology['water_budget']['sustainable_yield_estimate_af']:,} AF
- Current Overdraft: {hydrology['water_budget']['current_overdraft_af']:,} AF/yr
- GW Levels: seller area {hydrology['groundwater_levels']['rosedale_area_avg_ft']} ft, buyer area {hydrology['groundwater_levels']['semitropic_area_avg_ft']} ft
- Subsidence: basin avg {hydrology['subsidence']['basin_avg_rate_ft_per_yr']} ft/yr
- Drought: {hydrology['climate']['drought_status']}, SWP: {hydrology['climate']['swp_allocation_pct']}%

When answering:
- Be specific — use actual numbers from the data and policies
- Cite GSP page numbers (e.g. "GSP p.595") or SGMA statute sections
- If the user asks about the transfer, evaluate it against real policy criteria
- Keep answers focused and professional

Below you will receive RELEVANT POLICY TEXT retrieved from the actual documents, plus the user's question.
Answer based on the policy text and data above."""

conversation = []

# ── Chat loop ──
print(f"\n{C.CYAN}{'─'*60}{C.END}")
print(f"  Type your questions. The AI will answer using real Kern County")
print(f"  GSP and SGMA policy text retrieved via RAG.")
print(f"  Type {C.BOLD}quit{C.END} to exit, {C.BOLD}help{C.END} for sample questions.")
print(f"{C.CYAN}{'─'*60}{C.END}\n")

while True:
    try:
        query = input(f"{C.BOLD}{C.BLUE}You ❯ {C.END}").strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\n{C.DIM}Goodbye!{C.END}")
        break

    if not query:
        continue
    if query.lower() in ('quit', 'exit', 'q'):
        print(f"\n{C.DIM}Goodbye!{C.END}")
        break
    if query.lower() == 'help':
        print(f"""
  {C.BOLD}Sample questions:{C.END}
  • What is the sustainable yield of the Kern County Subbasin?
  • Is this transfer compliant with SGMA?
  • What are the subsidence thresholds for the buyer's area?
  • Does the buyer's water quality meet GSP requirements?
  • What permits are needed for an inter-GSA transfer?
  • What are the minimum thresholds for groundwater levels?
  • Can the seller legally sell 150 AF given their allocation?
  • What monitoring is required after the transfer?
  • What happens if the buyer exceeds their allocation?
  • Explain SGMA Section 10726.4 and how it applies here
  • What is the basin's overdraft status and 2040 sustainability path?
  • Are there GDEs or interconnected surface water near the buyer?
""")
        continue

    # ── RAG: retrieve relevant policy text ──
    chunks = policy_engine.retrieve_for_question(query, top_k=6)

    policy_context = ""
    sources = []
    for ch in chunks:
        policy_context += f"\n--- {ch.source}, Page {ch.page} [{ch.category}] ---\n"
        policy_context += ch.text[:600] + "\n"
        sources.append(f"{ch.source} p.{ch.page}")

    if sources:
        print(f"  {C.DIM}Retrieved: {', '.join(sources[:4])}{C.END}")

    # ── Build prompt ──
    user_prompt = f"""RETRIEVED POLICY TEXT:
{policy_context if policy_context.strip() else "(No highly relevant policy chunks found — answer from your knowledge of the GSP and SGMA)"}

CONVERSATION HISTORY:
{chr(10).join(f"- {m['role']}: {m['content'][:200]}" for m in conversation[-4:])}

USER QUESTION:
{query}

Answer concisely and cite specific policy pages or SGMA sections."""

    # ── Call Gemini ──
    try:
        full_prompt = f"{SYSTEM}\n\n---\n\n{user_prompt}"
        response = model.generate_content(
            full_prompt,
            generation_config={"temperature": 0.4, "max_output_tokens": 1500}
        )
        answer = response.text
    except Exception as e:
        answer = f"Error calling Gemini: {e}"

    # ── Print response ──
    print(f"\n{C.GREEN}{C.BOLD}AI ❯{C.END} {answer}\n")

    # ── Track history ──
    conversation.append({"role": "user", "content": query})
    conversation.append({"role": "assistant", "content": answer[:500]})
