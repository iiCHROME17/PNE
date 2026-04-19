import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')

# ── Colour palette ──────────────────────────────────────────────────────────
C_NPC    = '#1a3a5c'   # dark blue  – NPC personality
C_PLAYER = '#2e7d32'   # dark green – player input / skill check
C_BDI    = '#1565c0'   # mid blue   – BDI stages
C_LLM    = '#6a1b9a'   # purple     – LLM output
C_TERM   = '#b71c1c'   # red        – terminal
C_ARROW  = '#444444'
WHITE    = 'white'

def box(ax, x, y, w, h, label, sublabel='', color=C_BDI, fontsize=11):
    rect = FancyBboxPatch((x, y), w, h,
                          boxstyle="round,pad=0.08",
                          facecolor=color, edgecolor='white',
                          linewidth=1.5, zorder=3)
    ax.add_patch(rect)
    cy = y + h / 2
    if sublabel:
        ax.text(x + w/2, cy + 0.13, label, ha='center', va='center',
                color=WHITE, fontsize=fontsize, fontweight='bold', zorder=4)
        ax.text(x + w/2, cy - 0.22, sublabel, ha='center', va='center',
                color='#ddddff', fontsize=8.5, style='italic', zorder=4)
    else:
        ax.text(x + w/2, cy, label, ha='center', va='center',
                color=WHITE, fontsize=fontsize, fontweight='bold', zorder=4)

def arrow(ax, x1, y1, x2, y2, label='', color=C_ARROW):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.8), zorder=5)
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx + 0.08, my, label, ha='left', va='center',
                color=color, fontsize=8, style='italic')

def side_arrow(ax, x1, y1, x2, y2, label='', color=C_ARROW):
    """Horizontal then vertical arrow (elbow)."""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5,
                                connectionstyle='arc3,rad=0.0'), zorder=5)
    if label:
        ax.text((x1+x2)/2, (y1+y2)/2 + 0.12, label, ha='center', va='bottom',
                color=color, fontsize=8, style='italic')

# ── Title ────────────────────────────────────────────────────────────────────
ax.text(7, 9.6, 'PNE Pipeline — Per Turn', ha='center', va='center',
        fontsize=15, fontweight='bold', color='#1a1a2e')

# ── NPC Personality Model (left sidebar) ─────────────────────────────────────
box(ax, 0.3, 4.8, 2.2, 3.8,
    'NPC Personality\nModel', color=C_NPC, fontsize=10)
# sub-labels inside
for i, (lbl, sub) in enumerate([
    ('Cognitive', 'Self-esteem · Locus · Flexibility'),
    ('Social',    'Assertion · Empathy · Ideology'),
    ('World',     'History · Relation · Events'),
]):
    yy = 4.85 + i * 1.2
    ax.text(1.4, yy + 0.75, lbl, ha='center', va='center',
            color='#aac4e8', fontsize=8.5, fontweight='bold', zorder=4)
    ax.text(1.4, yy + 0.38, sub, ha='center', va='center',
            color='#cccccc', fontsize=7.2, zorder=4)
    if i < 2:
        ax.plot([0.45, 2.35], [yy + 1.15, yy + 1.15],
                color='#2a5080', lw=0.7, zorder=4)

# Bracket arrow from NPC model to pipeline
ax.annotate('', xy=(3.6, 6.65), xytext=(2.5, 6.65),
            arrowprops=dict(arrowstyle='->', color='#5599cc', lw=1.5,
                            linestyle='dashed'), zorder=5)
ax.text(3.0, 6.85, 'informs\nall stages', ha='center', va='bottom',
        color='#5599cc', fontsize=7.5, style='italic')

# ── Main pipeline (centre column) ────────────────────────────────────────────
BOX_X = 3.6
BOX_W = 4.2
GAP   = 1.3

stages = [
    # (y,    label,                   sublabel,                         color)
    (7.9,  'Player Input',           'LanguageArt · Tone signals',      C_PLAYER),
    (6.5,  'Skill Check  (2-Dice)',  'Player d6 vs NPC d6 → Success / Fail', C_PLAYER),
    (5.2,  'Belief',                 'CognitiveThoughtMatcher → internal thought', C_BDI),
    (3.9,  'Desire',                 'Desire Formation → goal + intensity', C_BDI),
    (2.6,  'Intention',              'Socialisation Filter → BehaviouralIntention', C_BDI),
    (1.3,  'LLM Output',             'Ollama prompt (BDI state + dice result) → NPC line', C_LLM),
]

BOX_H = 0.95
for (y, lbl, sub, col) in stages:
    box(ax, BOX_X, y, BOX_W, BOX_H, lbl, sub, color=col)

# Arrows between stages
for i in range(len(stages) - 1):
    y_from = stages[i][0]       # top of next is stages[i][0]
    y_to   = stages[i+1][0] + BOX_H
    arrow(ax, BOX_X + BOX_W/2, y_from,
              BOX_X + BOX_W/2, y_to + 0.01)

# ── Terminal check (right of LLM output) ─────────────────────────────────────
# Diamond shape via a rotated square
diamond_cx, diamond_cy = 10.5, 1.78
d = 0.6
diamond = plt.Polygon(
    [[diamond_cx, diamond_cy + d],
     [diamond_cx + d*1.5, diamond_cy],
     [diamond_cx, diamond_cy - d],
     [diamond_cx - d*1.5, diamond_cy]],
    closed=True, facecolor=C_TERM, edgecolor='white', lw=1.5, zorder=3)
ax.add_patch(diamond)
ax.text(diamond_cx, diamond_cy, 'Terminal?', ha='center', va='center',
        color=WHITE, fontsize=9, fontweight='bold', zorder=4)

# Arrow: LLM → Terminal check
arrow(ax, BOX_X + BOX_W, 1.78, diamond_cx - d*1.5, diamond_cy)

# YES → Outcome box
box(ax, 11.3, 2.7, 2.4, 1.0,
    'Outcome', 'Door opens · Quest unlocks\nConflict begins · Turned away',
    color=C_TERM, fontsize=9)
arrow(ax, diamond_cx, diamond_cy + d, 12.5, 2.7, label='YES', color=C_TERM)

# NO → loop back label
ax.annotate('', xy=(BOX_X + BOX_W/2, stages[0][0] + BOX_H),
            xytext=(diamond_cx, diamond_cy - d),
            arrowprops=dict(arrowstyle='->', color='#888888', lw=1.4,
                            connectionstyle='arc3,rad=-0.35'), zorder=5)
ax.text(10.1, 4.2, 'NO\n(next turn)', ha='center', va='center',
        color='#888888', fontsize=8.5, style='italic')

# ── Judgement score annotation ────────────────────────────────────────────────
box(ax, 8.2, 5.8, 2.1, 0.75,
    'Judgement Score', '0–100 accumulated', color='#37474f', fontsize=8.5)
# arrow from skill check to judgement
ax.annotate('', xy=(8.2 + 1.05, 5.8 + 0.75),
            xytext=(BOX_X + BOX_W, 6.5 + BOX_H/2),
            arrowprops=dict(arrowstyle='->', color='#888888', lw=1.2,
                            linestyle='dotted'), zorder=5)
# arrow from judgement to terminal diamond
ax.annotate('', xy=(diamond_cx - d*1.5 + 0.05, diamond_cy + 0.2),
            xytext=(8.2 + 2.1, 5.8 + 0.38),
            arrowprops=dict(arrowstyle='->', color='#888888', lw=1.2,
                            linestyle='dotted'), zorder=5)

# ── Legend ────────────────────────────────────────────────────────────────────
legend_items = [
    mpatches.Patch(color=C_PLAYER, label='Player / Skill Check'),
    mpatches.Patch(color=C_BDI,    label='BDI Pipeline (Belief → Desire → Intention)'),
    mpatches.Patch(color=C_LLM,    label='LLM (Ollama) — text generation only'),
    mpatches.Patch(color=C_TERM,   label='Terminal routing / Outcome'),
    mpatches.Patch(color=C_NPC,    label='NPC Personality Model'),
]
ax.legend(handles=legend_items, loc='lower left', fontsize=8,
          framealpha=0.9, bbox_to_anchor=(0.0, 0.0))

plt.tight_layout()
out_path = r'd:\Programming\PNE (Github)\cs3ip\Dissertation\Materials\pne_pipeline_flowchart.png'
plt.savefig(out_path, dpi=180, bbox_inches='tight', facecolor='#f5f7fa')
print(f'Saved: {out_path}')
plt.show()
