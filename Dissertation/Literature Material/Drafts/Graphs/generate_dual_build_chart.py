"""
Generate Troy dual-build comparison line chart.
Run A: Empathy build (authority:2, empathy:9) — SUCCEED in 2 turns
Run B: Assertion build (authority:9, empathy:2) — FAIL in 3 turns
Source: Section 6.5 / Table 6.5.1 of Dissertation_Draft1.md
Output: troy_dual_build_chart.png
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# ── Data ─────────────────────────────────────────────────────────────────────
# Relation values per turn from routing log deltas documented in §6.5
# Run A: +0.15 on T1, terminal SUCCEED on T2 (final 1.0)
# Run B: −0.15 on T1, −0.05 on T2 (backpedal_rejected), terminal FAIL on T3 (final 0.75)

run_a = {
    "label":    "Run A — Empathy Build\n(authority: 2, empathy: 9)",
    "turns":    [0,    1,    2],
    "relation": [0.50, 0.65, 1.00],
    "terminal_turn": 2,
    "terminal": "SUCCEED",
    "color":    "#2CA02C",
    "marker":   "o",
}

run_b = {
    "label":    "Run B — Assertion Build\n(authority: 9, empathy: 2)",
    "turns":    [0,    1,    2,    3],
    "relation": [0.50, 0.35, 0.30, 0.75],
    "terminal_turn": 3,
    "terminal": "FAIL",
    "color":    "#DD4D4D",
    "marker":   "s",
}

fig, ax = plt.subplots(figsize=(9, 5.5))
fig.patch.set_facecolor("#F8F8F8")
ax.set_facecolor("#FAFAFA")

# ── Grid ─────────────────────────────────────────────────────────────────────
ax.yaxis.grid(True, linestyle="--", linewidth=0.6, color="#CCCCCC", zorder=0)
ax.set_axisbelow(True)

# ── Reference bands ───────────────────────────────────────────────────────────
ax.axhspan(0.9, 1.0, alpha=0.08, color="#2CA02C", zorder=0)
ax.axhline(0.9, color="#2CA02C", linewidth=1.0, linestyle=":", alpha=0.6, zorder=1)
ax.text(3.08, 0.905, "terminal\nthreshold ≥ 0.9", fontsize=7.5, color="#2CA02C", va="bottom")

ax.axhline(0.5, color="#AAAAAA", linewidth=0.8, linestyle=":", alpha=0.5, zorder=1)
ax.text(3.08, 0.505, "neutral (0.5)", fontsize=7.5, color="#AAAAAA", va="bottom")

# ── Plot runs ────────────────────────────────────────────────────────────────
for run in [run_a, run_b]:
    turns = run["turns"]
    rels  = run["relation"]
    color = run["color"]

    ax.plot(turns, rels,
            color=color, linewidth=2.4,
            marker=run["marker"], markersize=8,
            zorder=3, label=run["label"])

    # Value labels
    for i, (t, r) in enumerate(zip(turns, rels)):
        is_terminal = (i == len(turns) - 1)
        yoff = 12 if r < 0.85 else -16
        ax.annotate(f"{r:.2f}", xy=(t, r),
                    xytext=(0, yoff),
                    textcoords="offset points",
                    ha="center", fontsize=9, color=color, fontweight="bold")

    # Terminal star (SUCCEED) or cross (FAIL)
    tt = run["terminal_turn"]
    tr = rels[-1]
    if run["terminal"] == "SUCCEED":
        ax.plot(tt, tr, marker="*", markersize=18, color=color, zorder=5)
        ax.text(tt, tr + 0.055, "SUCCEED", ha="center", fontsize=9,
                fontweight="bold", color=color, zorder=5)
    else:
        ax.plot(tt, tr, marker="X", markersize=13, color=color, zorder=5,
                markeredgecolor="#990000", markeredgewidth=1.2)
        ax.text(tt, tr - 0.07, "FAIL", ha="center", fontsize=9,
                fontweight="bold", color=color, zorder=5)

# ── Divergence annotation ─────────────────────────────────────────────────────
ax.annotate("Same NPC, same scenario\nDivergence driven by\nPlayerSkillSet alone",
            xy=(0.5, 0.5), xytext=(0.6, 0.78),
            arrowprops=dict(arrowstyle="->", color="#666666", lw=1.0),
            fontsize=8, color="#444444", ha="left",
            bbox=dict(boxstyle="round,pad=0.3", fc="#F0F0F0", ec="#CCCCCC", alpha=0.85))

# ── Turn 2 key event annotation (backpedal_rejected) ─────────────────────────
ax.annotate("`backpedal_rejected`\n(−0.05: rigid model\nlocked player as adversary)",
            xy=(2, 0.30), xytext=(1.55, 0.175),
            arrowprops=dict(arrowstyle="->", color="#DD4D4D", lw=1.2),
            fontsize=7.5, color="#DD4D4D", ha="center")

# ── Turn 1 (Run A) key event annotation ──────────────────────────────────────
ax.annotate("`ideological_filter` bias\n+0.15 — player reads as\nideologically aligned",
            xy=(1, 0.65), xytext=(1.35, 0.77),
            arrowprops=dict(arrowstyle="->", color="#2CA02C", lw=1.2),
            fontsize=7.5, color="#2CA02C", ha="left")

# ── Axes ─────────────────────────────────────────────────────────────────────
ax.set_xlim(-0.3, 3.7)
ax.set_ylim(0.1, 1.18)
ax.set_xticks([0, 1, 2, 3])
ax.set_xticklabels(["Start\n(Turn 0)", "Turn 1", "Turn 2", "Turn 3\n(Terminal)"], fontsize=9)
ax.set_yticks([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
ax.set_ylabel("player_relation", fontsize=10)
ax.set_xlabel("Conversation Turn", fontsize=10)

# ── Legend ────────────────────────────────────────────────────────────────────
ax.legend(loc="upper right", fontsize=9, framealpha=0.88,
          title="NPC: Troy  |  Scenario: door_guard_night", title_fontsize=8)

# ── Title ─────────────────────────────────────────────────────────────────────
ax.set_title(
    "Figure 6.5 — Troy: Empathy Build vs Assertion Build\n"
    "Same NPC · Same Scenario · Opposite Terminal Outcomes",
    fontsize=11, fontweight="bold", pad=12
)

plt.tight_layout()

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "troy_dual_build_chart.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#F8F8F8")
print(f"Saved: {out_path}")
plt.close()
