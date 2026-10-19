"""Smoke test: one real generation call and one real judging call, fully metered.

Checks, in order: the endpoint answers, the assembled prompt is accepted, the
generated text parses, the judge returns a verdict JSON, and the token/latency
cost of each call is reported.

Usage::

    set LLM_KEY=...
    python scripts/smoke_llm.py --repo targets/flask-main --entity Flask.__init__
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.criteria import registry  # noqa: E402
from codedoc.deps.relations_index import build_index, get_dep  # noqa: E402
from codedoc.judge.query import LLM_Remote_query, parse_verdict  # noqa: E402
from codedoc.writer.llm import LinguisticCore  # noqa: E402
from codedoc.writer.prompt import build_prompt  # noqa: E402
from codedoc.writer.usage import RECORDER  # noqa: E402


class _Args:
    relevant = True
    language = "English"
    prompt_template: str | None = None
    max_tokens = 10000
    source_budget = 8000


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=str(ROOT / "targets" / "flask-main"))
    ap.add_argument("--entity", default="Flask.__init__")
    ap.add_argument("--model", default=os.getenv("MODEL", "deepseek-chat"))
    ap.add_argument("--criteria", default="practice_docstring")
    ap.add_argument("--out", default=str(ROOT / "outputs" / "smoke"))
    args = ap.parse_args()

    key = os.getenv("LLM_KEY", "")
    if not key:
        print("LLM_KEY is not set", file=sys.stderr)
        return 2
    base_url = os.getenv("LLM_URL", "https://api.deepseek.com/v1")

    # ---- 1. dependency context and prompt -------------------------------------
    print("[1/4] building dependency context ...")
    index = build_index(args.repo)
    if index is None:
        print("no entities extracted", file=sys.stderr)
        return 1
    dep = get_dep(index, args.entity, "", "")
    if dep is None:
        print(f"entity {args.entity!r} not found", file=sys.stderr)
        return 1

    writer_args = _Args()
    writer_args.prompt_template = str(ROOT / "codedoc" / "writer" / "templates" / "iso_26514.txt")
    prompt = build_prompt(dep, writer_args)
    print(f"      entity={dep['qualified_name']} kind={dep['kind']} "
          f"prompt={len(prompt):,} chars relations={dep['relations']}")

    # ---- 2. generation --------------------------------------------------------
    print("[2/4] generating documentation ...")
    core = LinguisticCore()
    core.LLM_key = key
    core.LLM_url = base_url
    core.model = args.model
    core.temperature = 1
    core.create_socket()
    started = time.time()
    doc = core.process(prompt)
    gen_seconds = time.time() - started
    print(f"      {len(doc or '')} chars in {gen_seconds:.2f}s")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = args.entity.replace(".", "_")
    (out_dir / f"{safe}.generated.md").write_text(doc or "", encoding="utf-8")

    # ---- 3. judging -----------------------------------------------------------
    criterion_set = registry.load(args.criteria)
    criteria = list(criterion_set)
    spec = "\n".join(f"- {c.name}: {c.definition}" for c in criteria)
    judge = LLM_Remote_query(api_key=key, api_url=base_url, model=args.model)
    judge.load_JudgeContent_Once(spec)
    print(f"[3/4] judging with {len(criteria)} criteria ({args.criteria}, multi mode) ...")
    started = time.time()
    raw = judge.solo_query(doc or "")
    judge_seconds = time.time() - started
    verdict = parse_verdict(raw)
    (out_dir / f"{safe}.verdict.json").write_text(
        __import__("json").dumps(verdict, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      {len(verdict)} dimensions parsed in {judge_seconds:.2f}s")

    # ---- 4. cost report -------------------------------------------------------
    print("[4/4] cost report")
    RECORDER.save(str(out_dir / "cost_report.json"))
    summary = RECORDER.summary()
    total = summary.get("total", {})
    print()
    print("=" * 74)
    print(f"{'phase':<14}{'calls':>6}{'in tok':>10}{'out tok':>10}{'sec':>8}{'in/call':>10}{'out/call':>10}")
    print("-" * 74)
    for phase, stats in summary.get("by_phase", {}).items():
        print(f"{phase:<14}{stats['calls']:>6}{stats['prompt_tokens']:>10}"
              f"{stats['completion_tokens']:>10}{stats['seconds']:>8}"
              f"{stats['prompt_tokens_per_call']:>10}{stats['completion_tokens_per_call']:>10}")
    print("-" * 74)
    print(f"{'TOTAL':<14}{total['calls']:>6}{total['prompt_tokens']:>10}"
          f"{total['completion_tokens']:>10}{total['seconds']:>8}")
    print("=" * 74)

    sample_verdict = next(iter(verdict.items()), None)
    if sample_verdict:
        name, payload = sample_verdict
        score = payload.get("judge") if isinstance(payload, dict) else payload
        print(f"sample verdict: {name} -> {score}")
    print(f"artifacts: {out_dir}")
    ok = bool(doc) and bool(verdict)
    print(f"SMOKE {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
