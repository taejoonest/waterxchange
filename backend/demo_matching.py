#!/usr/bin/env python3
"""
WaterXchange — Algorithmic Matching Demo
==========================================

A 4-scene terminal demo showing:
  SCENE 1: Order Pool — 10 farmers with crops, water needs, prices
  SCENE 2: Economic Scoring — marginal value of water by crop
  SCENE 3: Matching Matrix — all pairs scored (economic × environmental)
  SCENE 4: Optimal Matches + Sensitivity Analysis

Run:
  cd /Users/mmm/Downloads/waterxchane/backend
  source venv/bin/activate
  python3 demo_matching.py

Add --auto for non-interactive mode (no pauses).
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

from services.matching_pool import get_farmer_pool, format_order_book, CROP_ECONOMICS
from services.smart_matching import (
    compute_economic_score, compute_environmental_risk,
    compute_match_score, run_matching, run_sensitivity
)


# ─────────────────────────────────────────────────────
# ANSI Colors
# ─────────────────────────────────────────────────────
class C:
    BOLD   = '\033[1m'
    DIM    = '\033[2m'
    CYAN   = '\033[96m'
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    MAG    = '\033[95m'
    WHITE  = '\033[97m'
    END    = '\033[0m'
    BG_DK  = '\033[48;5;234m'

AUTO = '--auto' in sys.argv


def wait():
    if not AUTO:
        print(f"\n{C.DIM}Press ENTER to continue...{C.END}")
        try:
            input()
        except EOFError:
            pass


def banner(title: str, subtitle: str = ''):
    w = 68
    print(f"\n{C.BOLD}{C.CYAN}{'═'*w}")
    print(f"  {title}")
    if subtitle:
        print(f"  {C.DIM}{subtitle}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'═'*w}{C.END}\n")


def section(title: str):
    print(f"\n{C.BOLD}{C.BLUE}── {title} ──{C.END}\n")


def risk_bar(value: float, width: int = 20) -> str:
    """Render a horizontal risk bar."""
    filled = int(value * width)
    empty  = width - filled
    if value < 0.3:
        color = C.GREEN
    elif value < 0.6:
        color = C.YELLOW
    else:
        color = C.RED
    return f"{color}{'█' * filled}{'░' * empty}{C.END} {value:.2f}"


def surplus_bar(value: float, max_val: float = 1400, width: int = 20) -> str:
    """Render economic surplus bar."""
    norm = min(1.0, max(0.0, value / max_val))
    filled = int(norm * width)
    empty  = width - filled
    return f"{C.GREEN}{'█' * filled}{'░' * empty}{C.END} ${value:,.0f}/AF"


# ═══════════════════════════════════════════════════════
#  SCENE 1 — ORDER POOL
# ═══════════════════════════════════════════════════════

def scene1_order_pool(pool):
    banner(
        "SCENE 1 — THIS WEEK'S ORDER POOL",
        "10 farmers in Kern County Subbasin — weekly spot orders (5-50 AF)"
    )

    sellers = [f for f in pool if f['role'] == 'SELLER']
    buyers  = [f for f in pool if f['role'] == 'BUYER']

    print(f"  {C.BOLD}SELL SIDE{C.END} ({len(sellers)} orders, {sum(s['selling_af'] for s in sellers)} AF total)")
    print(f"  {'─'*80}")
    print(f"  {C.DIM}{'ID':<5}{'Farmer':<24}{'GSA':<24}{'Qty':>6}  {'Ask':>8}  {'Marginal Crop':<20}{C.END}")
    for s in sorted(sellers, key=lambda x: x['ask_price']):
        print(
            f"  {C.BOLD}{s['id']:<5}{C.END}{s['name']:<24}{s['gsa']:<24}"
            f"{s['selling_af']:>5} AF  ${s['ask_price']:>6}/AF  "
            f"{C.DIM}{s['marginal_crop_fallowed']}{C.END}"
        )
        print(f"        {C.DIM}↳ {s.get('selling_note', '')}{C.END}")

    print()
    print(f"  {C.BOLD}BUY SIDE{C.END} ({len(buyers)} orders, {sum(b['buying_af'] for b in buyers)} AF total)")
    print(f"  {'─'*80}")
    print(f"  {C.DIM}{'ID':<5}{'Farmer':<24}{'GSA':<24}{'Qty':>6}  {'Bid':>8}  {'Expanding Crop':<20}{C.END}")
    for b in sorted(buyers, key=lambda x: -x['bid_price']):
        crop = b.get('marginal_crop_expanding', '?')
        print(
            f"  {C.BOLD}{b['id']:<5}{C.END}{b['name']:<24}{b['gsa']:<24}"
            f"{b['buying_af']:>5} AF  ${b['bid_price']:>6}/AF  "
            f"{C.DIM}{crop}{C.END}"
        )
        print(f"        {C.DIM}↳ {b.get('buying_note', '')}{C.END}")

    total_sell = sum(s['selling_af'] for s in sellers)
    total_buy  = sum(b['buying_af'] for b in buyers)
    print(f"\n  {C.DIM}Total supply: {total_sell} AF  |  Total demand: {total_buy} AF{C.END}")
    wait()


# ═══════════════════════════════════════════════════════
#  SCENE 2 — ECONOMIC MODEL
# ═══════════════════════════════════════════════════════

def scene2_economics(pool):
    banner(
        "SCENE 2 — ECONOMIC MODEL",
        "Marginal Revenue Product of Water (MRP) by crop"
    )

    section("Crop Economics Table (UC Davis / USDA)")

    crops_sorted = sorted(
        CROP_ECONOMICS.items(),
        key=lambda x: x[1]['marginal_value_af'],
        reverse=True
    )

    print(f"  {C.DIM}{'Crop':<24}{'Rev/ac':>9}{'Water Duty':>12}{'Var Cost':>11}{'MRP ($/AF)':>12}  {'Value Bar'}{C.END}")
    print(f"  {'─'*90}")
    for name, data in crops_sorted:
        if name == 'Fallowed':
            continue
        mrp = data['marginal_value_af']
        bar = surplus_bar(mrp)
        print(
            f"  {name:<24}${data['revenue_per_acre']:>7,}/ac  "
            f"{data['water_duty']:>5.1f} AF/ac  "
            f"${data['var_cost']:>7,}/ac  "
            f"${mrp:>8,}/AF  {bar}"
        )

    section("Why Trades Happen — Gains from Trade")

    sellers = sorted([f for f in pool if f['role'] == 'SELLER'], key=lambda x: x['ask_price'])
    buyers  = sorted([f for f in pool if f['role'] == 'BUYER'],  key=lambda x: -x['bid_price'])

    print(f"  The core economic insight:")
    print(f"  A farmer growing {C.RED}alfalfa{C.END} (MRP = ${C.RED}$60{C.END}/AF) should SELL water to")
    print(f"  a farmer growing {C.GREEN}mandarins{C.END} (MRP = {C.GREEN}$1,333{C.END}/AF).")
    print(f"  Gains from trade = $1,333 − $60 = {C.BOLD}{C.GREEN}$1,273/AF{C.END} in economic value created.\n")

    print(f"  {C.DIM}Ref: Hanak & Stryjewski (2012), PPIC — 'California's Water Market, By the Numbers'{C.END}")
    print(f"  {C.DIM}Ref: Ayres et al. (2021) — 'Impact of SGMA on Groundwater Markets'{C.END}")

    wait()


# ═══════════════════════════════════════════════════════
#  SCENE 3 — MATCHING MATRIX
# ═══════════════════════════════════════════════════════

def scene3_matching_matrix(pool):
    banner(
        "SCENE 3 — MATCHING MATRIX",
        "All (seller × buyer) pairs scored for economic benefit + environmental risk"
    )

    sellers = [f for f in pool if f['role'] == 'SELLER']
    buyers  = [f for f in pool if f['role'] == 'BUYER']

    section("Economic Scoring: Every Pair")

    # Header row
    header = f"  {'':<8}"
    for b in buyers:
        header += f"{b['id']:>12}"
    print(header)
    header2 = f"  {'Seller':<8}"
    for b in buyers:
        header2 += f"{'(' + b['name'][:8] + ')':>12}"
    print(f"  {C.DIM}{header2[2:]}{C.END}")
    print(f"  {'─' * (8 + 12 * len(buyers))}")

    for s in sellers:
        row = f"  {s['id']:<8}"
        for b in buyers:
            econ = compute_economic_score(s, b)
            if econ['feasible']:
                surplus = econ['total_surplus_per_af']
                if surplus > 600:
                    color = C.GREEN
                elif surplus > 300:
                    color = C.YELLOW
                else:
                    color = C.DIM
                row += f"{color}${surplus:>9,.0f}/AF{C.END}"
            else:
                row += f"{C.RED}{'—':>12}{C.END}"
        print(row)

    section("Environmental Risk Scoring: Buyer Location")

    print(f"  {C.DIM}Risk is assessed at the BUYER's location (where extraction increases){C.END}\n")
    print(f"  {'Buyer':<6}{'Name':<22}{'HCM Area':<18}{'Subsid':>8}{'GW Decl':>8}{'WQ':>8}{'DomWells':>8}  {'Composite'}")
    print(f"  {'─'*90}")
    for b in buyers:
        env = compute_environmental_risk(sellers[0], b)  # seller doesn't matter much for buyer risk
        print(
            f"  {b['id']:<6}{b['name']:<22}{b.get('hcm_area','?'):<18}"
            f"{env['subsidence_risk']:>8.2f}{env['gw_depletion_risk']:>8.2f}"
            f"{env['water_quality_risk']:>8.2f}{env['domestic_well_risk']:>8.2f}"
            f"  {risk_bar(env['composite_risk'])}"
        )

    section("Composite Match Score Matrix")

    print(f"  {C.DIM}Score = 0.6 × Economic − 0.4 × Environmental Risk{C.END}")
    print(f"  {C.DIM}(higher = better match){C.END}\n")

    header = f"  {'':<8}"
    for b in buyers:
        header += f"{b['id']:>12}"
    print(header)
    print(f"  {'─' * (8 + 12 * len(buyers))}")

    for s in sellers:
        row = f"  {s['id']:<8}"
        for b in buyers:
            m = compute_match_score(s, b)
            if m['feasible']:
                score = m['match_score']
                if score > 0.30:
                    color = C.GREEN + C.BOLD
                elif score > 0.15:
                    color = C.YELLOW
                elif score > 0:
                    color = C.DIM
                else:
                    color = C.RED
                row += f"{color}{score:>12.4f}{C.END}"
            else:
                row += f"{C.RED}{'—':>12}{C.END}"
        print(row)

    print(f"\n  {C.GREEN}██{C.END} > 0.30 Excellent  {C.YELLOW}██{C.END} > 0.15 Good  "
          f"{C.DIM}██{C.END} > 0.00 Marginal  {C.RED}██{C.END} Infeasible/Negative")

    wait()


# ═══════════════════════════════════════════════════════
#  SCENE 4 — OPTIMAL MATCHES + SENSITIVITY
# ═══════════════════════════════════════════════════════

def scene4_results(pool):
    banner(
        "SCENE 4 — OPTIMAL MATCHING RESULTS",
        "Greedy assignment maximizing composite score"
    )

    result = run_matching(pool, alpha=0.6, beta=0.4)

    section("Matched Trades (WaterXchange Default: α=0.6, β=0.4)")

    for i, m in enumerate(result['matches'], 1):
        finding_color = C.GREEN if m['environmental_risk'] < 0.3 else C.YELLOW if m['environmental_risk'] < 0.5 else C.RED
        print(f"  {C.BOLD}Trade #{i}{C.END}")
        print(f"  ┌─────────────────────────────────────────────────────────────┐")
        print(f"  │ {m['seller_name']:<22} ──({m['trade_quantity_af']} AF)──▶ {m['buyer_name']:<22}│")
        print(f"  │                                                             │")
        print(f"  │ Price: ${m['trade_price']:>7,.2f}/AF    Total: ${m['total_trade_value_usd']:>10,.2f}       │")
        print(f"  │ Surplus: {C.GREEN}${m['total_surplus_per_af']:>7,.2f}/AF{C.END}  Total Gain: {C.GREEN}${m['total_surplus_usd']:>10,.2f}{C.END}   │")
        print(f"  │ Env Risk: {risk_bar(m['environmental_risk'], 15)}                           │")
        print(f"  │ Match Score: {C.BOLD}{m['match_score']:+.4f}{C.END}                                       │")
        print(f"  └─────────────────────────────────────────────────────────────┘")

        # Show economic breakdown
        e = m['economic']
        print(f"    Economic: Seller opp cost ${e['seller_opp_cost']}/AF (crop: {result['matches'][i-1].get('seller_name','')})")
        print(f"              Buyer MRP ${e['buyer_mrp']}/AF → Consumer surplus ${e['consumer_surplus_per_af']}/AF")
        print(f"              Producer surplus ${e['producer_surplus_per_af']}/AF")
        # Show env breakdown
        env = m['environmental']
        print(f"    Environment: {env['buyer_hcm_area']} — "
              f"subsid={env['subsidence_risk']:.2f}, "
              f"gw_depl={env['gw_depletion_risk']:.2f}, "
              f"wq={env['water_quality_risk']:.2f}, "
              f"domwells={env['domestic_well_risk']:.2f}, "
              f"interGSA={env['inter_gsa_risk']:.2f}")
        print()

    # Show rejected trades
    if result.get('rejected'):
        print(f"  {C.RED}{C.BOLD}Rejected Trades{C.END} (negative composite score — env risk > economic benefit):")
        for r in result['rejected']:
            print(f"    {C.RED}X{C.END}  {r['seller_name']:<20} -> {r['buyer_name']:<20} "
                  f"score={r['match_score']:+.4f}  surplus=${r['total_surplus_per_af']:>6,.0f}/AF  "
                  f"risk={r['environmental_risk']:.2f}")
        print()

    if result['unmatched_sellers']:
        print(f"  {C.DIM}Unmatched sellers: {', '.join(s['name'] for s in result['unmatched_sellers'])}{C.END}")
    if result['unmatched_buyers']:
        print(f"  {C.DIM}Unmatched buyers: {', '.join(b['name'] for b in result['unmatched_buyers'])}{C.END}")

    section("Market Summary")

    print(f"  ┌────────────────────────────────────────────┐")
    print(f"  │  Trades Executed:     {C.BOLD}{result['num_trades']}{C.END}                     │")
    print(f"  │  Total Volume:        {C.BOLD}{result['total_volume_af']:,} AF{C.END}               │")
    print(f"  │  Total Trade Value:   {C.BOLD}${result['total_trade_value_usd']:>12,.2f}{C.END}      │")
    print(f"  │  Total Econ Surplus:  {C.GREEN}${result['total_economic_surplus']:>12,.2f}{C.END}      │")
    print(f"  │  Avg Env Risk:        {risk_bar(result['avg_environmental_risk'], 10)}               │")
    print(f"  └────────────────────────────────────────────┘")

    wait()

    # ── Sensitivity Analysis ──
    section("Sensitivity Analysis — How Does α/β Change Results?")

    scenarios = run_sensitivity(pool)

    print(f"  {C.DIM}{'Scenario':<26}{'α':>5}{'β':>5}{'Trades':>8}{'Volume':>10}{'Surplus':>14}{'Avg Risk':>10}{C.END}")
    print(f"  {'─'*80}")

    for s in scenarios:
        risk_color = C.GREEN if s['avg_environmental_risk'] < 0.3 else C.YELLOW if s['avg_environmental_risk'] < 0.5 else C.RED
        print(
            f"  {s['scenario_name']:<26}{s['alpha']:>5.1f}{s['beta']:>5.1f}"
            f"{s['num_trades']:>8}{s['total_volume_af']:>8} AF"
            f"  {C.GREEN}${s['total_economic_surplus']:>10,.0f}{C.END}"
            f"  {risk_color}{s['avg_environmental_risk']:.4f}{C.END}"
        )

    print()
    for s in scenarios:
        print(f"  {C.BOLD}{s['scenario_name']}{C.END}: {s['scenario_description']}")
        for m in s['matches']:
            icon = '✅' if m['environmental_risk'] < 0.3 else '⚠️' if m['environmental_risk'] < 0.5 else '❌'
            print(f"    {icon} {m['seller_name']:<20} → {m['buyer_name']:<20} "
                  f"{m['trade_quantity_af']:>4} AF @ ${m['trade_price']:>6,.0f}/AF  "
                  f"surplus=${m['total_surplus_per_af']:>6,.0f}/AF  risk={m['environmental_risk']:.2f}")
        print()

    print(f"  {C.BOLD}{C.CYAN}Key Insight:{C.END}")
    print(f"  When we prioritize economics only (α=1.0), the algorithm matches purely")
    print(f"  by surplus — but may route water to high-subsidence or high-nitrate areas.")
    print(f"  WaterXchange's balanced scoring (α=0.6, β=0.4) ensures that economically")
    print(f"  beneficial trades are also environmentally responsible.\n")
    print(f"  {C.DIM}This is the core innovation: no existing water market platform scores")
    print(f"  environmental risk as part of the matching algorithm.{C.END}")


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    os.system('clear' if os.name != 'nt' else 'cls')

    print(f"""{C.BOLD}{C.CYAN}
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║   W A T E R X C H A N G E  —  Weekly Spot Market Demo         ║
║                                                                ║
║   Multi-Objective Optimization:                                ║
║   Maximize Economic Benefit × Minimize Environmental Risk      ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
{C.END}""")

    print(f"  {C.DIM}Market Type: Weekly spot market — small, frequent trades (5-50 AF){C.END}")
    print(f"  {C.DIM}Economic Model: Marginal Revenue Product of Water (UC Davis, USDA){C.END}")
    print(f"  {C.DIM}Environmental Model: Kern County GSP Table 13-3 (subsidence, GW decline){C.END}")
    print(f"  {C.DIM}Basin: Kern County Subbasin (5-22.14) — Critically Overdrafted{C.END}")
    print(f"  {C.DIM}Snapshot: Week of Aug 12, 2025 (peak irrigation season){C.END}")

    pool = get_farmer_pool()
    print(f"\n  {C.GREEN}✓{C.END} Loaded {len(pool)} farmers ({sum(1 for f in pool if f['role']=='SELLER')} sellers, {sum(1 for f in pool if f['role']=='BUYER')} buyers)")

    wait()

    scene1_order_pool(pool)
    scene2_economics(pool)
    scene3_matching_matrix(pool)
    scene4_results(pool)

    print(f"\n{'═'*68}")
    print(f"  {C.BOLD}{C.CYAN}WaterXchange — Making water transfers transparent, compliant, and fair.{C.END}")
    print(f"{'═'*68}\n")


if __name__ == '__main__':
    main()
