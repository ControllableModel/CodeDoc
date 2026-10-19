"""Measure how batch generation scales with concurrency.

gpt-6-luna needs about 25 s per entity, so the whole-corpus run is only practical if
throughput scales with workers. This driver measures that, and appends every completed
configuration to the results file immediately, so an interrupted run keeps whatever it
already paid for.

Usage::

    python scripts/bench_concurrency.py --repo ragflow --limit 8 --workers 1 2 4 8 12
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_MD = ROOT / "results" / "analysis" / "concurrency_scaling.md"
OUT_JSON = ROOT / "results" / "analysis" / "concurrency_scaling.json"


def post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def run_once(base: str, repo: str, limit: int, seed: int, workers: int) -> dict:
    started = time.time()
    job = post(f"{base}/api/generate_all", {
        "repo": repo, "mode": "sample", "limit": limit, "seed": seed, "workers": workers,
    })["job"]
    progress: dict = {}
    for _ in range(1800):          # up to 15 minutes per configuration
        time.sleep(0.5)
        status = get(f"{base}/api/job?id={job}")
        if status.get("status") != "running":
            progress = status.get("progress", {})
            break
    elapsed = time.time() - started
    done = max(1, int(progress.get("done") or 0))
    return {
        "workers": workers,
        "elapsed_seconds": round(elapsed, 1),
        "done": progress.get("done", 0),
        "failed": progress.get("failed", 0),
        "entities_per_minute": round(done / elapsed * 60, 2),
        "seconds_per_entity": round(elapsed / done, 2),
        "prompt_tokens": progress.get("prompt_tokens", 0),
        "completion_tokens": progress.get("completion_tokens", 0),
        "cached_tokens": progress.get("cached_tokens", 0),
        "cost": progress.get("cost", 0.0),
        "cost_per_entity": round((progress.get("cost") or 0) / done, 6),
        "currency": progress.get("currency", "USD"),
    }


def write_report(rows: list) -> None:
    header = [
        "# Batch concurrency scaling",
        "",
        "* endpoint: gpt-6-luna, priced in USD (standard / short context)",
        "* each configuration runs the same sampled entity set, so the work is identical",
        "",
        "| workers | wall (s) | entities | failed | entities/min | s/entity | cost/entity |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        header.append(
            "| {workers} | {elapsed_seconds} | {done} | {failed} | {entities_per_minute} "
            "| {seconds_per_entity} | ${cost_per_entity} |".format(**row)
        )
    if len(rows) >= 2:
        serial = next((r for r in rows if r["workers"] == 1), None)
        best = max(rows, key=lambda r: r["entities_per_minute"])
        header += ["", f"* peak throughput: {best['entities_per_minute']} entities/min "
                       f"at {best['workers']} workers"]
        if serial:
            header.append(
                f"* speed-up over serial: {best['entities_per_minute'] / serial['entities_per_minute']:.1f}x"
            )
    OUT_MD.write_text("\n".join(header) + "\n", encoding="utf-8")
    OUT_JSON.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="http://127.0.0.1:8765")
    ap.add_argument("--repo", default="ragflow")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--seed", type=int, default=21)
    ap.add_argument("--workers", type=int, nargs="+", default=[1, 2, 4, 8])
    args = ap.parse_args()

    rows: list = []
    if OUT_JSON.exists():
        try:
            rows = json.loads(OUT_JSON.read_text(encoding="utf-8"))
        except ValueError:
            rows = []

    for workers in args.workers:
        if any(r.get("workers") == workers and r.get("done") for r in rows):
            print(f"skip workers={workers} (already measured)")
            continue
        print(f"running workers={workers} ...")
        try:
            row = run_once(args.base, args.repo, args.limit, args.seed, workers)
        except Exception as exc:  # noqa: BLE001 - keep the earlier rows
            print(f"  failed: {type(exc).__name__}: {exc}")
            continue
        rows = [r for r in rows if r.get("workers") != workers] + [row]
        rows.sort(key=lambda r: r["workers"])
        write_report(rows)
        print(f"  {row['elapsed_seconds']}s, {row['entities_per_minute']} entities/min, "
              f"failed={row['failed']}, ${row['cost_per_entity']}/entity")
    write_report(rows)
    print(f"written: {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
