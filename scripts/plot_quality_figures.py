"""Draw the two remaining data figures in the author's plotting style.

Style source: ``analysis.py`` of the author's plotting code -- palette from its
``colors_list``, ``savefig(..., format="pdf", dpi=300)``, serif labels. The canvas keeps the
two-column width of the paper rather than the standalone 10x6 in of that code, because a
wider canvas would overflow the page.

Figures produced
----------------
``figures/quality_categories_new.pdf``
    RQ2: mean score per rubric category, three methods, horizontal grouped bars. Categories
    are the mean of their dimensions, so a category with more dimensions does not dominate.

``figures/human_alignment_new.pdf``
    RQ1.b: human annotators against the two judge configurations. MemDocAgent is absent by
    omission, not by fitting: it was never annotated.
"""
from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"E:\Pycharm_projects\CodeEval")
PAPER = Path(r"D:\临时下载位置\Standards_Guided_and_Dependency_Aware_Code_Level_Documentation_Generation")
FIGDATA = ROOT / "results" / "figure_data"
sys.path.insert(0, str(ROOT))

#: author palette, converted from 0-255 triples
TEAL = "#108B96"
BRICK = "#A64036"
BLUE = "#4182A4"
NAVY = "#12264F"
SLATE = "#354E6B"
GOLD = "#FAC03D"
COLOURS = {"CodeDoc": TEAL, "RepoAgent": BRICK, "MemDocAgent": BLUE}
METHODS = ("CodeDoc", "RepoAgent", "MemDocAgent")

#: human evaluation, from the first submission: (human, judge single, judge per-dimension)
HUMAN = {"RepoAgent": (3.09, 3.24, 3.19), "CodeDoc": (3.61, 3.79, 3.72)}


def category_means(axis_code: str):
    """{method: {category: mean of its dimensions}} from the exported dimension means."""
    try:
        from codedoc.criteria import registry
        criteria = registry.load(axis_code)
        dim_cat = {c.name: c.category for c in criteria}
    except Exception:
        dim_cat = {}
    per = defaultdict(lambda: defaultdict(list))
    path = FIGDATA / f"{'iso' if axis_code.startswith('iso') else 'github'}_dimension_means.csv"
    for row in csv.DictReader(path.open(encoding="utf-8")):
        cat = dim_cat.get(row["dimension"], "Other")
        per[row["method"]][cat].append(float(row["mean_over_repositories"]))
    return {m: {c: statistics.mean(v) for c, v in cats.items()} for m, cats in per.items()}


def plot_categories(axis_code: str, title: str, out: Path) -> None:
    data = category_means(axis_code)
    cats = list(data["CodeDoc"])
    # keep the rubric's own order
    try:
        from codedoc.criteria import registry
        order, seen = [], set()
        for c in registry.load(axis_code):
            if c.category not in seen:
                seen.add(c.category)
                order.append(c.category)
        cats = [c for c in order if c in data["CodeDoc"]]
    except Exception:
        pass
    cats = cats[::-1]                      # bottom-up so the first category sits on top
    height = 0.8 / len(METHODS)

    fig, ax = plt.subplots(figsize=(6.09, 0.34 * len(cats) + 1.15))
    for i, method in enumerate(METHODS):
        vals = [data[method].get(c, float("nan")) for c in cats]
        pos = [y - 0.4 + height * (i + 0.5) for y in range(len(cats))]
        ax.barh(pos, vals, height=height, color=COLOURS[method], label=method,
                edgecolor="white", linewidth=0.4)
    ax.set_yticks(range(len(cats)))
    ax.set_yticklabels(cats, fontsize=7.5)
    ax.set_xlim(1.0, 5.0)
    ax.set_xlabel("Mean score (1--5)", fontsize=8.5)
    ax.xaxis.grid(True, color="#B0B0B0", linewidth=0.4)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.6)
    ax.tick_params(labelsize=8, width=0.6, length=2.5)
    ax.legend(loc="lower right", frameon=False, fontsize=7.5, ncol=1)
    ax.set_title(title, fontsize=9.5, loc="left")
    fig.subplots_adjust(left=0.30, right=0.985, top=0.93, bottom=0.14)
    fig.savefig(out, format="pdf", dpi=300)
    fig.savefig(out.with_suffix(".png"), dpi=300)
    plt.close(fig)
    print(f"  写出 {out}")


def plot_human(out: Path) -> None:
    methods = ["RepoAgent", "CodeDoc"]
    series = [("Human", 0, SLATE), ("Judge (S)", 1, BRICK), ("Judge (M)", 2, BLUE)]
    width = 0.8 / len(series)
    fig, ax = plt.subplots(figsize=(3.2, 2.3))
    for i, (label, idx, colour) in enumerate(series):
        vals = [HUMAN[m][idx] for m in methods]
        pos = [x - 0.4 + width * (i + 0.5) for x in range(len(methods))]
        ax.bar(pos, vals, width=width, color=colour, label=label, edgecolor="white", linewidth=0.4)
        for x, v in zip(pos, vals):
            ax.annotate(f"{v:.2f}", (x, v), textcoords="offset points", xytext=(0, 2),
                        ha="center", fontsize=6.2, color="#222222")
    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels(methods, fontsize=8)
    ax.set_ylim(2.6, 4.0)
    ax.set_ylabel("Score (1--5)", fontsize=8.5)
    ax.yaxis.grid(True, color="#B0B0B0", linewidth=0.4)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.6)
    ax.tick_params(labelsize=8, width=0.6, length=2.5)
    ax.legend(frameon=False, fontsize=7, ncol=3, loc="upper left", handletextpad=0.4,
              columnspacing=0.9)
    fig.subplots_adjust(left=0.16, right=0.985, top=0.93, bottom=0.16)
    fig.savefig(out, format="pdf", dpi=300)
    fig.savefig(out.with_suffix(".png"), dpi=300)
    plt.close(fig)
    print(f"  写出 {out}")


def main() -> int:
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "dejavuserif",
        "pdf.fonttype": 42,
    })
    plot_categories("iso_26514", "(a) ISO rubric, five categories", PAPER / "figures" / "quality_categories_iso_new.pdf")
    plot_categories("github_docs_style", "(b) GitHub rubric, five categories",
                    PAPER / "figures" / "quality_categories_github_new.pdf")
    plot_human(PAPER / "figures" / "human_alignment_new.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
