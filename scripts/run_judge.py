"""Score generated documentation against a criterion set (experiment step for judging).

This is the driver the published artifact was missing: the judge prompt builders
were in the repository, but nothing invoked them end to end.

Two modes, matching the archived data shape:

``single``  one criterion per call  -> ``{overall: {judge, evidence}}``
``multi``   all criteria in one call -> ``{dimension: {judge, evidence}}``

Usage::

    set LLM_KEY=...           # PowerShell: $env:LLM_KEY="..."
    python scripts/run_judge.py --doc_dir outputs/flask --criteria iso_26514 --mode multi
    python scripts/run_judge.py --doc_dir outputs/flask --criteria practice_docstring --mode single
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.criteria import registry  # noqa: E402
from codedoc.judge.query import LLM_Remote_query, judge_with_retry, parse_verdict  # noqa: E402


def documents(doc_dir: Path, pattern: str) -> list:
    return sorted(doc_dir.rglob(pattern))


def judge_document(judge: LLM_Remote_query, text: str, criteria, mode: str) -> dict:
    if mode == "multi":
        spec = "\n".join(f"- {c.name}: {c.definition}" for c in criteria)
        judge.load_JudgeContent_Once(spec)
        verdict, _attempts, _raw = judge_with_retry(judge, text)
        return verdict

    scores: dict = {}
    for criterion in criteria:
        judge.load_judgeContent(criterion.name, criterion.definition)
        verdict = parse_verdict(judge.solo_query(text))
        scores[criterion.name] = verdict.get("overall", {})
        time.sleep(0.5)
    return scores


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--doc_dir", required=True)
    ap.add_argument("--criteria", default="iso_26514")
    ap.add_argument("--mode", choices=["single", "multi"], default="multi")
    ap.add_argument("--pattern", default="*.md")
    ap.add_argument("--out", default=None, help="output directory (default: <doc_dir>/scores_<criteria>)")
    ap.add_argument("--entity_level_only", action="store_true",
                    help="score only criteria that govern a single code entity")
    ap.add_argument("--limit", type=int, default=0, help="only score the first N documents")
    ap.add_argument("--model", default=os.getenv("MODEL", "gpt-5-mini"))
    args = ap.parse_args()

    key = os.getenv("LLM_KEY", "")
    if not key:
        print("LLM_KEY is not set; the judge needs an API key.", file=sys.stderr)
        return 2

    criterion_set = registry.load(args.criteria)
    criteria = criterion_set.entity_level() if args.entity_level_only else list(criterion_set)
    if not criteria:
        print("no criteria selected", file=sys.stderr)
        return 2

    doc_dir = Path(args.doc_dir)
    files = documents(doc_dir, args.pattern)
    if args.limit:
        files = files[: args.limit]
    if not files:
        print(f"no documents matched {args.pattern} under {doc_dir}", file=sys.stderr)
        return 1

    out_dir = Path(args.out) if args.out else doc_dir / f"scores_{args.criteria}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"judging {len(files)} documents with {len(criteria)} criteria ({args.mode})")
    empty = 0
    for i, path in enumerate(files, 1):
        target = out_dir / f"{path.stem}quality.jsonl"
        if target.exists():
            print(f"[{i}/{len(files)}] skip (exists): {path.name}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        judge = LLM_Remote_query(api_key=key, api_url=os.getenv("LLM_URL", "https://api.openai.com/v1"),
                                 model=args.model)
        scores = judge_document(judge, text, criteria, args.mode)
        if not scores:
            empty += 1
            print(f"[{i}/{len(files)}] EMPTY verdict for {path.name}")
        target.write_text(json.dumps(scores, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[{i}/{len(files)}] {path.name}: {len(scores)} dimensions")

    print(f"done. empty verdicts: {empty}. output: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
