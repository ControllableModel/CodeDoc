"""Redraw the criterion-sensitivity figure from the original study's numbers.

No experiment is re-run: the values below are read off the data annotations of the
original ``figures/criterion_sensitivity.pdf``, and their internal consistency is checked
before anything is drawn (the panel-(b) decline must equal the panel-(a) drop relative to
the unmasked score). If that check fails the script stops, so the figure cannot silently
drift from the study it reports.

Original figure specification, measured from its vector geometry and text spans:

* canvas 6.09 x 2.60 in, two panels
* panel (a): x = 0/20/40/60 % categorical, y 2.0-4.5 step 0.5
* panel (b): x = 20/40/60 %, y 0-35 step 5
* two series, teal #2A9D8C and brick #E97051, line width 2.0, round markers
* value annotations above each point, 7.5 pt
* legend inside the axes, 8.5 pt, no frame: lower-left in (a), upper-left in (b)
* grid #B0B0B0, only left and bottom spines, panel captions 10 pt below the axes

Output: figures/criterion_sensitivity_new.pdf (original left untouched)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PAPER = Path(r"D:\临时下载位置\Standards_Guided_and_Dependency_Aware_Code_Level_Documentation_Generation")

#: Scores at 0/20/40/60 % masking, from the annotations of the original figure.
SCORES = {
    "ISO": [4.20, 3.81, 3.55, 2.91],
    "GitHub": [4.10, 3.74, 3.65, 3.18],
}
#: Relative decline reported by the original panel (b), kept for the cross-check.
REPORTED_DECLINE = {
    "ISO": {20: 9.3, 40: 15.5, 60: 30.8},
    "GitHub": {20: 8.7, 40: 11.0, 60: 22.4},
}
COLOURS = {"ISO": "#2A9D8C", "GitHub": "#E97051"}
RATIOS = [0, 20, 40, 60]
GRID = "#B0B0B0"
MARKER_PT = 6.75
_MARKER_CAL = 1.25          # same calibration as the cost-quality figure


def marker_area(diameter_pt: float) -> float:
    return _MARKER_CAL * 3.14159 * (diameter_pt / 2.0) ** 2


def decline(series):
    base = series[0]
    return {r: (base - v) / base * 100.0 for r, v in zip(RATIOS, series) if r}


def verify():
    """The two panels of the original must describe the same numbers."""
    problems = []
    for name, series in SCORES.items():
        derived = decline(series)
        for ratio, reported in REPORTED_DECLINE[name].items():
            if abs(derived[ratio] - reported) > 0.25:
                problems.append(f"{name} {ratio}%: 图中标注 {reported}% vs 由分数推出 {derived[ratio]:.1f}%")
    if problems:
        raise SystemExit("原始图自相矛盾，停止绘制：\n  " + "\n  ".join(problems))
    print("  自洽性检查通过：面板(b) 与面板(a) 一致")


def style(ax):
    ax.yaxis.grid(True, color=GRID, linewidth=0.5)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(labelsize=8.5, width=0.8, length=3)


def main():
    verify()
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "mathtext.fontset": "dejavuserif",
        "pdf.fonttype": 42,
    })
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(6.09, 2.60))

    for name, series in SCORES.items():
        ax_a.plot(RATIOS, series, "-o", color=COLOURS[name], linewidth=2.0,
                  markersize=2 * 3.375, markerfacecolor=COLOURS[name],
                  markeredgecolor=COLOURS[name], label=name)
    for name, series in SCORES.items():
        for x, y in zip(RATIOS, series):
            ax_a.annotate(f"{y:.2f}", (x, y), textcoords="offset points", xytext=(0, 7),
                          ha="center", fontsize=7.5, color="#222222")
    ax_a.set_xticks(RATIOS)
    ax_a.set_xticklabels([f"{r}%" for r in RATIOS])
    ax_a.set_xlim(-12, 72)
    ax_a.set_ylim(2.0, 4.5)
    ax_a.set_yticks([2.0, 2.5, 3.0, 3.5, 4.0, 4.5])
    ax_a.set_xlabel("Content Masking Ratio", fontsize=9)
    ax_a.set_ylabel("Average Score (1-5)", fontsize=9)
    ax_a.legend(loc="lower left", bbox_to_anchor=(0.06, 0.10), frameon=False, fontsize=8.5,
                handletextpad=0.5, labelspacing=0.35)
    style(ax_a)

    for name, series in SCORES.items():
        d = decline(series)
        xs = sorted(d)
        ys = [d[x] for x in xs]
        ax_b.plot(xs, ys, "-o", color=COLOURS[name], linewidth=2.0,
                  markersize=2 * 3.375, markerfacecolor=COLOURS[name],
                  markeredgecolor=COLOURS[name], label=name)
        # annotate the percentage the original study reports, so the figure text stays
        # identical to the published claim; the derived value is checked in verify()
        for x, y in zip(xs, ys):
            shown = REPORTED_DECLINE[name][x]
            ax_b.annotate(f"{shown:.1f}%", (x, y), textcoords="offset points", xytext=(0, 7),
                          ha="center", fontsize=7.5, color="#222222")
    ax_b.set_xticks([20, 40, 60])
    ax_b.set_xticklabels(["20%", "40%", "60%"])
    ax_b.set_xlim(12, 68)
    ax_b.set_ylim(0, 35)
    ax_b.set_yticks([0, 5, 10, 15, 20, 25, 30, 35])
    ax_b.set_xlabel("Content Masking Ratio", fontsize=9)
    ax_b.set_ylabel("Relative Score Decline (%)", fontsize=9)
    ax_b.legend(loc="upper left", bbox_to_anchor=(0.10, 0.97), frameon=False, fontsize=8.5,
                handletextpad=0.5, labelspacing=0.35)
    style(ax_b)

    fig.subplots_adjust(left=0.085, right=0.99, top=0.97, bottom=0.27, wspace=0.30)
    for ax, caption in ((ax_a, "(a) Score vs. masking ratio"),
                        (ax_b, "(b) Relative score decline")):
        box = ax.get_position()
        fig.text((box.x0 + box.x1) / 2.0, 0.035, caption, ha="center", va="bottom", fontsize=10)

    out = PAPER / "figures" / "criterion_sensitivity_new.pdf"
    fig.savefig(out)
    fig.savefig(out.with_suffix(".png"), dpi=300)
    print(f"  写出 {out}")
    print(f"  写出 {out.with_suffix('.png')}")
    for name, series in SCORES.items():
        d = decline(series)
        print(f"  {name}: 分数 {series} → 降幅 " +
              ", ".join(f"{k}%:{v:.1f}%" for k, v in sorted(d.items())))


if __name__ == "__main__":
    main()
