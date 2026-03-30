"""
BDI Classical vs PNE Comparison Diagram
Generates: bdi_comparison.png
Shows how PNE relates to and diverges from classical BDI architecture.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(14, 9))
ax.set_xlim(0, 14)
ax.set_ylim(0, 9)
ax.axis('off')

# ── Colours ──────────────────────────────────────────────────────────────────
C_CLASSIC   = '#4A90D9'
C_PNE       = '#5B9B6A'
C_SHARED    = '#E07B39'
C_DIVERGE   = '#C0392B'
C_HEADER_BG = '#2C3E50'
C_LIGHT     = '#F8F9FA'
C_TEXT_D    = '#2C3E50'

def panel(ax, x, y, w, h, color, alpha=0.08):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.12", linewidth=2,
                          edgecolor=color, facecolor=color, alpha=alpha, zorder=1)
    ax.add_patch(rect)

def row_box(ax, x, y, w, h, label, sublabel=None, color='#4A90D9',
            text_color='white', fontsize=9.5, alpha=1.0):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.07", linewidth=1.4,
                          edgecolor='#333333', facecolor=color,
                          alpha=alpha, zorder=3)
    ax.add_patch(rect)
    cx = x + w / 2
    cy = y + h / 2
    if sublabel:
        ax.text(cx, cy + 0.13, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color=text_color, zorder=4)
        ax.text(cx, cy - 0.2, sublabel, ha='center', va='center',
                fontsize=7.2, color=text_color, style='italic', zorder=4)
    else:
        ax.text(cx, cy, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color=text_color, zorder=4)

def divider_label(ax, x, y, label, color='#888888'):
    ax.text(x, y, label, ha='center', va='center',
            fontsize=8, color=color, style='italic', zorder=5)

# ── Column panels ─────────────────────────────────────────────────────────────
panel(ax, 0.3, 0.4, 5.8, 8.2, C_CLASSIC, alpha=0.06)
panel(ax, 7.9, 0.4, 5.8, 8.2, C_PNE,     alpha=0.06)

# ── Column headers ────────────────────────────────────────────────────────────
row_box(ax, 0.3, 8.1, 5.8, 0.7, 'Classical BDI',
        'Rao & Georgeff (1995)  ·  Wooldridge (2000)  ·  Jason / AgentSpeak (2007)',
        color=C_CLASSIC, fontsize=11)

row_box(ax, 7.9, 8.1, 5.8, 0.7, 'PNE BDI (this project)',
        'Domain-constrained variant  ·  NPC dialogue  ·  Real-time game context',
        color=C_PNE, fontsize=11)

# ── Centre column label ───────────────────────────────────────────────────────
ax.text(7.0, 8.45, 'vs', ha='center', va='center',
        fontsize=16, fontweight='bold', color='#AAAAAA', zorder=5)

# ── Row data: (label, classic_sub, pne_sub, diverge) ─────────────────────────
rows = [
    # (aspect, classic description, PNE description, diverges?)
    ('Theoretical\nBasis',
     'Bratman (1987) intentionality\nModal logic formalisation',
     'Bratman (1987) intentionality\nHeuristic / schema-driven',
     False),

    ('Belief\nRepresentation',
     'Formal belief sets\nModal operator semantics',
     'NPC personality JSON config\nTemplate-matched schema activation',
     True),

    ('Cognitive\nReasoning',
     'Logic inference over belief base\nFull plan search',
     '810 thought-pattern templates\nWeighted heuristic selection',
     True),

    ('Intention\nSpace',
     'Unbounded plan library\n(AgentSpeak plan files)',
     '19 canonical behavioural intentions\n(closed vocabulary registry)',
     True),

    ('Commitment\nStrategy',
     'Blind / single-minded / open-minded\n(configurable)',
     'Open-minded commitment\nDesire recalculated each turn',
     False),

    ('Text\nGeneration',
     'Not addressed — output is\nagent action, not natural language',
     'LLM (Qwen2.5:3b via Ollama)\nConstrained by selected intention',
     True),

    ('Scalability\nApproach',
     'General-purpose reasoner\nFrame problem grows with world model',
     'Constrained world model\nTractability via deliberate limitation',
     True),

    ('Deployment\nContext',
     'Robots, logistics, simulation\nServer-class or unlimited compute',
     'Consumer NPC dialogue\n~2 GB VRAM, offline-capable',
     True),
]

y_start = 7.6
row_h   = 0.72
gap     = 0.08

for i, (aspect, classic, pne, diverges) in enumerate(rows):
    y = y_start - i * (row_h + gap)
    mid_y = y - row_h / 2

    # Aspect label (centre column)
    ax.text(7.0, y - row_h / 2, aspect,
            ha='center', va='center', fontsize=8.5,
            fontweight='bold', color=C_TEXT_D, zorder=5)

    # Divergence indicator
    ind_color = C_DIVERGE if diverges else C_SHARED
    ind_label = '≠' if diverges else '≈'
    ax.text(7.0, y - row_h / 2 + 0.26, ind_label,
            ha='center', va='center', fontsize=13,
            color=ind_color, fontweight='bold', zorder=5)

    # Classic box
    b_color = '#EBF4FB' if not diverges else '#FDFEFE'
    row_box(ax, 0.5, y - row_h, 5.2, row_h - 0.04,
            classic, color=b_color, text_color=C_TEXT_D,
            fontsize=8.2, alpha=1.0)

    # PNE box
    p_color = '#EAF5EC' if not diverges else '#FDFEFE'
    row_box(ax, 8.1, y - row_h, 5.2, row_h - 0.04,
            pne, color=p_color, text_color=C_TEXT_D,
            fontsize=8.2, alpha=1.0)

# ── Legend ────────────────────────────────────────────────────────────────────
legend_y = 0.62
ax.add_patch(FancyBboxPatch((0.3, 0.3), 13.4, 0.52,
             boxstyle="round,pad=0.06", linewidth=1,
             edgecolor='#CCCCCC', facecolor='#F8F9FA', zorder=2))

ax.text(0.65, legend_y, '≈  Shared design principle',
        fontsize=8, color=C_SHARED, fontweight='bold', va='center', zorder=5)
ax.text(4.2, legend_y, '≠  PNE diverges from classical BDI',
        fontsize=8, color=C_DIVERGE, fontweight='bold', va='center', zorder=5)
ax.text(8.8, legend_y,
        'PNE is a domain-constrained BDI variant — formal correctness traded for real-time tractability',
        fontsize=7.8, color='#666666', style='italic', va='center', zorder=5)

# ── Title ─────────────────────────────────────────────────────────────────────
ax.text(7.0, 9.05, 'Classical BDI Architecture vs PNE Implementation',
        ha='center', va='center', fontsize=13.5, fontweight='bold',
        color=C_TEXT_D, zorder=6)

plt.tight_layout(pad=0.3)
plt.savefig('d:/Programming/PNE (Github)/cs3ip/Dissertation/Literature Material/Graphs/bdi_comparison.png',
            dpi=180, bbox_inches='tight', facecolor='white')
print('Saved: bdi_comparison.png')
plt.close()
