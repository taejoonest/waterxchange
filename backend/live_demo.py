#!/usr/bin/env python3
"""
WaterXchange — Interactive Transfer Compliance Demo
====================================================

You type a water transfer. The system:
  1. Parses the transfer
  2. Generates compliance questions from SGMA/GSP policies
  3. For each question, shows:
     - Knowledge Graph traversal path (HOW we know what to check)
     - Retrieved policy text via RAG
     - Gemini's answer with reasoning
  4. Delivers a final verdict

Run:
  cd backend && source venv/bin/activate
  export GEMINI_API_KEY="your_key"
  python3 live_demo.py
"""

import os, sys, json, time
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


# ═══════════════════════════════════════════════════════════════
#  ANSI COLORS
# ═══════════════════════════════════════════════════════════════
class C:
    BOLD   = '\033[1m'
    DIM    = '\033[2m'
    CYAN   = '\033[96m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    BLUE   = '\033[94m'
    MAG    = '\033[95m'
    WHITE  = '\033[97m'
    END    = '\033[0m'
    BG_DARK = '\033[48;5;236m'


# ═══════════════════════════════════════════════════════════════
#  KNOWLEDGE GRAPH
# ═══════════════════════════════════════════════════════════════
class ComplianceKnowledgeGraph:
    """
    Loads the v3 knowledge graph and provides traversal methods
    to show HOW the LLM arrives at each compliance answer.
    """

    def __init__(self, path: str = None):
        if path is None:
            path = os.path.join(os.path.dirname(__file__), "..", "data", "policies", "knowledge_graph_v3.json")
        with open(path) as f:
            data = json.load(f)
        self.entities = {e["id"]: e for e in data["entities"]}
        self.relationships = data["relationships"]
        self.rels_by_source = {}
        self.rels_by_target = {}
        for r in self.relationships:
            self.rels_by_source.setdefault(r["source"], []).append(r)
            self.rels_by_target.setdefault(r["target"], []).append(r)

    def get_entity(self, eid):
        return self.entities.get(eid)

    def traverse(self, start_id, rel_types, max_depth=1):
        """Follow edges of given types from start, return paths."""
        paths = []
        for r in self.rels_by_source.get(start_id, []):
            if r["type"] in rel_types:
                target = self.entities.get(r["target"])
                if target:
                    paths.append((start_id, r["type"], r["target"]))
        return paths

    def get_compliance_chain(self, question_id: str, seller_gsa: str, buyer_gsa: str):
        """
        For a given compliance question, return the knowledge graph
        traversal chain showing exactly which entities and relationships
        are involved in evaluating this question.
        """
        # Map question IDs to the relevant KG traversal paths
        chains = {
            "Q1": self._chain_allocation_surplus(seller_gsa),
            "Q2": self._chain_allocation_extraction(seller_gsa),
            "Q3": self._chain_groundwater_levels(buyer_gsa),
            "Q4": self._chain_subsidence(buyer_gsa),
            "Q5": self._chain_water_quality(buyer_gsa),
            "Q6": self._chain_well_interference(buyer_gsa),
            "Q7": self._chain_metering(),
            "Q8": self._chain_overdraft(),
            "Q9": self._chain_buyer_compliance(buyer_gsa),
            "Q10": self._chain_gde_isw(),
            "Q11": self._chain_inter_gsa(seller_gsa, buyer_gsa),
            "Q12": self._chain_drought(),
        }
        return chains.get(question_id, [])

    def _chain_allocation_surplus(self, gsa_id):
        return [
            ("tt_inter_gsa", "CONSTRAINED_BY", gsa_id.replace("gsa_", "alloc_"),
             "Transfer must comply with GSA's allocation framework"),
            (gsa_id.replace("gsa_", "alloc_"), "DERIVED_FROM", "water_budget",
             "Allocation is derived from the basin water budget"),
            (gsa_id.replace("gsa_", "alloc_"), "CONSTRAINED_BY", "sustainable_yield",
             "Total allocations cannot exceed sustainable yield"),
            ("kern_gsp", "ESTABLISHES", gsa_id.replace("gsa_", "alloc_"),
             "GSP establishes the allocation framework"),
            ("statute_10726_4", "AUTHORIZES", gsa_id.replace("gsa_", "alloc_"),
             "SGMA §10726.4 authorizes GSAs to regulate allocations & transfers"),
        ]

    def _chain_allocation_extraction(self, gsa_id):
        return [
            ("tt_inter_gsa", "CONSTRAINED_BY", gsa_id.replace("gsa_", "alloc_"),
             "Extraction must stay within allocation"),
            (gsa_id, "GOVERNS", gsa_id.replace("gsa_", "alloc_"),
             "GSA governs allocation rules for its members"),
            ("statute_10726_4", "AUTHORIZES", gsa_id.replace("gsa_", "alloc_"),
             "SGMA §10726.4 grants GSA power to regulate extraction"),
            ("statute_10732", "ENABLES", "enforce_gsa",
             "SGMA §10732 enables GSA enforcement for violations"),
        ]

    def _chain_groundwater_levels(self, gsa_id):
        ma_id = "ma_semitropic" if "semitropic" in gsa_id else "ma_rosedale"
        return [
            ("tt_inter_gsa", "MUST_NOT_VIOLATE", "mt_gw_semitropic" if "semitropic" in gsa_id else "mt_gw_rosedale",
             "Transfer must not push levels below Minimum Threshold"),
            ("mt_gw_semitropic" if "semitropic" in gsa_id else "mt_gw_rosedale", "APPLIES_TO", "ind_gw_levels",
             "MT is set for the Chronic Lowering of GW Levels indicator"),
            ("ind_gw_levels", "EVALUATED_IN", ma_id,
             f"Indicator evaluated in the buyer's management area"),
            ("mon_gw_levels", "MEASURES", "ind_gw_levels",
             "GW Level Monitoring Network measures this indicator"),
            ("mon_gw_levels", "OPERATES_IN", ma_id,
             "Monitoring network operates in the buyer's HCM area"),
            ("kern_gsp", "ESTABLISHES_CRITERIA_FOR", "ind_gw_levels",
             "GSP establishes sustainability criteria for GW levels"),
            ("statute_10727_2", "REQUIRES_TRACKING", "ind_gw_levels",
             "SGMA §10727.2(b)(1) requires tracking this indicator"),
            ("ind_gw_levels", "TRIGGERS_WHEN_BREACHED", "ur_gw_levels",
             "If breached → triggers Undesirable Result declaration"),
        ]

    def _chain_subsidence(self, gsa_id):
        ma_id = "ma_semitropic" if "semitropic" in gsa_id else "ma_rosedale"
        return [
            ("tt_inter_gsa", "MUST_NOT_VIOLATE", "mt_sub_semitropic",
             "Transfer must not worsen subsidence beyond MT"),
            ("mt_sub_semitropic", "APPLIES_TO", "ind_subsidence",
             "MT is set for the Land Subsidence indicator"),
            ("ind_subsidence", "EVALUATED_IN", ma_id,
             "Subsidence evaluated in buyer's management area"),
            ("mon_subsidence", "MEASURES", "ind_subsidence",
             "InSAR/extensometer network measures subsidence"),
            ("wb_extraction", "CONTRIBUTES_TO", "ind_subsidence",
             "Groundwater extraction contributes to subsidence"),
            ("hgu_corcoran_clay", None, None,
             "Corcoran Clay layer is critical — irreversible compaction"),
            ("statute_10727_2", "REQUIRES_TRACKING", "ind_subsidence",
             "SGMA §10727.2(b)(3) requires tracking subsidence"),
        ]

    def _chain_water_quality(self, gsa_id):
        return [
            ("tt_inter_gsa", "MUST_NOT_VIOLATE", "mt_wq_nitrate",
             "Transfer must not worsen water quality beyond MT"),
            ("mt_wq_nitrate", "APPLIES_TO", "ind_water_quality",
             "Nitrate MT applies to Degraded Water Quality indicator"),
            ("mon_water_quality", "MEASURES", "ind_water_quality",
             "Water quality monitoring network tracks constituents"),
            ("wb_extraction", "MAY_AFFECT", "ind_water_quality",
             "Changed pumping patterns may mobilize contaminants"),
            ("statute_10727_2", "REQUIRES_TRACKING", "ind_water_quality",
             "SGMA §10727.2(b)(4) requires tracking water quality"),
        ]

    def _chain_well_interference(self, gsa_id):
        return [
            ("tt_inter_gsa", "REQUIRES", "req_monitoring_compliance",
             "Transfer requires post-transfer monitoring"),
            ("wb_extraction", "DIRECTLY_IMPACTS", "ind_gw_levels",
             "Additional extraction directly impacts water levels"),
            ("ind_gw_levels", "EVALUATED_IN", "ma_semitropic",
             "Water levels evaluated at buyer's location"),
            ("statute_10726_4", "AUTHORIZES", "alloc_semitropic",
             "GSA has authority to protect domestic well users"),
        ]

    def _chain_metering(self):
        return [
            ("tt_inter_gsa", "REQUIRES", "req_metering",
             "Transfer requires metered wells"),
            ("statute_10725_2", "MANDATES", "req_metering",
             "SGMA §10725.2 mandates extraction metering"),
            ("tt_inter_gsa", "REQUIRES", "req_reporting",
             "Transfer requires annual extraction reporting"),
            ("statute_10728_2", "MANDATES", "req_reporting",
             "SGMA §10728.2 mandates annual reporting"),
        ]

    def _chain_overdraft(self):
        return [
            ("tt_inter_gsa", "CONSTRAINED_BY", "alloc_rosedale",
             "Transfer constrained by allocation limits"),
            ("alloc_rosedale", "CONSTRAINED_BY", "sustainable_yield",
             "Allocations constrained by sustainable yield"),
            ("water_budget", "DETERMINES", "sustainable_yield",
             "Water budget determines sustainable yield"),
            ("wb_extraction", "CONTRIBUTES_TO", "water_budget",
             "All extraction contributes to water budget"),
            ("kern_gsp", "ESTABLISHES_CRITERIA_FOR", "ind_storage",
             "GSP tracks reduction in groundwater storage"),
            ("statute_10735", "ENABLES", "enforce_state",
             "State intervention if basin doesn't reach sustainability"),
        ]

    def _chain_buyer_compliance(self, gsa_id):
        return [
            (gsa_id, "GOVERNS", gsa_id.replace("gsa_", "alloc_"),
             "GSA governs buyer's allocation"),
            (gsa_id, "MAY_INVOKE", "enforce_gsa",
             "GSA may invoke enforcement for violations"),
            ("statute_10732", "ENABLES", "enforce_gsa",
             "SGMA §10732 enables enforcement actions"),
            ("tt_inter_gsa", "REPORTED_TO", gsa_id,
             "Transfer must be reported to buyer's GSA"),
        ]

    def _chain_gde_isw(self):
        return [
            ("tt_inter_gsa", "MUST_NOT_VIOLATE", "mt_storage",
             "Transfer must not impact GDE/ISW beyond MT"),
            ("mon_isw", "MEASURES", "ind_isw",
             "ISW monitoring tracks depletion"),
            ("statute_10727_2", "REQUIRES_TRACKING", "ind_isw",
             "SGMA §10727.2(b)(6) requires tracking ISW depletion"),
            ("kern_gsp", "ESTABLISHES_CRITERIA_FOR", "ind_isw",
             "GSP establishes criteria for ISW"),
        ]

    def _chain_inter_gsa(self, seller_gsa, buyer_gsa):
        return [
            ("tt_inter_gsa", "REPORTED_TO", seller_gsa,
             "Transfer reported to seller's GSA"),
            ("tt_inter_gsa", "REPORTED_TO", buyer_gsa,
             "Transfer reported to buyer's GSA"),
            ("tt_inter_gsa", "ADDITIONALLY_REQUIRES", "req_notification",
             "Inter-GSA transfers require formal notification"),
            ("tt_inter_gsa", "REQUIRES", "req_accounting",
             "Both GSAs must record transfer in accounting ledgers"),
            (seller_gsa, "ADOPTS", "kern_gsp",
             "Both GSAs operate under the same coordinated GSP"),
            (buyer_gsa, "ADOPTS", "kern_gsp",
             "Both GSAs operate under the same coordinated GSP"),
            ("statute_10726_4", "AUTHORIZES", "alloc_rosedale",
             "SGMA authorizes inter-GSA coordination"),
        ]

    def _chain_drought(self):
        return [
            ("tt_inter_gsa", "CONSTRAINED_BY", "alloc_rosedale",
             "Transfer subject to drought-adjusted allocation"),
            ("alloc_rosedale", "DERIVED_FROM", "water_budget",
             "Allocation derived from water budget (climate-sensitive)"),
            ("wb_surface_inflow", "CONTRIBUTES_TO", "water_budget",
             "Surface water inflow is climate-dependent"),
            ("wb_recharge_natural", "CONTRIBUTES_TO", "water_budget",
             "Natural recharge varies with precipitation"),
            ("kern_gsp", "ESTABLISHES", "alloc_rosedale",
             "GSP may include drought contingency provisions"),
        ]

    def format_chain(self, chain):
        """Format a KG traversal chain for terminal display."""
        lines = []
        for i, step in enumerate(chain):
            src_id, rel_type, tgt_id, explanation = step
            src = self.entities.get(src_id, {})
            tgt = self.entities.get(tgt_id, {}) if tgt_id else {}
            src_name = src.get("name", src_id) if src else src_id
            src_type = src.get("type", "?") if src else "?"
            tgt_name = tgt.get("name", tgt_id or "—") if tgt else (tgt_id or "—")
            tgt_type = tgt.get("type", "?") if tgt else "?"

            # Tree color
            src_tree = src.get("tree", "bridge") if src else "bridge"
            if src_tree == "governance":
                tree_color = C.BLUE
            elif src_tree == "hydrology":
                tree_color = C.GREEN
            else:
                tree_color = C.MAG

            prefix = "  ╰─" if i == len(chain) - 1 else "  ├─"
            connector = "  │ " if i < len(chain) - 1 else "    "

            if rel_type:
                lines.append(f"  {tree_color}│{C.END}")
                lines.append(f"  {tree_color}{prefix}{C.END} {C.DIM}[{src_type}]{C.END} {C.BOLD}{src_name[:45]}{C.END}")
                lines.append(f"  {tree_color}{connector}   {C.YELLOW}──{rel_type}──▶{C.END}")
                lines.append(f"  {tree_color}{connector}   {C.DIM}[{tgt_type}]{C.END} {C.BOLD}{tgt_name[:45]}{C.END}")
                lines.append(f"  {tree_color}{connector}   {C.DIM}↳ {explanation}{C.END}")
            else:
                lines.append(f"  {tree_color}│{C.END}")
                lines.append(f"  {tree_color}{prefix}{C.END} {C.DIM}[{src_type}]{C.END} {C.BOLD}{src_name[:45]}{C.END}")
                lines.append(f"  {tree_color}{connector}   {C.DIM}↳ {explanation}{C.END}")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
#  LLM CLIENT
# ═══════════════════════════════════════════════════════════════
class LLMClient:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
        if not api_key:
            print(f"\n  {C.RED}ERROR: Set GEMINI_API_KEY first{C.END}")
            print(f"  {C.DIM}export GEMINI_API_KEY=your_key{C.END}\n")
            sys.exit(1)
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.provider = "Gemini 2.0 Flash"

    def call(self, system_prompt, user_prompt):
        full = f"{system_prompt}\n\n---\n\n{user_prompt}"
        response = self.model.generate_content(
            full, generation_config={"temperature": 0.3, "max_output_tokens": 1200}
        )
        return response.text


# ═══════════════════════════════════════════════════════════════
#  MAIN DEMO
# ═══════════════════════════════════════════════════════════════

def main():
    os.system('clear' if os.name != 'nt' else 'cls')

    print(f"""
{C.CYAN}{C.BOLD}
  ╔════════════════════════════════════════════════════════════╗
  ║                                                            ║
  ║    W A T E R X C H A N G E   —   Live Compliance Demo     ║
  ║                                                            ║
  ╚════════════════════════════════════════════════════════════╝{C.END}
""")

    # ── Load everything ──
    print(f"  {C.DIM}Loading...{C.END}")

    policy_engine = PolicyEngine()
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "policies")
    stats = policy_engine.load_policies(data_dir)
    print(f"  {C.GREEN}✓{C.END} {stats['total_chunks']} policy chunks loaded (GSP + SGMA)")

    kg = ComplianceKnowledgeGraph()
    print(f"  {C.GREEN}✓{C.END} Knowledge Graph loaded ({len(kg.entities)} entities, {len(kg.relationships)} relationships)")

    llm = LLMClient()
    print(f"  {C.GREEN}✓{C.END} LLM connected: {llm.provider}")

    seller   = get_farmer_a_seller()
    buyer    = get_farmer_b_buyer()
    transfer = get_transfer_details()
    hydrology = get_hydrology_data()
    print(f"  {C.GREEN}✓{C.END} Farmer data loaded")

    # Map GSA names to KG entity IDs
    seller_gsa_id = "gsa_rosedale"
    buyer_gsa_id = "gsa_semitropic"

    system_prompt = """You are a SGMA compliance analyst for the WaterXchange platform.
You analyze groundwater transfers for compliance with California's Sustainable Groundwater Management Act
and the Kern County Subbasin Groundwater Sustainability Plan (2025).
Be precise, cite specific policy sections and page numbers when available, and use actual data values.
Your analysis directly determines whether water transfers are approved or denied."""

    # ── Prompt user for transfer ──
    print(f"\n{C.CYAN}{'═'*62}{C.END}")
    print(f"  Enter a transfer to evaluate. Examples:")
    print(f"  {C.DIM}• 150 AF from John Martinez to Sarah Chen in Kern County")
    print(f"  • Sell 200 AF from Rosedale GSA to Semitropic GSA")
    print(f"  • Transfer 100 acre-feet within Kern County Subbasin{C.END}")
    print(f"{C.CYAN}{'═'*62}{C.END}\n")

    try:
        user_input = input(f"  {C.BOLD}{C.BLUE}Describe transfer ❯ {C.END}").strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\n{C.DIM}Goodbye.{C.END}")
        return

    if not user_input:
        user_input = "150 AF from John Martinez (Green Valley Farm, Rosedale GSA) to Sarah Chen (Sunrise Farms, Semitropic GSA) in Kern County Subbasin"

    # ── Show parsed transfer ──
    print(f"\n{C.CYAN}{'═'*62}{C.END}")
    print(f"  {C.BOLD}TRANSFER PARSED{C.END}")
    print(f"{C.CYAN}{'═'*62}{C.END}")
    print(f"  {C.DIM}Your input:{C.END} {user_input}")
    print(f"\n  {C.BOLD}Matched Transfer:{C.END}")
    print(f"    ID:     {transfer['transfer_id']}")
    print(f"    Seller: {seller['name']} ({seller['farm_name']}) — {seller['gsa']}")
    print(f"    Buyer:  {buyer['name']} ({buyer['farm_name']}) — {buyer['gsa']}")
    print(f"    Amount: {transfer['quantity_af']} AF @ ${transfer['price_per_af']}/AF = ${transfer['total_value_usd']:,.0f}")
    print(f"    Basin:  {transfer['basin']}")
    print(f"    Type:   {transfer['transfer_type']}")

    wait("\nPress ENTER to generate compliance questions...")

    # ── Generate Questions ──
    print(f"\n{C.CYAN}{'═'*62}{C.END}")
    print(f"  {C.BOLD}COMPLIANCE QUESTIONS GENERATED{C.END}")
    print(f"  {C.DIM}12 questions from SGMA sustainability indicators{C.END}")
    print(f"{C.CYAN}{'═'*62}{C.END}\n")

    for q in COMPLIANCE_QUESTIONS:
        sev = q['severity']
        sc = C.RED if sev == 'critical' else C.YELLOW if sev == 'high' else C.CYAN
        print(f"  {C.BOLD}{q['id']}{C.END} [{sc}{sev.upper():8s}{C.END}] {q['question'][:75]}")

    print(f"\n  {C.DIM}CRITICAL = must pass  |  HIGH = strong weight  |  MEDIUM = advisory{C.END}")

    wait("\nPress ENTER to begin analysis (each question → KG traversal → RAG → Gemini)...")

    # ── Evaluate each question ──
    question_results = []

    for i, q in enumerate(COMPLIANCE_QUESTIONS):
        sev = q['severity']
        sc = C.RED if sev == 'critical' else C.YELLOW if sev == 'high' else C.CYAN

        print(f"\n{'{'+'═'*60+'}'}")
        print(f"  {C.BOLD}{q['id']}{C.END} [{sc}{sev.upper()}{C.END}]  {C.BOLD}{q['question']}{C.END}")
        print(f"{'{'+'═'*60+'}'}")

        # ── Step 1: Knowledge Graph Traversal ──
        print(f"\n  {C.MAG}{C.BOLD}STEP 1 — Knowledge Graph Traversal{C.END}")
        print(f"  {C.DIM}How do we know what to check? The KG tells us:{C.END}\n")

        chain = kg.get_compliance_chain(q['id'], seller_gsa_id, buyer_gsa_id)
        if chain:
            print(kg.format_chain(chain))
        else:
            print(f"  {C.DIM}(No specific KG chain for this question){C.END}")

        # ── Step 2: Gather Farmer Data ──
        print(f"\n  {C.GREEN}{C.BOLD}STEP 2 — Farmer & Hydrology Data{C.END}")
        data_context = get_data_for_question(q, seller, buyer, hydrology)
        for line in data_context.split('\n')[:10]:
            print(f"  {C.DIM}│{C.END} {line}")
        remaining = data_context.count('\n') - 10
        if remaining > 0:
            print(f"  {C.DIM}│ ... ({remaining} more lines){C.END}")

        # ── Step 3: RAG Policy Retrieval ──
        print(f"\n  {C.BLUE}{C.BOLD}STEP 3 — Policy Text Retrieved (RAG){C.END}")
        policy_chunks = policy_engine.retrieve_for_question(q['question'], top_k=4)
        cat_chunks = policy_engine.retrieve_by_categories(q['policy_categories'], max_per_cat=2)
        seen = set()
        all_policy = []
        for ch in policy_chunks + cat_chunks:
            key = (ch.source, ch.page)
            if key not in seen:
                seen.add(key)
                all_policy.append(ch)

        policy_text = ""
        for ch in all_policy[:5]:
            policy_text += f"\n--- {ch.source}, Page {ch.page} ({ch.category}) ---\n"
            policy_text += ch.text[:800] + "\n"
            print(f"  {C.GREEN}✓{C.END} {ch.source}, p.{ch.page} ({ch.category})")

        # ── Step 4: Gemini Analysis ──
        print(f"\n  {C.YELLOW}{C.BOLD}STEP 4 — Gemini Analysis{C.END}")
        print(f"  {C.DIM}Sending: question + farmer data + policy text + KG context → Gemini 2.0 Flash...{C.END}")

        # Add KG context to prompt
        kg_context = ""
        if chain:
            kg_context = "\n\nKNOWLEDGE GRAPH COMPLIANCE CHAIN (the regulatory reasoning path):\n"
            for src, rel, tgt, expl in chain:
                src_name = kg.entities.get(src, {}).get("name", src) if src else src
                tgt_name = kg.entities.get(tgt, {}).get("name", tgt) if tgt else "—"
                if rel:
                    kg_context += f"  [{src_name}] --{rel}--> [{tgt_name}]: {expl}\n"
                else:
                    kg_context += f"  [{src_name}]: {expl}\n"

        user_prompt = build_compliance_prompt(q, data_context, policy_text + kg_context, seller, buyer)

        try:
            t0 = time.time()
            response = llm.call(system_prompt, user_prompt)
            elapsed = time.time() - t0
        except Exception as e:
            response = f"FINDING: ERROR\nREASONING: LLM call failed: {e}\nCONDITIONS: None\nRISKS: Unable to evaluate."
            elapsed = 0

        # Parse finding
        finding = "PASS"
        if "FINDING: FAIL" in response or "FINDING:FAIL" in response:
            finding = "FAIL"
        elif "CONDITIONAL PASS" in response or "CONDITIONAL" in response.split('\n')[0]:
            finding = "CONDITIONAL PASS"

        fc = C.GREEN if finding == "PASS" else C.YELLOW if "CONDITIONAL" in finding else C.RED
        icon = "✅" if finding == "PASS" else "⚠️ " if "CONDITIONAL" in finding else "❌"

        print(f"\n  {icon} {fc}{C.BOLD}{finding}{C.END}  {C.DIM}({elapsed:.1f}s){C.END}")
        print(f"  {C.DIM}{'─'*56}{C.END}")

        # Print response with formatting
        for line in response.strip().split('\n'):
            line_s = line.strip()
            if line_s.startswith("FINDING:"):
                print(f"  {fc}{C.BOLD}{line_s}{C.END}")
            elif line_s.startswith("REASONING:"):
                print(f"  {C.WHITE}{line_s}{C.END}")
            elif line_s.startswith("CONDITIONS:"):
                print(f"  {C.YELLOW}{line_s}{C.END}")
            elif line_s.startswith("RISKS:"):
                print(f"  {C.RED}{line_s}{C.END}")
            else:
                print(f"  {line_s}")

        question_results.append({
            "id": q['id'],
            "question": q['question'],
            "severity": q['severity'],
            "finding": finding,
            "summary": response[:500],
            "full_response": response,
        })

        if i < len(COMPLIANCE_QUESTIONS) - 1:
            wait(f"\nPress ENTER for {q['id']} → next question ({i+2}/{len(COMPLIANCE_QUESTIONS)})...")

    # ═══════════════════════════════════════════════════════════
    #  FINAL VERDICT
    # ═══════════════════════════════════════════════════════════
    wait("\nPress ENTER for FINAL VERDICT...")

    passes = sum(1 for r in question_results if r['finding'] == 'PASS')
    conditionals = sum(1 for r in question_results if 'CONDITIONAL' in r['finding'])
    fails = sum(1 for r in question_results if r['finding'] == 'FAIL')

    print(f"\n{C.CYAN}{'═'*62}{C.END}")
    print(f"  {C.BOLD}FINAL VERDICT{C.END}")
    print(f"{C.CYAN}{'═'*62}{C.END}\n")

    print(f"  {C.BOLD}Score:{C.END}  {C.GREEN}PASS: {passes}{C.END}  |  {C.YELLOW}CONDITIONAL: {conditionals}{C.END}  |  {C.RED}FAIL: {fails}{C.END}\n")

    for r in question_results:
        fc = C.GREEN if r['finding'] == 'PASS' else C.YELLOW if 'CONDITIONAL' in r['finding'] else C.RED
        icon = '✅' if r['finding'] == 'PASS' else '⚠️ ' if 'CONDITIONAL' in r['finding'] else '❌'
        print(f"  {icon} {r['id']} [{r['severity']:8s}] {fc}{r['finding']:18s}{C.END} {r['question'][:48]}...")

    # Get LLM verdict
    print(f"\n  {C.DIM}Generating final verdict via Gemini...{C.END}")
    verdict_prompt = build_verdict_prompt(question_results, seller, buyer, hydrology)
    try:
        verdict = llm.call(system_prompt, verdict_prompt)
    except Exception as e:
        verdict = f"Error: {e}"

    # Determine overall
    if fails > 0 and any(r['finding'] == 'FAIL' and r['severity'] == 'critical' for r in question_results):
        overall, oc = "DENIED", C.RED
    elif conditionals > 0 or fails > 0:
        overall, oc = "CONDITIONALLY APPROVED", C.YELLOW
    else:
        overall, oc = "APPROVED", C.GREEN

    print(f"""
{oc}{C.BOLD}
  ╔════════════════════════════════════════════════════════════╗
  ║                                                            ║
  ║   TRANSFER {transfer['transfer_id']}:  {overall:^24s}       ║
  ║                                                            ║
  ╚════════════════════════════════════════════════════════════╝
{C.END}""")

    for line in verdict.strip().split('\n'):
        print(f"  {line}")

    print(f"\n{C.CYAN}{'═'*62}{C.END}")
    print(f"  {C.DIM}Powered by:{C.END}")
    print(f"    • Kern County GSP 2025 ({stats['gsp_chunks']} policy sections)")
    print(f"    • SGMA statute ({stats['sgma_chunks']} sections)")
    print(f"    • Knowledge Graph ({len(kg.entities)} entities, {len(kg.relationships)} relationships)")
    print(f"    • {llm.provider}")
    print(f"\n  {C.BOLD}{C.CYAN}WaterXchange — Making water transfers transparent, compliant, and fair.{C.END}\n")


def wait(msg="Press ENTER to continue..."):
    print(f"\n{C.DIM}{msg}{C.END}")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
