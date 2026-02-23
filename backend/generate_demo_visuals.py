"""
WaterXchange — Professional Report-Style Visuals
=================================================
Clean white background, consulting-grade layout.

Run:
  cd /Users/mmm/Downloads/waterxchane/backend
  source venv/bin/activate
  python3 generate_demo_visuals.py
"""

import sys, os
sys.path.insert(0, '.')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
import matplotlib.patheffects as pe
import numpy as np

from services.farmer_data import get_farmer_a_seller, get_farmer_b_buyer, get_hydrology_data
from services.compliance_engine import COMPLIANCE_QUESTIONS

# ═══════════════════════════════════════════════════════════════
#  PROFESSIONAL DESIGN SYSTEM — Light/White
# ═══════════════════════════════════════════════════════════════

BG         = '#FFFFFF'
BG_LIGHT   = '#F7F8FC'     # very light gray for alternating rows
BG_CARD    = '#F0F2F8'     # card background
BORDER     = '#D8DCE8'     # card border

NAVY       = '#1B2A4A'     # primary text
DARK       = '#2D3748'     # secondary text
MID        = '#718096'     # tertiary / labels
LIGHT      = '#A0AEC0'     # dim text
FAINT      = '#CBD5E0'     # very dim

BLUE       = '#2B6CB0'     # primary accent
TEAL       = '#0D9488'     # positive / pass
RED        = '#C53030'     # danger / fail
AMBER      = '#D97706'     # warning / conditional
GREEN      = '#16A34A'     # success
PURPLE     = '#6B46C1'     # highlight

BRAND      = '#0077B6'     # WaterXchange brand blue

# Font kwargs — no weight key to avoid matplotlib conflicts
F = {'family': 'sans-serif'}


def make_fig(w=20, h=12.5):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    return fig, ax


def draw_header(ax, title, subtitle='', y_top=0.98):
    """Professional header with brand mark and thin underline."""
    ax.text(0.03, y_top, 'WaterXchange', ha='left', va='top',
            fontsize=10, color=BRAND, fontweight='bold', **F)
    ax.text(0.50, y_top, title, ha='center', va='top',
            fontsize=20, color=NAVY, fontweight='bold', **F)
    if subtitle:
        ax.text(0.50, y_top - 0.038, subtitle, ha='center', va='top',
                fontsize=9.5, color=MID, **F)
    # Clean underline
    line_y = y_top - 0.055
    ax.plot([0.03, 0.97], [line_y, line_y], color=BORDER, lw=1.2, solid_capstyle='round')
    ax.plot([0.03, 0.18], [line_y, line_y], color=BRAND, lw=2.5, solid_capstyle='round')
    return line_y


def draw_card(ax, x, y, w, h, bg=BG_CARD, edge=BORDER, lw=1.0):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.008",
                          facecolor=bg, edgecolor=edge, linewidth=lw)
    ax.add_patch(rect)


def draw_section_title(ax, x, y, text, color=NAVY):
    ax.text(x, y, text, ha='left', va='top',
            fontsize=11, color=color, fontweight='bold', **F)
    ax.plot([x, x + 0.005], [y - 0.012, y - 0.012], color=color, lw=3, solid_capstyle='round')


def draw_kv(ax, x, y, key, val, key_color=MID, val_color=NAVY, fs=8):
    ax.text(x, y, key, ha='left', va='center', fontsize=fs, color=key_color, **F)
    ax.text(x + 0.18, y, val, ha='right', va='center', fontsize=fs, color=val_color, fontweight='bold', **F)


seller = get_farmer_a_seller()
buyer  = get_farmer_b_buyer()
hydro  = get_hydrology_data()


# ═══════════════════════════════════════════════════════════════
#  ACT 2 — Transfer Request Architecture
# ═══════════════════════════════════════════════════════════════

def generate_act2():
    fig, ax = make_fig(20, 13)
    line_y = draw_header(ax, 'Transfer Request Architecture',
                         'Intra-basin groundwater credit transfer  |  Kern County Subbasin  |  WXT-2026-0042')

    # ── SELLER CARD ──
    sx, sy, sw, sh = 0.03, 0.24, 0.28, 0.62
    draw_card(ax, sx, sy, sw, sh, bg='#F0FAF4', edge='#86EFAC')

    draw_section_title(ax, sx + 0.015, sy + sh - 0.015, 'SELLER', color=TEAL)
    ax.text(sx + 0.015, sy + sh - 0.050, 'John Martinez', ha='left', va='top',
            fontsize=14, color=NAVY, fontweight='bold', **F)
    ax.text(sx + 0.015, sy + sh - 0.078, 'Green Valley Farm', ha='left', va='top',
            fontsize=10, color=MID, **F)

    # Info rows
    info_y = sy + sh - 0.115
    seller_info = [
        ('GSA', 'Rosedale-Rio Bravo WSD', 'p.761'),
        ('HCM Area', 'Kern River Fan', 'p.681'),
        ('Acreage', '640 ac (580 irrigated)', ''),
        ('Irrigation', 'Micro-drip, 92% efficiency', ''),
    ]
    for i, (k, v, cite) in enumerate(seller_info):
        iy = info_y - i * 0.030
        ax.text(sx + 0.015, iy, k, ha='left', va='center', fontsize=7.5, color=MID, **F)
        ax.text(sx + sw - 0.015, iy, v, ha='right', va='center', fontsize=7.5, color=DARK, fontweight='bold', **F)
        if cite:
            ax.text(sx + sw - 0.015, iy - 0.013, f'GSP {cite}', ha='right', va='center',
                    fontsize=5.5, color=LIGHT, style='italic', **F)

    # Crops - horizontal bars
    crop_y = info_y - len(seller_info) * 0.030 - 0.025
    ax.text(sx + 0.015, crop_y, 'Crops', ha='left', va='center', fontsize=7.5, color=MID, fontweight='bold', **F)
    crops_s = [('Almonds', 320, TEAL), ('Pistachios', 200, BLUE), ('Fallowed', 60, FAINT)]
    max_ac = 640
    for i, (name, ac, color) in enumerate(crops_s):
        by = crop_y - 0.025 - i * 0.028
        bar_w = (ac / max_ac) * (sw - 0.04)
        rect = FancyBboxPatch((sx + 0.015, by - 0.008), bar_w, 0.016,
                              boxstyle="round,pad=0.003",
                              facecolor=color, edgecolor='none', alpha=0.25)
        ax.add_patch(rect)
        ax.text(sx + 0.020, by, f'{name}', ha='left', va='center', fontsize=7, color=DARK, **F)
        ax.text(sx + sw - 0.015, by, f'{ac} ac', ha='right', va='center', fontsize=7, color=MID, **F)

    # Water budget
    budget_y = crop_y - 0.025 - len(crops_s) * 0.028 - 0.015
    ax.plot([sx + 0.015, sx + sw - 0.015], [budget_y + 0.008, budget_y + 0.008], color=BORDER, lw=0.5)
    ax.text(sx + 0.015, budget_y, 'Water Budget', ha='left', va='center', fontsize=7.5, color=MID, fontweight='bold', **F)
    budget_items = [
        ('GSA Allocation', '1,850 AF', DARK),
        ('Surface Water', '280 AF', MID),
        ('Carryover', '220 AF', MID),
        ('Total Available', '2,350 AF', TEAL),
        ('Crop Demand', '1,720 AF', AMBER),
        ('Surplus', '630 AF', GREEN),
    ]
    for i, (k, v, color) in enumerate(budget_items):
        iy = budget_y - 0.025 - i * 0.028
        ax.text(sx + 0.015, iy, k, ha='left', va='center', fontsize=7.5, color=MID, **F)
        ax.text(sx + sw - 0.015, iy, v, ha='right', va='center', fontsize=7.5, color=color, fontweight='bold', **F)

    # Subsidence badge
    sub_y = sy + 0.025
    draw_card(ax, sx + 0.010, sub_y, sw - 0.020, 0.040, bg='#ECFDF5', edge=TEAL)
    ax.text(sx + sw/2, sub_y + 0.028, 'Subsidence: 0.022 ft/yr   |   MT: 0.029 ft/yr   |   Below Threshold',
            ha='center', va='center', fontsize=7.5, color=TEAL, fontweight='bold', **F)
    ax.text(sx + sw/2, sub_y + 0.008, 'GSP Table 13-3, p.681',
            ha='center', va='center', fontsize=6, color=LIGHT, style='italic', **F)

    # ── BUYER CARD ──
    bx, by_, bw, bh = 0.69, 0.24, 0.28, 0.62
    draw_card(ax, bx, by_, bw, bh, bg='#FFF7ED', edge='#FDBA74')

    draw_section_title(ax, bx + 0.015, by_ + bh - 0.015, 'BUYER', color=AMBER)
    ax.text(bx + 0.015, by_ + bh - 0.050, 'Sarah Chen', ha='left', va='top',
            fontsize=14, color=NAVY, fontweight='bold', **F)
    ax.text(bx + 0.015, by_ + bh - 0.078, 'Sunrise Farms', ha='left', va='top',
            fontsize=10, color=MID, **F)

    buyer_info = [
        ('GSA', 'Semitropic WSD', 'p.761'),
        ('HCM Area', 'North Basin', 'p.681'),
        ('Acreage', '320 ac (300 irrigated)', ''),
        ('Irrigation', 'Flood + Drip, 78% efficiency', ''),
    ]
    info_y = by_ + bh - 0.115
    for i, (k, v, cite) in enumerate(buyer_info):
        iy = info_y - i * 0.030
        ax.text(bx + 0.015, iy, k, ha='left', va='center', fontsize=7.5, color=MID, **F)
        ax.text(bx + bw - 0.015, iy, v, ha='right', va='center', fontsize=7.5, color=DARK, fontweight='bold', **F)
        if cite:
            ax.text(bx + bw - 0.015, iy - 0.013, f'GSP {cite}', ha='right', va='center',
                    fontsize=5.5, color=LIGHT, style='italic', **F)

    crop_y = info_y - len(buyer_info) * 0.030 - 0.025
    ax.text(bx + 0.015, crop_y, 'Crops', ha='left', va='center', fontsize=7.5, color=MID, fontweight='bold', **F)
    crops_b = [('Alfalfa (out)', 120, AMBER), ('Pistachios (new)', 100, BLUE), ('Tomatoes', 80, RED)]
    for i, (name, ac, color) in enumerate(crops_b):
        cy = crop_y - 0.025 - i * 0.028
        bar_w = (ac / 320) * (bw - 0.04)
        rect = FancyBboxPatch((bx + 0.015, cy - 0.008), bar_w, 0.016,
                              boxstyle="round,pad=0.003",
                              facecolor=color, edgecolor='none', alpha=0.20)
        ax.add_patch(rect)
        ax.text(bx + 0.020, cy, f'{name}', ha='left', va='center', fontsize=7, color=DARK, **F)
        ax.text(bx + bw - 0.015, cy, f'{ac} ac', ha='right', va='center', fontsize=7, color=MID, **F)

    budget_y = crop_y - 0.025 - len(crops_b) * 0.028 - 0.015
    ax.plot([bx + 0.015, bx + bw - 0.015], [budget_y + 0.008, budget_y + 0.008], color=BORDER, lw=0.5)
    ax.text(bx + 0.015, budget_y, 'Water Budget', ha='left', va='center', fontsize=7.5, color=MID, fontweight='bold', **F)
    budget_b = [
        ('GSA Allocation', '900 AF', DARK),
        ('Surface Water', '120 AF', MID),
        ('Carryover', '50 AF', MID),
        ('Total Available', '1,070 AF', AMBER),
        ('Crop Demand', '1,144 AF', RED),
        ('Deficit', '-74 AF', RED),
    ]
    for i, (k, v, color) in enumerate(budget_b):
        iy = budget_y - 0.025 - i * 0.028
        ax.text(bx + 0.015, iy, k, ha='left', va='center', fontsize=7.5, color=MID, **F)
        ax.text(bx + bw - 0.015, iy, v, ha='right', va='center', fontsize=7.5, color=color, fontweight='bold', **F)

    sub_y = by_ + 0.025
    draw_card(ax, bx + 0.010, sub_y, bw - 0.020, 0.040, bg='#FEF2F2', edge=RED)
    ax.text(bx + bw/2, sub_y + 0.028, 'Subsidence: 0.059 ft/yr   |   MT: 0.053 ft/yr   |   Exceeds Threshold',
            ha='center', va='center', fontsize=7.5, color=RED, fontweight='bold', **F)
    ax.text(bx + bw/2, sub_y + 0.008, 'GSP Table 13-3, p.681',
            ha='center', va='center', fontsize=6, color=LIGHT, style='italic', **F)

    # ── TRANSFER CENTER ──
    tx, ty, tw, th = 0.335, 0.40, 0.33, 0.46
    draw_card(ax, tx, ty, tw, th, bg='#EFF6FF', edge=BLUE)

    ax.text(tx + tw/2, ty + th - 0.020, 'Proposed Transfer', ha='center', va='top',
            fontsize=12, color=BLUE, fontweight='bold', **F)
    ax.text(tx + tw/2, ty + th - 0.048, 'WXT-2026-0042', ha='center', va='top',
            fontsize=8, color=MID, **F)

    # Large number
    ax.text(tx + tw/2, ty + th - 0.13, '150 AF', ha='center', va='center',
            fontsize=42, color=BLUE, fontweight='bold', **F)
    ax.text(tx + tw/2, ty + th - 0.19, '$415 / AF   =   $62,250', ha='center', va='center',
            fontsize=12, color=NAVY, fontweight='bold', **F)

    ax.plot([tx + 0.02, tx + tw - 0.02], [ty + th - 0.22, ty + th - 0.22], color=BORDER, lw=0.7)

    meta = [
        ('Type', 'Intra-basin credit transfer'),
        ('Mechanism', 'GSA ledger (no physical conveyance)'),
        ('Duration', 'WY 2025-2026'),
        ('Basin', 'Kern County Subbasin (5-22.14)'),
        ('Status', 'Critically Overdrafted'),
    ]
    for i, (k, v) in enumerate(meta):
        my = ty + th - 0.255 - i * 0.030
        ax.text(tx + 0.025, my, k, ha='left', va='center', fontsize=7.5, color=MID, **F)
        ax.text(tx + tw - 0.025, my, v, ha='right', va='center', fontsize=7.5, color=DARK, **F)

    # Arrows
    ax.annotate('', xy=(tx, 0.60), xytext=(sx + sw, 0.60),
                arrowprops=dict(arrowstyle='->', color=TEAL, lw=2, connectionstyle='arc3,rad=0'))
    ax.text((sx + sw + tx) / 2, 0.615, '150 AF', ha='center', va='bottom',
            fontsize=9, color=TEAL, fontweight='bold', **F)

    ax.annotate('', xy=(bx, 0.60), xytext=(tx + tw, 0.60),
                arrowprops=dict(arrowstyle='->', color=AMBER, lw=2, connectionstyle='arc3,rad=0'))
    ax.text((tx + tw + bx) / 2, 0.615, '150 AF', ha='center', va='bottom',
            fontsize=9, color=AMBER, fontweight='bold', **F)

    # ── BASIN HYDROLOGY BAR ──
    draw_card(ax, 0.03, 0.03, 0.94, 0.175, bg=BG_LIGHT, edge=BORDER)
    ax.text(0.50, 0.19, 'Kern County Subbasin  |  Basin-Level Hydrology', ha='center', va='top',
            fontsize=10, color=NAVY, fontweight='bold', **F)

    stats = [
        ('1.31M', 'Sustainable Yield (AFY)', TEAL, 'GSP p.595'),
        ('1.59M', 'GW Pumping (AFY)', AMBER, 'GSP p.595'),
        ('-274K', 'Storage Change (AFY)', RED, 'GSP p.54'),
        ('372K', '2030 Projected Deficit', RED, 'GSP p.776'),
        ('+85.6K', 'With SGMA Projects', GREEN, 'GSP p.627'),
        ('20', 'GSAs in Subbasin', NAVY, 'GSP p.43'),
        ('85', 'PMAs Implemented', NAVY, 'GSP p.797'),
    ]
    for i, (val, label, color, cite) in enumerate(stats):
        cx = 0.085 + i * 0.125
        ax.text(cx, 0.145, val, ha='center', va='center',
                fontsize=18, color=color, fontweight='bold', **F)
        ax.text(cx, 0.100, label, ha='center', va='center',
                fontsize=6.5, color=MID, **F)
        ax.text(cx, 0.065, cite, ha='center', va='center',
                fontsize=5.5, color=LIGHT, style='italic', **F)

    # Footer
    ax.text(0.50, 0.010, 'All basin-level data sourced from Kern County Subbasin GSP 2025 with page citations. Farmer data is simulated user input.',
            ha='center', va='center', fontsize=6.5, color=LIGHT, style='italic', **F)

    fig.savefig('/Users/mmm/Downloads/waterxchane/act2_transfer_diagram.png',
                dpi=200, bbox_inches='tight', facecolor=BG)
    plt.close(fig)
    print("  ACT 2 saved")


# ═══════════════════════════════════════════════════════════════
#  ACT 3 — Compliance Question Engine
# ═══════════════════════════════════════════════════════════════

def generate_act3():
    fig, ax = make_fig(20, 13.5)
    line_y = draw_header(ax, 'Compliance Question Engine',
                         '12 structured questions generated from SGMA sustainability indicators')

    # ── Pipeline diagram ──
    pipe_y = line_y - 0.030
    stages = ['Policy PDFs', 'Chunk & Index', 'Generate\nQuestions', 'Assemble\nData Packets',
              'Retrieve\nPolicy Text', 'Send to\nGemini 2.0']
    stage_colors = [TEAL, BLUE, AMBER, PURPLE, RED, BRAND]
    for i, (label, color) in enumerate(zip(stages, stage_colors)):
        cx = 0.09 + i * 0.158
        draw_card(ax, cx - 0.055, pipe_y - 0.025, 0.11, 0.050, bg=BG, edge=color)
        ax.text(cx, pipe_y, label, ha='center', va='center',
                fontsize=7.5, color=color, fontweight='bold', **F, linespacing=1.2)
        if i < len(stages) - 1:
            ax.annotate('', xy=(cx + 0.065, pipe_y), xytext=(cx + 0.092, pipe_y),
                        arrowprops=dict(arrowstyle='->', color=FAINT, lw=1.2))

    # ── Table ──
    severity_colors = {'critical': RED, 'high': AMBER, 'medium': BLUE}
    severity_bg = {'critical': '#FEF2F2', 'high': '#FFFBEB', 'medium': '#EFF6FF'}
    row_h = 0.052
    start_y = line_y - 0.100

    # Column headers
    cols = [(0.045, 'ID'), (0.10, 'SEVERITY'), (0.39, 'COMPLIANCE QUESTION'),
            (0.72, 'DATA INPUTS'), (0.90, 'POLICY CATEGORIES')]
    for x, label in cols:
        ax.text(x, start_y + 0.015, label, ha='center' if x < 0.15 else 'left', va='center',
                fontsize=7, color=MID, fontweight='bold', **F)
    ax.plot([0.03, 0.97], [start_y + 0.003, start_y + 0.003], color=BORDER, lw=0.8)

    for i, q in enumerate(COMPLIANCE_QUESTIONS):
        y = start_y - i * row_h
        sc = severity_colors[q['severity']]
        sbg = severity_bg[q['severity']]

        # Alternating row background
        if i % 2 == 0:
            rect = FancyBboxPatch((0.03, y - row_h + 0.008), 0.94, row_h - 0.004,
                                  boxstyle="round,pad=0.003", facecolor=BG_LIGHT, edgecolor='none')
            ax.add_patch(rect)

        # ID
        ax.text(0.045, y - 0.008, q['id'], ha='center', va='center',
                fontsize=9, color=NAVY, fontweight='bold', **F)

        # Severity pill
        pill_w = 0.055
        pill = FancyBboxPatch((0.075, y - 0.017), pill_w, 0.018,
                              boxstyle="round,pad=0.004", facecolor=sbg, edgecolor=sc, linewidth=0.6)
        ax.add_patch(pill)
        ax.text(0.075 + pill_w/2, y - 0.008, q['severity'].upper(), ha='center', va='center',
                fontsize=5.5, color=sc, fontweight='bold', **F)

        # Question
        qtext = q['question'] if len(q['question']) <= 85 else q['question'][:82] + '...'
        ax.text(0.145, y - 0.008, qtext, ha='left', va='center',
                fontsize=7, color=DARK, **F)

        # Data fields
        fields = [f.split('.')[-1] for f in q['data_needed'][:3]]
        data_str = ', '.join(fields)
        if len(q['data_needed']) > 3:
            data_str += f'  +{len(q["data_needed"])-3}'
        ax.text(0.65, y - 0.008, data_str, ha='left', va='center',
                fontsize=5.5, color=LIGHT, family='monospace')

        # Policy categories
        cats = ', '.join(q['policy_categories'])
        ax.text(0.85, y - 0.008, cats, ha='left', va='center',
                fontsize=5.5, color=LIGHT, family='monospace')

    # ── Severity summary ──
    summary_y = 0.065
    counts = {'critical': 0, 'high': 0, 'medium': 0}
    for q in COMPLIANCE_QUESTIONS:
        counts[q['severity']] += 1

    for i, (sev, count, color, bg, desc) in enumerate([
        ('CRITICAL', counts['critical'], RED, '#FEF2F2', 'Must pass for transfer approval'),
        ('HIGH', counts['high'], AMBER, '#FFFBEB', 'Failure requires binding conditions'),
        ('MEDIUM', counts['medium'], BLUE, '#EFF6FF', 'Advisory — may require monitoring'),
    ]):
        cx = 0.17 + i * 0.33
        draw_card(ax, cx - 0.12, summary_y - 0.028, 0.24, 0.065, bg=bg, edge=color)
        ax.text(cx - 0.06, summary_y + 0.008, f'{count}', ha='center', va='center',
                fontsize=22, color=color, fontweight='bold', **F)
        ax.text(cx + 0.02, summary_y + 0.012, sev, ha='left', va='center',
                fontsize=10, color=color, fontweight='bold', **F)
        ax.text(cx + 0.02, summary_y - 0.008, desc, ha='left', va='center',
                fontsize=7, color=MID, **F)

    ax.text(0.50, 0.015, 'Each question maps to policy categories (for RAG retrieval) and farmer data fields (assembled into context packets)',
            ha='center', va='center', fontsize=7, color=LIGHT, style='italic', **F)

    fig.savefig('/Users/mmm/Downloads/waterxchane/act3_compliance_questions.png',
                dpi=200, bbox_inches='tight', facecolor=BG)
    plt.close(fig)
    print("  ACT 3 saved")


# ═══════════════════════════════════════════════════════════════
#  ACT 4 — Gemini AI Compliance Analysis
# ═══════════════════════════════════════════════════════════════

def generate_act4():
    results = [
        ("Q1",  "PASS",  "Seller surplus 630 AF; only transferring 150 AF"),
        ("Q2",  "PASS",  "Post-transfer: 1,580 AF < 1,850 AF allocation"),
        ("Q3",  "FAIL",  "North Basin GW decline -5.2 ft/yr; exceeds Minimum Threshold"),
        ("Q4",  "COND",  "Buyer subsidence 0.059 > MT 0.053 ft/yr; modeling required"),
        ("Q5",  "COND",  "Buyer nitrate 12.5 mg/L elevated; pumping may worsen quality"),
        ("Q6",  "COND",  "7 domestic wells within 1 mi of buyer at risk of interference"),
        ("Q7",  "PASS",  "All production wells metered and reporting extraction data"),
        ("Q8",  "COND",  "Critically overdrafted basin; must align with reduction MOs"),
        ("Q9",  "COND",  "Buyer 2023 over-extraction at 107%; corrective action unverified"),
        ("Q10", "PASS",  "No GDE within 1,000 ft; no interconnected surface water impacts"),
        ("Q11", "COND",  "Inter-GSA coordination agreement between GSAs not yet verified"),
        ("Q12", "COND",  "Drought/SWP allocation conditions require further analysis"),
    ]

    fig, ax = make_fig(20, 14)
    line_y = draw_header(ax, 'Gemini AI Compliance Analysis',
                         'RAG pipeline: Question + Farmer Data + Policy Text  -->  Gemini 2.0 Flash  -->  Per-Question Verdict')

    # Pipeline
    pipe_y = line_y - 0.028
    for i, (label, color, cx) in enumerate([
        ('Compliance\nQuestion', TEAL, 0.10),
        ('Farmer Data\nPacket', BLUE, 0.28),
        ('Retrieved\nPolicy Text', AMBER, 0.46),
        ('Gemini 2.0\nFlash', PURPLE, 0.64),
        ('Verdict +\nCitations', NAVY, 0.82),
    ]):
        draw_card(ax, cx - 0.060, pipe_y - 0.025, 0.12, 0.050, bg=BG, edge=color)
        ax.text(cx, pipe_y, label, ha='center', va='center',
                fontsize=7.5, color=color, fontweight='bold', **F, linespacing=1.2)
        if i < 4:
            sym = '+' if i < 2 else '-->'
            ncx = [0.10, 0.28, 0.46, 0.64, 0.82][i+1]
            mid = (cx + 0.063 + ncx - 0.063) / 2
            ax.text(mid, pipe_y, sym, ha='center', va='center',
                    fontsize=9, color=FAINT, fontweight='bold', **F)

    # Table
    finding_config = {
        'PASS': (GREEN, '#ECFDF5', '#BBF7D0'),
        'FAIL': (RED,   '#FEF2F2', '#FECACA'),
        'COND': (AMBER, '#FFFBEB', '#FDE68A'),
    }
    finding_labels = {'PASS': 'PASS', 'FAIL': 'FAIL', 'COND': 'CONDITIONAL'}

    row_h = 0.052
    start_y = line_y - 0.098

    # Headers
    for x, label in [(0.045, 'ID'), (0.10, 'SEV'), (0.38, 'QUESTION'), (0.635, 'FINDING'), (0.80, 'KEY REASONING')]:
        ax.text(x, start_y + 0.015, label, ha='center' if x < 0.15 else 'left', va='center',
                fontsize=7, color=MID, fontweight='bold', **F)
    ax.plot([0.03, 0.97], [start_y + 0.003, start_y + 0.003], color=BORDER, lw=0.8)

    severity_colors = {'critical': RED, 'high': AMBER, 'medium': BLUE}

    for i, (qid, finding, reason) in enumerate(results):
        q = COMPLIANCE_QUESTIONS[i]
        y = start_y - i * row_h
        fc, fbg, fedge = finding_config[finding]
        sc = severity_colors[q['severity']]

        # Row bg
        if finding == 'FAIL':
            rect = FancyBboxPatch((0.03, y - row_h + 0.008), 0.94, row_h - 0.004,
                                  boxstyle="round,pad=0.003", facecolor='#FEF2F2', edgecolor=RED, linewidth=0.5)
            ax.add_patch(rect)
        elif i % 2 == 0:
            rect = FancyBboxPatch((0.03, y - row_h + 0.008), 0.94, row_h - 0.004,
                                  boxstyle="round,pad=0.003", facecolor=BG_LIGHT, edgecolor='none')
            ax.add_patch(rect)

        # ID
        ax.text(0.045, y - 0.008, qid, ha='center', va='center',
                fontsize=9, color=NAVY, fontweight='bold', **F)

        # Severity dot
        dot = Circle((0.085, y - 0.008), 0.005, facecolor=sc, edgecolor='none')
        ax.add_patch(dot)

        # Question
        qtext = q['question'][:65] + '...' if len(q['question']) > 65 else q['question']
        ax.text(0.105, y - 0.008, qtext, ha='left', va='center',
                fontsize=6.5, color=DARK, **F)

        # Finding badge
        badge_text = finding_labels[finding]
        bw = 0.065 if finding != 'COND' else 0.085
        badge = FancyBboxPatch((0.605, y - 0.018), bw, 0.020,
                               boxstyle="round,pad=0.004", facecolor=fbg, edgecolor=fc, linewidth=0.8)
        ax.add_patch(badge)
        ax.text(0.605 + bw/2, y - 0.008, badge_text, ha='center', va='center',
                fontsize=6.5, color=fc, fontweight='bold', **F)

        # Reasoning
        reason_short = reason[:60] + '...' if len(reason) > 60 else reason
        ax.text(0.71, y - 0.008, reason_short, ha='left', va='center',
                fontsize=6.5, color=MID, **F)

    # Summary bar
    bar_y = 0.075
    pass_n = sum(1 for _, f, _ in results if f == 'PASS')
    cond_n = sum(1 for _, f, _ in results if f == 'COND')
    fail_n = sum(1 for _, f, _ in results if f == 'FAIL')
    total = len(results)

    bar_left, bar_w = 0.10, 0.80
    pw = (pass_n / total) * bar_w
    cw = (cond_n / total) * bar_w
    fw = (fail_n / total) * bar_w

    for x, w, color, bg, label, n in [
        (bar_left, pw, GREEN, '#ECFDF5', 'PASS', pass_n),
        (bar_left + pw, cw, AMBER, '#FFFBEB', 'CONDITIONAL', cond_n),
        (bar_left + pw + cw, fw, RED, '#FEF2F2', 'FAIL', fail_n),
    ]:
        rect = FancyBboxPatch((x + 0.002, bar_y), w - 0.004, 0.035,
                              boxstyle="round,pad=0.005", facecolor=bg, edgecolor=color, linewidth=1)
        ax.add_patch(rect)
        ax.text(x + w/2, bar_y + 0.017, f'{label}  {n}', ha='center', va='center',
                fontsize=10, color=color, fontweight='bold', **F)

    ax.text(0.50, 0.045, 'All findings cite specific GSP page numbers (p.54, p.59, p.197, p.438, p.595, p.627, p.681, p.728, p.776, p.792, p.795)',
            ha='center', va='center', fontsize=6.5, color=LIGHT, style='italic', **F)
    ax.text(0.50, 0.020, 'Gemini 2.0 Flash  |  Average response time: 3.5s per question  |  Total policy context: ~4,000 chars per question',
            ha='center', va='center', fontsize=6.5, color=LIGHT, **F)

    fig.savefig('/Users/mmm/Downloads/waterxchane/act4_gemini_analysis.png',
                dpi=200, bbox_inches='tight', facecolor=BG)
    plt.close(fig)
    print("  ACT 4 saved")


# ═══════════════════════════════════════════════════════════════
#  ACT 5 — Final Compliance Verdict
# ═══════════════════════════════════════════════════════════════

def generate_act5():
    fig, ax = make_fig(20, 14)
    line_y = draw_header(ax, 'Compliance Verdict',
                         'Transfer WXT-2026-0042  |  John Martinez  -->  Sarah Chen  |  150 AF @ $415/AF  |  $62,250')

    # ── VERDICT BANNER ──
    banner_y = line_y - 0.075
    draw_card(ax, 0.10, banner_y, 0.80, 0.060, bg='#FFFBEB', edge=AMBER)
    ax.text(0.50, banner_y + 0.038, 'CONDITIONALLY  APPROVED', ha='center', va='center',
            fontsize=24, color=AMBER, fontweight='bold', **F)

    # ── Risk gauge ──
    gauge_y = banner_y - 0.005
    ax.text(0.22, gauge_y, 'Risk Score', ha='right', va='center',
            fontsize=8, color=MID, **F)
    for j in range(10):
        seg_x = 0.24 + j * 0.048
        if j < 3:
            seg_c = GREEN
        elif j < 6:
            seg_c = AMBER
        else:
            seg_c = RED
        filled = j < 7
        bg = seg_c if filled else '#F0F2F8'
        alpha = 0.7 if filled else 0.3
        rect = FancyBboxPatch((seg_x, gauge_y - 0.008), 0.044, 0.016,
                              boxstyle="round,pad=0.003",
                              facecolor=bg, edgecolor=seg_c if filled else BORDER,
                              alpha=alpha, linewidth=0.5)
        ax.add_patch(rect)
    ax.text(0.73, gauge_y, '7 / 10', ha='left', va='center',
            fontsize=12, color=AMBER, fontweight='bold', **F)

    # ── SCORECARD (left) ──
    sc_x, sc_y, sc_w, sc_h = 0.03, 0.31, 0.20, 0.48
    draw_card(ax, sc_x, sc_y, sc_w, sc_h)
    draw_section_title(ax, sc_x + 0.012, sc_y + sc_h - 0.015, 'Scorecard', NAVY)

    scorecard = [
        ('Q1',  'Seller surplus',     'PASS'),
        ('Q2',  'Allocation check',   'PASS'),
        ('Q3',  'GW levels / MT',     'FAIL'),
        ('Q4',  'Subsidence risk',    'COND'),
        ('Q5',  'Water quality',      'COND'),
        ('Q6',  'Well interference',  'COND'),
        ('Q7',  'Well metering',      'PASS'),
        ('Q8',  'Overdraft timeline', 'COND'),
        ('Q9',  'Buyer history',      'COND'),
        ('Q10', 'GDE impacts',        'PASS'),
        ('Q11', 'GSA coordination',   'COND'),
        ('Q12', 'Drought / SWP',      'COND'),
    ]
    fc_map = {'PASS': GREEN, 'FAIL': RED, 'COND': AMBER}
    for i, (qid, label, finding) in enumerate(scorecard):
        sy_ = sc_y + sc_h - 0.060 - i * 0.033
        fc = fc_map[finding]
        dot = Circle((sc_x + 0.015, sy_), 0.004, facecolor=fc, edgecolor='none')
        ax.add_patch(dot)
        ax.text(sc_x + 0.025, sy_, qid, ha='left', va='center', fontsize=7, color=MID, **F)
        ax.text(sc_x + 0.055, sy_, label, ha='left', va='center', fontsize=7, color=DARK, **F)
        ax.text(sc_x + sc_w - 0.012, sy_, finding, ha='right', va='center',
                fontsize=7, color=fc, fontweight='bold', **F)

    # ── CONDITIONS (center) ──
    cd_x, cd_y, cd_w, cd_h = 0.245, 0.31, 0.37, 0.48
    draw_card(ax, cd_x, cd_y, cd_w, cd_h, bg='#FFFBEB', edge=AMBER)
    draw_section_title(ax, cd_x + 0.012, cd_y + cd_h - 0.015, '7 Conditions for Approval', AMBER)

    conditions = [
        ('Q3:', 'Submit mitigation plan to prevent GW levels from declining\nbelow Minimum Threshold at buyer location'),
        ('Q4:', 'Provide subsidence impact modeling demonstrating no\nworsening in North Basin HCM area'),
        ('Q5:', 'Implement water quality monitoring program for arsenic,\nnitrate, and TDS near buyer wells'),
        ('Q6:', 'Conduct well interference study for 7 domestic wells\nwithin 1-mile radius of buyer'),
        ('Q8:', 'Demonstrate alignment with basin overdraft reduction\nMeasurable Objectives'),
        ('Q9:', 'GSA verification that buyer corrective action plan is\neffective and extraction is compliant'),
        ('Q11:', 'Provide documentation of active inter-GSA coordination\nagreement (Rosedale <-> Semitropic)'),
    ]
    for i, (qid, text) in enumerate(conditions):
        cy = cd_y + cd_h - 0.060 - i * 0.060
        # Number
        circle = Circle((cd_x + 0.020, cy + 0.006), 0.009,
                        facecolor='none', edgecolor=AMBER, linewidth=1)
        ax.add_patch(circle)
        ax.text(cd_x + 0.020, cy + 0.006, str(i+1), ha='center', va='center',
                fontsize=6.5, color=AMBER, fontweight='bold', **F)
        ax.text(cd_x + 0.038, cy + 0.006, qid, ha='left', va='center',
                fontsize=7, color=AMBER, fontweight='bold', **F)
        ax.text(cd_x + 0.065, cy + 0.006, text, ha='left', va='center',
                fontsize=6.5, color=DARK, **F, linespacing=1.3)

    # ── MONITORING (right top) ──
    mn_x, mn_y, mn_w, mn_h = 0.63, 0.54, 0.34, 0.25
    draw_card(ax, mn_x, mn_y, mn_w, mn_h, bg='#EFF6FF', edge=BLUE)
    draw_section_title(ax, mn_x + 0.012, mn_y + mn_h - 0.015, '5 Monitoring Mandates', BLUE)

    monitoring = [
        ('Groundwater Levels', 'Quarterly at buyer wells'),
        ('Subsidence', 'Annual InSAR — North Basin HCM'),
        ('Water Quality', 'Semi-annual As/NO3/TDS testing'),
        ('Extraction Data', 'Monthly meter reads + GSA report'),
        ('Domestic Wells', 'Annual check of 7 nearby wells'),
    ]
    for i, (title, desc) in enumerate(monitoring):
        my = mn_y + mn_h - 0.058 - i * 0.036
        dot = Circle((mn_x + 0.015, my), 0.004, facecolor=BLUE, edgecolor='none')
        ax.add_patch(dot)
        ax.text(mn_x + 0.028, my, title, ha='left', va='center',
                fontsize=7.5, color=NAVY, fontweight='bold', **F)
        ax.text(mn_x + mn_w - 0.012, my, desc, ha='right', va='center',
                fontsize=7, color=MID, **F)

    # ── POLICY BASIS (right bottom) ──
    pb_x, pb_y, pb_w, pb_h = 0.63, 0.31, 0.34, 0.215
    draw_card(ax, pb_x, pb_y, pb_w, pb_h, bg='#ECFDF5', edge=TEAL)
    draw_section_title(ax, pb_x + 0.012, pb_y + pb_h - 0.015, 'Policy Basis', TEAL)

    policies = [
        ('SGMA Statute', 'CA Water Code 10720 et seq.'),
        ('GSP p.595', 'Sustainable Yield = 1,312,218 AFY'),
        ('GSP p.681', 'HCM subsidence & GW level MTs'),
        ('GSP p.54', 'Storage change = -274,200 AFY'),
        ('GSP p.776', '2030 deficit = 372,120 AFY'),
        ('GSP p.793', 'MT exceedance response (App K-1)'),
    ]
    for i, (source, desc) in enumerate(policies):
        py_ = pb_y + pb_h - 0.055 - i * 0.028
        ax.text(pb_x + 0.012, py_, source, ha='left', va='center',
                fontsize=7, color=TEAL, fontweight='bold', **F)
        ax.text(pb_x + 0.09, py_, desc, ha='left', va='center',
                fontsize=7, color=DARK, **F)

    # ── RISK FACTORS (bottom) ──
    rf_y, rf_h = 0.065, 0.225
    draw_card(ax, 0.03, rf_y, 0.94, rf_h, bg='#FEF2F2', edge='#FECACA')
    draw_section_title(ax, 0.045, rf_y + rf_h - 0.015, 'Key Risk Factors', RED)

    risks = [
        (RED,   'Q3 FAIL', 'Buyer North Basin GW decline rate of -5.2 ft/yr will push levels below Minimum Threshold with additional extraction'),
        (RED,   'Subsidence', 'Buyer area subsidence at 0.059 ft/yr EXCEEDS the rate MT of 0.053 ft/yr — risk of infrastructure damage [GSP p.681]'),
        (AMBER, 'Overdraft', 'Basin shows -274,200 AFY storage deficit with projected 372,120 AFY gap by 2030 under climate change scenario'),
        (AMBER, 'Buyer History', '2023 over-extraction at 107% of allocation; buyer currently at 111% — corrective action plan filed but unverified'),
        (AMBER, 'Domestic Wells', '7 domestic wells within 1 mile of buyer — SGMA requires rural community protection (CWC 10720.3)'),
        (BLUE,  'Inter-GSA', 'Transfer crosses Rosedale-Rio Bravo <-> Semitropic GSA boundary; coordination agreement not yet verified'),
    ]
    col_w = 0.46
    for i, (color, title, desc) in enumerate(risks):
        col = 0 if i < 3 else 1
        row = i if i < 3 else i - 3
        rx = 0.045 + col * col_w
        ry = rf_y + rf_h - 0.055 - row * 0.060
        dot = Circle((rx, ry + 0.006), 0.004, facecolor=color, edgecolor='none')
        ax.add_patch(dot)
        ax.text(rx + 0.012, ry + 0.006, title, ha='left', va='center',
                fontsize=7.5, color=color, fontweight='bold', **F)
        ax.text(rx + 0.012, ry - 0.014, desc, ha='left', va='center',
                fontsize=6, color=MID, **F)

    # Architecture footer
    ax.text(0.50, 0.040, 'PDF Ingestion  -->  Chunking  -->  Category Index  -->  12 Questions  -->  RAG Retrieval  -->  Gemini 2.0  -->  Per-Q Verdict  -->  Final Decision',
            ha='center', va='center', fontsize=7, color=LIGHT, **F)
    ax.text(0.50, 0.015, 'All policy data from Kern County Subbasin GSP 2025 with page citations.  Farmer data is simulated user input.  Basin data verified against GSP.',
            ha='center', va='center', fontsize=6.5, color=LIGHT, style='italic', **F)

    fig.savefig('/Users/mmm/Downloads/waterxchane/act5_final_verdict.png',
                dpi=200, bbox_inches='tight', facecolor=BG)
    plt.close(fig)
    print("  ACT 5 saved")


# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("\n  WaterXchange — Generating professional report visuals...\n")
    generate_act2()
    generate_act3()
    generate_act4()
    generate_act5()
    print(f"\n  Done! Files in /Users/mmm/Downloads/waterxchane/\n")
