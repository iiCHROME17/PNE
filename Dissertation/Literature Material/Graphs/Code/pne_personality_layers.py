"""
PNE Three-Layer NPC Personality Model
Generates: pne_personality_layers.png
Shows the three personality layers and their mapping to BDI components.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

fig, ax = plt.subplots(figsize=(12, 8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 8)
ax.axis('off')

C_COG    = '#4A90D9'
C_SOC    = '#5B9B6A'
C_WORLD  = '#E07B39'
C_BDI_B  = '#2980B9'
C_BDI_D  = '#27AE60'
C_BDI_I  = '#8E44AD'
C_DARK   = '#2C3E50'
C_LIGHT  = '#ECF0F1'

def rounded_box(ax, x, y, w, h, label, sublabel=None, color='#4A90D9',
                text_color='white', fontsize=10, zorder=3):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.1", linewidth=1.8,
                          edgecolor='#333333', facecolor=color, zorder=zorder)
    ax.add_patch(rect)
    cx, cy = x + w/2, y + h/2
    if sublabel:
        ax.text(cx, cy + 0.15, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color=text_color, zorder=zorder+1)
        ax.text(cx, cy - 0.22, sublabel, ha='center', va='center',
                fontsize=7.5, color=text_color, style='italic', zorder=zorder+1)
    else:
        ax.text(cx, cy, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color=text_color, zorder=zorder+1)

# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(6, 7.7, 'PNE — Three-Layer NPC Personality Model & BDI Mapping',
        ha='center', va='center', fontsize=13, fontweight='bold', color=C_DARK)

# ─────────────────────────────────────────────────────────────────────────────
# LEFT SIDE: Three personality layers
# ─────────────────────────────────────────────────────────────────────────────
ax.text(2.5, 7.1, 'NPC Personality Layers', ha='center', fontsize=10.5,
        fontweight='bold', color=C_DARK)

layer_data = [
    # (y, color, title, params)
    (5.7, C_COG,   'COGNITIVE LAYER',
     'self_esteem  ·  locus_of_control  ·  cog_flexibility\ncognitive_bias_type  ·  emotional_reactivity'),
    (3.7, C_SOC,   'SOCIAL LAYER',
     'assertiveness  ·  empathy  ·  conf_indep\nfaction  ·  confrontation_level'),
    (1.7, C_WORLD, 'WORLD KNOWLEDGE LAYER',
     'relationship awareness  ·  environmental context\nscenario-specific beliefs'),
]

for (y, color, title, params) in layer_data:
    rounded_box(ax, 0.3, y, 4.4, 1.55, title, params, color=color, fontsize=9.5)

# Arrows between layers (left side)
for y_tip in [5.7, 3.7]:
    ax.annotate('', xy=(2.5, y_tip - 0.05),
                xytext=(2.5, y_tip + 1.55 + 0.05),
                arrowprops=dict(arrowstyle='->', color='#888888',
                                lw=1.5, mutation_scale=14), zorder=5)

# ─────────────────────────────────────────────────────────────────────────────
# RIGHT SIDE: BDI pipeline stages
# ─────────────────────────────────────────────────────────────────────────────
ax.text(9.5, 7.1, 'BDI Pipeline Stages', ha='center', fontsize=10.5,
        fontweight='bold', color=C_DARK)

bdi_stages = [
    (6.3, C_BDI_B, 'BELIEF UPDATE',
     'Cognitive layer templates\nactivate schema → thought'),
    (4.6, C_BDI_D, 'DESIRE FORMATION',
     'Belief → goal state\n(information / affiliation /\nprotection / dominance)'),
    (2.9, C_BDI_I, 'INTENTION SELECTION',
     'Desire → 1 of 19 canonical\nbehavioural intentions'),
    (1.2, C_DARK,  'OUTCOME APPLICATION',
     'State Δ: stance · relation\njudgement score update'),
]

for (y, color, title, desc) in bdi_stages:
    rounded_box(ax, 7.3, y, 4.4, 1.3, title, desc, color=color, fontsize=9)

# Arrows between BDI stages
for y_tip in [6.3, 4.6, 2.9]:
    ax.annotate('', xy=(9.5, y_tip - 0.08),
                xytext=(9.5, y_tip + 1.3 + 0.08),
                arrowprops=dict(arrowstyle='->', color='#888888',
                                lw=1.5, mutation_scale=14), zorder=5)

# ─────────────────────────────────────────────────────────────────────────────
# CENTRE: Mapping arrows
# ─────────────────────────────────────────────────────────────────────────────
ax.text(6.0, 7.1, 'maps to', ha='center', fontsize=8.5,
        color='#888888', style='italic')

mappings = [
    # (left_y_centre, right_y_centre, label)
    (5.7 + 0.775, 6.3 + 0.65,   'Cognitive layer\n→ Belief'),
    (3.7 + 0.775, 4.6 + 0.65,   'Social layer\n→ Desire / Intention'),
    (1.7 + 0.775, 1.2 + 0.65,   'World knowledge\n→ Outcome context'),
]

for (ly, ry, label) in mappings:
    ax.annotate('', xy=(7.3, ry),
                xytext=(4.7, ly),
                arrowprops=dict(arrowstyle='->', color='#AAAAAA',
                                lw=1.4, mutation_scale=13,
                                connectionstyle='arc3,rad=0.0'),
                zorder=4)
    mx = 6.0
    my = (ly + ry) / 2
    ax.text(mx, my, label, ha='center', va='center',
            fontsize=7, color='#777777', style='italic',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                      edgecolor='#CCCCCC', linewidth=0.8),
            zorder=6)

plt.tight_layout(pad=0.3)
plt.savefig('d:/Programming/PNE (Github)/cs3ip/Dissertation/Literature Material/Graphs/pne_personality_layers.png',
            dpi=180, bbox_inches='tight', facecolor='white')
print('Saved: pne_personality_layers.png')
plt.close()
