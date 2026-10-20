"""Judge the ISO and GitHub document sets produced by run_matrix.py.

Each axis is scored against its own rubric, and the two score sets are written to
separate directories, mirroring the document layout. Documents are matched back to
entities by rebuilding the identical sample (same limit and seed), because the file name
is a lossy translation of the qualified name.

Two levels are reported, because the paper needs both:

* every individual rubric dimension;
* the rubric's main dimensions (ISO: 8 categories, GitHub: 5), computed as the mean of
  that category's dimension means so a category with more dimensions does not dominate
  by weight alone.

A dimension the judge never returned is reported as missing rather than scored zero, and
dimension names returned with different casing or punctuation are matched back to the
rubric instead of being dropped.

Usage::

    python scripts/judge_matrix.py                       # judge everything not yet scored
    python scripts/judge_matrix.py --axes iso_26514 --repos flask-main joblib
    python scripts/judge_matrix.py --report-only         # re-aggregate existing scores
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.config import TARGETS  # noqa: E402
from codedoc.criteria import registry  # noqa: E402
from codedoc.deps.relations_index import build_index  # noqa: E402
from codedoc.judge.query import LLM_Remote_query, judge_with_retry  # noqa: E402
from codedoc.writer.usage import RECORDER  # noqa: E402
from codedoc.sampling import pick_entities  # noqa: E402

MATRIX = ROOT / "outputs" / "matrix"
DOCS_ROOT = MATRIX
LAYOUT = "matrix"
ANALYSIS = ROOT / "results" / "analysis"

#: rubric id -> judge settings
AXES = {
    "iso_26514": {"entity_level_only": True, "label": "ISO/IEC 26514"},
    "github_docs_style": {"entity_level_only": False, "label": "GitHub docs style"},
}

#: judged tokens are priced by the judge's own endpoint (CNY per million)
JUDGE_PRICE = {"currency": "CNY", "input": 2.0, "cached_input": 0.2, "output": 8.0}

DEFAULTS = {
    #: The judge runs on the DeepSeek official API, not on the generation gateway:
    #: it accepts temperature 0, which gpt-6-luna does not, and a scoring instrument has
    #: to be reproducible.
    "base_url": os.environ.get("JUDGE_URL", "https://api.deepseek.com/v1"),
    "model": os.environ.get("JUDGE_MODEL", "deepseek-chat"),
    "judge_temperature": 0.0,
}


def safe_name(qname: str) -> str:
    return (qname.replace(".", "_").replace("/", "_").replace("#", "_")
            .replace("<", "_").replace(">", "_"))


def normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


def build_qname_map(repo: str, limit: int, seed: int) -> dict:
    """safe file stem -> entity facts, using the same deterministic sample."""
    index = build_index(str(TARGETS / repo))
    if index is None:
        return {}
    mapping = {}
    for ctx in pick_entities(index, limit, seed):
        qname = ctx.entity.qualified_name
        mapping[safe_name(qname)] = {
            "qname": qname,
            "kind": str(ctx.entity.kind),
            "path": ctx.entity.path,
        }
    return mapping


def doc_dir(axis: str, repo: str) -> Path:
    """Where the documents for this axis live.

    The matrix layout separates the two generated sets (root/axis/repo); a baseline
    produces one set only, so the same documents are scored once per rubric
    (root/repo) and the score directories keep them apart.
    """
    if LAYOUT == "flat":
        return DOCS_ROOT / repo
    return DOCS_ROOT / axis / repo


def rubric_for(axis: str) -> list:
    """Dimensions the judge is asked about for this axis."""
    criteria = registry.load(axis)
    if AXES[axis]["entity_level_only"]:
        # filter on level, not on applies_to(kind): a dimension that names no kinds
        # applies to every kind, so the kind test silently keeps all 26 ISO dimensions
        criteria = criteria.entity_level()
    return criteria


def score_of(entry) -> float | None:
    """A judge entry is {'judge': int, 'evidence': str}; never invent a score."""
    if isinstance(entry, dict):
        value = entry.get("judge")
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            match = re.search(r"[1-5]", value)
            if match:
                return float(match.group(0))
    if isinstance(entry, (int, float)):
        return float(entry)
    return None


def run_judging(args, tasks: list, criteria_sets: dict, api_key: str) -> dict:
    lock = threading.Lock()
    stats = {"done": 0, "failed": 0, "unparsed": 0, "started": time.time()}

    def judge_document(task) -> None:
        axis = task["axis"]
        criteria = criteria_sets[axis]
        judge = LLM_Remote_query(api_key=api_key, api_url=DEFAULTS["base_url"],
                                 model=DEFAULTS["model"])
        judge.judge_temperature = DEFAULTS["judge_temperature"]
        judge.use_max_completion_tokens = True
        judge.max_token = max(1024, 200 * len(criteria))

        spec = "\n".join(f"- {c.name}: {c.definition}" for c in criteria)
        judge.load_JudgeContent_Once(spec)
        text = task["doc"].read_text(encoding="utf-8")
        verdict, attempts, reason = judge_with_retry(judge, text)

        payload = {
            "axis": axis,
            "repo": task["repo"],
            "document": task["doc"].name,
            "qname": task["info"].get("qname", ""),
            "kind": task["info"].get("kind", ""),
            "verdict": verdict,
            "attempts": attempts,
            "unparsed": reason,
            "dimensions_asked": [c.name for c in criteria],
            "model": DEFAULTS["model"],
        }
        task["out"].write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        with lock:
            stats["done"] += 1
            if not verdict:
                stats["unparsed"] += 1
            if stats["done"] % 20 == 0:
                rate = stats["done"] / max(1e-9, time.time() - stats["started"]) * 60
                print(f"  {stats['done']}/{len(tasks)} | {rate:.1f}/min | "
                      f"unparsed={stats['unparsed']} | failed={stats['failed']}", flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(judge_document, task) for task in tasks]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:  # noqa: BLE001 - report and continue
                with lock:
                    stats["failed"] += 1
                print(f"  failed: {type(exc).__name__}: {exc}", flush=True)
    return stats


def aggregate(axis: str) -> dict:
    """Collect every score file for one axis into per-dimension and per-category tables."""
    criteria = rubric_for(axis)
    by_name = {c.name: c for c in criteria}
    by_norm = {normalize(c.name): c for c in criteria}

    per_dim: dict = {c.name: [] for c in criteria}
    per_repo_dim: dict = {}
    per_kind_dim: dict = {}
    unmatched: dict = {}
    documents = 0
    empty = 0

    for score_file in sorted(DOCS_ROOT.rglob(f"scores_{axis}/*.json")):
        try:
            payload = json.loads(score_file.read_text(encoding="utf-8"))
        except ValueError:
            continue
        documents += 1
        repo = payload.get("repo") or score_file.parent.parent.name
        kind = payload.get("kind") or "unknown"
        verdict = payload.get("verdict") or {}
        if not verdict:
            empty += 1
            continue
        for raw_name, entry in verdict.items():
            criterion = by_name.get(raw_name) or by_norm.get(normalize(raw_name))
            if criterion is None:
                unmatched[raw_name] = unmatched.get(raw_name, 0) + 1
                continue
            value = score_of(entry)
            if value is None:
                continue
            per_dim[criterion.name].append(value)
            per_repo_dim.setdefault(repo, {}).setdefault(criterion.name, []).append(value)
            per_kind_dim.setdefault(kind, {}).setdefault(criterion.name, []).append(value)

    dimensions = []
    for criterion in criteria:
        values = per_dim[criterion.name]
        dimensions.append({
            "dimension": criterion.name,
            "category": criterion.category,
            "n": len(values),
            "mean": round(statistics.mean(values), 3) if values else None,
            "sd": round(statistics.pstdev(values), 3) if len(values) > 1 else None,
            "missing": len(values) == 0,
        })

    # main dimensions: mean of the category's dimension means, so a category with six
    # dimensions does not outweigh one with two
    categories: dict = {}
    for row in dimensions:
        categories.setdefault(row["category"], []).append(row)
    main_dimensions = []
    for category, rows in categories.items():
        scored = [r["mean"] for r in rows if r["mean"] is not None]
        pooled = [v for r in rows for v in per_dim[r["dimension"]]]
        main_dimensions.append({
            "category": category,
            "dimensions": len(rows),
            "scored_dimensions": len(scored),
            "mean_of_dimension_means": round(statistics.mean(scored), 3) if scored else None,
            "pooled_mean": round(statistics.mean(pooled), 3) if pooled else None,
            "n_verdicts": len(pooled),
        })
    main_dimensions.sort(key=lambda r: -(r["mean_of_dimension_means"] or 0))

    per_repo = {}
    for repo, dims in sorted(per_repo_dim.items()):
        all_values = [v for values in dims.values() for v in values]
        per_repo[repo] = {
            "verdicts": len(all_values),
            "mean": round(statistics.mean(all_values), 3) if all_values else None,
            "dimensions": {name: round(statistics.mean(values), 3)
                           for name, values in dims.items() if values},
        }

    per_kind = {}
    for kind, dims in sorted(per_kind_dim.items()):
        values = [v for entries in dims.values() for v in entries]
        per_kind[kind] = {
            "verdicts": len(values),
            "mean": round(statistics.mean(values), 3) if values else None,
            "dimensions": {name: round(statistics.mean(entries), 3)
                           for name, entries in dims.items() if entries},
        }

    covered_categories = {c.category for c in criteria}
    from codedoc.criteria import registry as _registry
    all_categories = {c.category for c in _registry.load(axis)}
    uncovered_sorted = sorted(all_categories - covered_categories)

    all_scored = [v for values in per_dim.values() for v in values]
    return {
        "axis": axis,
        "label": AXES[axis]["label"],
        "documents": documents,
        "empty_verdicts": empty,
        "dimensions_asked": len(criteria),
        "dimensions_scored": sum(1 for r in dimensions if not r["missing"]),
        "overall_mean": round(statistics.mean(all_scored), 3) if all_scored else None,
        "main_dimensions": main_dimensions,
        "dimensions": dimensions,
        "per_repo": per_repo,
        "per_kind": per_kind,
        "all_main_dimensions": sorted(all_categories),
        "uncovered_main_dimensions": uncovered_sorted,
        "unmatched_keys": unmatched,
    }


def write_reports(results: list, tag: str = "") -> None:
    lines = ["# Rubric scores for the generated documentation sets", "",
             f"* judge: `{DEFAULTS['model']}`, temperature {DEFAULTS['judge_temperature']}",
             "* two levels are reported: the rubric's main dimensions (ISO: 8 categories, "
             "GitHub: 5) and every individual dimension",
             "* a main dimension is the mean of its dimensions' means, so a category with "
             "more dimensions does not dominate by weight",
             "* ISO scores only its entity-applicable dimensions; GitHub scores its full set",
             ""]

    for result in results:
        lines += [f"## {result['axis']} ({result['label']})", ""]
        lines += [f"* documents judged: {result['documents']} "
                  f"({result['empty_verdicts']} returned no parseable verdict)",
                  f"* dimensions asked: {result['dimensions_asked']}, "
                  f"scored: {result['dimensions_scored']}",
                  f"* overall mean: {result['overall_mean']}"]
        uncovered = result.get("uncovered_main_dimensions") or []
        if uncovered:
            lines.append(f"* main dimensions with no entity-applicable dimension at all: "
                         f"{', '.join(uncovered)} -- these govern a document set and cannot be "
                         f"scored on a single entity, which is the paper's evaluation-unit argument "
                         f"in concrete numbers")
        lines.append("")
        lines += ["### Main dimensions", "",
                  "| main dimension | dims | scored | mean | pooled | verdicts |",
                  "|---|---|---|---|---|---|"]
        for row in result["main_dimensions"]:
            lines.append(f"| {row['category']} | {row['dimensions']} | {row['scored_dimensions']} "
                         f"| {row['mean_of_dimension_means']} | {row['pooled_mean']} "
                         f"| {row['n_verdicts']} |")
        lines += ["", "### Dimensions", "",
                  "| main dimension | dimension | n | mean | sd |",
                  "|---|---|---|---|---|"]
        ordered = sorted(result["dimensions"],
                         key=lambda r: (r["category"], -(r["mean"] if r["mean"] is not None else -1)))
        for row in ordered:
            mean = row["mean"] if row["mean"] is not None else "**missing**"
            lines.append(f"| {row['category']} | {row['dimension']} | {row['n']} | {mean} | {row['sd'] or '-'} |")
        lines += ["", "### Per repository", "",
                  "| repo | verdicts | mean |", "|---|---|---|"]
        for repo, stats in result["per_repo"].items():
            lines.append(f"| {repo} | {stats['verdicts']} | {stats['mean']} |")
        lines += ["", "### Per entity kind", "",
                  "| kind | verdicts | mean |", "|---|---|---|"]
        for kind, stats in result["per_kind"].items():
            lines.append(f"| {kind} | {stats['verdicts']} | {stats['mean']} |")
        if result["unmatched_keys"]:
            lines += ["", "Judge returned dimension names that match no rubric entry "
                          "(excluded from the tables above, listed so nothing disappears quietly):", ""]
            for name, count in sorted(result["unmatched_keys"].items(), key=lambda kv: -kv[1]):
                lines.append(f"* `{name}` x{count}")
        lines.append("")

    if len(results) > 1:
        lines += ["## Axis comparison", "",
                  "Each axis grades its own document set against its own rubric, so these are",
                  "rubric-fit scores rather than a head-to-head grade of one text.", "",
                  "| axis | documents | dimensions | overall mean | main dimensions |",
                  "|---|---|---|---|---|"]
        for result in results:
            lines.append(f"| {result['axis']} | {result['documents']} "
                         f"| {result['dimensions_asked']} | {result['overall_mean']} "
                         f"| {len(result['main_dimensions'])} |")
        lines += ["", "| repo | " + " | ".join(r["axis"] for r in results) + " |",
                  "|---|" + "---|" * len(results)]
        repos = sorted({repo for r in results for repo in r["per_repo"]})
        for repo in repos:
            cells = []
            for result in results:
                value = (result["per_repo"].get(repo) or {}).get("mean")
                cells.append("—" if value is None else str(value))
            lines.append(f"| {repo} | " + " | ".join(cells) + " |")
        lines.append("")

    (ANALYSIS / f"matrix_scores{tag}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ANALYSIS / f"matrix_scores{tag}.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    # one flat CSV per axis, for LaTeX tables
    for result in results:
        rows = ["main_dimension,dimension,n,mean,sd"]
        for row in result["dimensions"]:
            rows.append(f"\"{row['category']}\",\"{row['dimension']}\",{row['n']},"
                        f"{row['mean'] if row['mean'] is not None else ''},{row['sd'] or ''}")
        (ANALYSIS / f"matrix_scores{tag}_{result['axis']}.csv").write_text(
            "\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--axes", nargs="+", default=list(AXES))
    ap.add_argument("--repos", nargs="+", default=None)
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit-docs", type=int, default=0)
    ap.add_argument("--judge-url", default=None)
    ap.add_argument("--judge-model", default=None)
    ap.add_argument("--docs-root", default=str(MATRIX),
                    help="root holding the documents (default outputs/matrix)")
    ap.add_argument("--layout", choices=["matrix", "flat"], default="matrix",
                    help="matrix: <root>/<axis>/<repo>; flat: <root>/<repo> scored per axis")
    ap.add_argument("--report-tag", default="", help="suffix for the report files")
    ap.add_argument("--report-only", action="store_true",
                    help="skip judging, only re-aggregate existing score files")
    args = ap.parse_args()
    if args.judge_url:
        DEFAULTS["base_url"] = args.judge_url
    if args.judge_model:
        DEFAULTS["model"] = args.judge_model
    globals()["DOCS_ROOT"] = Path(args.docs_root)
    globals()["LAYOUT"] = args.layout

    if not args.report_only:
        api_key = os.environ.get("JUDGE_KEY") or os.environ.get("LLM_KEY", "")
        if not api_key:
            print("JUDGE_KEY (or LLM_KEY) is not set; refusing to run")
            return 2
        root_for_repos = DOCS_ROOT if LAYOUT == "flat" else DOCS_ROOT / args.axes[0]
        repos = args.repos or sorted(p.name for p in root_for_repos.iterdir() if p.is_dir())
        qname_maps = {repo: build_qname_map(repo, args.limit, args.seed) for repo in repos}
        criteria_sets = {axis: rubric_for(axis) for axis in args.axes}

        tasks = []
        for axis in args.axes:
            for repo in repos:
                docs_dir = doc_dir(axis, repo)
                if not docs_dir.is_dir():
                    continue
                score_dir = docs_dir / f"scores_{axis}"
                score_dir.mkdir(parents=True, exist_ok=True)
                docs = sorted(docs_dir.glob("*.md"))
                if args.limit_docs:
                    docs = docs[:args.limit_docs]
                for doc in docs:
                    out = score_dir / f"{doc.stem}.json"
                    if out.exists() and out.stat().st_size > 0:
                        continue
                    tasks.append({"axis": axis, "repo": repo, "doc": doc, "out": out,
                                  "info": qname_maps.get(repo, {}).get(doc.stem, {})})

        print(f"documents to judge: {len(tasks)} (already-scored skipped)")
        if tasks:
            before = [r for r in RECORDER.records if r.get("phase", "").startswith("judge")]
            stats = run_judging(args, tasks, criteria_sets, api_key)
            mine = [r for r in RECORDER.records
                    if r.get("phase", "").startswith("judge")][len(before):]
            prompt_tokens = sum(r["prompt_tokens"] for r in mine)
            completion_tokens = sum(r["completion_tokens"] for r in mine)
            cached = sum(r.get("cached_tokens", 0) for r in mine)
            cost = (max(0, prompt_tokens - cached) / 1e6 * JUDGE_PRICE["input"]
                    + cached / 1e6 * JUDGE_PRICE["cached_input"]
                    + completion_tokens / 1e6 * JUDGE_PRICE["output"])
            print(f"judged {stats['done']}, failed {stats['failed']}, "
                  f"unparsed {stats['unparsed']}, "
                  f"{(time.time() - stats['started']) / 60:.1f} min")
            print(f"judge tokens: in {prompt_tokens:,} (cached {cached:,}) / "
                  f"out {completion_tokens:,} -> {JUDGE_PRICE['currency']} {cost:.2f}")

    results = [aggregate(axis) for axis in args.axes]
    write_reports(results, args.report_tag)
    for result in results:
        print(f"\n{result['axis']}: {result['documents']} docs, "
              f"overall {result['overall_mean']}, "
              f"{len(result['main_dimensions'])} main dimensions")
        for row in result["main_dimensions"]:
            print(f"   {row['category']:<34} {row['mean_of_dimension_means']}")
    print(f"\nreport: {ANALYSIS / f'matrix_scores{args.report_tag}.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
