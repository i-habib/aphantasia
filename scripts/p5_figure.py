"""Draft figure for the P5 paper, drawn from aggregate results only.

Left: autism minus comparison difference in overall imagery at each percentile,
with 95% bootstrap intervals, in both studies.
Right: percentage of people with no imagery at all in each sense.

    python3 scripts/p5_exploratory.py --preregistration-url https://osf.io/87udm
    python3 scripts/p5_figure.py
Writes runs/latest/P5/p5_figure_tails.png and .pdf.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "runs" / "latest" / "P5"
NEW, ARNOLD = "#2a78d6", "#eb6834"
INK, MUTED, GRID = "#1f1f1e", "#6b6a63", "#e4e3dd"
SENSES = [("visual", "Sight"), ("auditory", "Sound"), ("smell", "Smell"), ("taste", "Taste"), ("touch", "Touch"), ("movement", "Movement")]


def main() -> int:
    data = json.loads((RESULTS / "p5_exploratory.json").read_text())
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                         "ytick.color": MUTED, "font.family": "sans-serif"})
    fig, (left, right) = plt.subplots(1, 2, figsize=(7.2, 3.1), gridspec_kw={"width_ratios": [1.15, 1]})

    for block, colour, label, offset in ((data, NEW, "New et al.", -0.6), (data["arnold"], ARNOLD, "Arnold et al.", 0.6)):
        curve = block["E3_percentile_curve_unadjusted"]
        x = np.array([row["percentile"] for row in curve]) + offset
        y = np.array([row["difference"] for row in curve])
        low = np.array([row["ci95"][0] for row in curve])
        high = np.array([row["ci95"][1] for row in curve])
        left.vlines(x, low, high, color=colour, linewidth=1.2, alpha=0.55)
        left.plot(x, y, color=colour, linewidth=2, marker="o", markersize=3.5, label=label)
    left.axhline(0, color=MUTED, linewidth=0.8)
    left.set_xlabel("Percentile of overall imagery")
    left.set_ylabel("Autism minus comparison (SD)")
    left.set_xticks([5, 25, 50, 75, 95])
    left.grid(axis="y", color=GRID, linewidth=0.6)
    left.legend(frameon=False, fontsize=7.5, loc="lower right")
    left.set_title("A. Where the gap sits", loc="left", fontsize=9, color=INK)

    width = 0.38
    positions = np.arange(len(SENSES))
    for block, colour, label, shift in ((data, NEW, "New et al.", -width / 2), (data["arnold"], ARNOLD, "Arnold et al.", width / 2)):
        style = block["E1_answering_style"]
        autism = [style[key]["floor"]["autism_pct"] for key, _ in SENSES]
        comparison = [style[key]["floor"]["comparison_pct"] for key, _ in SENSES]
        right.bar(positions + shift, autism, width - 0.04, color=colour, label=f"{label}, autism")
        right.scatter(positions + shift, comparison, s=18, color="white", edgecolor=INK, linewidth=0.9, zorder=3,
                      label="Comparison group" if colour == NEW else None)
    right.set_xticks(positions, [name for _, name in SENSES], rotation=30, ha="right")
    right.set_ylim(0, 16)
    right.set_ylabel("No imagery in that sense (%)")
    right.grid(axis="y", color=GRID, linewidth=0.6)
    right.set_axisbelow(True)
    right.legend(frameon=False, fontsize=7.5, loc="upper right")
    right.set_title("B. How often imagery is absent", loc="left", fontsize=9, color=INK)

    for axis in (left, right):
        axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        fig.savefig(RESULTS / f"p5_figure_tails.{suffix}", dpi=300)
    print(RESULTS / "p5_figure_tails.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
