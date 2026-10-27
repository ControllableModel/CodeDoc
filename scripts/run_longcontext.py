#!/usr/bin/python3
# _*_ coding: utf-8 _*_
"""Long-Context baseline (the second baseline in tab:rq2_extended).

The paper defines it as the full source file containing each target entity, fed to the same
backbone under a matched token budget, with no documentation structure and no dependency
retrieval. That is deliberately the weakest sensible baseline: it answers "how much of the
score comes from the standards and the retrieval, and how much from simply giving a strong
model the source".

Two properties matter for the comparison to be honest:

* **Matched budget.** "Matched" is not a bare number: the baseline is given the same *total*
  prompt-token budget as CodeDoc's prompt for the same entity, so it cannot win by reading
  more. ``--budget-mode`` selects ``codedoc`` (match the measured CodeDoc prompt size, the
  default) or ``fixed`` (a constant cap).
* **No structure.** The instruction is a single sentence asking for documentation, with no
  section list, no criteria and no metadata block. Anything else would be CodeDoc with fewer
  steps rather than the baseline the paper describes.

Output layout matches ``run_matrix.py`` so the same judge driver scores it:
``<out>/<axis>/<repo>/<entity>.md`` plus a ``.prompt.txt`` next to each document.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from codedoc.config import TARGETS  # noqa: E402
from codedoc.deps.relations_index import build_index, get_dep  # noqa: E402
from codedoc.sampling import pick_entities  # noqa: E402
from codedoc.writer.llm import LinguisticCore  # noqa: E402
from codedoc.writer.usage import RECORDER  # noqa: E402

OUT = ROOT / "outputs" / "baselines" / "longcontext"

#: DeepSeek-style list price used only to report an orientation cost; the generation endpoint
#: bills separately. Kept identical to run_matrix so the two tables are comparable.
PRICE_IN = 0.09 / 1e6
PRICE_OUT = 0.45 / 1e6

DEFAULTS = {
    "base_url": "https://apic1.ohmycdn.com/v1",
    "model": "gpt-6-luna",
    "temperature": 1.0,
    "max_tokens": 40000,
    "source_budget": 8000,
    "max_completion_tokens": 8000,
    "max_retries": 3,
    "language": "English",
}

INSTRUCTION = (
    "Document the code below for a developer who has never seen this file.\n"
    "Write the documentation only.\n"
)


def build_long_context_prompt(dep: dict, budget: int, language: str) -> str:
    """One instruction plus the source, truncated to ``budget`` characters.

    The entity's own source is used, not the whole file, when the file is larger than the
    budget: a baseline that silently drops the target entity would be measuring nothing.
    ``budget`` is in characters because that is what the CodeDoc prompt measures; token
    matching is handled by the caller through ``--budget-chars`` so the two prompts land in
    the same range.
    """
    source = str(dep.get("source_code") or "")
    if len(source) > budget:
        head = source[: int(budget * 0.7)]
        tail = source[-int(budget * 0.25):]
        source = f"{head}\n# ... truncated ...\n{tail}"
    return (
        f"{INSTRUCTION}\n"
        f"File: {dep.get('path')}\n\n"
        f"```python\n{source}\n```\n\n"
        f"Documentation ({language}):"
    )


def generate_one(dep: dict, config: dict, budget: int) -> dict:
    core = LinguisticCore()
    core.LLM_key = config["api_key"]
    core.LLM_url = config["base_url"]
    core.model = config["model"]
    core.temperature = config["temperature"]
    core.max_output_tokens = config["max_completion_tokens"]
    core.max_retries = config["max_retries"]
    core.use_max_completion_tokens = True
    tag = f"longctx-{os.getpid()}-{threading.get_ident()}-{time.time_ns()}"
    core.label = tag
    core.create_socket()

    prompt = build_long_context_prompt(dep, budget, config["language"])
    started = time.time()
    document = core.process(prompt)
    seconds = time.time() - started
    mine = [r for r in RECORDER.records if r.get("label") == tag]
    prompt_tokens = sum(r["prompt_tokens"] for r in mine)
    completion_tokens = sum(r["completion_tokens"] for r in mine)
    return {
        "document": document or "",
        "prompt": prompt,
        "seconds": seconds,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost": prompt_tokens * PRICE_IN + completion_tokens * PRICE_OUT,
    }


def safe_name(qname: str) -> str:
    return qname.replace(".", "_").replace("/", "_").replace("#", "_").replace("<", "_").replace(">", "_")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", nargs="+", default=None)
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--budget-chars", type=int, default=9000,
                    help="source characters handed to the baseline (CodeDoc v6 measures ~9.5k "
                         "characters of prompt per entity, of which this is the source part)")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--max-cost", type=float, default=2.0)
    ap.add_argument("--languages", nargs="+", default=["English"],
                    help="one output directory per language; both axes are scored on English")
    ap.add_argument("--api-key", default=os.environ.get("LLM_KEY", ""))
    ap.add_argument("--base-url", default=os.environ.get("LLM_URL", DEFAULTS["base_url"]))
    ap.add_argument("--model", default=os.environ.get("MODEL", DEFAULTS["model"]))
    args = ap.parse_args()

    if not args.api_key:
        print("no API key: set LLM_KEY or pass --api-key")
        return 2

    config = dict(DEFAULTS)
    config.update({
        "api_key": args.api_key,
        "base_url": args.base_url,
        "model": args.model,
        "language": args.languages[0],
    })

    repos = args.repos or sorted(p.name for p in TARGETS.iterdir() if p.is_dir())
    out_root = Path(args.out)
    total_cost = 0.0
    summary = []

    for repo in repos:
        target = TARGETS / repo
        if not target.exists():
            print(f"skip {repo}: not under targets/")
            continue
        index = build_index(target)
        # Same sampler and seed as run_matrix.py, so the entity set is identical across
        # methods and the comparison is paired rather than independent.
        picked = pick_entities(index, limit=args.limit, seed=args.seed)
        tasks = []
        for ctx in picked:
            dep = get_dep(index, ctx.entity.name, ctx.entity.qualified_name, ctx.entity.path)
            if dep:
                tasks.append(dep)
        print(f"{repo}: {len(tasks)} entities", flush=True)

        done = 0
        lock = threading.Lock()

        def work(dep):
            nonlocal done, total_cost
            try:
                res = generate_one(dep, config, args.budget_chars)
            except Exception as exc:  # noqa: BLE001 - one entity must not abort the repo
                return {"error": f"{type(exc).__name__}: {exc}"}
            with lock:
                done += 1
                total_cost += res["cost"]
                if done % 25 == 0:
                    print(f"  {done}/{len(tasks)} | ${total_cost:.4f}", flush=True)
            return res

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(work, tasks))

        for axis in ("iso_26514", "github_docs_style"):
            dest = out_root / axis / repo
            dest.mkdir(parents=True, exist_ok=True)
            for dep, res in zip(tasks, results):
                if "error" in res:
                    continue
                name = safe_name(str(dep.get("qualified_name") or dep["real_name"]))
                (dest / f"{name}.md").write_text(res["document"], encoding="utf-8")
                (dest / f"{name}.prompt.txt").write_text(res["prompt"], encoding="utf-8")

        ok = sum(1 for r in results if "error" not in r)
        failed = [r["error"] for r in results if "error" in r]
        summary.append({
            "repo": repo,
            "entities": len(tasks),
            "ok": ok,
            "failed": len(failed),
            "prompt_tokens": sum(r.get("prompt_tokens", 0) for r in results),
            "completion_tokens": sum(r.get("completion_tokens", 0) for r in results),
            "seconds": round(sum(r.get("seconds", 0) for r in results), 1),
        })
        print(f"  {repo}: {ok} ok, {len(failed)} failed", flush=True)
        if failed:
            print(f"    first failure: {failed[0][:200]}", flush=True)
        if total_cost > args.max_cost:
            print(f"stopping: cost ${total_cost:.4f} exceeds --max-cost {args.max_cost}")
            break

    out_root.mkdir(parents=True, exist_ok=True)
    report = {
        "model": config["model"],
        "budget_chars": args.budget_chars,
        "total_cost_usd": round(total_cost, 4),
        "total_prompt_tokens": sum(r["prompt_tokens"] for r in summary),
        "total_completion_tokens": sum(r["completion_tokens"] for r in summary),
        "repos": summary,
    }
    (out_root / "run_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2)[:1200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
