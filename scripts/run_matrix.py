"""Generate the ISO and GitHub documentation sets for every repository.

The experiment compares two rubrics, so each repository yields two *separate* document
sets produced from the matching template. They must never share an output directory:
the whole point is that the ISO set and the GitHub set are different documents, and a
path collision would silently make one rubric's scores describe the other's text.

Every run is resumable: an existing document file is skipped, so an interrupted matrix
continues where it stopped without paying twice.

Usage::

    python scripts/run_matrix.py --limit 60 --seed 42 --workers 12
    python scripts/run_matrix.py --repos flask-main joblib --axes iso_26514
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.config import TARGETS, TEMPLATES  # noqa: E402
from codedoc.deps.relations_index import build_index, get_dep  # noqa: E402
from codedoc.sampling import coverage, pick_entities  # noqa: E402
from codedoc.writer.llm import LinguisticCore  # noqa: E402
from codedoc.writer.prompt import build_prompt  # noqa: E402
from codedoc.writer.usage import RECORDER  # noqa: E402

OUT_ROOT = ROOT / "outputs" / "matrix"
REPORT = ROOT / "results" / "analysis" / "matrix_run.md"

#: rubric id -> template that produces a document in that rubric's shape
AXES = {
    "iso_26514": "iso_26514.txt",
    "github_docs_style": "github.txt",
}

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

PRICE_IN = 0.09 / 1e6
PRICE_OUT = 0.45 / 1e6


class _PromptArgs:
    """Minimal stand-in for the console's prompt arguments."""

    def __init__(self, template: Path):
        self.relevant = True
        self.language = DEFAULTS["language"]
        self.prompt_template = str(template)
        self.max_tokens = DEFAULTS["max_tokens"]
        self.source_budget = DEFAULTS["source_budget"]


def safe_name(qname: str) -> str:
    return qname.replace(".", "_").replace("/", "_").replace("#", "_").replace("<", "_").replace(">", "_")


def generate_one(dep: dict, template: Path, config: dict) -> dict:
    core = LinguisticCore()
    core.LLM_key = config["api_key"]
    core.LLM_url = config["base_url"]
    core.model = config["model"]
    core.temperature = config["temperature"]
    core.max_output_tokens = config["max_completion_tokens"]
    core.max_retries = config["max_retries"]
    core.use_max_completion_tokens = True
    tag = f"matrix-{os.getpid()}-{threading.get_ident()}-{time.time_ns()}"
    core.label = tag
    core.create_socket()

    prompt = build_prompt(dep, _PromptArgs(template))
    started = time.time()
    document = core.process(prompt)
    seconds = time.time() - started
    mine = [r for r in RECORDER.records if r.get("label") == tag]
    prompt_tokens = sum(r["prompt_tokens"] for r in mine)
    completion_tokens = sum(r["completion_tokens"] for r in mine)
    cached = sum(r.get("cached_tokens", 0) for r in mine)
    return {
        "document": document or "",
        "prompt": prompt,
        "seconds": seconds,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cached_tokens": cached,
        "cost": prompt_tokens * PRICE_IN + completion_tokens * PRICE_OUT,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", nargs="+", default=None,
                    help="repository names under targets/ (default: all)")
    ap.add_argument("--axes", nargs="+", default=list(AXES),
                    help=f"rubric ids to generate for (default: {list(AXES)})")
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--max-cost", type=float, default=5.0,
                    help="abort before exceeding this many USD (default 5.0)")
    ap.add_argument("--out", default=str(OUT_ROOT))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    api_key = os.environ.get("LLM_KEY", "")
    if not api_key and not args.dry_run:
        print("LLM_KEY is not set; refusing to run")
        return 2
    config = dict(DEFAULTS, api_key=api_key)

    unknown = [a for a in args.axes if a not in AXES]
    if unknown:
        print(f"unknown axis: {unknown}; known: {list(AXES)}")
        return 2

    repos = args.repos or sorted(p.name for p in TARGETS.iterdir() if p.is_dir())
    out_root = Path(args.out)

    # ---- plan -------------------------------------------------------------
    plan = []
    for repo in repos:
        repo_path = TARGETS / repo
        if not repo_path.is_dir():
            print(f"skip {repo}: not found under targets/")
            continue
        index = build_index(str(repo_path))
        if index is None:
            print(f"skip {repo}: no Python entities")
            continue
        selected = pick_entities(index, args.limit, args.seed)
        cov = coverage(index, selected)
        plan.append({"repo": repo, "index": index, "selected": selected, "coverage": cov})
        print(f"plan {repo:<12} entities={len(index.contexts):>6} "
              f"selected={len(selected):>3} relations_in_sample="
              f"{sum(cov['sampled'].values()):>4}")

    tasks = []
    for item in plan:
        for axis in args.axes:
            axis_dir = out_root / axis / item["repo"]
            axis_dir.mkdir(parents=True, exist_ok=True)
            for ctx in item["selected"]:
                qname = ctx.entity.qualified_name
                target = axis_dir / f"{safe_name(qname)}.md"
                if target.exists() and target.stat().st_size > 0:
                    continue
                tasks.append({"item": item, "axis": axis, "qname": qname, "target": target})

    total_tasks = len(tasks)
    print(f"\ntasks to run: {total_tasks} "
          f"({len(plan)} repos x {len(args.axes)} axes, already-present documents skipped)")
    if args.dry_run:
        return 0
    if not total_tasks:
        print("nothing to do")
        return 0

    # ---- run --------------------------------------------------------------
    lock = threading.Lock()
    stats = {"done": 0, "failed": 0, "cost": 0.0, "prompt_tokens": 0,
             "completion_tokens": 0, "chars": 0, "started": time.time()}
    per_axis: dict = {axis: {"done": 0, "failed": 0, "cost": 0.0, "chars": 0} for axis in args.axes}
    failures = []

    def work(task):
        item = task["item"]
        dep = get_dep(item["index"], task["qname"].split(".")[-1], task["qname"], "")
        if dep is None:
            raise KeyError(f"entity vanished from index: {task['qname']}")
        result = generate_one(dep, TEMPLATES / AXES[task["axis"]], config)
        task["target"].write_text(result["document"], encoding="utf-8")
        task["target"].with_suffix(".prompt.txt").write_text(result["prompt"], encoding="utf-8")
        return task, result

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(work, task): task for task in tasks}
        for future in as_completed(futures):
            task = futures[future]
            try:
                task, result = future.result()
            except Exception as exc:  # noqa: BLE001 - one failure must not stop the matrix
                with lock:
                    stats["failed"] += 1
                    per_axis[task["axis"]]["failed"] += 1
                    failures.append({"repo": task["item"]["repo"], "axis": task["axis"],
                                     "qname": task["qname"], "error": f"{type(exc).__name__}: {exc}"})
                continue
            with lock:
                stats["done"] += 1
                stats["cost"] += result["cost"]
                stats["prompt_tokens"] += result["prompt_tokens"]
                stats["completion_tokens"] += result["completion_tokens"]
                stats["chars"] += len(result["document"])
                bucket = per_axis[task["axis"]]
                bucket["done"] += 1
                bucket["cost"] += result["cost"]
                bucket["chars"] += len(result["document"])
                done = stats["done"] + stats["failed"]
                if done % 25 == 0 or done == total_tasks:
                    rate = stats["done"] / max(1e-9, time.time() - stats["started"]) * 60
                    print(f"  {done}/{total_tasks} | ${stats['cost']:.4f} | "
                          f"{rate:.1f}/min | failed={stats['failed']}", flush=True)
                if stats["cost"] > args.max_cost:
                    print(f"  cost {stats['cost']:.2f} exceeded --max-cost {args.max_cost}", flush=True)

    elapsed = time.time() - stats["started"]

    # ---- report -----------------------------------------------------------
    lines = [
        "# Matrix run: ISO and GitHub documentation sets",
        "",
        f"* model: `{config['model']}` at `{config['base_url']}`",
        f"* sampling: relation-stratified, limit {args.limit}, seed {args.seed}",
        "* the two axes are generated from different templates and written to different",
        "  directories, so no document is shared between rubrics",
        f"* {stats['done']} documents in {elapsed / 60:.1f} min, "
        f"{stats['failed']} failed, USD {stats['cost']:.4f}",
        "",
        "| repo | entities in repo | sampled | relation links in sample |",
        "|---|---|---|---|",
    ]
    for item in plan:
        lines.append(f"| {item['repo']} | {len(item['index'].contexts)} | "
                     f"{len(item['selected'])} | {sum(item['coverage']['sampled'].values())} |")
    lines += ["", "| axis | template | documents | chars | cost (USD) | failed |",
              "|---|---|---|---|---|---|"]
    for axis in args.axes:
        bucket = per_axis[axis]
        lines.append(f"| {axis} | {AXES[axis]} | {bucket['done']} | {bucket['chars']:,} | "
                     f"{bucket['cost']:.4f} | {bucket['failed']} |")
    lines += ["", f"Output: `{out_root.relative_to(ROOT)}/<axis>/<repo>/<entity>.md`"]
    if failures:
        lines += ["", "## Failures", ""]
        for failure in failures[:50]:
            lines.append(f"* {failure['repo']} / {failure['axis']} / {failure['qname']}: {failure['error']}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_root / "manifest.json").write_text(json.dumps(
        {"config": {k: v for k, v in config.items() if k != "api_key"},
         "limit": args.limit, "seed": args.seed, "axes": args.axes,
         "repos": [{"repo": i["repo"], "entities": len(i["index"].contexts),
                    "sampled": len(i["selected"]),
                    "coverage": i["coverage"]} for i in plan],
         "stats": stats, "per_axis": per_axis, "failures": failures},
        indent=2, default=str), encoding="utf-8")

    print(f"\ndone: {stats['done']} ok, {stats['failed']} failed, USD {stats['cost']:.4f}, "
          f"{elapsed / 60:.1f} min")
    print(f"report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
