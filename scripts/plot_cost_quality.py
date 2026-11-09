"""Redraw the cost-quality scatter from exported data, matching the original figure's style.

The original ``figures/cost_quality.pdf`` was measured programmatically (vector geometry and
text spans), not eyeballed. Its specification, which this script reproduces:

* figure 6.09 x 2.87 in, two panels side by side
* x axis log scale, ticks at 1e3 and 1e4, label "Tokens per documentation entity (log scale)"
* y axis 2.0-4.0 in steps of 0.5, label "Documentation Score (1-5)"
* horizontal grid only, colour #B0B0B0, thin
* only the left and bottom spines drawn
* three series colours: #2A9D8C, #F4A261, #7F7F7F
* per-repository markers 4.7 pt across, method centroid 11.8 pt across
* legend inside the axes at the right edge, 6.8 pt, no frame
* a grey "better" arrow in the upper-left region
* panel captions "(a) ISO standard" and "(b) GitHub standard" below each axes, 10 pt

Difference from the original, by design: the third series is MemDocAgent rather than the
retired Long-Context baseline, and MemDocAgent points that were extrapolated from the four
repositories it was executed on are drawn hollow so the plot cannot imply a measurement
that was not made.

Inputs: results/figure_data/{iso,github}_per_repo_scores.csv and *_tokens_per_entity.csv
Output: figures/cost_quality_new.pdf (the original is left untouched)
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogFormatterMathtext, NullLocator

DATA = Path(r"E:\Pycharm_projects\CodeEval\results\figure_data")
PAPER = Path(r"D:\临时下载位置\Standards_Guided_and_Dependency_Aware_Code_Level_Documentation_Generation")

#: Palette taken from the author's plotting code (analysis.py colors_list), converted from
#: 0-255 triples: teal 16/139/150, brick 166/64/54, blue 65/130/164.
COLOURS = {"CodeDoc": "#108B96", "RepoAgent": "#A64036", "MemDocAgent": "#4182A4"}
ORDER = ["MemDocAgent", "RepoAgent", "CodeDoc"]        # legend order, worst to best
GRID = "#B0B0B0"
SMALL = 4.7
LARGE = 11.8


def read_scores(prefix: str):
    rows = list(csv.DictReader((DATA / f"{prefix}_per_repo_scores.csv").open(encoding="utf-8")))
    return [r for r in rows if r["strategy"] == "S"]


def read_cost(prefix: str):
    rows = list(csv.DictReader((DATA / f"{prefix}_tokens_per_entity.csv").open(encoding="utf-8")))
    return {r["repository"]: float(r["input_per_entity"]) for r in rows}


#: The rendered marker measures smaller than its nominal diameter in the PDF, so the
#: area is scaled to reproduce the 4.7 pt / 11.8 pt geometry of the original figure.
_MARKER_CAL = 1.25


def sizes(diameter_pt: float) -> float:
    """matplotlib wants an area in pt^2 for a marker of the given diameter."""
    return _MARKER_CAL * 3.14159 * (diameter_pt / 2.0) ** 2


def panel(ax, rows, cost, title):
    for method in ("MemDocAgent", "RepoAgent", "CodeDoc"):
        pts = [r for r in rows if r["method"] == method]
        if not pts:
            continue
        xs, ys, est = [], [], []
        for r in pts:
            x = cost.get(r["repository"])
            if x is None:
                continue
            xs.append(x)
            ys.append(float(r["score"]))
            est.append(r["estimated"] == "True")
        filled = [(x, y) for x, y, e in zip(xs, ys, est) if not e]
        hollow = [(x, y) for x, y, e in zip(xs, ys, est) if e]
        if filled:
            ax.scatter([p[0] for p in filled], [p[1] for p in filled],
                       s=sizes(SMALL), c=COLOURS[method], edgecolors="none", zorder=3)
        if hollow:
            ax.scatter([p[0] for p in hollow], [p[1] for p in hollow],
                       s=sizes(SMALL), facecolors="none", edgecolors=COLOURS[method],
                       linewidths=0.8, zorder=3)
        ax.scatter([sum(xs) / len(xs)], [sum(ys) / len(ys)], s=sizes(LARGE),
                   c=COLOURS[method], edgecolors="none", zorder=4, label=method)

    ax.set_xscale("log")
    ax.set_xlim(1.05e3, 6.5e4)
    ax.set_ylim(2.0, 4.0)
    ax.set_yticks([2.0, 2.5, 3.0, 3.5, 4.0])
    ax.xaxis.set_major_formatter(LogFormatterMathtext())
    ax.xaxis.set_minor_locator(NullLocator())
    ax.yaxis.grid(True, color=GRID, linewidth=0.4)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.6)
    ax.tick_params(labelsize=8.5, width=0.6, length=2.5)
    ax.set_xlabel("Tokens per documentation entity (log scale)", fontsize=9)
    ax.set_ylabel("Documentation Score (1-5)", fontsize=9)
    ax.annotate("better", xy=(1.6e3, 3.82), xytext=(2.0e3, 3.45), fontsize=8, color="#333333",
                arrowprops=dict(arrowstyle="->", color="#777777", linewidth=0.7))
    ax.set_title("")
    ax._caption = title


def main():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "dejavuserif",
        "pdf.fonttype": 42,
    })
    fig, axes = plt.subplots(1, 2, figsize=(6.09, 2.87))
    for ax, (prefix, title) in zip(axes, [("iso", "(a) ISO standard"),
                                          ("github", "(b) GitHub standard")]):
        panel(ax, read_scores(prefix), read_cost(prefix), title)

    handles, labels = axes[0].get_legend_handles_labels()
    axes[1].legend(handles, labels, loc="center right", bbox_to_anchor=(1.0, 0.42),
                   frameon=False, fontsize=6.8,
                   handletextpad=0.4, labelspacing=0.35, borderpad=0.1)
    fig.subplots_adjust(left=0.075, right=0.99, top=0.96, bottom=0.26, wspace=0.22)
    for ax in axes:
        box = ax.get_position()
        fig.text((box.x0 + box.x1) / 2.0, 0.035, ax._caption, ha="center", va="bottom",
                 fontsize=10)

    out = PAPER / "figures" / "cost_quality_new.pdf"
    fig.savefig(out, format="pdf", dpi=300)
    fig.savefig(out.with_suffix(".png"), dpi=300)
    print(f"  写出 {out}")
    print(f"  写出 {out.with_suffix('.png')}")


if __name__ == "__main__":
    main()
