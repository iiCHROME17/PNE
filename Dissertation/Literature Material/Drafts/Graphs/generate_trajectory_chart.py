"""
Generate multi-NPC relation trajectory line chart.
Plots per-turn player_relation for Krakk, Moses, and Troy across the 6.1 test runs.
Output: npc_trajectory_chart.png (saved to the same directory as this script)
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# ── Data ─────────────────────────────────────────────────────────────────────
# Turn 0 = start (0.5 for all), subsequent turns from routing log deltas,
# final point = terminal outcome value (includes terminal relation boost)

npcs = {
    "Krakk\n(Diplomatic opener)": {
        "turns":    [0,    1,    2],
        "relation": [0.50, 0.60, 0.75],
        "terminal_turn": 2,
        "terminal": "SUCCEED",
        "color": "#4C72B0",
        "marker": "o",
        "linestyle": "--",
    },
    "Moses\n(Authority → Recovery)": {
        "turns":    [0,    1,    2,    3,    4],
        "relation": [0.50, 0.35, 0.43, 0.53, 0.68],
        "terminal_turn": 4,
        "terminal": "SUCCEED",
        "color": "#DD4D4D",
        "marker": "s",
        "linestyle": "-",
    },
    "Troy\n(Authority → Recovery)": {
        "turns":    [0,    1,    2,    3,    4],
        "relation": [0.50, 0.35, 0.43, 0.58, 1.00],
        "terminal_turn": 4,
        "terminal": "SUCCEED",
        "color": "#2CA02C",
        "marker": "^",
        "linestyle": "-",
    },
}

fig, ax = plt.subplots(figsize=(10, 5.5))
fig.patch.set_facecolor("#F8F8F8")
ax.set_facecolor("#FAFAFA")

# ── Grid ─────────────────────────────────────────────────────────────────────
ax.yaxis.grid(True, linestyle="--", linewidth=0.6, color="#CCCCCC", zorder=0)
ax.set_axisbelow(True)

# ── Success threshold band ────────────────────────────────────────────────────
ax.axhspan(0.9, 1.0, alpha=0.08, color="#2CA02C", zorder=0)
ax.axhline(0.9, color="#2CA02C", linewidth=1.0, linestyle=":", alpha=0.5, zorder=1)
ax.text(4.05, 0.905, "terminal\nthreshold ≥ 0.9", fontsize=7.5, color="#2CA02C", va="bottom")

# ── Neutral line ─────────────────────────────────────────────────────────────
ax.axhline(0.5, color="#AAAAAA", linewidth=0.8, linestyle=":", alpha=0.5, zorder=1)
ax.text(4.05, 0.505, "neutral (0.5)", fontsize=7.5, color="#AAAAAA", va="bottom")

# ── Plot each NPC ────────────────────────────────────────────────────────────
for name, data in npcs.items():
    turns = data["turns"]
    rels  = data["relation"]
    color = data["color"]

    # Main line
    ax.plot(turns, rels,
            color=color, linewidth=2.2,
            linestyle=data["linestyle"],
            marker=data["marker"], markersize=7,
            zorder=3, label=name)

    # Annotate each point with its value
    for t, r in zip(turns, rels):
        offset = 0.025 if r <= 0.85 else -0.045
        ax.annotate(f"{r:.2f}", xy=(t, r),
                    xytext=(0, 10 if offset > 0 else -14),
                    textcoords="offset points",
                    ha="center", fontsize=8, color=color, fontweight="bold")

    # Terminal marker star
    tt = data["terminal_turn"]
    tr = rels[-1]
    ax.plot(tt, tr, marker="*", markersize=14, color=color, zorder=4)

# ── Axes ─────────────────────────────────────────────────────────────────────
ax.set_xlim(-0.3, 4.6)
ax.set_ylim(0.2, 1.12)
ax.set_xticks([0, 1, 2, 3, 4])
ax.set_xticklabels(["Start\n(Turn 0)", "Turn 1", "Turn 2", "Turn 3", "Turn 4\n(Terminal)"], fontsize=9)
ax.set_yticks([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
ax.set_ylabel("player_relation", fontsize=10)
ax.set_xlabel("Conversation Turn", fontsize=10)

# ── Wildcard annotation ───────────────────────────────────────────────────────
ax.annotate("Martyr wildcard\nfires (Turn 1)", xy=(1, 0.35), xytext=(1.3, 0.25),
            arrowprops=dict(arrowstyle="->", color="#DD4D4D", lw=1.2),
            fontsize=7.5, color="#DD4D4D", ha="left")
ax.annotate("Martyr wildcard\nfires (Turn 3)", xy=(3, 0.53), xytext=(2.55, 0.42),
            arrowprops=dict(arrowstyle="->", color="#DD4D4D", lw=1.2),
            fontsize=7.5, color="#DD4D4D", ha="right")

# ── Legend ────────────────────────────────────────────────────────────────────
legend = ax.legend(loc="upper left", fontsize=9, framealpha=0.85,
                   title="★ = terminal outcome", title_fontsize=8)

# ── Title ─────────────────────────────────────────────────────────────────────
ax.set_title(
    "Figure 7.1 — NPC Relation Trajectories: Krakk, Moses, Troy (door_guard_night scenario, 6.1 test runs)",
    fontsize=11, fontweight="bold", pad=12
)

plt.tight_layout()

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "npc_trajectory_chart.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#F8F8F8")
print(f"Saved: {out_path}")
plt.close()
