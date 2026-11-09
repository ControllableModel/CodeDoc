"""Run the per-dimension (M) judging for every method, repository and axis.

Sequential and resumable: judge_matrix.py skips any document that already has a score
file, so re-running this after an interruption picks up where it stopped.

Scale, measured on the flask ISO pilot (60 documents, 14 dimensions, 12 workers):
6.6 minutes, 1.10M judge input tokens, CNY 2.96.

Sources differ in layout:
  CodeDoc      outputs/matrix_v6                    matrix layout (<root>/<axis>/<repo>)
  RepoAgent    outputs/baselines/repoagent          flat layout   (<root>/<repo>)
  MemDocAgent  outputs/baselines/memdocagent        flat layout   (<root>/<repo>)

Usage::

    python scripts/run_m_judging.py                 # everything still missing
    python scripts/run_m_judging.py --axes github_docs_style
    python scripts/run_m_judging.py --only CodeDoc
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
CONFIG = ROOT / "webapp" / "config.local.json"

SOURCES = {
    "CodeDoc": ("outputs/matrix_v6", "matrix"),
    "RepoAgent": ("outputs/baselines/repoagent", "flat"),
    "MemDocAgent": ("outputs/baselines/memdocagent", "flat"),
}
AXES = ("iso_26514", "github_docs_style")


def judge_key() -> str:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    return cfg.get("judge_api_key") or cfg.get("api_key") or ""


def doc_count(root: str, layout: str, axis: str, repo: str) -> int:
    base = ROOT / root / axis / repo if layout == "matrix" else ROOT / root / repo
    return len(list(base.glob("*.md"))) if base.is_dir() else 0


def repos(root: str, layout: str, axis: str) -> list:
    base = ROOT / root / axis if layout == "matrix" else ROOT / root
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.iterdir()
                  if p.is_dir() and doc_count(root, layout, axis, p.name))


def pending(root: str, layout: str, axis: str, repo: str, limit: int = 0) -> int:
    base = ROOT / root / axis / repo if layout == "matrix" else ROOT / root / repo
    scored = base / f"scores_{axis}_M"
    have = {p.stem for p in scored.glob("*.json")} if scored.is_dir() else set()
    docs = sorted(base.glob("*.md"))
    if limit:
        docs = docs[:limit]
    return sum(1 for p in docs if p.stem not in have)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--axes", nargs="+", default=list(AXES))
    ap.add_argument("--only", nargs="+", default=list(SOURCES))
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--limit-docs", type=int, default=0,
                    help="judge only the first N documents of each repository (0 = all)")
    args = ap.parse_args()

    key = judge_key()
    if not key:
        print("  no judge key in webapp/config.local.json")
        return 2
    env = dict(os.environ, JUDGE_KEY=key, PYTHONPATH=str(ROOT),
               PYTHONIOENCODING="utf-8")
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if cfg.get("judge_base_url"):
        env["JUDGE_URL"] = cfg["judge_base_url"]
    if cfg.get("judge_model"):
        env["JUDGE_MODEL"] = cfg["judge_model"]

    planned = []
    for axis in args.axes:
        for source in args.only:
            root, layout = SOURCES[source]
            for repo in repos(root, layout, axis):
                n = pending(root, layout, axis, repo, args.limit_docs)
                if n:
                    planned.append((source, axis, repo, n))
    total = sum(p[3] for p in planned)
    print(f"  {len(planned)} runs, {total} documents to judge", flush=True)
    for source, axis, repo, n in planned:
        print(f"    {source:<12}{axis:<18}{repo:<12}{n:>4} docs", flush=True)

    started = time.time()
    for index, (source, axis, repo, n) in enumerate(planned, 1):
        root, layout = SOURCES[source]
        tag = f"_{source}_{axis}_M"
        cmd = [PY, str(ROOT / "scripts" / "judge_matrix.py"),
               "--mode", "per-dim", "--axes", axis, "--repos", repo,
               "--layout", layout, "--docs-root", str(ROOT / root),
               "--workers", str(args.workers), "--report-tag", tag]
        if args.limit_docs:
            cmd += ["--limit-docs", str(args.limit_docs)]
        print(f"\n[{index}/{len(planned)}] {source} {axis} {repo} ({n} docs) "
              f"elapsed {time.time() - started:.0f}s", flush=True)
        done = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        tail = (done.stdout or "").strip().splitlines()[-6:]
        for line in tail:
            print("    " + line, flush=True)
        if done.returncode != 0:
            print("    stderr: " + (done.stderr or "")[-500:], flush=True)
        Path(ROOT / "results" / "analysis" / "m_judging.log").open("a", encoding="utf-8").write(
            f"\n=== {source} {axis} {repo} rc={done.returncode} ===\n"
            + (done.stdout or "")[-4000:] + (done.stderr or "")[-2000:])

    print(f"\n  finished in {(time.time() - started) / 60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
