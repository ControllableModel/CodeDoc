"""Run the MemDocAgent baseline (NeurIPS 2026) over the sampled entities.

MemDocAgent (Bae et al., "Remember Your Trace", arXiv:2605.14563) walks the repository in
dependency order and documents one component at a time, so its unit matches ours exactly:
``documentation.json`` is keyed by qualified name. The harness only has to cut that file
back into one document per sampled entity.

The public release does not run as shipped; six repairs are needed and are recorded in the
artifact (see ``third_party/README-memdocagent.md``):

1. the OpenAI client cannot target an OpenAI-compatible gateway;
2. ``gpt-6-luna`` is missing from the ``max_completion_tokens`` model test;
3. ``agent/base.py`` -- the ``BaseAgent`` that ``WorkerAgent`` inherits and whose
   ``_memory`` it uses 73 times -- is absent from the release;
4. ``agent/__init__.py`` imports a module the release no longer contains;
5. ``llm/factory.py`` imports ``torch`` at module scope, so the OpenAI path demanded a
   multi-gigabyte GPU dependency;
6. the restored ``base.py`` passes ``max_tokens`` to a method that now takes
   ``max_output_tokens``.

Two behaviours are *not* repaired, because they are the system under test: an empty
document is written when a component's ReAct loop ends without a draft, and those empty
documents are counted as missing rather than scored.

Usage::

    python scripts/run_memdocagent.py --repos flask-main joblib sonnet
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from run_repoagent import prepare as prepare_pruned  # noqa: E402
from run_repoagent import sample_map  # noqa: E402

TOOL = ROOT / "third_party" / "MemDocAgent"
PY = ROOT / "third_party" / ".venv-codewiki" / "Scripts" / "python.exe"
WORK = ROOT / "third_party" / "mdwork_src"
OUTDIR = ROOT / "third_party" / "mdwork"
OUT = ROOT / "outputs" / "baselines" / "memdocagent"


def safe_name(qname: str) -> str:
    return (qname.replace(".", "_").replace("/", "_").replace("#", "_")
            .replace("<", "_").replace(">", "_"))


def run_tool(repo: str, work: Path, timeout: int, wanted_ids: list) -> dict:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = f"{TOOL}{os.pathsep}{TOOL / 'src'}"
    env["TOKENIZERS_PARALLELISM"] = "false"
    # Restrict the tool to the sampled components; its own pruning is per file, so without
    # this a 60-entity sample still documents every component in those files.
    allow = OUTDIR / repo / "only.json"
    allow.parent.mkdir(parents=True, exist_ok=True)
    allow.write_text(json.dumps(sorted(wanted_ids)), encoding="utf-8")
    env["MEMDOC_ONLY"] = str(allow)
    cmd = [str(PY), "main.py",
           "--repo-path", str(work),
           "--config-path", "config/agent_config.yaml",
           "--output-dir", str(OUTDIR / repo),
           "--mode", "default"]
    started = time.time()
    # Output goes to a file, never a pipe: these agents print per-component reasoning
    # traces, which overflow the OS pipe buffer and deadlock a capturing parent long
    # before the run finishes.
    log_path = OUTDIR / repo / "run.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timed_out = False
    with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
        try:
            result = subprocess.run(cmd, cwd=str(TOOL), stdout=fh,
                                    stderr=subprocess.STDOUT, env=env, timeout=timeout)
            rc = result.returncode
        except subprocess.TimeoutExpired:
            rc, timed_out = -1, True
    text = log_path.read_text(encoding="utf-8", errors="replace")
    tail = text[-4000:]
    if timed_out:
        tail += f"\n[timed out after {timeout}s]"
    return {"seconds": round(time.time() - started, 1), "returncode": rc,
            "log_path": str(log_path), "stdout_tail": tail, "stderr_tail": ""}


def adapt(repo: str, by_file: dict) -> dict:
    payload = OUTDIR / repo / "documentation" / repo / "documentation.json"
    out_dir = OUT / repo
    out_dir.mkdir(parents=True, exist_ok=True)
    if not payload.exists():
        return {"written": 0, "empty": [], "missing": [e["qname"] for es in by_file.values() for e in es],
                "error": f"missing {payload}"}
    data = json.loads(payload.read_text(encoding="utf-8"))
    components = data.get("components", {})
    written, empty, missing = 0, [], []
    for _rel, entities in by_file.items():
        for entity in entities:
            entry = components.get(entity["qname"])
            if entry is None:
                missing.append(entity["qname"])
                continue
            body = (entry.get("documentation") or "").strip()
            if not body:
                empty.append(entity["qname"])
                continue
            header = f"# `{entity['qname']}`\n\n"
            (out_dir / f"{safe_name(entity['qname'])}.md").write_text(
                header + body + "\n", encoding="utf-8")
            written += 1
    return {"written": written, "empty": empty, "missing": missing,
            "tool_components": len(components), "elapsed_seconds": data.get("elapsed_seconds")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", nargs="+", required=True)
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--timeout", type=int, default=14400)
    ap.add_argument("--reuse-work", action="store_true", default=True)
    ap.add_argument("--only-missing", action="store_true",
                    help="re-document only entities that have no document yet")
    args = ap.parse_args()

    if not PY.exists():
        print(f"python not found at {PY}")
        return 2
    summary_path = OUT / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else []
    for repo in args.repos:
        by_file = sample_map(repo, args.limit, args.seed)
        if not by_file:
            print(f"skip {repo}: no sampled entities")
            continue
        work = WORK / repo
        if not work.exists() or not args.reuse_work:
            import run_repoagent
            original = run_repoagent.WORK
            run_repoagent.WORK = WORK
            try:
                work = prepare_pruned(repo, by_file)
            finally:
                run_repoagent.WORK = original
        if args.only_missing:
            existing = {p.stem for p in (OUT / repo).glob("*.md")}
            filtered = {}
            for rel, ents in by_file.items():
                keep = [e for e in ents if safe_name(e["qname"]) not in existing]
                if keep:
                    filtered[rel] = keep
            skipped = sum(len(v) for v in by_file.values()) - sum(len(v) for v in filtered.values())
            print(f"{repo}: --only-missing skips {skipped} already documented", flush=True)
            by_file = filtered
            if not by_file:
                print(f"{repo}: nothing left to do", flush=True)
                continue
        entities = sum(len(v) for v in by_file.values())
        print(f"{repo}: {entities} entities in {len(by_file)} files -> {work}", flush=True)
        wanted = [e["qname"] for ents in by_file.values() for e in ents]
        result = run_tool(repo, work, args.timeout, wanted)
        print(f"  tool: rc={result['returncode']} {result['seconds']}s", flush=True)
        adapted = adapt(repo, by_file)
        print(f"  adapted: {adapted['written']} documents, {len(adapted['empty'])} empty, "
              f"{len(adapted['missing'])} missing", flush=True)
        if adapted.get("error"):
            print(f"  {adapted['error']}", flush=True)
        summary = [s for s in summary if s.get("repo") != repo]
        summary.append({"repo": repo, "entities": entities, "files": len(by_file),
                        "seconds": result["seconds"], "returncode": result["returncode"],
                        "tool_components": adapted.get("tool_components"),
                        "written": adapted["written"], "empty": adapted["empty"],
                        "missing": adapted["missing"], "error": adapted.get("error")})
        OUT.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    total_w = sum(s["written"] for s in summary)
    total_e = sum(s["entities"] for s in summary)
    print(f"\ncoverage: {total_w}/{total_e} entities documented with content")
    print(f"summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
