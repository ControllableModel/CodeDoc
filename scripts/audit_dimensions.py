"""Dimension discrimination audit + aggregation sensitivity (reviewer items).

Uses only archived evidence under ``results/per-repository`` — no model calls.

Answers three review comments at once:

* "results are almost entirely aggregated"  -> per-dimension mean/sd table
* "averaging assumes equal weights / one dimension" -> aggregation sensitivity
* "which 8 dimensions?"                      -> explicit dimension inventory,
  including which dimensions never vary on code-level artifacts (and therefore
  dilute both the absolute score and any masking effect).

Usage::

    python scripts/audit_dimensions.py
    python scripts/audit_dimensions.py --root results/per-repository --out results/analysis
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.config import RESULTS  # noqa: E402
from codedoc.criteria import registry  # noqa: E402
from codedoc.judge import aggregate, stats  # noqa: E402

#: A dimension whose scores barely move carries no discriminative information.
SD_EPS = 0.05


def load_records(root: Path, suffix: str) -> dict:
    return {
        path.relative_to(root).as_posix(): aggregate.load_quality_record(path)
        for path in sorted(root.rglob(f"*quality{suffix}.jsonl"))
    }


def dimension_table(records: dict) -> list:
    by_dim: dict = {}
    for scores in records.values():
        for name, value in scores.items():
            by_dim.setdefault(name, []).append(value)
    rows = []
    for name, values in by_dim.items():
        d = stats.describe(values)
        rows.append(
            {
                "dimension": name,
                "n": d["n"],
                "mean": round(d["mean"], 3),
                "sd": round(d["sd"], 3),
                "min": d["min"],
                "max": d["max"],
                "discriminative": d["sd"] > SD_EPS,
            }
        )
    return sorted(rows, key=lambda r: (-r["sd"], r["dimension"]))


def category_groups(set_name: str) -> dict:
    cs = registry.load(set_name)
    return {cat: [c.name for c in criteria] for cat, criteria in cs.by_category().items()}


def sensitivity_table(records: dict) -> dict:
    groups = category_groups("iso_26514")
    dims = sorted({d for scores in records.values() for d in scores})
    boosted = ("Correctness", "Completeness", "Conciseness")

    def usable(scores):
        return {k: v for k, v in scores.items() if k in dims}

    schemes = {
        "flat_mean(all dimensions)": lambda s: aggregate.flat_mean(s),
        "category_balanced": lambda s: aggregate.category_balanced(s, groups),
        "weighted(correctness x2)": lambda s: aggregate.weighted(
            s, aggregate.boost_weights(dims, boosted, 2.0)
        ),
    }
    # Restricted scheme: drop dimensions that never vary, if any were detected.
    degenerate = [r["dimension"] for r in dimension_table(records) if not r["discriminative"]]
    if degenerate:
        keep = [d for d in dims if d not in degenerate]
        schemes["flat_mean(discriminative only)"] = lambda s: aggregate.flat_mean(s, keep)

    result = aggregate.sensitivity(records, {k: (lambda fn: (lambda s: fn(usable(s))))(v)
                                             for k, v in schemes.items()})
    summary = aggregate.spread(result)
    return {"per_record": result, "degenerate_dimensions": degenerate, "summary": summary}


def to_markdown(dim_rows: list, sens: dict) -> str:
    lines = ["# Dimension audit (archived evidence)", ""]
    lines.append("## Per-dimension distribution")
    lines.append("")
    lines.append("| Dimension | n | mean | sd | min | max | discriminative |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in dim_rows:
        lines.append(
            f"| {r['dimension']} | {r['n']} | {r['mean']} | {r['sd']} | {r['min']} | "
            f"{r['max']} | {'yes' if r['discriminative'] else '**no**'} |"
        )
    degenerate = sens["degenerate_dimensions"]
    lines += ["", f"Dimensions with sd <= {SD_EPS}: **{len(degenerate)}**", ""]
    if degenerate:
        lines.append("> These dimensions do not separate methods on code-level artifacts, "
                     "so they dilute any mean and any masking-effect measurement.")
        lines.append("")
        lines.append(", ".join(f"`{d}`" for d in degenerate))
    lines += ["", "## Aggregation sensitivity", ""]
    summary = sens["summary"]
    if summary:
        means = summary["means"]  # type: ignore[index]
        lines.append("| Aggregation | mean score |")
        lines.append("|---|---|")
        for name, value in means.items():
            lines.append(f"| {name} | {value:.3f} |")
        lines += ["", f"Range across schemes: **{summary['range']:.3f}**", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(RESULTS / "per-repository"))
    ap.add_argument("--out", default=str(RESULTS / "analysis"))
    args = ap.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"No archived evidence found at {root}", file=sys.stderr)
        return 1
    records = load_records(root, "")
    if not records:
        print(f"No *quality.jsonl files under {root}", file=sys.stderr)
        return 1

    rows = dimension_table(records)
    sens = sensitivity_table(records)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "dimension_audit.json").write_text(
        json.dumps({"dimensions": rows, "sensitivity": sens}, indent=2), encoding="utf-8"
    )
    md = to_markdown(rows, sens)
    (out / "dimension_audit.md").write_text(md + "\n", encoding="utf-8")
    print(md)
    print(f"\nwritten: {out/'dimension_audit.md'}, {out/'dimension_audit.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
