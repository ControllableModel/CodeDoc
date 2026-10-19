"""Benchmark the dependency backends across the evaluated repositories.

Produces the table the paper needs for the dependency layer: per repository, how
many classes/methods/functions exist, how many relation instances each backend
recovers, and how much of the call graph is resolved to a project entity versus
left external. Numbers are measured, never assumed.

Usage::

    python scripts/benchmark_dependencies.py                     # all repositories
    python scripts/benchmark_dependencies.py --repos flask-main numpy
    python scripts/benchmark_dependencies.py --backend pyright --budget 400
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.config import RESULTS, TARGETS  # noqa: E402
from codedoc.deps.schema import RelationKind  # noqa: E402

DEFAULT_REPOS = [
    "numpy", "openui", "ragflow", "dify_api", "flask-main",
    "joblib", "pyro", "fairseq", "sonnet", "torch",
]
RELATION_ORDER = [
    RelationKind.INHERITS, RelationKind.SUBCLASSED_BY, RelationKind.INSTANTIATED_AT,
    RelationKind.OVERRIDES, RelationKind.OVERRIDDEN_BY, RelationKind.DISPATCH_CANDIDATES,
    RelationKind.CALLS, RelationKind.CALLED_BY,
]


def count_relations(contexts) -> dict:
    counts = {kind: 0 for kind in RelationKind.ALL}
    for ctx in contexts:
        for kind, relations in ctx.relations.items():
            counts[kind] = counts.get(kind, 0) + len(relations)
    return counts


def run_backend(backend: str, repo: str, budget, timeout: float) -> dict:
    if backend == "ast":
        from codedoc.deps.languages.python_ast import PythonAstExtractor as Impl
        extractor = Impl()
    elif backend == "pyright":
        from codedoc.deps.languages.python_pyright import PythonPyrightExtractor as Impl
        extractor = Impl(timeout=timeout, max_entities=budget)
    else:
        raise ValueError(backend)

    root = TARGETS / repo
    record: dict = {"repo": repo, "backend": backend}
    started = time.time()
    try:
        record["measure"] = extractor.measure(str(root))
        contexts = extractor.extract(str(root))
        record["elapsed_s"] = round(time.time() - started, 1)
        record["contexts"] = len(contexts)
        record["relations"] = count_relations(contexts)
        stats = getattr(extractor, "stats", None)
        if stats:
            stats = dict(stats)
            internal = record["relations"].get(RelationKind.CALLS, 0)
            external = stats.get("external_calls", 0)
            total = internal + external
            record["call_resolution"] = round(internal / total, 3) if total else None
            record["stats"] = stats
        if backend == "ast":
            record["coverage"] = extractor.coverage_report(str(root))
    except Exception as exc:  # noqa: BLE001 - report, never abort the sweep
        record["elapsed_s"] = round(time.time() - started, 1)
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc(limit=3)
    return record


def to_markdown(records: list) -> str:
    lines = ["# Dependency-backend benchmark", ""]
    header = (
        "| repo | backend | files | classes | methods | functions | inherits | subclassed_by | "
        "instantiated_at | overrides | dispatch | calls (internal) | call resolution | sec |"
    )
    lines += [header, "|" + "---|" * 13]
    for rec in records:
        if "error" in rec:
            lines.append(f"| {rec['repo']} | {rec['backend']} | — | — | — | — | — | — | — | — | — | — | — | {rec.get('elapsed_s','—')} |")
            continue
        m = rec["measure"]
        rel = rec["relations"]
        res = rec.get("call_resolution")
        lines.append(
            f"| {rec['repo']} | {rec['backend']} | {m.get('files','—')} | {m.get('classes','—')} | "
            f"{m.get('methods','—')} | {m.get('functions','—')} | {rel.get(RelationKind.INHERITS,0)} | "
            f"{rel.get(RelationKind.SUBCLASSED_BY,0)} | {rel.get(RelationKind.INSTANTIATED_AT,0)} | "
            f"{rel.get(RelationKind.OVERRIDES,0)} | {rel.get(RelationKind.DISPATCH_CANDIDATES,0)} | "
            f"{rel.get(RelationKind.CALLS,0)} | "
            f"{(f'{res:.0%}' if isinstance(res, float) else '—')} | {rec['elapsed_s']} |"
        )
    errors = [r for r in records if "error" in r]
    lines += ["", "## Failures", ""]
    if errors:
        for rec in errors:
            lines.append(f"* **{rec['repo']} / {rec['backend']}**: `{rec['error']}`")
    else:
        lines.append("None — every repository produced dependency contexts.")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", nargs="*", default=None)
    ap.add_argument("--backend", choices=["ast", "pyright", "both"], default="both")
    ap.add_argument("--budget", type=int, default=None,
                    help="cap on entities queried per repository (pyright only)")
    ap.add_argument("--timeout", type=float, default=25.0)
    ap.add_argument("--out", default=str(RESULTS / "analysis"))
    args = ap.parse_args()

    repos = args.repos or DEFAULT_REPOS
    backends = ["ast", "pyright"] if args.backend == "both" else [args.backend]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    records = []
    print(f"{'repo':<12}{'backend':<10}{'entities':>9}{'calls':>8}{'res%':>7}{'sec':>7}")
    print("-" * 53)
    for repo in repos:
        if not (TARGETS / repo).exists():
            print(f"{repo:<12}missing under targets/")
            continue
        for backend in backends:
            rec = run_backend(backend, repo, args.budget, args.timeout)
            records.append(rec)
            if "error" in rec:
                print(f"{repo:<12}{backend:<10}  FAIL {rec['error'][:40]}")
            else:
                res = rec.get("call_resolution")
                print(f"{repo:<12}{backend:<10}{rec['contexts']:>9}{rec['relations'].get(RelationKind.CALLS,0):>8}"
                      f"{(f'{res:.0%}' if isinstance(res,float) else '—'):>7}{rec['elapsed_s']:>7}")
            sys.stdout.flush()

    (out_dir / "dependency_backends.json").write_text(
        json.dumps(records, indent=2), encoding="utf-8")
    md = to_markdown(records)
    (out_dir / "dependency_backends.md").write_text(md + "\n", encoding="utf-8")
    print(f"\nwritten: {out_dir/'dependency_backends.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
