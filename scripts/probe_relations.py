"""Dependency-extraction probe (experiment step S1).

Prints, for every registered language extractor, which relations it can actually
produce, then runs the implemented ones on a target repository and reports the
counts.  The output is the evidence needed to decide whether a new backend is
required — the published pipeline only produces ``calls``/``called_by``, so class
hierarchy, instantiation sites and override relations show up as missing.

Usage::

    python scripts/probe_relations.py                      # capability matrix only
    python scripts/probe_relations.py --target targets/flask
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.config import TARGETS, resolve_target  # noqa: E402
from codedoc.deps import languages  # noqa: E402
from codedoc.deps.schema import RelationKind  # noqa: E402


def print_matrix() -> None:
    rows = languages.describe()
    print("== Extractor capability matrix ==")
    header = f"{'language':<12}{'backend':<16}{'status':<13}{'supported relations'}"
    print(header)
    print("-" * len(header))
    for row in rows:
        rels = ", ".join(row["supported_relations"]) or "-"
        print(f"{row['language']:<12}{row['backend']:<16}{row['status']:<11}{rels}")
    print()
    print("NOTE: rows with status=skeleton declare an interface but do not return")
    print("relations yet; they are never selected as a language's default backend.")
    print()
    print("== Schema relations not covered by at least one backend ==")
    for kind in RelationKind.ALL:
        done = [f"{r['language']}:{r['backend']}" for r in rows
                if kind in r["supported_relations"] and r["status"] == "implemented"]
        planned = [f"{r['language']}:{r['backend']}" for r in rows
                   if kind in r["supported_relations"] and r["status"] != "implemented"]
        if done:
            state = "implemented by " + ", ".join(done)
        elif planned:
            state = "**not implemented yet** (declared by " + ", ".join(planned) + ")"
        else:
            state = "**UNSUPPORTED BY ANY BACKEND**"
        print(f"  {kind:<22} {state}")
    print()


def probe(target: str) -> dict:
    path = resolve_target(target)
    if not path.exists():
        print(f"[skip] target not found: {path}", file=sys.stderr)
        return {}
    detected = languages.detect(str(path))
    print(f"== Probing {path} ==")
    print(f"languages detected: {detected or 'none'}")
    report: dict = {"target": str(path), "detected": detected, "extractors": {}}
    for language in detected:
        try:
            extractor = languages.get(language)
        except KeyError as exc:
            print(f"  [--] {language}: {exc}")
            continue
        try:
            counts = extractor.measure(str(path))
            print(f"  [ok] {language} ({extractor.backend}): {counts}")
            print(f"       missing relations: {', '.join(extractor.missing_relations()) or 'none'}")
            report["extractors"][language] = {"counts": counts, "ok": True}
        except NotImplementedError as exc:
            print(f"  [--] {language}: not implemented -> {exc}")
            report["extractors"][language] = {"ok": False, "reason": "not implemented"}
        except Exception as exc:  # pragma: no cover - environment dependent
            print(f"  [!!] {language}: {type(exc).__name__}: {exc}")
            traceback.print_exc(limit=2)
            report["extractors"][language] = {"ok": False, "reason": str(exc)}
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target", default=None, help="repository to probe")
    ap.add_argument("--json-out", default=None, help="write the report as JSON")
    args = ap.parse_args()

    print_matrix()
    report = {}
    if args.target:
        report = probe(args.target)
    elif TARGETS.exists() and any(p.is_dir() for p in TARGETS.iterdir()):
        dirs = [p.name for p in TARGETS.iterdir() if p.is_dir()]
        print(f"hint: pass --target <name>; available under targets/: {dirs[:8]}")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"written: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
