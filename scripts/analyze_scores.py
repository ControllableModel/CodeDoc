"""Analyse judge scores, excluding criterion/entity-kind pairs that cannot apply.

Why this script exists
----------------------
Scoring every entity on every entity-level criterion mixes a quality signal with a
rubric artefact. In the first full-corpus run, free functions scored 1.78 on
``Inheritance/Polymorphism Contract`` — a property a free function cannot have. The
judge reads "not mentioned" as "absent and therefore bad", so the number measured
the rubric, not the document, and it dragged down every function mean.

Two views are reported side by side:

``raw``       every verdict the judge produced (what the earlier numbers used)
``filtered``  verdicts for (criterion, kind) pairs the criterion declares applicable

The difference between the two columns *is* the artefact, and reporting both keeps
the change auditable rather than silently rewriting history.

Usage::

    python scripts/analyze_scores.py --scores outputs/bench_flask/scores.json --repo flask-main
    python scripts/analyze_scores.py --scores outputs/bench_flask/scores.json --repo flask-main --csv
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.config import TARGETS  # noqa: E402
from codedoc.criteria import registry  # noqa: E402

KINDS = ("class", "method", "function")


def load_kind_map(repo: str) -> Dict[str, str]:
    """Map qualified entity name -> entity kind, plus the stem form used in filenames."""
    from codedoc.deps.relations_index import build_index

    index = build_index(str(TARGETS / repo))
    if index is None:
        return {}
    mapping: Dict[str, str] = {}
    for ctx in index.contexts:
        mapping[ctx.entity.qualified_name] = str(ctx.entity.kind)
    return mapping


def _score_of(payload) -> Optional[int]:
    value = payload.get("judge") if isinstance(payload, dict) else payload
    try:
        return int(str(value).strip())
    except Exception:  # noqa: BLE001 - the judge occasionally emits "4/5" or prose
        return None


def collect(
    scores: Dict[str, Dict[str, dict]],
    kind_map: Dict[str, str],
    criteria_set,
    filtered: bool,
) -> Dict[str, List[int]]:
    """Gather scores per dimension, optionally dropping non-applicable pairs."""
    by_dim: Dict[str, List[int]] = {}
    for qname, verdicts in scores.items():
        kind = kind_map.get(qname)
        applicable = None if criteria_set is None else {
            c.name for c in criteria_set.for_kind(kind)
        }
        for dim, payload in (verdicts or {}).items():
            if filtered and applicable is not None and dim not in applicable:
                continue
            value = _score_of(payload)
            if value is not None:
                by_dim.setdefault(dim, []).append(value)
    return by_dim


def mean(values: List[int]) -> float:
    return statistics.mean(values) if values else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scores", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--criteria", default="practice_docstring")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    scores = json.loads(Path(args.scores).read_text(encoding="utf-8"))
    kind_map = load_kind_map(args.repo)
    if not kind_map:
        print(f"cannot infer entity kinds for {args.repo}", file=sys.stderr)
        return 1
    criteria_set = registry.load(args.criteria)

    missing = [q for q in scores if q not in kind_map]
    empty = [q for q, v in scores.items() if not v]

    print(f"documents scored : {len(scores)}")
    print(f"unscored (empty) : {len(empty)}")
    if missing:
        print(f"no kind for       : {len(missing)} (e.g. {missing[0]})")
    counts = {k: sum(1 for q in scores if kind_map.get(q) == k) for k in KINDS}
    print(f"entity kinds     : " + ", ".join(f"{k}={v}" for k, v in counts.items()))

    # ---- applicability audit -------------------------------------------------
    print()
    print("APPLICABILITY AUDIT (entity-level criteria per kind)")
    print("-" * 78)
    print(f"{'criterion':<40}{'class':>8}{'method':>9}{'function':>10}")
    print("-" * 78)
    for criterion in criteria_set.entity_level():
        marks = ["yes" if criterion.applies_to(k) else "N/A" for k in KINDS]
        name = criterion.name[:38]
        print(f"{name:<40}{marks[0]:>8}{marks[1]:>9}{marks[2]:>10}")

    # ---- raw vs filtered -----------------------------------------------------
    raw_all = collect(scores, kind_map, criteria_set, filtered=False)
    filtered_all = collect(scores, kind_map, criteria_set, filtered=True)
    raw_by_kind = {
        k: collect({q: v for q, v in scores.items() if kind_map.get(q) == k},
                   kind_map, criteria_set, filtered=False)
        for k in KINDS
    }
    filtered_by_kind = {
        k: collect({q: v for q, v in scores.items() if kind_map.get(q) == k},
                   kind_map, criteria_set, filtered=True)
        for k in KINDS
    }

    print()
    print("PER-DIMENSION MEANS: raw vs applicability-filtered")
    print("-" * 96)
    print(f"{'dimension':<38}{'raw':>8}{'filt':>8}{'Δ':>7}"
          f"{'class':>8}{'method':>8}{'function':>9}")
    print("-" * 96)
    for dim in sorted(raw_all, key=lambda d: -mean(raw_all[d])):
        r, f = mean(raw_all[dim]), mean(filtered_all.get(dim, []))
        row = [mean(filtered_by_kind[k].get(dim, [])) for k in KINDS]
        delta = f - r if (r == r and f == f) else float("nan")
        cells = "".join(
            f"{c:>9.2f}" if c == c else f"{'—':>9}" for c in row
        )
        print(f"{dim[:36]:<38}{r:>8.2f}{f:>8.2f}{delta:>7.2f}{cells[:8]}{cells[8:]}")
    print("-" * 96)

    raw_flat = [v for dim in raw_all.values() for v in dim]
    filt_flat = [v for dim in filtered_all.values() for v in dim]
    print(f"{'ALL (pooled)':<38}{mean(raw_flat):>8.2f}{mean(filt_flat):>8.2f}"
          f"{mean(filt_flat) - mean(raw_flat):>7.2f}")
    print()
    print(f"{'mean per kind':<38}{'':>8}{'':>8}{'':>7}"
          f"{mean([v for d in filtered_by_kind['class'].values() for v in d]):>8.2f}"
          f"{mean([v for d in filtered_by_kind['method'].values() for v in d]):>8.2f}"
          f"{mean([v for d in filtered_by_kind['function'].values() for v in d]):>9.2f}")
    print("-" * 96)
    print(f"verdicts: raw={len(raw_flat)}  filtered={len(filt_flat)}  "
          f"excluded={len(raw_flat) - len(filt_flat)}")

    if args.json_out:
        payload = {
            "repo": args.repo,
            "criteria": args.criteria,
            "documents": len(scores),
            "unscored": len(empty),
            "kinds": counts,
            "raw": {d: {"n": len(v), "mean": mean(v)} for d, v in raw_all.items()},
            "filtered": {d: {"n": len(v), "mean": mean(v)} for d, v in filtered_all.items()},
            "filtered_by_kind": {
                k: {d: {"n": len(v), "mean": mean(v)} for d, v in dims.items()}
                for k, dims in filtered_by_kind.items()
            },
            "excluded_verdicts": len(raw_flat) - len(filt_flat),
        }
        Path(args.json_out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"written: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
