"""Same-sample comparison of the AST and Pyright dependency backends.

Why a dedicated harness
-----------------------
The earlier sweep (`benchmark_dependencies.py`) reported an AST call *count* and a
Pyright call *resolution rate*, measured over different entity sets — a 250-entity
sample versus the whole repository. Those numbers cannot be compared, and comparing
them would overstate whichever backend happens to be measured on the easier set.

This harness removes the confound: both backends are asked about **the same
entity sample** in the same repository, and both report the same metric.

Metric
------
``internal call resolution rate`` = internal calls / all call sites seen in the
sample entities. A call counts as internal when it resolves to an entity declared
in the repository; builtins, standard library and third-party calls are external
for both backends. Precision is *not* measured here — that needs ground truth and
is a separate annotation study.

Usage::

    python scripts/benchmark_ast_vs_pyright.py --repos flask-main openui joblib
    python scripts/benchmark_ast_vs_pyright.py --all --sample 100
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.config import RESULTS, TARGETS  # noqa: E402
from codedoc.deps.schema import EntityKind  # noqa: E402

DEFAULT_REPOS = ["flask-main", "openui", "joblib", "sonnet", "pyro", "ragflow", "numpy", "fairseq", "dify_api", "torch"]


def ast_pass(repo: str, sample_size: int, seed: int) -> dict:
    """Resolution statistics and timing for the AST backend."""
    from codedoc.deps.languages.python_ast import PythonAstExtractor

    started = time.time()
    extractor = PythonAstExtractor()
    index = extractor._build(str(TARGETS / repo))  # noqa: SLF001 - benchmark harness
    build_seconds = time.time() - started

    functions = [(q, f) for q, f in index.functions.items()
                 if f.kind in (EntityKind.FUNCTION, EntityKind.METHOD)]
    functions.sort(key=lambda item: item[0])
    rng = random.Random(seed)
    sample = rng.sample(functions, min(sample_size, len(functions)))

    resolved = unresolved = 0
    for _qname, info in sample:
        resolved += len(info.calls)
        unresolved += info.unresolved

    total = resolved + unresolved
    declared_bases = sum(len(c.bases_raw) for c in index.classes.values())
    resolved_bases = declared_bases - len(index.unresolved_bases)
    return {
        "backend": "ast",
        "build_seconds": round(build_seconds, 2),
        "n_sample": len(sample),
        "calls_total": total,
        "calls_internal": resolved,
        "call_resolution": round(resolved / total, 4) if total else None,
        "bases_declared": declared_bases,
        "bases_internal": resolved_bases,
        "base_resolution": round(resolved_bases / declared_bases, 4) if declared_bases else None,
        "classes": len(index.classes),
        "entities": len(index.functions),
    }


def pyright_pass(repo: str, sample_qnames, seed: int) -> dict:
    """Resolution statistics and timing for the Pyright backend, same entities."""
    from codedoc.deps.languages.python_pyright import PythonPyrightExtractor

    extractor = PythonPyrightExtractor(timeout=30.0)
    index = extractor._prepare(str(TARGETS / repo))  # noqa: SLF001
    root = Path(TARGETS / repo).resolve()

    internal = external = 0
    queried = 0
    started = time.time()
    client = extractor._client(str(TARGETS / repo))  # noqa: SLF001
    client.start()
    try:
        for qname in sample_qnames:
            info = index.functions.get(qname)
            if info is None:
                continue
            column = extractor._name_column(info.path, info.lineno, info.name)  # noqa: SLF001
            items = client.prepare_call_hierarchy(info.path, info.lineno, column)
            if not items:
                continue
            queried += 1
            for call in client.outgoing_calls(items[0]):
                target = call.get("to", {})
                resolved = extractor._entity_of_item(target, root, str(TARGETS / repo))  # noqa: SLF001
                if resolved:
                    internal += 1
                else:
                    external += 1
    finally:
        client.stop()
    elapsed = time.time() - started

    total = internal + external
    return {
        "backend": "pyright",
        "query_seconds": round(elapsed, 2),
        "n_sample": queried,
        "calls_total": total,
        "calls_internal": internal,
        "call_resolution": round(internal / total, 4) if total else None,
        "seconds_per_entity": round(elapsed / queried, 3) if queried else None,
        "lsp_requests": client.n_requests,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", nargs="*", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--sample", type=int, default=100)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(RESULTS / "analysis"))
    args = ap.parse_args()

    repos = DEFAULT_REPOS if (args.all or not args.repos) else args.repos
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    records = []
    print(f"sample={args.sample} entities/repo, seed={args.seed}")
    header = (f"{'repo':<12}{'n':>5}{'AST rate':>10}{'AST build':>11}"
              f"{'PR rate':>9}{'PR query':>10}{'PR s/ent':>10}{'calls A/PR':>12}")
    print(header)
    print("-" * len(header))

    for repo in repos:
        if not (TARGETS / repo).exists():
            print(f"{repo:<12} missing")
            continue
        record: dict = {"repo": repo}
        try:
            ast_stats = ast_pass(repo, args.sample, args.seed)
            record["ast"] = ast_stats

            # identical entity sample for the pyright pass
            from codedoc.deps.languages.python_ast import PythonAstExtractor

            idx = PythonAstExtractor()._build(str(TARGETS / repo))  # noqa: SLF001
            names = sorted(q for q, f in idx.functions.items()
                           if f.kind in (EntityKind.FUNCTION, EntityKind.METHOD))
            rng = random.Random(args.seed)
            sample_names = [q for q, _ in rng.sample(
                [(q, idx.functions[q]) for q in names], min(args.sample, len(names)))]

            pr_stats = pyright_pass(repo, sample_names, args.seed)
            record["pyright"] = pr_stats
            records.append(record)

            ast_rate = ast_stats["call_resolution"]
            pr_rate = pr_stats["call_resolution"]
            print(f"{repo:<12}{ast_stats['n_sample']:>5}"
                  f"{(f'{ast_rate:.1%}' if ast_rate is not None else '-'):>10}"
                  f"{ast_stats['build_seconds']:>11}"
                  f"{(f'{pr_rate:.1%}' if pr_rate is not None else '-'):>9}"
                  f"{pr_stats['query_seconds']:>10}"
                  f"{(pr_stats['seconds_per_entity'] or 0):>10}"
                  f"{ast_stats['calls_total']:>6}/{pr_stats['calls_total']:<6}")
        except Exception as exc:  # noqa: BLE001 - keep sweeping
            record["error"] = f"{type(exc).__name__}: {exc}"
            record["traceback"] = traceback.format_exc(limit=3)
            records.append(record)
            print(f"{repo:<12} FAIL {record['error'][:60]}")
        sys.stdout.flush()

    (out_dir / "ast_vs_pyright.json").write_text(json.dumps(records, indent=2), encoding="utf-8")

    md = ["# AST vs Pyright: same-sample comparison", "",
          "* sample: %d entities per repository, seed %d" % (args.sample, args.seed),
          "* metric: internal call resolution = internal calls / all call sites in the sample",
          "", "| repo | sample | AST rate | AST build (s) | Pyright rate | Pyright query (s) | s/entity |",
          "|---|---|---|---|---|---|---|"]
    for rec in records:
        if "error" in rec:
            md.append("| %s | — | — | — | — | — | — |" % rec["repo"])
            continue
        a, p = rec["ast"], rec["pyright"]
        a_rate = a["call_resolution"]
        p_rate = p["call_resolution"]
        a_txt = "%.1f%%" % (a_rate * 100) if a_rate is not None else "—"
        p_txt = "%.1f%%" % (p_rate * 100) if p_rate is not None else "—"
        md.append(
            "| %s | %d | %s | %s | %s | %s | %s |"
            % (rec["repo"], a["n_sample"], a_txt, a["build_seconds"],
               p_txt, p["query_seconds"], p["seconds_per_entity"])
        )
    (out_dir / "ast_vs_pyright.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nwritten: {out_dir/'ast_vs_pyright.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
