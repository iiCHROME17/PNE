"""
PNE Pipeline Flowchart
Generates: pne_pipeline_flowchart.png
Shows the full per-turn processing pipeline from player input to NPC response.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(10, 18))
ax.set_xlim(0, 10)
ax.set_ylim(0, 18)
ax.axis('off')

# ── Colour palette ──────────────────────────────────────────────────────────
C_PLAYER   = '#4A90D9'   # blue  – player-side
C_GATE     = '#E07B39'   # orange – gate/check
C_BDI      = '#5B9B6A'   # green  – BDI pipeline stages
C_LLM      = '#9B59B6'   # purple – LLM generation
C_FSM      = '#C0392B'   # red    – FSM / narrative routing
C_OUTPUT   = '#2C3E50'   # dark   – output
C_BDI_BOX  = '#EAF5EC'   # light green – BDI container background
C_TEXT     = 'white'
C_DARK_TXT = '#2C3E50'

def box(ax, x, y, w, h, label, sublabel=None, color=C_BDI, text_color=C_TEXT, fontsize=10):
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle="round,pad=0.08", linewidth=1.5,
                          edgecolor='#333333', facecolor=color, zorder=3)
    ax.add_patch(rect)
    if sublabel:
        ax.text(x, y + 0.13, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color=text_color, zorder=4)
        ax.text(x, y - 0.22, sublabel, ha='center', va='center',
                fontsize=7.5, color=text_color, style='italic', zorder=4)
    else:
        ax.text(x, y, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color=text_color, zorder=4)

def arrow(ax, x, y_start, y_end, color='#555555'):
    ax.annotate('', xy=(x, y_end + 0.02),
                xytext=(x, y_start - 0.02),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=1.8, mutation_scale=16),
                zorder=5)

def side_arrow(ax, x_start, x_end, y, label='', color='#E07B39'):
    ax.annotate('', xy=(x_end, y),
                xytext=(x_start, y),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=1.6, mutation_scale=14),
                zorder=5)
    if label:
        mx = (x_start + x_end) / 2
        ax.text(mx, y + 0.15, label, ha='center', fontsize=7.5,
                color=color, fontweight='bold', zorder=6)

# ── BDI container background ────────────────────────────────────────────────
bdi_top    = 11.8
bdi_bottom = 7.2
bdi_rect = FancyBboxPatch((1.2, bdi_bottom), 7.6, bdi_top - bdi_bottom,
                           boxstyle="round,pad=0.15", linewidth=2,
                           edgecolor='#5B9B6A', facecolor=C_BDI_BOX,
                           linestyle='--', zorder=1)
ax.add_patch(bdi_rect)
ax.text(5, bdi_top - 0.28, 'BDI PIPELINE',
        ha='center', fontsize=9, fontweight='bold',
        color='#5B9B6A', zorder=2)

# ── Nodes (top → bottom) ────────────────────────────────────────────────────
# 1. Player dialogue choice
box(ax, 5, 17.0, 5.5, 0.75,
    'Player Selects Dialogue Choice',
    'JSON: spoken text · tone weights · skill requirements',
    color=C_PLAYER, fontsize=9.5)

arrow(ax, 5, 16.62, 16.12)

# 2. Hard gate check
box(ax, 5, 15.75, 5.5, 0.65,
    'Hard Gate Check',
    'Player skill / relationship threshold evaluation',
    color=C_GATE, fontsize=9.5)

# Gate fail branch
side_arrow(ax, 7.75, 9.2, 15.75, color='#E07B39')
block_rect = FancyBboxPatch((9.2, 15.42), 0.72, 0.66,
                             boxstyle="round,pad=0.06", linewidth=1.2,
                             edgecolor='#E07B39', facecolor='#FDEBD0', zorder=3)
ax.add_patch(block_rect)
ax.text(9.56, 15.75, 'BLOCKED\n(hidden)', ha='center', va='center',
        fontsize=7, color='#A04000', fontweight='bold', zorder=4)

ax.text(8.48, 15.95, 'FAIL', fontsize=7.5, color='#E07B39',
        fontweight='bold', ha='center', zorder=6)

arrow(ax, 5, 15.42, 14.92)

# 3. Skill-check dice roll
box(ax, 5, 14.55, 5.5, 0.65,
    'Skill-Check Dice Roll  (2d20)',
    'P(success) = f(player skill, NPC personality, relationship, difficulty)',
    color=C_GATE, fontsize=9.5)

# Success / Fail labels
ax.text(4.3, 14.18, 'SUCCESS', fontsize=7.5, color='#27AE60',
        fontweight='bold', ha='center', zorder=6)
ax.text(5.7, 14.18, 'FAIL', fontsize=7.5, color='#C0392B',
        fontweight='bold', ha='center', zorder=6)

arrow(ax, 5, 14.22, 13.62)

# 4. Outcome tag
box(ax, 5, 13.25, 5.0, 0.65,
    'Outcome Tagged  →  SUCCESS | FAIL',
    'Modifies downstream belief weight and desire intensity',
    color=C_GATE, fontsize=9.5)

arrow(ax, 5, 12.92, 12.15)

# ── BDI stages ──────────────────────────────────────────────────────────────
# 4a. Cognitive layer
box(ax, 5, 11.7, 6.4, 0.72,
    'COGNITIVE LAYER',
    'Template-matched thought pattern → NPC belief update (schema-driven)',
    color=C_BDI, fontsize=9.5)

arrow(ax, 5, 11.34, 10.84)

# 4b. Desire layer
box(ax, 5, 10.5, 6.4, 0.65,
    'DESIRE LAYER',
    'Belief → goal state  (information · affiliation · protection · dominance)',
    color=C_BDI, fontsize=9.5)

arrow(ax, 5, 10.17, 9.67)

# 4c. Social layer
box(ax, 5, 9.3, 6.4, 0.65,
    'SOCIAL LAYER',
    'Desire → intention  (select from 19 canonical behavioural intentions)',
    color=C_BDI, fontsize=9.5)

arrow(ax, 5, 8.97, 8.47)

# 4d. Outcome layer
box(ax, 5, 8.1, 6.4, 0.65,
    'OUTCOME LAYER',
    'Apply state Δ:  stance · player_relation · judgement score (+/−)',
    color=C_BDI, fontsize=9.5)

arrow(ax, 5, 7.77, 7.07)

# 5. LLM text generation
box(ax, 5, 6.7, 5.5, 0.65,
    'LLM Text Generation  (Qwen2.5:3b via Ollama)',
    'Prompt = NPC identity + BDI state + intention + scene direction',
    color=C_LLM, fontsize=9.5)

arrow(ax, 5, 6.37, 5.87)

# 6. FSM evaluation
box(ax, 5, 5.5, 5.5, 0.65,
    'FSM Evaluation',
    'Judgement score + intention → narrative state transition',
    color=C_FSM, fontsize=9.5)

arrow(ax, 5, 5.17, 4.67)

# 7. NPC spoken response
box(ax, 5, 4.3, 5.5, 0.65,
    'NPC Spoken Response  →  Next Scenario Node',
    'WebSocket token stream to game engine client',
    color=C_OUTPUT, fontsize=9.5)

# ── Recovery mechanic note ───────────────────────────────────────────────────
ax.annotate('', xy=(3.1, 13.25),
            xytext=(3.1, 8.1),
            arrowprops=dict(arrowstyle='->', color='#999999',
                            lw=1.2, mutation_scale=12,
                            connectionstyle='arc3,rad=-0.4'),
            zorder=5)
ax.text(1.2, 10.65, 'Recovery\nmechanic\n(FAIL path\ndoes not\nbreak\nnarrative)',
        ha='center', va='center', fontsize=7, color='#777777',
        style='italic', zorder=6)

# ── Title ────────────────────────────────────────────────────────────────────
ax.text(5, 17.75, 'PNE — Per-Turn Processing Pipeline',
        ha='center', va='center', fontsize=13, fontweight='bold',
        color=C_DARK_TXT, zorder=6)

plt.tight_layout(pad=0.4)
plt.savefig('d:/Programming/PNE (Github)/cs3ip/Dissertation/Literature Material/Graphs/pne_pipeline_flowchart.png',
            dpi=180, bbox_inches='tight', facecolor='white')
print('Saved: pne_pipeline_flowchart.png')
plt.close()
