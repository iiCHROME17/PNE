"""
Generate NPC personality radar charts for Krakk, Moses, and Troy.
Output: npc_radar_charts.png (saved to the same directory as this script)
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# ── NPC data ──────────────────────────────────────────────────────────────────
labels = [
    "Self-Esteem",
    "Locus of Control\n(Internal)",
    "Cog. Flexibility",
    "Assertion",
    "Conf./Independence",
    "Empathy",
]
N = len(labels)

npcs = {
    "Krakk\n(Inferiority wildcard)": {
        "values": [0.5, 0.8, 0.4, 0.3, 0.9, 0.8],
        "color": "#4C72B0",
        "wildcard": "Inferiority",
    },
    "Moses\n(Martyr wildcard)": {
        "values": [0.8, 0.475, 0.3, 1.0, 0.7, 0.45],
        "color": "#DD4D4D",
        "wildcard": "Martyr",
    },
    "Troy\n(no wildcard)": {
        "values": [0.2, 0.85, 0.1, 0.8, 0.1, 0.5],
        "color": "#2CA02C",
        "wildcard": None,
    },
}

# ── Compute angles ─────────────────────────────────────────────────────────────
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]  # close the polygon

# ── Plot ───────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5.5), subplot_kw=dict(polar=True))
fig.patch.set_facecolor("#F8F8F8")

for ax, (name, data) in zip(axes, npcs.items()):
    vals = data["values"] + data["values"][:1]
    color = data["color"]

    # Grid rings
    for r in [0.2, 0.4, 0.6, 0.8, 1.0]:
        ax.plot(angles, [r] * (N + 1), color="#CCCCCC", linewidth=0.6, linestyle="--")

    # Filled area
    ax.fill(angles, vals, color=color, alpha=0.20)
    # Outline
    ax.plot(angles, vals, color=color, linewidth=2.2, marker="o", markersize=5)

    # Axis labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=8.5, fontweight="bold")
    ax.set_yticklabels([])
    ax.set_ylim(0, 1)

    # Ring value labels on one spoke
    for r_val in [0.2, 0.4, 0.6, 0.8, 1.0]:
        ax.text(
            angles[0], r_val + 0.04, str(r_val),
            ha="center", va="bottom", size=7, color="#888888"
        )

    # Title
    ax.set_title(name, size=11, fontweight="bold", pad=18, color=color)

    # Spoke lines
    for angle in angles[:-1]:
        ax.plot([angle, angle], [0, 1], color="#BBBBBB", linewidth=0.8)

    ax.set_facecolor("#FAFAFA")

fig.suptitle(
    "Figure 6.2 — NPC Personality Profiles: Krakk, Moses, Troy",
    fontsize=13, fontweight="bold", y=1.02
)

plt.tight_layout(pad=2.0)

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "npc_radar_charts.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#F8F8F8")
print(f"Saved: {out_path}")
plt.close()
