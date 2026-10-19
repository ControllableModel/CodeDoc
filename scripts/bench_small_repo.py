"""End-to-end cost and time measurement on one small repository.

Runs the real pipeline (dependency context -> prompt -> generation -> judging) over
a bounded entity set and reports what it cost: API calls, input/output tokens, API
seconds, and wall time — then extrapolates to the full experiment matrix.

Every number comes from the SDK response (``usage.prompt_tokens`` /
``usage.completion_tokens``) via :mod:`codedoc.writer.usage`, not from character
counts, so the report can be quoted directly.

Usage::

    set LLM_KEY=...
    python scripts/bench_small_repo.py --repo ragflow --limit 65 --workers 4
    python scripts/bench_small_repo.py --repo flask-main --limit 30 --out outputs/bench_flask
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.config import TARGETS  # noqa: E402
from codedoc.criteria import registry  # noqa: E402
from codedoc.deps.relations_index import build_index, get_dep  # noqa: E402
from codedoc.judge.query import LLM_Remote_query, judge_with_retry, parse_verdict  # noqa: E402
from codedoc.writer.llm import LinguisticCore  # noqa: E402
from codedoc.writer.prompt import build_prompt  # noqa: E402
from codedoc.writer.usage import RECORDER  # noqa: E402


class _PromptArgs:
    relevant = True
    language = "English"
    prompt_template: str | None = None
    max_tokens = 10000
    source_budget = 8000


def pick_entities(index, limit: int, seed: int = 42) -> list:
    """Deterministic, kind-balanced entity selection."""
    import random

    by_kind: dict = {}
    for ctx in index.contexts:
        by_kind.setdefault(str(ctx.entity.kind), []).append(ctx)
    for ctxs in by_kind.values():
        ctxs.sort(key=lambda c: c.entity.qualified_name)

    rng = random.Random(seed)
    if limit <= 0 or limit >= len(index.contexts):
        return sorted(index.contexts, key=lambda c: str(c.entity.qualified_name))

    kinds = sorted(by_kind)
    per_kind = max(1, limit // max(1, len(kinds)))
    picked = []
    for kind in kinds:
        picked.extend(rng.sample(by_kind[kind], min(per_kind, len(by_kind[kind]))))
    # top up if rounding left us short
    remaining = [c for c in index.contexts if c not in picked]
    remaining.sort(key=lambda c: c.entity.qualified_name)
    if len(picked) < limit and remaining:
        picked.extend(rng.sample(remaining, min(limit - len(picked), len(remaining))))
    return sorted(picked, key=lambda c: str(c.entity.qualified_name))[:limit]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="ragflow", help="directory under targets/")
    ap.add_argument("--limit", type=int, default=65, help="entities to process (0 = all)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--judge_workers", type=int, default=3)
    ap.add_argument("--model", default=os.getenv("MODEL", "deepseek-chat"))
    ap.add_argument("--criteria", default="practice_docstring")
    ap.add_argument("--out", default=None)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    key = os.getenv("LLM_KEY", "")
    if not key:
        print("LLM_KEY is not set", file=sys.stderr)
        return 2
    base_url = os.getenv("LLM_URL", "https://api.deepseek.com/v1")

    repo_path = TARGETS / args.repo
    if not repo_path.exists():
        print(f"repository not found: {repo_path}", file=sys.stderr)
        return 2

    out_dir = Path(args.out) if args.out else ROOT / "outputs" / f"bench_{args.repo}"
    doc_dir = out_dir / "docs"
    doc_dir.mkdir(parents=True, exist_ok=True)

    wall_started = time.time()

    # ---- extraction (no API cost) --------------------------------------------
    print(f"[1/4] extracting dependency context from {args.repo} ...")
    t0 = time.time()
    index = build_index(str(repo_path))
    if index is None:
        print("no entities extracted", file=sys.stderr)
        return 1
    extract_seconds = time.time() - t0
    entities = pick_entities(index, args.limit, args.seed)
    print(f"      {len(index.contexts)} entities found, {len(entities)} selected, "
          f"{extract_seconds:.1f}s")

    prompt_args = _PromptArgs()
    prompt_args.prompt_template = str(ROOT / "codedoc" / "writer" / "templates" / "iso_26514.txt")

    # ---- generation ----------------------------------------------------------
    print(f"[2/4] generating {len(entities)} documents ({args.workers} workers) ...")
    docs: dict = {}
    gen_started = time.time()

    def generate(ctx):
        dep = get_dep(index, ctx.entity.name, ctx.entity.qualified_name, ctx.entity.path)
        if not dep:
            return None, None
        prompt = build_prompt(dep, prompt_args)
        core = LinguisticCore()
        core.LLM_key, core.LLM_url, core.model = key, base_url, args.model
        core.temperature = 1
        core.create_socket()
        text = core.process(prompt)
        return ctx, text

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(generate, ctx) for ctx in entities]
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                ctx, text = fut.result()
            except Exception as exc:  # noqa: BLE001
                print(f"      [FAIL] {exc}"[:150])
                continue
            if ctx is None:
                continue
            docs[ctx.entity.qualified_name] = text
            name = ctx.entity.qualified_name.replace(".", "_").replace("/", "_")
            (doc_dir / f"{name}.md").write_text(text or "", encoding="utf-8")
            print(f"      [{i}/{len(futures)}] {ctx.entity.name} ({len(text or '')} chars)")
    gen_seconds = time.time() - gen_started

    if not docs:
        print("no documents generated", file=sys.stderr)
        return 1

    # ---- judging -------------------------------------------------------------
    criterion_set = registry.load(args.criteria)
    # One specification per entity kind: a free function is not asked about the
    # inheritance contract it cannot have (see criteria.schema.applies_to_kinds).
    spec_by_kind = {
        kind: "\n".join(f"- {c.name}: {c.definition}" for c in criterion_set.for_kind(kind))
        for kind in ("class", "method", "function")
    }
    kind_of = {ctx.entity.qualified_name: str(ctx.entity.kind) for ctx in index.contexts}
    per_kind = {kind: sum(1 for q in docs if kind_of.get(q) == kind) for kind in spec_by_kind}
    n_criteria = {kind: len(criterion_set.for_kind(kind)) for kind in spec_by_kind}
    print(f"[3/4] judging {len(docs)} documents "
          f"({', '.join(f'{k}={v}x{n_criteria[k]}dims' for k, v in per_kind.items() if v)}, "
          f"{args.judge_workers} workers) ...")
    scores: dict = {}
    judge_started = time.time()

    def judge_one(item):
        qname, text = item
        kind = kind_of.get(qname, "function")
        spec = spec_by_kind.get(kind) or spec_by_kind["function"]
        judge = LLM_Remote_query(api_key=key, api_url=base_url, model=args.model)
        # Output budget scales with the number of dimensions: a 14-dimension rubric
        # does not fit in the historical 1024-token cap and gets truncated mid-JSON.
        judge.max_token = max(1024, 200 * max(1, len(criteria)))
        judge.load_JudgeContent_Once(spec)
        verdict, attempts, raw = judge_with_retry(judge, text or "")
        if not verdict:
            print(f"      [WARN] unparseable verdict for {qname} after {attempts} tries")
        return qname, verdict

    with ThreadPoolExecutor(max_workers=args.judge_workers) as pool:
        futures = [pool.submit(judge_one, item) for item in docs.items()]
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                qname, verdict = fut.result()
            except Exception as exc:  # noqa: BLE001
                print(f"      [FAIL] {exc}"[:150])
                continue
            scores[qname] = verdict
            print(f"      [{i}/{len(futures)}] {len(verdict)} dimensions")
    judge_seconds = time.time() - judge_started
    wall_seconds = time.time() - wall_started

    # ---- report --------------------------------------------------------------
    summary = RECORDER.summary()
    RECORDER.save(str(out_dir / "cost_report.json"))
    (out_dir / "scores.json").write_text(json.dumps(scores, indent=2, ensure_ascii=False),
                                         encoding="utf-8")
    (out_dir / "run_meta.json").write_text(json.dumps({
        "repo": args.repo, "model": args.model, "criteria": args.criteria,
        "entities": len(docs), "limit": args.limit, "seed": args.seed,
        "extract_seconds": round(extract_seconds, 2),
        "generation_wall_seconds": round(gen_seconds, 2),
        "judging_wall_seconds": round(judge_seconds, 2),
        "total_wall_seconds": round(wall_seconds, 2),
    }, indent=2), encoding="utf-8")

    total = summary.get("total", {})
    by_phase = summary.get("by_phase", {})
    n = len(docs)

    def pct(part, whole):
        return 0.0 if not whole else 100.0 * part / whole

    print()
    print("=" * 88)
    print(f"BENCHMARK  repo={args.repo}  model={args.model}  criteria={args.criteria}")
    print(f"entities={n}  extraction={extract_seconds:.1f}s (no API)")
    print("=" * 88)
    header = f"{'phase':<14}{'calls':>6}{'in tok':>11}{'out tok':>11}{'tok/call':>10}{'api sec':>10}{'wall sec':>10}"
    print(header)
    print("-" * 88)
    for phase, st in by_phase.items():
        print(f"{phase:<14}{st['calls']:>6}{st['prompt_tokens']:>11}{st['completion_tokens']:>11}"
              f"{int((st['prompt_tokens'] + st['completion_tokens']) / max(1, st['calls'])):>10}"
              f"{st['seconds']:>10.1f}"
              f"{(gen_seconds if phase == 'generation' else judge_seconds):>10.1f}")
    print("-" * 88)
    print(f"{'TOTAL':<14}{total.get('calls',0):>6}{total.get('prompt_tokens',0):>11}"
          f"{total.get('completion_tokens',0):>11}"
          f"{int(total.get('total_tokens',0)/max(1,total.get('calls',1))):>10}"
          f"{total.get('seconds',0):>10.1f}{wall_seconds:>10.1f}")
    print("=" * 88)
    print(f"per entity: {total.get('prompt_tokens',0)/max(1,n):,.0f} in / "
          f"{total.get('completion_tokens',0)/max(1,n):,.0f} out tokens, "
          f"{wall_seconds/max(1,n):.1f}s wall")

    # ---- extrapolation -------------------------------------------------------
    # DeepSeek list price used only for orientation; tokens are the reportable unit.
    in_price, out_price = 2.0, 8.0   # CNY per 1M tokens (deepseek-chat, verify at order time)
    in_tok, out_tok = total.get("prompt_tokens", 0), total.get("completion_tokens", 0)
    per_doc_in = in_tok / max(1, n)
    per_doc_out = out_tok / max(1, n)
    print()
    print("EXTRAPOLATION (linear in documents; unit = one generated+judged entity)")
    print(f"{'scale':<26}{'docs':>8}{'in tok':>12}{'out tok':>12}{'CNY≈':>10}{'hours≈':>9}")
    print("-" * 88)
    rows = [
        ("RQ2.1 main table (5x3x60)", 900),
        ("RQ2.2 fairness (2x3x60)", 360),
        ("RQ3 ablation (4x1x60)", 240),
        ("RQ4.1 class entities (3x60)", 180),
        ("RQ4.2 multi-language (2x60)", 120),
    ]
    sec_per_doc = wall_seconds / max(1, n)
    for label, count in rows:
        i_tok = per_doc_in * count
        o_tok = per_doc_out * count
        cny = i_tok / 1e6 * in_price + o_tok / 1e6 * out_price
        hours = sec_per_doc * count / 3600
        print(f"{label:<26}{count:>8}{i_tok:>12,.0f}{o_tok:>12,.0f}{cny:>10.2f}{hours:>9.2f}")
    grand = sum(r[1] for r in rows)
    i_tok, o_tok = per_doc_in * grand, per_doc_out * grand
    cny = i_tok / 1e6 * in_price + o_tok / 1e6 * out_price
    print("-" * 88)
    print(f"{'ALL RQs (this plan)':<26}{grand:>8}{i_tok:>12,.0f}{o_tok:>12,.0f}{cny:>10.2f}"
          f"{sec_per_doc * grand / 3600:>9.2f}")
    print("=" * 88)
    print(f"artifacts: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
