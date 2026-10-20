"""Build the RQ2 comparison table: CodeDoc against the RepoAgent baseline.

Reads the two aggregate score files produced by scripts/judge_matrix.py and writes one
document with the pair-wise comparison the paper needs:

* per rubric, overall means for each method;
* per rubric and per main dimension, the gap;
* per repository, so a single unusual repository is visible rather than averaged away;
* per entity kind.

Scores are only comparable within a rubric: CodeDoc and RepoAgent are graded by the same
judge and the same rubric, but their documents are generated differently, and the ISO and
GitHub rubrics score different dimension sets.

Usage::

    python scripts/compare_methods.py
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "results" / "analysis"

METHODS = [
    ("codoc", ANALYSIS / "matrix_scores.json", "CodeDoc (this work)"),
    ("repoagent", ANALYSIS / "matrix_scores_repoagent.json", "RepoAgent"),
]

AXIS_LABEL = {
    "iso_26514": "ISO/IEC 26514 (entity-level dimensions)",
    "github_docs_style": "GitHub docs style (full set)",
}


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    return {row["axis"]: row for row in payload}


def main() -> int:
    loaded = [(key, load(path), label) for key, path, label in METHODS]
    missing = [label for key, data, label in loaded if not data]
    if missing:
        print(f"missing score files for: {', '.join(missing)}; run the judges first")
    available = [(key, data, label) for key, data, label in loaded if data]
    if len(available) < 2:
        print("need at least two methods to compare")
        return 2

    axes = sorted({axis for key, data, label in available for axis in data})
    lines = [
        "# RQ2 comparison: CodeDoc against RepoAgent",
        "",
        "Both methods are scored by the same judge under the same rubric; each rubric's",
        "own dimension set is used, so ISO and GitHub numbers must not be compared with",
        "each other.",
        "",
    ]

    for axis in axes:
        rows = []
        for key, data, label in available:
            row = data.get(axis)
            if row:
                rows.append((key, label, row))
        if len(rows) < 2:
            continue
        lines += [f"## {AXIS_LABEL.get(axis, axis)}", ""]
        lines += ["| method | documents | dimensions | overall mean |",
                  "|---|---|---|---|"]
        for key, label, row in rows:
            lines.append(f"| {label} | {row['documents']} | {row['dimensions_asked']} "
                         f"| {row['overall_mean']} |")
        best = max(rows, key=lambda r: r[2]["overall_mean"] or 0)
        worst = min(rows, key=lambda r: r[2]["overall_mean"] or 0)
        if best[0] != worst[0] and worst[2]["overall_mean"]:
            gap = best[2]["overall_mean"] - worst[2]["overall_mean"]
            lines += ["", f"* {best[1]} leads {worst[1]} by {gap:+.2f} overall "
                          f"({gap / worst[2]['overall_mean'] * 100:+.1f}%)."]

        # main dimensions
        category_scores: dict = {}
        for key, label, row in rows:
            for entry in row["main_dimensions"]:
                category_scores.setdefault(entry["category"], {})[label] = entry["mean_of_dimension_means"]
        labels = [label for key, label, row in rows]
        lines += ["", "| main dimension | " + " | ".join(labels) + " | gap |",
                  "|---|" + "---|" * len(labels) + "---|"]
        for category, scores in sorted(category_scores.items(),
                                       key=lambda kv: -(kv[1].get(labels[0]) or 0)):
            values = [scores.get(label) for label in labels]
            gap = ""
            present = [v for v in values if v is not None]
            if len(present) == 2:
                gap = f"{present[0] - present[1]:+.2f}"
            for index, value in enumerate(values):
                if value is None:
                    values[index] = "—"
                else:
                    values[index] = f"{value:.2f}"
            lines.append(f"| {category} | " + " | ".join(values) + f" | {gap} |")

        # per repository
        repos = sorted({repo for key, label, row in rows for repo in row["per_repo"]})
        lines += ["", "| repository | " + " | ".join(labels) + " | gap |",
                  "|---|" + "---|" * len(labels) + "---|"]
        for repo in repos:
            values = [row["per_repo"].get(repo, {}).get("mean") for key, label, row in rows]
            gap = ""
            present = [v for v in values if v is not None]
            if len(present) == 2:
                gap = f"{present[0] - present[1]:+.2f}"
            rendered = [("—" if v is None else f"{v:.2f}") for v in values]
            lines.append(f"| {repo} | " + " | ".join(rendered) + f" | {gap} |")

        # per entity kind
        kinds = sorted({kind for key, label, row in rows for kind in row.get("per_kind", {})})
        if kinds:
            lines += ["", "| kind | " + " | ".join(labels) + " | gap |",
                      "|---|" + "---|" * len(labels) + "---|"]
            for kind in kinds:
                values = [row.get("per_kind", {}).get(kind, {}).get("mean")
                          for key, label, row in rows]
                gap = ""
                present = [v for v in values if v is not None]
                if len(present) == 2:
                    gap = f"{present[0] - present[1]:+.2f}"
                rendered = [("—" if v is None else f"{v:.2f}") for v in values]
                lines.append(f"| {kind} | " + " | ".join(rendered) + f" | {gap} |")
        lines.append("")

    out = ANALYSIS / "rq2_comparison.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:60]))
    print(f"\nwritten: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
