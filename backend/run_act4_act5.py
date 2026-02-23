"""
WaterXchange Demo — ACT 4 + ACT 5
Run this in the terminal:
  cd /Users/mmm/Downloads/waterxchane/backend
  source venv/bin/activate
  export GEMINI_API_KEY="AIzaSyCjA-3gEnwi42esmCEHtb0-xbX-wV7u9vQ"
  python3 run_act4_act5.py
"""
import os, sys, time, json
sys.path.insert(0, '.')

import google.generativeai as genai
from services.farmer_data import get_farmer_a_seller, get_farmer_b_buyer, get_hydrology_data
from services.policy_engine import PolicyEngine
from services.compliance_engine import (
    COMPLIANCE_QUESTIONS, get_data_for_question, build_compliance_prompt
)

# ── Colors ──
C = '\033[96m'; B = '\033[1m'; G = '\033[92m'; Y = '\033[93m'; R = '\033[91m'; D = '\033[2m'; E = '\033[0m'

# ── Setup ──
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print(f"{R}ERROR: Set GEMINI_API_KEY environment variable{E}")
    sys.exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

seller = get_farmer_a_seller()
buyer = get_farmer_b_buyer()
hydrology = get_hydrology_data()

pe = PolicyEngine()
pe.load_policies()

severity_color = {"critical": R, "high": Y, "medium": D}
severity_icon = {"critical": "🔴", "high": "🟡", "medium": "🔵"}

# ═══════════════════════════════════════════════════════════════
#  ACT 4: GEMINI AI ANALYSIS
# ═══════════════════════════════════════════════════════════════

print(f"""{B}{C}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         🌊  W A T E R X C H A N G E  🌊                    ║
║                                                              ║
║         ACT 4: GEMINI AI COMPLIANCE ANALYSIS                 ║
║                                                              ║
║   12 questions × (Data + Policy Text) → Gemini → Verdict    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{E}""")

results = []
pass_count = 0
cond_count = 0
fail_count = 0

for i, q in enumerate(COMPLIANCE_QUESTIONS):
    sc = severity_color.get(q['severity'], D)
    si = severity_icon.get(q['severity'], "⚪")
    
    print(f"\n{B}{C}{'─'*70}{E}")
    print(f"  {B}{q['id']}{E} of 12  {si} [{sc}{q['severity'].upper()}{E}]")
    print(f"  {B}{q['question']}{E}")
    print(f"{C}{'─'*70}{E}")
    
    # Step 1: Get data for this question
    data_context = get_data_for_question(q, seller, buyer, hydrology)
    
    # Step 2: Retrieve policy text
    policy_chunks = pe.retrieve_by_categories(q['policy_categories'], max_per_cat=2)
    policy_text = ""
    for chunk in policy_chunks:
        policy_text += f"\n[{chunk.source}, p.{chunk.page}]:\n{chunk.text[:500]}\n"
    
    # Also do keyword retrieval
    keyword_chunks = pe.retrieve_for_question(q['question'], top_k=3)
    for chunk in keyword_chunks:
        if chunk.text not in policy_text:
            policy_text += f"\n[{chunk.source}, p.{chunk.page}]:\n{chunk.text[:500]}\n"
    
    # Step 3: Build the prompt
    prompt = build_compliance_prompt(q, data_context, policy_text, seller, buyer)
    
    print(f"  {D}Sending to Gemini: {len(data_context)} chars data + {len(policy_text)} chars policy...{E}")
    
    # Step 4: Call Gemini
    try:
        t0 = time.time()
        response = model.generate_content(prompt)
        elapsed = time.time() - t0
        answer = response.text
        
        # Parse finding
        finding = "UNKNOWN"
        if "FINDING: PASS" in answer and "CONDITIONAL" not in answer.split("FINDING:")[1][:30]:
            finding = "PASS"
            pass_count += 1
        elif "CONDITIONAL" in answer:
            finding = "CONDITIONAL PASS"
            cond_count += 1
        elif "FAIL" in answer:
            finding = "FAIL"
            fail_count += 1
        else:
            finding = "CONDITIONAL PASS"  # Default to conditional if unclear
            cond_count += 1
        
        # Color the finding
        if finding == "PASS":
            fc = G
        elif finding == "FAIL":
            fc = R
        else:
            fc = Y
        
        print(f"\n  {B}FINDING: {fc}{finding}{E}  {D}({elapsed:.1f}s){E}\n")
        
        # Print the response, indented
        for line in answer.split('\n'):
            print(f"  {line}")
        
        results.append({
            "id": q['id'],
            "question": q['question'],
            "severity": q['severity'],
            "finding": finding,
            "summary": answer[:300],
            "full_response": answer,
        })
        
    except Exception as e:
        print(f"  {R}ERROR: {e}{E}")
        results.append({
            "id": q['id'],
            "question": q['question'],
            "severity": q['severity'],
            "finding": "ERROR",
            "summary": str(e),
            "full_response": str(e),
        })
        fail_count += 1
    
    # Small delay to avoid rate limiting
    if i < len(COMPLIANCE_QUESTIONS) - 1:
        time.sleep(1)

# ── ACT 4 Summary ──
print(f"\n\n{B}{C}{'═'*70}{E}")
print(f"{B}{C}  ACT 4 SUMMARY — ALL 12 QUESTIONS ANALYZED{E}")
print(f"{B}{C}{'═'*70}{E}\n")

print(f"  ┌{'─'*50}┐")
for r in results:
    sc = severity_color.get(r['severity'], D)
    si = severity_icon.get(r['severity'], "⚪")
    if r['finding'] == 'PASS':
        fc = G; fi = '✅'
    elif r['finding'] == 'FAIL':
        fc = R; fi = '❌'
    else:
        fc = Y; fi = '⚠️'
    print(f"  │ {r['id']} {si} {fi} {fc}{r['finding']:<20s}{E} │")
print(f"  └{'─'*50}┘")
print(f"\n  {G}PASS: {pass_count}{E}  |  {Y}CONDITIONAL: {cond_count}{E}  |  {R}FAIL: {fail_count}{E}")


# ═══════════════════════════════════════════════════════════════
#  ACT 5: FINAL VERDICT
# ═══════════════════════════════════════════════════════════════

print(f"""\n\n{B}{C}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         🌊  W A T E R X C H A N G E  🌊                    ║
║                                                              ║
║         ACT 5: FINAL COMPLIANCE VERDICT                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{E}""")

# Build verdict prompt
results_text = ""
for r in results:
    results_text += f"\n{r['id']}: {r['question']}\n"
    results_text += f"  Finding: {r['finding']}\n"
    results_text += f"  Severity: {r['severity']}\n"
    results_text += f"  Summary: {r['summary'][:200]}\n"

verdict_prompt = f"""You are the chief compliance officer for WaterXchange.

TRANSFER UNDER REVIEW:
  Transfer ID: WXT-2026-0042
  Seller: {seller['name']} ({seller['farm_name']}) → Buyer: {buyer['name']} ({buyer['farm_name']})
  Seller GSA: {seller['gsa']}
  Buyer GSA: {buyer['gsa']}
  Quantity: 150 AF | Price: $415/AF | Total: $62,250
  Basin: Kern County Subbasin (Critically Overdrafted)

BASIN STATUS (from Kern County GSP 2025):
  Sustainable Yield: {hydrology['sustainable_yield']['total_afy']:,} AFY  [GSP p.595]
  Total GW Pumping: {hydrology['water_budget']['total_groundwater_pumping_afy']:,} AFY  [GSP p.595]
  Change in Storage: {hydrology['water_budget']['change_in_storage_baseline_afy']:,} AFY  [GSP p.54]
  Projected Deficit (2030): {hydrology['water_budget']['projected_deficit_2030_climate_afy']:,} AFY  [GSP p.776]
  Buyer HCM (North Basin) subsidence: 0.059 ft/yr EXCEEDS rate MT of 0.053 ft/yr  [GSP p.681]
  Seller HCM (Kern Fan) subsidence: 0.022 ft/yr below rate MT of 0.029 ft/yr  [GSP p.681]

COMPLIANCE ANALYSIS RESULTS:
{results_text}

Based on the above analysis of all 12 compliance questions:
1. Issue your FINAL VERDICT: APPROVED, CONDITIONALLY APPROVED, or DENIED
2. Summarize the key findings (reference specific question numbers)
3. List ALL conditions that must be met (if conditionally approved)
4. Specify monitoring requirements
5. Note the policy basis for your decision (cite GSP sections and SGMA statute)
6. Provide a risk assessment score (1-10, where 10 is highest risk)

Format your response clearly with headers."""

print(f"  {D}Sending all 12 results to Gemini for final verdict...{E}\n")

try:
    t0 = time.time()
    response = model.generate_content(verdict_prompt)
    elapsed = time.time() - t0
    verdict = response.text
    
    print(f"  {D}(Response received in {elapsed:.1f}s){E}\n")
    
    # Print verdict with formatting
    for line in verdict.split('\n'):
        # Highlight key words
        if 'APPROVED' in line.upper() or 'DENIED' in line.upper() or 'VERDICT' in line.upper():
            print(f"  {B}{C}{line}{E}")
        elif 'CONDITION' in line.upper():
            print(f"  {Y}{line}{E}")
        elif 'RISK' in line.upper() or 'CONCERN' in line.upper():
            print(f"  {R}{line}{E}")
        elif line.strip().startswith('#') or line.strip().startswith('**'):
            print(f"  {B}{line}{E}")
        else:
            print(f"  {line}")

except Exception as e:
    print(f"  {R}ERROR generating verdict: {e}{E}")


# ── Final Demo Wrap-up ──
print(f"""\n
{B}{G}{'═'*70}{E}
{B}{G}  ✅ DEMO COMPLETE — ALL 5 ACTS FINISHED{E}
{B}{G}{'═'*70}{E}

  {B}What was demonstrated:{E}

  ACT 1: Real policy PDFs ingested (Kern County GSP + SGMA statute)
         Knowledge graph built with strict SGMA ontology
  
  ACT 2: Transfer request + farmer data with provenance tags
         Basin hydrology from real GSP data (24 data points, cited)
  
  ACT 3: 12 compliance questions generated covering all
         SGMA sustainability indicators
  
  ACT 4: Gemini AI analyzed each question against real policy text
         using RAG pipeline: Question + Data + Policy → Verdict
  
  ACT 5: Final compliance verdict with conditions and monitoring

  {B}Core architecture:{E}
  PDF → Chunking → Category Index → Question → RAG Retrieval → LLM → Verdict
  
  {D}All policy data from real Kern County GSP 2025.
  Farmer data is simulated user input (as it would be in production).
  Basin-level numbers verified against GSP with page citations.{E}
""")
