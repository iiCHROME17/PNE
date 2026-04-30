"""
PNE Detailed Flowcharts (5 total)
Uses standard flowchart symbols:
  Oval       = Terminator (Start / End)
  Rectangle  = Process
  Diamond    = Decision
  Parallelogram = Input / Output

Run this file to regenerate all 5 PNGs.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import FancyBboxPatch, Ellipse
from matplotlib.patches import Polygon as MplPolygon

# ── Palette ──────────────────────────────────────────────────────────────────
C_TERM   = '#1A252F'
C_DEC    = '#D35400'
C_IO     = '#626567'
C_GATE   = '#CA6F1E'
C_PLAYER = '#1A5276'
C_COG    = '#6C3483'
C_DESIRE = '#0E6655'
C_SOC    = '#1E8449'
C_LLM    = '#5B2C6F'
C_FSM    = '#922B21'
C_RECOV  = '#784212'
C_REF    = '#2E4057'
WT = 'white'

OUTPUT = 'd:/Programming/PNE (Github)/cs3ip/Dissertation/Literature Material/Graphs/'

# ── Primitive drawing helpers ────────────────────────────────────────────────

def _text(ax, cx, cy, txt, fs, tc, bold=True, z=6):
    ax.text(cx, cy, txt, ha='center', va='center', fontsize=fs,
            color=tc, fontweight='bold' if bold else 'normal',
            multialignment='center', zorder=z)

def oval(ax, cx, cy, rw, rh, txt, color=C_TERM, tc=WT, fs=9, z=4):
    e = Ellipse((cx, cy), rw*2, rh*2,
                facecolor=color, edgecolor='#111', linewidth=1.8, zorder=z)
    ax.add_patch(e)
    _text(ax, cx, cy, txt, fs, tc, z=z+1)

def rect(ax, cx, cy, w, h, txt, color=C_PLAYER, tc=WT, fs=8.5, z=4):
    p = FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                       boxstyle="square,pad=0.04",
                       linewidth=1.6, edgecolor='#111', facecolor=color, zorder=z)
    ax.add_patch(p)
    _text(ax, cx, cy, txt, fs, tc, z=z+1)

def diamond(ax, cx, cy, w, h, txt, color=C_DEC, tc=WT, fs=8, z=4):
    pts = np.array([[cx, cy+h/2],[cx+w/2, cy],[cx, cy-h/2],[cx-w/2, cy]])
    poly = MplPolygon(pts, closed=True,
                      facecolor=color, edgecolor='#111', linewidth=1.6, zorder=z)
    ax.add_patch(poly)
    _text(ax, cx, cy, txt, fs, tc, z=z+1)

def para(ax, cx, cy, w, h, txt, color=C_IO, tc=WT, fs=8.5, sk=0.35, z=4):
    pts = np.array([[cx-w/2+sk, cy+h/2],[cx+w/2+sk, cy+h/2],
                    [cx+w/2-sk, cy-h/2],[cx-w/2-sk, cy-h/2]])
    poly = MplPolygon(pts, closed=True,
                      facecolor=color, edgecolor='#111', linewidth=1.6, zorder=z)
    ax.add_patch(poly)
    _text(ax, cx, cy, txt, fs, tc, z=z+1)

def arr(ax, x1, y1, x2, y2, lbl='', lc='#333', lfs=7.5, z=5):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=lc, lw=1.5, mutation_scale=14),
                zorder=z)
    if lbl:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ox = 0.3 if abs(x2-x1) < 0.1 else 0
        ax.text(mx+ox, my, lbl, ha='center', va='center', fontsize=lfs,
                color=lc, fontweight='bold', zorder=z+1,
                bbox=dict(boxstyle='round,pad=0.12', fc='white', ec='none', alpha=0.85))

def loop_back(ax, fx, fy, tx, ty, off=-1.8, lc='#666', lbl=''):
    """Route: from (fx,fy) → left edge → up → into (tx,ty) from left."""
    lx = min(fx, tx) + off
    ax.plot([fx, lx, lx, tx], [fy, fy, ty, ty],
            color=lc, lw=1.5, zorder=3, solid_capstyle='round')
    ax.annotate('', xy=(tx, ty), xytext=(tx-0.05, ty),
                arrowprops=dict(arrowstyle='->', color=lc, lw=1.5, mutation_scale=13),
                zorder=4)
    if lbl:
        ax.text(lx - 0.25, (fy+ty)/2, lbl, ha='right', va='center',
                fontsize=7, color=lc, rotation=90, fontweight='bold')

def legend_row(ax, x, y, shape, color, label, fs=8):
    if shape == 'oval':
        e = Ellipse((x+0.35, y), 0.7, 0.32, facecolor=color,
                    edgecolor='#333', linewidth=1.2, zorder=4)
        ax.add_patch(e)
    elif shape == 'rect':
        p = FancyBboxPatch((x, y-0.16), 0.7, 0.32, boxstyle="square,pad=0.02",
                           linewidth=1.2, edgecolor='#333', facecolor=color, zorder=4)
        ax.add_patch(p)
    elif shape == 'diamond':
        pts = np.array([[x+0.35, y+0.2],[x+0.7, y],[x+0.35, y-0.2],[x, y]])
        poly = MplPolygon(pts, closed=True, facecolor=color,
                          edgecolor='#333', linewidth=1.2, zorder=4)
        ax.add_patch(poly)
    elif shape == 'para':
        pts = np.array([[x+0.1, y+0.16],[x+0.8, y+0.16],
                        [x+0.6, y-0.16],[x-0.1, y-0.16]])
        poly = MplPolygon(pts, closed=True, facecolor=color,
                          edgecolor='#333', linewidth=1.2, zorder=4)
        ax.add_patch(poly)
    ax.text(x+0.9, y, label, va='center', fontsize=fs, color='#2C3E50')

# ════════════════════════════════════════════════════════════════════════════
# CHART 1 — Master Pipeline Overview
# ════════════════════════════════════════════════════════════════════════════
def chart1():
    W, H = 11, 23
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')

    X = 5.5   # main column centre

    # Title
    ax.text(X, 22.5, 'PNE — Master Pipeline Overview (Per Turn)',
            ha='center', fontsize=13, fontweight='bold', color='#1A252F')

    # START
    oval(ax, X, 21.8, 2.2, 0.42, 'START\nNew Player Turn')
    arr(ax, X, 21.38, X, 20.92)

    # Stage I – NPC Intent Layer
    rect(ax, X, 20.5, 7.0, 0.72,
         'Stage I — NPC Intent Layer\nLoad NPCModel · scenario · terminal outcome set · player skills',
         color=C_REF)
    arr(ax, X, 20.14, X, 19.58)

    # Two-stage choice filter header
    rect(ax, X, 19.15, 7.0, 0.72,
         'Choice Filter — Stage 1 (Hard Gates / ChoiceFilter)\nskill threshold · relation · NPC flags · prerequisites · failed_choices',
         color=C_GATE)
    arr(ax, X, 18.79, X, 18.23)

    # Decision: all filtered?
    diamond(ax, X, 17.8, 4.2, 0.78,
            'All choices\nfiltered out?', color=C_DEC)
    # YES branch → right
    arr(ax, X+2.1, 17.8, 8.7, 17.8, 'YES', lc='#C0392B')
    rect(ax, 9.4, 17.8, 1.8, 0.62,
         'Smart\nFallback:\nRelax gates', color=C_GATE, fs=7.5)
    arr(ax, 9.4, 17.49, 9.4, 16.98)
    arr(ax, 8.5, 16.98, X+2.35, 17.1, lc='#888')  # back into NO path
    # NO branch ↓
    arr(ax, X, 17.41, X, 16.88, 'NO', lc='#27AE60')

    # Stage 2 coherence filter
    rect(ax, X, 16.45, 7.0, 0.72,
         'Choice Filter — Stage 2 (Dialogue Momentum Filter)\nscore coherence [0–1] · remove < 0.3 · skip if all would be removed',
         color=C_GATE)
    arr(ax, X, 16.09, X, 15.53)

    # Decision: recovery_mode?
    diamond(ax, X, 15.1, 4.0, 0.72,
            'recovery_mode\n= True?', color=C_DEC)
    arr(ax, X+2.0, 15.1, 8.5, 15.1, 'YES', lc='#C0392B')
    rect(ax, 9.35, 15.1, 1.9, 0.62,
         'Serve\nRecovery\nChoices', color=C_RECOV, fs=7.5)
    arr(ax, 9.35, 14.79, 9.35, 14.28)
    arr(ax, 8.45, 14.28, X+1.82, 14.28, lc='#888')
    arr(ax, X, 14.74, X, 14.28, 'NO', lc='#27AE60')

    # I/O: Player selects choice
    para(ax, X, 13.82, 6.0, 0.72,
         'Stage II — Player Selects Dialogue Choice\n→ Parsed to PlayerDialogueInput (text · LanguageArt · tone floats)',
         color=C_PLAYER)
    arr(ax, X, 13.46, X, 12.9)

    # Skill check
    rect(ax, X, 12.45, 7.0, 0.8,
         'Stage IIa — 2-Dice Skill Check\nPlayer d6 vs NPC d6  ·  player_bias = skill/10 + relation_bias + difficulty_adj\nnpc_bias = calc_threshold(npc, language_art)',
         color=C_GATE)
    arr(ax, X, 12.05, X, 11.52)

    # Decision: success_pct < 50?
    diamond(ax, X, 11.1, 4.0, 0.72,
            'success_pct\n< 50%?', color=C_DEC)
    arr(ax, X+2.0, 11.1, 8.5, 11.1, 'YES', lc='#C0392B')
    rect(ax, 9.4, 11.1, 1.9, 0.62,
         'Apply Risk\nMultiplier\nto Δ', color=C_GATE, fs=7.5)
    arr(ax, 9.4, 10.79, 9.4, 10.42)
    arr(ax, 8.5, 10.42, X+1.82, 10.42, lc='#888')
    arr(ax, X, 10.74, X, 10.42, 'NO', lc='#27AE60')

    # Merge → decision SUCCESS?
    arr(ax, X, 10.42, X, 9.98)
    diamond(ax, X, 9.55, 3.6, 0.72, 'Dice\nSUCCESS?', color=C_DEC)

    # Two outcome branches
    arr(ax, X-1.8, 9.55, 2.8, 9.55, 'YES', lc='#27AE60')
    rect(ax, 2.0, 9.0, 2.5, 0.8,
         'Select\ninteraction_\noutcomes\n+ ve Δ judgement', color=C_SOC, fs=7.5)
    arr(ax, X+1.8, 9.55, 8.2, 9.55, 'NO', lc='#C0392B')
    rect(ax, 9.0, 9.0, 2.5, 0.8,
         'Select\nfailure_\noutcomes\n− ve Δ judgement', color=C_FSM, fs=7.5)

    # Merge both branches back to centre
    arr(ax, 2.0, 8.6, 2.0, 7.98, lc='#888')
    arr(ax, 9.0, 8.6, 9.0, 7.98, lc='#888')
    ax.plot([2.0, X, 9.0], [7.98, 7.98, 7.98], color='#888', lw=1.5, zorder=3)
    arr(ax, X, 7.98, X, 7.52)

    # BDI pipeline reference box
    rect(ax, X, 7.1, 7.0, 0.72,
         'Stages III–V — BDI Pipeline  (see Charts 2, 3, 4)\nCognitive Interpretation → Desire Formation → Socialisation Filter',
         color=C_REF)
    arr(ax, X, 6.74, X, 6.18)

    # Outcome application + Ollama
    rect(ax, X, 5.75, 7.0, 0.72,
         'Stage VI — Apply Interaction Outcome\nrelation_delta · stance_delta · intention_shift  →  Build Ollama Prompt',
         color=C_LLM)
    arr(ax, X, 5.39, X, 4.83)

    rect(ax, X, 4.4, 7.0, 0.72,
         'Ollama: Generate NPC Dialogue (Qwen2.5:3b)\n7-section prompt  ·  DICE CONTEXT injected  ·  ≤ 40 words output',
         color=C_LLM)
    arr(ax, X, 4.04, X, 3.48)

    # I/O stream to client
    para(ax, X, 3.05, 6.0, 0.72,
         'Stream NPC Dialogue via WebSocket to Game Engine\nIncrement turn_count  ·  Append to history',
         color=C_IO)
    arr(ax, X, 2.69, X, 2.13)

    # FSM
    rect(ax, X, 1.7, 7.0, 0.72,
         'Stage VII — TransitionResolver\njudgement · player_relation · intention_match · turn_count · choices_made',
         color=C_FSM)
    arr(ax, X, 1.34, X, 0.88)

    # Decision: terminal?
    diamond(ax, X, 0.45, 3.6, 0.7, 'Terminal\ncondition?', color=C_DEC)

    # YES → right side END
    arr(ax, X+1.8, 0.45, 8.2, 0.45, 'YES', lc='#C0392B')
    oval(ax, 9.3, 0.45, 1.7, 0.38, 'END\nTerminal Outcome', color=C_FSM)

    # NO → loop back to filter
    loop_back(ax, X-1.8, 0.45, X-3.5, 19.15, off=0, lc='#555',
              lbl='NO → next node')

    # ── Legend ────────────────────────────────────────────────────────────────
    lx, ly = 0.15, 5.0
    ax.text(lx+0.35, ly+0.55, 'SYMBOLS', fontsize=7.5, fontweight='bold', color='#444')
    legend_row(ax, lx, ly+0.1,     'oval',    C_TERM,   'Terminator (Start/End)')
    legend_row(ax, lx, ly-0.42,    'rect',    C_PLAYER, 'Process / Stage')
    legend_row(ax, lx, ly-0.94,    'diamond', C_DEC,    'Decision')
    legend_row(ax, lx, ly-1.46,    'para',    C_IO,     'Input / Output')

    plt.tight_layout(pad=0.3)
    plt.savefig(OUTPUT + 'fc1_master_pipeline.png', dpi=160,
                bbox_inches='tight', facecolor='white')
    print('Saved fc1_master_pipeline.png')
    plt.close()


# ════════════════════════════════════════════════════════════════════════════
# CHART 2 — Stage III: Cognitive Interpretation (CognitiveThoughtMatcher)
# ════════════════════════════════════════════════════════════════════════════
def chart2():
    W, H = 10, 17
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
    X = 5.0

    ax.text(X, 16.5, 'Stage III — Cognitive Interpretation\n(CognitiveThoughtMatcher)',
            ha='center', fontsize=12, fontweight='bold', color='#1A252F')

    oval(ax, X, 15.85, 2.1, 0.4, 'START\nEnter Cognitive Layer')
    arr(ax, X, 15.45, X, 14.92)

    para(ax, X, 14.5, 7.0, 0.72,
         'INPUT: PlayerDialogueInput  +  NPCModel\n'
         'language_art · authority_tone · diplomacy_tone · empathy_tone · manipulation_tone',
         color=C_IO)
    arr(ax, X, 14.14, X, 13.58)

    rect(ax, X, 13.15, 7.5, 0.72,
         'Extract NPC Cognitive Attributes\n'
         'self_esteem · locus_of_control · cog_flexibility · player_relation',
         color=C_COG)
    arr(ax, X, 12.79, X, 12.23)

    rect(ax, X, 11.8, 7.5, 0.72,
         'Load cognitive_thoughts.json Template Library\n'
         'Each template has: bias_type · match_weights · thought_variants · belief_variants',
         color=C_COG)
    arr(ax, X, 11.44, X, 10.88)

    rect(ax, X, 10.45, 7.5, 0.8,
         'Score Each Template Against Current State\n'
         '• language_art  →  discrete table lookup\n'
         '• numeric params  →  gate on min / max / range  →  award weight if in range\n'
         '  (self_esteem · locus_of_control · cog_flexibility · tone floats · player_relation)',
         color=C_COG)
    arr(ax, X, 10.05, X, 9.52)

    rect(ax, X, 9.1, 7.5, 0.72,
         'Normalise Each Score  ÷  Total Possible Weight\n'
         'Produces score ∈ [0, 1] for every candidate template',
         color=C_COG)
    arr(ax, X, 8.74, X, 8.18)

    diamond(ax, X, 7.75, 4.8, 0.72,
            'Any template\nscore ≥ 0.35?', color=C_DEC)

    # YES branch
    arr(ax, X, 7.39, X, 6.83, 'YES', lc='#27AE60')
    rect(ax, X, 6.4, 7.5, 0.72,
         'Select Highest-Scoring Template\n'
         'Retrieve bias_type  →  feeds Desire Formation (Stage IV)',
         color=C_COG)
    arr(ax, X, 6.04, X, 5.52)

    # NO branch → right
    arr(ax, X+2.4, 7.75, 8.45, 7.75, 'NO', lc='#C0392B')
    rect(ax, 9.0, 7.75, 1.8, 0.65,
         'Fallback:\ncynical_realism\ntemplate', color=C_FSM, fs=7.5)
    arr(ax, 9.0, 7.42, 9.0, 5.9, lc='#C0392B')
    arr(ax, 8.1, 5.9, X+3.0, 5.9, lc='#888')  # merge into next

    # Merge into pick variant
    arr(ax, X, 5.52, X, 5.08)
    rect(ax, X, 4.65, 7.5, 0.72,
         'Pick Random Variant from Selected Template\n'
         'thought_variants  →  internal_thought  ·  belief_variants  →  subjective_belief',
         color=C_COG)
    arr(ax, X, 4.29, X, 3.73)

    rect(ax, X, 3.3, 7.5, 0.72,
         'Compute Emotional Valence\n'
         'Weighted sum of tone floats vs NPC empathy/self_esteem  →  float [−1, +1]',
         color=C_COG)
    arr(ax, X, 2.94, X, 2.38)

    para(ax, X, 1.95, 7.5, 0.72,
         'OUTPUT: ThoughtReaction\n'
         'internal_thought (private) · subjective_belief · emotional_valence · bias_type',
         color=C_IO)
    arr(ax, X, 1.59, X, 1.1)

    oval(ax, X, 0.7, 2.1, 0.4, 'END\n→ Stage IV: Desire Formation')

    plt.tight_layout(pad=0.3)
    plt.savefig(OUTPUT + 'fc2_cognitive_layer.png', dpi=160,
                bbox_inches='tight', facecolor='white')
    print('Saved fc2_cognitive_layer.png')
    plt.close()


# ════════════════════════════════════════════════════════════════════════════
# CHART 3 — Stage IV: Desire Formation Layer
# ════════════════════════════════════════════════════════════════════════════
def chart3():
    W, H = 11, 20
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
    X = 5.5

    ax.text(X, 19.5, 'Stage IV — Desire Formation Layer',
            ha='center', fontsize=12, fontweight='bold', color='#1A252F')

    oval(ax, X, 18.85, 2.1, 0.4, 'START\nEnter Desire Formation')
    arr(ax, X, 18.45, X, 17.92)

    para(ax, X, 17.5, 7.5, 0.72,
         'INPUT: ThoughtReaction (subjective_belief · bias_type)  +  NPCModel\n'
         'npc.cognitive  ·  npc.social.ideology  ·  player_input.ideology_alignment',
         color=C_IO)
    arr(ax, X, 17.14, X, 16.58)

    rect(ax, X, 16.15, 7.5, 0.72,
         'Extract Keyword Signals from subjective_belief\n'
         'Scan for pattern keywords (uncertainty · sincerity · threat · opportunism · ideology · valence)',
         color=C_DESIRE)
    arr(ax, X, 15.79, X, 15.26)

    # 7 pattern rows
    patterns = [
        ('P1', 'Uncertainty keywords\n(unclear · unsure · testing · cheap)',
         'self_esteem > 0.6?', 'information-seeking', 'protection'),
        ('P2', 'Sincerity keywords\n(genuine · sincere · authentic · honest)',
         'empathy > 0.5?', 'affiliation', 'guarded\ninformation-seeking'),
        ('P3', 'Threat keywords\n(manipulative · threat · attack · deceive)',
         'Martyr wildcard\nOR assertion > 0.7?', 'dominance', 'protection'),
        ('P4', 'Opportunism keywords\n(using · exploit · advantage)',
         None, 'information-seeking\n(NPC suspects exploitation)', None),
        ('P5', 'Ideology alignment\n(player ideology in npc.ideology)',
         'alignment_strength\n> 0.6?', 'affiliation', 'information-seeking'),
        ('P6', 'Emotional valence defaults\n(valence < −0.3 or > +0.3)',
         'valence < −0.3?', 'protection', 'affiliation'),
        ('P7', 'Fallback — long_term_desire keywords\n(protect/secure/power → info-seeking  ·  else → info-seeking)',
         None, 'information-seeking\n(protect keywords)', None),
    ]

    P_COLORS = [C_DESIRE, C_DESIRE, C_DESIRE, '#0A7764', '#0A7764', '#0A7764', '#0A7764']
    y = 15.26
    for i, (pid, trigger, dec_txt, yes_out, no_out) in enumerate(patterns):
        bh = 0.68 if '\n' in trigger else 0.6
        # Pattern label + trigger box
        rect(ax, X, y - bh/2 - 0.04, 7.5, bh,
             f'{pid}: {trigger}', color=P_COLORS[i], fs=7.8)
        bot = y - bh - 0.08

        if dec_txt is None:
            # No branch — just output
            arr(ax, X, bot, X, bot - 0.42)
            rect(ax, X, bot - 0.72, 5.5, 0.55,
                 yes_out, color='#148F77', fs=7.5)
            arr(ax, X, bot - 0.99, X, bot - 1.42)
            y = bot - 1.42
        else:
            # Decision diamond
            arr(ax, X, bot, X, bot - 0.38)
            dh = 0.62
            diamond(ax, X, bot - 0.7, 4.2, dh, dec_txt, color=C_DEC, fs=7.5)
            # YES (left)
            arr(ax, X - 2.1, bot - 0.7, 2.5, bot - 0.7, 'YES', lc='#27AE60')
            rect(ax, 1.55, bot - 1.15, 2.1, 0.62, yes_out, color=C_SOC, fs=7.2)
            # NO (right)
            arr(ax, X + 2.1, bot - 0.7, 8.5, bot - 0.7, 'NO', lc='#C0392B')
            rect(ax, 9.35, bot - 1.15, 2.1, 0.62, no_out or '—', color=C_FSM, fs=7.2)
            # Both merge down
            merge_y = bot - 1.62
            ax.plot([1.55, X, 9.35], [merge_y, merge_y, merge_y],
                    color='#888', lw=1.3, zorder=3)
            arr(ax, X, merge_y, X, merge_y - 0.38)
            y = merge_y - 0.38

        if i < len(patterns) - 1:
            # "matched?" decision between patterns
            diamond(ax, X, y - 0.3, 3.8, 0.52, 'Pattern\nmatched?', color='#555', fs=7.5)
            arr(ax, X - 1.9, y - 0.3, X - 1.9, y - 0.3 - 0.26, 'YES  ↓  skip remaining', lc='#888')
            arr(ax, X, y - 0.56, X, y - 0.82, 'NO', lc='#888')
            y = y - 0.82

    arr(ax, X, y, X, y - 0.45)

    # Cognitive bias modifier
    rect(ax, X, y - 0.82, 8.0, 0.65,
         'Apply Cognitive Bias Modifier  (BIAS_TO_DESIRE_MODIFIER)\n'
         'hostile_attribution→protection +0.20  ·  optimism_bias→affiliation +0.15  ·  '
         'empathy_resonance→affiliation +0.25  ·  etc.',
         color='#1A5276', fs=7.8)
    by = y - 0.82
    arr(ax, X, by - 0.33, X, by - 0.79)

    rect(ax, X, by - 1.12, 7.0, 0.62,
         'Clamp intensity  ∈  [0, 1]\n'
         'intensity nudges final confrontation level toward template upper band',
         color=C_DESIRE)
    arr(ax, X, by - 1.43, X, by - 1.88)

    para(ax, X, by - 2.22, 7.5, 0.62,
         'OUTPUT: DesireState\n'
         'immediate_desire (natural language)  ·  desire_type  ·  intensity',
         color=C_IO)
    arr(ax, X, by - 2.53, X, by - 2.95)

    oval(ax, X, by - 3.28, 2.2, 0.4, 'END\n→ Stage V: Socialisation Filter')

    plt.tight_layout(pad=0.3)
    plt.savefig(OUTPUT + 'fc3_desire_formation.png', dpi=160,
                bbox_inches='tight', facecolor='white')
    print('Saved fc3_desire_formation.png')
    plt.close()


# ════════════════════════════════════════════════════════════════════════════
# CHART 4 — Stage V: Socialisation Filter (Intention Registry)
# ════════════════════════════════════════════════════════════════════════════
def chart4():
    W, H = 10, 17
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
    X = 5.0

    ax.text(X, 16.5, 'Stage V — Socialisation Filter\n(Intention Registry Selection)',
            ha='center', fontsize=12, fontweight='bold', color='#1A252F')

    oval(ax, X, 15.85, 2.2, 0.4, 'START\nEnter Socialisation Filter')
    arr(ax, X, 15.45, X, 14.92)

    para(ax, X, 14.5, 7.5, 0.72,
         'INPUT: DesireState  +  NPCModel  +  PlayerDialogueInput\n'
         'desire_type · intensity · wildcard · social.assertion · confrontation_level',
         color=C_IO)
    arr(ax, X, 14.14, X, 13.58)

    # Wildcard override check
    diamond(ax, X, 13.15, 5.2, 0.72,
            'Wildcard hard-override\nconditions met?\n(e.g. Inferiority + authority_tone > 0.7)',
            color=C_DEC, fs=8)
    arr(ax, X+2.6, 13.15, 8.45, 13.15, 'YES', lc='#C0392B')
    rect(ax, 9.22, 13.15, 1.7, 0.72,
         'Bypass\nRegistry\n→ Fixed\nintention\n(e.g. Submit)', color=C_FSM, fs=7.2)
    # YES branch goes directly to output
    arr(ax, 9.22, 12.79, 9.22, 4.42, lc='#C0392B')
    arr(ax, 8.37, 4.42, X+3.0, 4.42, lc='#888')

    arr(ax, X, 12.79, X, 12.23, 'NO', lc='#27AE60')

    # Pre-filter
    rect(ax, X, 11.8, 7.5, 0.72,
         'Pre-filter Intention Registry\n'
         'Keep only templates where template.desire_type == current desire_type',
         color=C_SOC)
    arr(ax, X, 11.44, X, 10.88)

    # Scoring
    rect(ax, X, 10.45, 7.5, 0.88,
         'Score Each Candidate Template  (0 – 1)\n'
         '• Keyword overlap between desire text and template keywords  (50 % weight)\n'
         '• Confrontation band fit  [confrontation_min, confrontation_max]  (40 % weight)\n'
         '• Intensity bonus  (10 % weight)\n'
         '• Hard gates: wildcard_required · npc_conditions  →  disqualify if not met',
         color=C_SOC, fs=8)
    arr(ax, X, 10.01, X, 9.48)

    # Decision: any candidate?
    diamond(ax, X, 9.05, 4.4, 0.72,
            'Any candidate\nscore > 0?', color=C_DEC)

    arr(ax, X, 8.69, X, 8.13, 'YES', lc='#27AE60')
    rect(ax, X, 7.7, 7.5, 0.72,
         'Select Highest-Scoring Template\n'
         'Retrieve intention name · emotional_expression · wildcard_triggered flag',
         color=C_SOC)
    arr(ax, X, 7.34, X, 6.78)

    # NO → fallback
    arr(ax, X+2.2, 9.05, 8.45, 9.05, 'NO', lc='#C0392B')
    rect(ax, 9.2, 9.05, 1.7, 0.65,
         "Fallback:\n'Neutral\nResponse'", color=C_FSM, fs=7.5)
    arr(ax, 9.2, 8.72, 9.2, 7.5, lc='#C0392B')
    arr(ax, 8.35, 7.5, X+3.0, 7.5, lc='#888')

    # Confrontation compute
    rect(ax, X, 6.35, 7.5, 0.72,
         'Compute Confrontation Level\n'
         'Clamp NPC natural confrontation into [template.min, template.max]  ·  nudge by intensity',
         color=C_SOC)
    arr(ax, X, 5.99, X, 5.43)

    rect(ax, X, 5.0, 7.5, 0.72,
         'Build BehaviouralIntention Object\n'
         'intention_type (canonical name)  ·  confrontation_level  ·  emotional_expression',
         color=C_SOC)
    arr(ax, X, 4.64, X, 4.08)

    para(ax, X, 3.65, 7.5, 0.72,
         'OUTPUT: BehaviouralIntention\n'
         'intention_type  ·  confrontation_level  ·  emotional_expression  ·  wildcard_triggered',
         color=C_IO)
    arr(ax, X, 3.29, X, 2.73)

    rect(ax, X, 2.3, 7.5, 0.72,
         'intention_type written verbatim into:\n'
         '(a) Ollama prompt CURRENT STATE section  ·  (b) TransitionResolver routing conditions',
         color=C_REF, fs=8)
    arr(ax, X, 1.94, X, 1.42)

    oval(ax, X, 1.0, 2.2, 0.4, 'END\n→ Stage VI: Outcome')

    plt.tight_layout(pad=0.3)
    plt.savefig(OUTPUT + 'fc4_social_intention.png', dpi=160,
                bbox_inches='tight', facecolor='white')
    print('Saved fc4_social_intention.png')
    plt.close()


# ════════════════════════════════════════════════════════════════════════════
# CHART 5 — Stages VI + VII: Outcome Application, LLM Generation, FSM
# ════════════════════════════════════════════════════════════════════════════
def chart5():
    W, H = 11, 20
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
    X = 5.5

    ax.text(X, 19.5,
            'Stages VI + VII — Outcome Application · LLM Generation · FSM Routing',
            ha='center', fontsize=12, fontweight='bold', color='#1A252F')

    oval(ax, X, 18.85, 2.2, 0.4, 'START\nEnter Stage VI')
    arr(ax, X, 18.45, X, 17.92)

    para(ax, X, 17.5, 8.0, 0.72,
         'INPUT: BehaviouralIntention  +  DiceCheckResult  +  NPCModel  +  Scenario Node\n'
         'intention_type · confrontation_level · player_die · npc_die · success flag · scene direction',
         color=C_IO)
    arr(ax, X, 17.14, X, 16.58)

    # Decision: dice success?
    diamond(ax, X, 16.15, 4.0, 0.72, 'Dice\nSUCCESS?', color=C_DEC)

    arr(ax, X-2.0, 16.15, 2.5, 16.15, 'YES', lc='#27AE60')
    rect(ax, 1.6, 15.6, 2.2, 0.82,
         'Select from\ninteraction_\noutcomes\n(positive set)', color=C_SOC, fs=7.5)

    arr(ax, X+2.0, 16.15, 8.5, 16.15, 'NO', lc='#C0392B')
    rect(ax, 9.35, 15.6, 2.2, 0.82,
         'Select from\nfailure_\noutcomes\n(negative set)', color=C_FSM, fs=7.5)

    merge_y = 15.12
    ax.plot([1.6, X, 9.35], [merge_y, merge_y, merge_y], color='#888', lw=1.5, zorder=3)
    arr(ax, X, merge_y, X, 14.58)

    # Apply deltas
    rect(ax, X, 14.15, 8.0, 0.72,
         'Apply Interaction Outcome to NPCModel\n'
         'relation_delta → player_relation  ·  stance_delta → cognitive/social attributes',
         color=C_LLM)
    arr(ax, X, 13.79, X, 13.23)

    rect(ax, X, 12.8, 8.0, 0.72,
         'Update intention_shift\n'
         'Tags conversation momentum  →  feeds DialogueMomentumFilter next turn',
         color=C_LLM)
    arr(ax, X, 12.44, X, 11.88)

    # Recovery mode check
    diamond(ax, X, 11.45, 4.2, 0.72, 'recovery_mode\n= True?', color=C_DEC)
    arr(ax, X+2.1, 11.45, 8.5, 11.45, 'YES', lc='#C0392B')
    rect(ax, 9.4, 11.1, 2.0, 0.62,
         'Serve\nRecovery\nChoices only\n(skip Ollama)', color=C_RECOV, fs=7.5)
    arr(ax, 9.4, 10.79, 9.4, 6.82, lc='#C0392B')
    arr(ax, 8.4, 6.82, X+3.5, 6.82, lc='#888')

    arr(ax, X, 11.09, X, 10.53, 'NO', lc='#27AE60')

    # Build Ollama prompt
    rect(ax, X, 10.1, 8.0, 0.8,
         'Build Ollama Prompt  (7 sections)\n'
         'IDENTITY · BACKGROUND · CURRENT STATE (belief + intention + stance)\n'
         'SCENE DIRECTION · DICE CONTEXT · RESPONSE RANGE · HISTORY (last 6 turns)',
         color=C_LLM, fs=8)
    arr(ax, X, 9.7, X, 9.14)

    # Wildcard temp
    diamond(ax, X, 8.71, 4.4, 0.72,
            'NPC has\nwildcard defined?', color=C_DEC)
    arr(ax, X+2.2, 8.71, 8.5, 8.71, 'YES', lc='#C0392B')
    rect(ax, 9.42, 8.71, 2.2, 0.62,
         'Apply wildcard\ntemperature\noffset to\nbase (0.85)', color=C_RECOV, fs=7.5)
    arr(ax, 9.42, 8.4, 9.42, 7.68, lc='#888')
    arr(ax, 8.52, 7.68, X+3.52, 7.68, lc='#888')
    arr(ax, X, 8.35, X, 7.68, 'NO', lc='#27AE60')

    arr(ax, X, 7.68, X, 7.12)

    # Ollama call
    rect(ax, X, 6.68, 8.0, 0.72,
         'Call Ollama (Qwen2.5:3b)  —  generate_response_with_direction\n'
         'Generate NPC dialogue line  ≤ 40 words  ·  stay in character  ·  no action brackets',
         color=C_LLM)
    arr(ax, X, 6.32, X, 5.78)

    para(ax, X, 5.35, 7.5, 0.72,
         'OUTPUT: NPC Dialogue  →  WebSocket stream to game engine\n'
         'Increment turn_count  ·  Append full BDI metadata to NPCConversationState.history',
         color=C_IO)
    arr(ax, X, 4.99, X, 4.45)

    # FSM
    rect(ax, X, 4.02, 8.0, 0.72,
         'Stage VII — TransitionResolver: Evaluate All Conditions\n'
         'turn_count ≥ N  ·  judgement ≥/≤ N  ·  player_relation ≥ N  ·  '
         'intention_match  ·  choices_made includes X',
         color=C_FSM)
    arr(ax, X, 3.66, X, 3.1)

    diamond(ax, X, 2.67, 4.0, 0.72, 'Terminal\ncondition\nmet?', color=C_DEC)

    # YES → terminal flow
    arr(ax, X+2.0, 2.67, 8.45, 2.67, 'YES', lc='#C0392B')
    rect(ax, 9.35, 2.2, 2.1, 0.72,
         'generate_\nterminal()\nFinal NPC\nline', color=C_FSM, fs=7.5)
    arr(ax, 9.35, 1.84, 9.35, 1.22, lc='#C0392B')
    oval(ax, 9.35, 0.82, 1.65, 0.38,
         'END\nTerminal\nOutcome', color=C_FSM, fs=7.5)

    # NO → update stage + route
    arr(ax, X-2.0, 2.67, 2.5, 2.67, 'NO', lc='#27AE60')
    rect(ax, 1.55, 2.2, 2.2, 0.72,
         'Update\nConversation\nStage\n(opening/\ndev/crisis/\nresolution)', color=C_SOC, fs=7.5)
    arr(ax, 1.55, 1.84, 1.55, 1.28, lc='#27AE60')
    rect(ax, 1.55, 0.9, 2.2, 0.58,
         'Route to\nNext Node\n→ Stage II', color=C_REF, fs=7.5)
    oval(ax, 1.55, 0.35, 1.8, 0.3, 'NEXT TURN', color=C_TERM, fs=7.5)

    plt.tight_layout(pad=0.3)
    plt.savefig(OUTPUT + 'fc5_outcome_llm_fsm.png', dpi=160,
                bbox_inches='tight', facecolor='white')
    print('Saved fc5_outcome_llm_fsm.png')
    plt.close()


# ── Run all ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    chart1()
    chart2()
    chart3()
    chart4()
    chart5()
    print('\nAll 5 flowcharts generated.')
