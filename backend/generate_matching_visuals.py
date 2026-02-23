"""
WaterXchange — Algorithmic Matching Visuals
=============================================
Professional report-style PNGs for the matching demo.

Generates 3 images:
  1. matching_orderbook.png  — Order pool + crop economics
  2. matching_matrix.png     — Scoring matrix heatmap
  3. matching_results.png    — Optimal matches + sensitivity

Run:
  cd /Users/mmm/Downloads/waterxchane/backend
  source venv/bin/activate
  python3 generate_matching_visuals.py
"""

import sys, os
sys.path.insert(0, '.')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

from services.matching_pool import get_farmer_pool, CROP_ECONOMICS
from services.smart_matching import (
    compute_economic_score, compute_environmental_risk,
    compute_match_score, run_matching, run_sensitivity
)

# ═══════════════════════════════════════════════════════
#  DESIGN SYSTEM (matches existing compliance visuals)
# ═══════════════════════════════════════════════════════

BG         = '#FFFFFF'
BG_LIGHT   = '#F7F8FC'
BG_CARD    = '#F0F2F8'
BORDER     = '#D8DCE8'

NAVY       = '#1B2A4A'
DARK       = '#2D3748'
MID        = '#718096'
LIGHT      = '#A0AEC0'
FAINT      = '#CBD5E0'

BLUE       = '#2B6CB0'
TEAL       = '#0D9488'
RED        = '#C53030'
AMBER      = '#D97706'
GREEN      = '#16A34A'
PURPLE     = '#6B46C1'

BRAND      = '#0077B6'

F = {'family': 'sans-serif'}


def make_fig(w=20, h=13):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    return fig, ax


def draw_header(ax, title, subtitle='', y_top=0.98):
    ax.text(0.03, y_top, 'WaterXchange', ha='left', va='top',
            fontsize=10, color=BRAND, fontweight='bold', **F)
    ax.text(0.50, y_top, title, ha='center', va='top',
            fontsize=20, color=NAVY, fontweight='bold', **F)
    if subtitle:
        ax.text(0.50, y_top - 0.038, subtitle, ha='center', va='top',
                fontsize=9.5, color=MID, **F)
    line_y = y_top - 0.055
    ax.plot([0.03, 0.97], [line_y, line_y], color=BORDER, lw=1.2, solid_capstyle='round')
    ax.plot([0.03, 0.18], [line_y, line_y], color=BRAND, lw=2.5, solid_capstyle='round')
    return line_y


def draw_card(ax, x, y, w, h, bg=BG_CARD, edge=BORDER, lw=1.0):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.008",
                          facecolor=bg, edgecolor=edge, linewidth=lw)
    ax.add_patch(rect)


def draw_section(ax, x, y, text, color=NAVY):
    ax.text(x, y, text, ha='left', va='top',
            fontsize=12, color=color, fontweight='bold', **F)
    ax.plot([x, x + 0.005], [y - 0.014, y - 0.014],
            color=color, lw=3, solid_capstyle='round')


# ═══════════════════════════════════════════════════════
#  IMAGE 1 — ORDER BOOK + CROP ECONOMICS
# ═══════════════════════════════════════════════════════

def generate_orderbook():
    fig, ax = make_fig(20, 14)
    pool = get_farmer_pool()
    sellers = sorted([f for f in pool if f['role'] == 'SELLER'], key=lambda x: x['ask_price'])
    buyers  = sorted([f for f in pool if f['role'] == 'BUYER'],  key=lambda x: -x['bid_price'])

    yl = draw_header(ax, 'Weekly Spot Market — Order Pool & Economics',
                     'Kern County Subbasin  |  Week of Aug 12, 2025  |  10 Farmers  |  5-50 AF Spot Orders')

    # ── Left side: Order Book ──
    y = yl - 0.04
    draw_section(ax, 0.03, y, 'SELL ORDERS')
    y -= 0.035

    cols_x = [0.04, 0.12, 0.32, 0.47, 0.55, 0.63]
    headers = ['ID', 'Farmer', 'GSA', 'Qty (AF)', 'Ask ($/AF)', 'Marginal Crop']
    for cx, h in zip(cols_x, headers):
        ax.text(cx, y, h, fontsize=7.5, color=MID, fontweight='bold', **F)
    y -= 0.005
    ax.plot([0.03, 0.78], [y, y], color=BORDER, lw=0.8)
    y -= 0.018

    for s in sellers:
        bg_c = BG_LIGHT if sellers.index(s) % 2 == 0 else BG
        draw_card(ax, 0.035, y - 0.008, 0.74, 0.022, bg=bg_c, edge='none')
        ax.text(cols_x[0], y, s['id'], fontsize=8, color=NAVY, fontweight='bold', **F)
        ax.text(cols_x[1], y, s['name'], fontsize=8, color=DARK, **F)
        ax.text(cols_x[2], y, s['gsa'], fontsize=7, color=MID, **F)
        ax.text(cols_x[3], y, f"{s['selling_af']}", fontsize=8.5, color=NAVY, fontweight='bold', **F)
        ax.text(cols_x[4], y, f"${s['ask_price']}", fontsize=8.5, color=TEAL, fontweight='bold', **F)
        ax.text(cols_x[5], y, s['marginal_crop_fallowed'], fontsize=7.5, color=MID, **F)
        y -= 0.016
        ax.text(cols_x[1], y, s.get('selling_note', ''), fontsize=6, color=LIGHT, fontstyle='italic', **F)
        y -= 0.018

    y -= 0.015
    draw_section(ax, 0.03, y, 'BUY ORDERS')
    y -= 0.035

    for cx, h in zip(cols_x, ['ID', 'Farmer', 'GSA', 'Qty (AF)', 'Bid ($/AF)', 'Expanding Crop']):
        ax.text(cx, y, h, fontsize=7.5, color=MID, fontweight='bold', **F)
    y -= 0.005
    ax.plot([0.03, 0.78], [y, y], color=BORDER, lw=0.8)
    y -= 0.018

    for b in buyers:
        bg_c = BG_LIGHT if buyers.index(b) % 2 == 0 else BG
        draw_card(ax, 0.035, y - 0.008, 0.74, 0.022, bg='#FEF3E2' if b['bid_price'] >= 600 else bg_c, edge='none')
        ax.text(cols_x[0], y, b['id'], fontsize=8, color=NAVY, fontweight='bold', **F)
        ax.text(cols_x[1], y, b['name'], fontsize=8, color=DARK, **F)
        ax.text(cols_x[2], y, b['gsa'], fontsize=7, color=MID, **F)
        ax.text(cols_x[3], y, f"{b['buying_af']}", fontsize=8.5, color=NAVY, fontweight='bold', **F)
        bid_color = GREEN if b['bid_price'] >= 600 else AMBER if b['bid_price'] >= 400 else DARK
        ax.text(cols_x[4], y, f"${b['bid_price']}", fontsize=8.5, color=bid_color, fontweight='bold', **F)
        ax.text(cols_x[5], y, b.get('marginal_crop_expanding', '?'), fontsize=7.5, color=MID, **F)
        y -= 0.016
        ax.text(cols_x[1], y, b.get('buying_note', ''), fontsize=6, color=LIGHT, fontstyle='italic', **F)
        y -= 0.018

    # ── Right side: Crop Economics Chart ──
    x0 = 0.80
    y_chart = yl - 0.04
    draw_section(ax, x0, y_chart, 'Marginal Value of Water by Crop')
    y_chart -= 0.035

    ax.text(x0, y_chart, 'Revenue Product per AF ($/AF)', fontsize=7, color=MID, **F)
    y_chart -= 0.025

    crops_sorted = sorted(
        [(k, v) for k, v in CROP_ECONOMICS.items() if k != 'Fallowed'],
        key=lambda x: x[1]['marginal_value_af'], reverse=True
    )

    bar_w = 0.15
    bar_h = 0.018
    max_mrp = 1400

    for name, data in crops_sorted:
        mrp = data['marginal_value_af']
        norm = min(1.0, mrp / max_mrp)
        bar_len = norm * bar_w

        # Color gradient
        if mrp > 800:
            bar_color = '#0D9488'
        elif mrp > 400:
            bar_color = '#38A169'
        elif mrp > 200:
            bar_color = '#D97706'
        else:
            bar_color = '#C53030'

        ax.text(x0, y_chart, name, fontsize=7, color=DARK, va='center', **F)
        rect = FancyBboxPatch((x0 + 0.11, y_chart - bar_h/2), bar_len, bar_h,
                              boxstyle="round,pad=0.002",
                              facecolor=bar_color, edgecolor='none', alpha=0.85)
        ax.add_patch(rect)
        ax.text(x0 + 0.115 + bar_len, y_chart, f'${mrp:,}/AF',
                fontsize=7, color=bar_color, fontweight='bold', va='center', **F)
        y_chart -= 0.028

    # ── Footer insight ──
    y_foot = 0.03
    draw_card(ax, 0.03, y_foot - 0.01, 0.94, 0.05, bg='#EBF5FF', edge=BRAND)
    ax.text(0.05, y_foot + 0.025, 'KEY ECONOMIC INSIGHT', fontsize=8, color=BRAND, fontweight='bold', **F)
    ax.text(0.05, y_foot + 0.005,
            'A farmer growing alfalfa (MRP = $60/AF) should SELL water to a farmer growing mandarins '
            '(MRP = $1,333/AF).  Gains from trade = $1,273/AF in pure economic surplus created.',
            fontsize=7.5, color=DARK, **F)
    ax.text(0.78, y_foot + 0.005,
            'Ref: UC Davis Cost & Return Studies 2024',
            fontsize=6.5, color=LIGHT, fontstyle='italic', **F)

    out = os.path.join('..', 'matching_orderbook.png')
    fig.savefig(out, dpi=180, bbox_inches='tight', facecolor=BG)
    plt.close(fig)
    print(f"  Saved: {out}")


# ═══════════════════════════════════════════════════════
#  IMAGE 2 — SCORING MATRIX HEATMAP
# ═══════════════════════════════════════════════════════

def generate_matrix():
    fig, ax = make_fig(20, 14)
    pool = get_farmer_pool()
    sellers = [f for f in pool if f['role'] == 'SELLER']
    buyers  = [f for f in pool if f['role'] == 'BUYER']

    yl = draw_header(ax, 'Matching Matrix — Economic Benefit vs Environmental Risk',
                     'Composite Score = 0.6 x Economic Score  -  0.4 x Environmental Risk')

    # ── Build matrices ──
    n_s, n_b = len(sellers), len(buyers)

    econ_matrix = np.zeros((n_s, n_b))
    risk_matrix = np.zeros((n_s, n_b))
    comp_matrix = np.zeros((n_s, n_b))
    feasible    = np.ones((n_s, n_b), dtype=bool)

    for i, s in enumerate(sellers):
        for j, b in enumerate(buyers):
            m = compute_match_score(s, b)
            if m['feasible']:
                econ_matrix[i, j] = m['economic']['total_surplus_per_af']
                risk_matrix[i, j] = m['environmental']['composite_risk']
                comp_matrix[i, j] = m['match_score']
            else:
                feasible[i, j] = False
                econ_matrix[i, j] = 0
                risk_matrix[i, j] = 0
                comp_matrix[i, j] = -0.5

    # ── Draw heatmaps ──
    y_base = yl - 0.06

    # Panel 1: Economic Surplus
    panel_w, panel_h = 0.28, 0.35
    panel1_x = 0.04
    draw_section(ax, panel1_x, y_base, 'Economic Surplus ($/AF)')

    cell_w = panel_w / n_b
    cell_h = panel_h / n_s
    grid_y = y_base - 0.04

    # Column headers
    for j, b in enumerate(buyers):
        cx = panel1_x + j * cell_w + cell_w / 2
        ax.text(cx, grid_y + 0.01, b['id'], fontsize=7, color=MID, ha='center', fontweight='bold', **F)

    for i, s in enumerate(sellers):
        cy = grid_y - i * cell_h - cell_h / 2
        ax.text(panel1_x - 0.01, cy, s['id'], fontsize=7, color=MID, ha='right', va='center', fontweight='bold', **F)
        for j, b in enumerate(buyers):
            cx = panel1_x + j * cell_w
            if feasible[i, j]:
                val = econ_matrix[i, j]
                norm = min(1.0, max(0.0, val / 1300))
                r = int(220 - norm * 180)
                g = int(220 - norm * 50)
                b_c = int(220 - norm * 180)
                color = f'#{r:02x}{g:02x}{b_c:02x}'
                rect = FancyBboxPatch((cx, cy - cell_h/2), cell_w * 0.95, cell_h * 0.85,
                                      boxstyle="round,pad=0.002",
                                      facecolor=color, edgecolor=BORDER, linewidth=0.5)
                ax.add_patch(rect)
                ax.text(cx + cell_w/2, cy, f'${val:,.0f}',
                        fontsize=6, color='white' if norm > 0.5 else DARK,
                        ha='center', va='center', fontweight='bold', **F)
            else:
                rect = FancyBboxPatch((cx, cy - cell_h/2), cell_w * 0.95, cell_h * 0.85,
                                      boxstyle="round,pad=0.002",
                                      facecolor='#FEE2E2', edgecolor='#FCA5A5', linewidth=0.5)
                ax.add_patch(rect)
                ax.text(cx + cell_w/2, cy, '--',
                        fontsize=6, color=RED, ha='center', va='center', **F)

    # Panel 2: Environmental Risk
    panel2_x = 0.37
    draw_section(ax, panel2_x, y_base, 'Environmental Risk (0-1)')

    for j, b_f in enumerate(buyers):
        cx = panel2_x + j * cell_w + cell_w / 2
        ax.text(cx, grid_y + 0.01, b_f['id'], fontsize=7, color=MID, ha='center', fontweight='bold', **F)

    for i, s in enumerate(sellers):
        cy = grid_y - i * cell_h - cell_h / 2
        ax.text(panel2_x - 0.01, cy, s['id'], fontsize=7, color=MID, ha='right', va='center', fontweight='bold', **F)
        for j, b_f in enumerate(buyers):
            cx = panel2_x + j * cell_w
            if feasible[i, j]:
                val = risk_matrix[i, j]
                # Red gradient — higher risk = darker red
                if val < 0.3:
                    color = '#C6F6D5'
                    txt_c = DARK
                elif val < 0.5:
                    color = '#FEFCE8'
                    txt_c = DARK
                else:
                    color = '#FEE2E2'
                    txt_c = RED
                rect = FancyBboxPatch((cx, cy - cell_h/2), cell_w * 0.95, cell_h * 0.85,
                                      boxstyle="round,pad=0.002",
                                      facecolor=color, edgecolor=BORDER, linewidth=0.5)
                ax.add_patch(rect)
                ax.text(cx + cell_w/2, cy, f'{val:.2f}',
                        fontsize=6.5, color=txt_c,
                        ha='center', va='center', fontweight='bold', **F)
            else:
                rect = FancyBboxPatch((cx, cy - cell_h/2), cell_w * 0.95, cell_h * 0.85,
                                      boxstyle="round,pad=0.002",
                                      facecolor='#FEE2E2', edgecolor='#FCA5A5', linewidth=0.5)
                ax.add_patch(rect)
                ax.text(cx + cell_w/2, cy, '--',
                        fontsize=6, color=RED, ha='center', va='center', **F)

    # Panel 3: Composite Score
    panel3_x = 0.70
    draw_section(ax, panel3_x, y_base, 'Composite Match Score')

    for j, b_f in enumerate(buyers):
        cx = panel3_x + j * cell_w + cell_w / 2
        ax.text(cx, grid_y + 0.01, b_f['id'], fontsize=7, color=MID, ha='center', fontweight='bold', **F)

    # Find the best match for highlighting
    result = run_matching(pool, 0.6, 0.4)
    matched_pairs = set()
    for m in result['matches']:
        matched_pairs.add((m['seller_id'], m['buyer_id']))

    for i, s in enumerate(sellers):
        cy = grid_y - i * cell_h - cell_h / 2
        ax.text(panel3_x - 0.01, cy, s['id'], fontsize=7, color=MID, ha='right', va='center', fontweight='bold', **F)
        for j, b_f in enumerate(buyers):
            cx = panel3_x + j * cell_w
            is_matched = (s['id'], b_f['id']) in matched_pairs
            if feasible[i, j]:
                val = comp_matrix[i, j]
                if is_matched:
                    bg_color = '#0D9488'
                    txt_c = 'white'
                    edge_c = '#047857'
                    edge_w = 2.5
                elif val > 0.25:
                    bg_color = '#C6F6D5'
                    txt_c = DARK
                    edge_c = BORDER
                    edge_w = 0.5
                elif val > 0.10:
                    bg_color = '#FEFCE8'
                    txt_c = DARK
                    edge_c = BORDER
                    edge_w = 0.5
                elif val > 0:
                    bg_color = BG_LIGHT
                    txt_c = MID
                    edge_c = BORDER
                    edge_w = 0.5
                else:
                    bg_color = '#FEE2E2'
                    txt_c = RED
                    edge_c = BORDER
                    edge_w = 0.5
                rect = FancyBboxPatch((cx, cy - cell_h/2), cell_w * 0.95, cell_h * 0.85,
                                      boxstyle="round,pad=0.002",
                                      facecolor=bg_color, edgecolor=edge_c, linewidth=edge_w)
                ax.add_patch(rect)
                label = f'{val:+.3f}'
                if is_matched:
                    label = f'>> {val:+.3f}'
                ax.text(cx + cell_w/2, cy, label,
                        fontsize=6 if not is_matched else 6.5, color=txt_c,
                        ha='center', va='center', fontweight='bold', **F)
            else:
                rect = FancyBboxPatch((cx, cy - cell_h/2), cell_w * 0.95, cell_h * 0.85,
                                      boxstyle="round,pad=0.002",
                                      facecolor='#FEE2E2', edgecolor='#FCA5A5', linewidth=0.5)
                ax.add_patch(rect)
                ax.text(cx + cell_w/2, cy, '--',
                        fontsize=6, color=RED, ha='center', va='center', **F)

    # ── Legend ──
    y_leg = grid_y - n_s * cell_h - 0.04
    draw_card(ax, 0.70, y_leg - 0.01, 0.27, 0.05, bg=BG_LIGHT)
    ax.text(0.72, y_leg + 0.025, 'Legend', fontsize=8, color=NAVY, fontweight='bold', **F)
    legend_items = [
        ('#0D9488', 'Optimal Match (selected)'),
        ('#C6F6D5', 'Score > 0.25 (excellent)'),
        ('#FEFCE8', 'Score > 0.10 (good)'),
        ('#FEE2E2', 'Score < 0 or infeasible'),
    ]
    for k, (lc, lt) in enumerate(legend_items):
        lx = 0.72
        ly = y_leg + 0.008 - k * 0.012
        rect = FancyBboxPatch((lx, ly - 0.004), 0.015, 0.008,
                              boxstyle="round,pad=0.001",
                              facecolor=lc, edgecolor=BORDER, linewidth=0.5)
        ax.add_patch(rect)
        ax.text(lx + 0.02, ly, lt, fontsize=6.5, color=DARK, va='center', **F)

    # ── Environmental Risk detail for each buyer ──
    y_env = y_leg - 0.08
    draw_section(ax, 0.04, y_env, 'Buyer Environmental Risk Breakdown (GSP Table 13-3, p.681)')
    y_env -= 0.035

    risk_factors = ['Subsidence', 'GW Depletion', 'Water Quality', 'Domestic Wells', 'Inter-GSA']
    factor_keys  = ['subsidence_risk', 'gw_depletion_risk', 'water_quality_risk', 'domestic_well_risk', 'inter_gsa_risk']
    factor_colors = [RED, AMBER, PURPLE, BLUE, MID]

    # Table header
    ax.text(0.05, y_env, 'Buyer', fontsize=7, color=MID, fontweight='bold', **F)
    ax.text(0.13, y_env, 'HCM Area', fontsize=7, color=MID, fontweight='bold', **F)
    for k, rf in enumerate(risk_factors):
        ax.text(0.30 + k * 0.12, y_env, rf, fontsize=6.5, color=factor_colors[k], fontweight='bold', ha='center', **F)
    ax.text(0.91, y_env, 'Composite', fontsize=7, color=NAVY, fontweight='bold', ha='center', **F)
    y_env -= 0.005
    ax.plot([0.04, 0.97], [y_env, y_env], color=BORDER, lw=0.8)
    y_env -= 0.018

    for b_f in buyers:
        env = compute_environmental_risk(sellers[0], b_f)
        bg_c = BG_LIGHT if buyers.index(b_f) % 2 == 0 else BG
        draw_card(ax, 0.045, y_env - 0.008, 0.92, 0.022, bg=bg_c, edge='none')
        ax.text(0.05, y_env, b_f['id'], fontsize=7.5, color=NAVY, fontweight='bold', **F)
        ax.text(0.13, y_env, b_f.get('hcm_area', '?'), fontsize=7, color=MID, **F)
        for k, fk in enumerate(factor_keys):
            val = env[fk]
            fc = GREEN if val < 0.3 else AMBER if val < 0.6 else RED
            # Mini bar
            bar_x = 0.26 + k * 0.12
            bar_w = 0.07
            bar_h_px = 0.008
            # Background
            rect_bg = FancyBboxPatch((bar_x, y_env - 0.004), bar_w, bar_h_px,
                                     boxstyle="round,pad=0.001",
                                     facecolor=FAINT, edgecolor='none', alpha=0.5)
            ax.add_patch(rect_bg)
            # Fill
            rect_fill = FancyBboxPatch((bar_x, y_env - 0.004), bar_w * val, bar_h_px,
                                       boxstyle="round,pad=0.001",
                                       facecolor=fc, edgecolor='none', alpha=0.8)
            ax.add_patch(rect_fill)
            ax.text(bar_x + bar_w + 0.005, y_env, f'{val:.2f}',
                    fontsize=5.5, color=fc, va='center', fontweight='bold', **F)

        # Composite
        comp = env['composite_risk']
        comp_color = GREEN if comp < 0.3 else AMBER if comp < 0.5 else RED
        ax.text(0.91, y_env, f'{comp:.3f}', fontsize=8, color=comp_color,
                ha='center', va='center', fontweight='bold', **F)
        y_env -= 0.026

    out = os.path.join('..', 'matching_matrix.png')
    fig.savefig(out, dpi=180, bbox_inches='tight', facecolor=BG)
    plt.close(fig)
    print(f"  Saved: {out}")


# ═══════════════════════════════════════════════════════
#  IMAGE 3 — OPTIMAL MATCHES + SENSITIVITY
# ═══════════════════════════════════════════════════════

def generate_results():
    fig, ax = make_fig(20, 15)
    pool = get_farmer_pool()

    yl = draw_header(ax, 'Optimal Matching Results & Sensitivity Analysis',
                     'Greedy Assignment  |  Multi-Objective Optimization  |  3 Scenarios')

    result = run_matching(pool, 0.6, 0.4)
    scenarios = run_sensitivity(pool)

    # ── Matched Trades ──
    y = yl - 0.05
    draw_section(ax, 0.03, y, 'Matched Trades — WaterXchange Default (alpha=0.6, beta=0.4)')
    y -= 0.04

    for idx, m in enumerate(result['matches']):
        x0 = 0.04
        card_h = 0.075
        risk_val = m['environmental_risk']
        if risk_val < 0.3:
            edge_c, badge_bg, badge_txt = TEAL, '#ECFDF5', 'LOW RISK'
        elif risk_val < 0.5:
            edge_c, badge_bg, badge_txt = AMBER, '#FFFBEB', 'MED RISK'
        else:
            edge_c, badge_bg, badge_txt = RED, '#FEF2F2', 'HIGH RISK'

        draw_card(ax, x0, y - card_h, 0.92, card_h, bg=BG, edge=edge_c, lw=1.5)

        # Trade number + score
        ax.text(x0 + 0.015, y - 0.012, f'Trade #{idx+1}', fontsize=9,
                color=NAVY, fontweight='bold', **F)
        ax.text(x0 + 0.015, y - 0.032, f'Score: {m["match_score"]:+.4f}',
                fontsize=8, color=edge_c, fontweight='bold', **F)

        # Seller → Buyer flow
        sx = x0 + 0.14
        ax.text(sx, y - 0.015, m['seller_name'], fontsize=9, color=DARK, fontweight='bold', **F)
        ax.text(sx, y - 0.032, f'Opp cost: ${m["economic"]["seller_opp_cost"]}/AF', fontsize=7, color=MID, **F)

        # Arrow
        arrow_x = sx + 0.17
        ax.annotate('', xy=(arrow_x + 0.08, y - 0.025), xytext=(arrow_x, y - 0.025),
                    arrowprops=dict(arrowstyle='->', color=TEAL, lw=2))
        ax.text(arrow_x + 0.04, y - 0.012, f'{m["trade_quantity_af"]} AF',
                fontsize=8.5, color=TEAL, ha='center', fontweight='bold', **F)
        ax.text(arrow_x + 0.04, y - 0.038, f'@ ${m["trade_price"]:,.0f}/AF',
                fontsize=7, color=MID, ha='center', **F)

        # Buyer
        bx = arrow_x + 0.10
        ax.text(bx, y - 0.015, m['buyer_name'], fontsize=9, color=DARK, fontweight='bold', **F)
        ax.text(bx, y - 0.032, f'MRP: ${m["economic"]["buyer_mrp"]}/AF', fontsize=7, color=MID, **F)

        # Surplus
        spx = bx + 0.18
        ax.text(spx, y - 0.012, 'Surplus', fontsize=7, color=MID, **F)
        ax.text(spx, y - 0.030, f'${m["total_surplus_per_af"]:,.0f}/AF',
                fontsize=10, color=GREEN, fontweight='bold', **F)
        ax.text(spx, y - 0.048, f'Total: ${m["total_surplus_usd"]:,.0f}',
                fontsize=7, color=MID, **F)

        # Trade value
        tvx = spx + 0.12
        ax.text(tvx, y - 0.012, 'Trade Value', fontsize=7, color=MID, **F)
        ax.text(tvx, y - 0.030, f'${m["total_trade_value_usd"]:,.0f}',
                fontsize=10, color=NAVY, fontweight='bold', **F)

        # Risk badge
        bx2 = tvx + 0.12
        risk_badge = FancyBboxPatch((bx2, y - 0.035), 0.07, 0.02,
                                     boxstyle="round,pad=0.004",
                                     facecolor=badge_bg, edgecolor=edge_c, linewidth=1)
        ax.add_patch(risk_badge)
        ax.text(bx2 + 0.035, y - 0.025, badge_txt,
                fontsize=6.5, color=edge_c, ha='center', va='center', fontweight='bold', **F)

        # Env risk bar
        env_bar_x = bx2
        env_bar_y = y - 0.055
        env_bar_w = 0.07
        rect_bg = FancyBboxPatch((env_bar_x, env_bar_y), env_bar_w, 0.006,
                                  boxstyle="round,pad=0.001",
                                  facecolor=FAINT, edgecolor='none')
        ax.add_patch(rect_bg)
        rect_fill = FancyBboxPatch((env_bar_x, env_bar_y), env_bar_w * risk_val, 0.006,
                                    boxstyle="round,pad=0.001",
                                    facecolor=edge_c, edgecolor='none')
        ax.add_patch(rect_fill)
        ax.text(env_bar_x + env_bar_w + 0.01, env_bar_y + 0.003,
                f'Risk: {risk_val:.2f}', fontsize=6, color=edge_c, va='center', **F)

        y -= card_h + 0.015

    # ── Market Summary ──
    y -= 0.015
    draw_section(ax, 0.03, y, 'Market Summary')
    y -= 0.03

    summary_items = [
        ('Trades Executed', str(result['num_trades'])),
        ('Total Volume', f'{result["total_volume_af"]:,} AF'),
        ('Total Trade Value', f'${result["total_trade_value_usd"]:,.0f}'),
        ('Economic Surplus Created', f'${result["total_economic_surplus"]:,.0f}'),
        ('Avg Environmental Risk', f'{result["avg_environmental_risk"]:.4f}'),
    ]

    for k, (label, val) in enumerate(summary_items):
        sx = 0.05 + k * 0.185
        draw_card(ax, sx, y - 0.05, 0.17, 0.05, bg=BG_CARD)
        ax.text(sx + 0.085, y - 0.01, label, fontsize=7, color=MID,
                ha='center', **F)
        fs = 14 if k < 4 else 10
        vc = GREEN if k == 3 else NAVY
        ax.text(sx + 0.085, y - 0.035, val, fontsize=fs, color=vc,
                ha='center', fontweight='bold', **F)

    # ── Sensitivity Analysis ──
    y -= 0.09
    draw_section(ax, 0.03, y, 'Sensitivity Analysis — How alpha/beta Changes Results')
    y -= 0.03

    ax.text(0.05, y, 'Scenario', fontsize=8, color=MID, fontweight='bold', **F)
    ax.text(0.28, y, 'alpha', fontsize=8, color=MID, fontweight='bold', ha='center', **F)
    ax.text(0.34, y, 'beta', fontsize=8, color=MID, fontweight='bold', ha='center', **F)
    ax.text(0.42, y, 'Trades', fontsize=8, color=MID, fontweight='bold', ha='center', **F)
    ax.text(0.52, y, 'Volume', fontsize=8, color=MID, fontweight='bold', ha='center', **F)
    ax.text(0.64, y, 'Econ Surplus', fontsize=8, color=MID, fontweight='bold', ha='center', **F)
    ax.text(0.78, y, 'Avg Env Risk', fontsize=8, color=MID, fontweight='bold', ha='center', **F)
    ax.text(0.90, y, 'Matched Pairs', fontsize=8, color=MID, fontweight='bold', ha='center', **F)
    y -= 0.005
    ax.plot([0.04, 0.96], [y, y], color=BORDER, lw=0.8)
    y -= 0.022

    scenario_colors = [AMBER, TEAL, BLUE]
    for k, s in enumerate(scenarios):
        bg_c = BG_LIGHT if k % 2 == 0 else BG
        draw_card(ax, 0.045, y - 0.008, 0.91, 0.025, bg=bg_c, edge='none')

        name_color = scenario_colors[k]
        ax.text(0.05, y, s['scenario_name'], fontsize=8.5, color=name_color, fontweight='bold', **F)
        ax.text(0.28, y, f'{s["alpha"]:.1f}', fontsize=8, color=DARK, ha='center', **F)
        ax.text(0.34, y, f'{s["beta"]:.1f}', fontsize=8, color=DARK, ha='center', **F)
        ax.text(0.42, y, str(s['num_trades']), fontsize=9, color=NAVY, ha='center', fontweight='bold', **F)
        ax.text(0.52, y, f'{s["total_volume_af"]} AF', fontsize=8, color=DARK, ha='center', **F)
        ax.text(0.64, y, f'${s["total_economic_surplus"]:,.0f}', fontsize=9, color=GREEN, ha='center', fontweight='bold', **F)
        risk_c = GREEN if s['avg_environmental_risk'] < 0.3 else AMBER if s['avg_environmental_risk'] < 0.5 else RED
        ax.text(0.78, y, f'{s["avg_environmental_risk"]:.4f}', fontsize=9, color=risk_c, ha='center', fontweight='bold', **F)

        pairs = ', '.join(f'{m["seller_id"]}->{m["buyer_id"]}' for m in s['matches'])
        ax.text(0.90, y, pairs, fontsize=6, color=MID, ha='center', **F)
        y -= 0.030

    # ── Key insight box ──
    y -= 0.015
    draw_card(ax, 0.03, y - 0.06, 0.94, 0.06, bg='#EBF5FF', edge=BRAND)
    ax.text(0.05, y - 0.01, 'CORE INNOVATION', fontsize=9, color=BRAND, fontweight='bold', **F)
    ax.text(0.05, y - 0.03,
            'No existing water market platform scores environmental risk as part of the matching algorithm.',
            fontsize=8, color=DARK, **F)
    ax.text(0.05, y - 0.048,
            'WaterXchange\'s balanced scoring ensures trades are both economically beneficial and environmentally responsible — '
            'exactly what SGMA compliance requires.',
            fontsize=7.5, color=MID, **F)

    out = os.path.join('..', 'matching_results.png')
    fig.savefig(out, dpi=180, bbox_inches='tight', facecolor=BG)
    plt.close(fig)
    print(f"  Saved: {out}")


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

if __name__ == '__main__':
    print("Generating matching demo visuals...")
    generate_orderbook()
    generate_matrix()
    generate_results()
    print("\nDone! Files saved to project root:")
    print("  - matching_orderbook.png")
    print("  - matching_matrix.png")
    print("  - matching_results.png")
