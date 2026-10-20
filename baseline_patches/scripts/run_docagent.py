"""Run the DocAgent baseline (facebookresearch/DocAgent, ACL 2025 demo).

DocAgent writes docstrings back into the source files rather than emitting documents, so
the harness works in three steps: prepare a pruned working copy holding only the sampled
entities, run DocAgent's generator over it, then read the docstrings it wrote and save one
document per sampled entity so the same judge can score it.

Disclosures that belong in the paper, not just here:

* DocAgent's Searcher agent retrieves external context through Perplexity, and no
  Perplexity key is available for this study. The retrieval path degrades to empty on its
  own, so the four-agent system runs with three agents doing work.
* DocAgent's output unit is a *docstring*, while the rubrics were written for documents.
  Scores from the ISO and GitHub rubrics therefore answer "how good is this docstring as
  documentation", not "is this a good document"; Report it as a docstring-unit baseline.
* Two local patches were needed and are recorded in the artifact: the OpenAI client had no
  way to point at an OpenAI-compatible gateway, and the provider imports were made lazy
  because only the OpenAI path is used.

Usage::

    python scripts/run_docagent.py --repo ragflow
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.config import TARGETS  # noqa: E402

# reuse the RepoAgent sampler and pruner so both baselines see the identical entity set
sys.path.insert(0, str(ROOT / "scripts"))
from run_repoagent import prepare as prepare_pruned  # noqa: E402
from run_repoagent import sample_map  # noqa: E402

DOCAGENT = ROOT / "third_party" / "DocAgent"
SITE = ROOT / "third_party" / "docagent_site310"
WORK = ROOT / "third_party" / "dawork"
OUT = ROOT / "outputs" / "baselines" / "docagent"
PYTHON_310 = Path("E:/miniconda/envs/Scalpel/python.exe")


def safe_name(qname: str) -> str:
    return (qname.replace(".", "_").replace("/", "_").replace("#", "_")
            .replace("<", "_").replace(">", "_"))


def run_docagent(work: Path, timeout: int) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{SITE}{os.pathsep}{DOCAGENT / 'src'}"
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [
        str(PYTHON_310), "generate_docstrings.py",
        "--repo-path", str(work),
        "--config-path", "config/agent_config.yaml",
        "--order-mode", "topo",
        "--overwrite-docstrings",
    ]
    started = time.time()
    result = subprocess.run(cmd, cwd=str(DOCAGENT), capture_output=True, text=True,
                            encoding="utf-8", errors="replace", env=env, timeout=timeout)
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    # DocAgent prints its own cost summary; capture it rather than estimating.
    import re
    cost = None
    for match in re.finditer(r"TOTAL COST:\s*\$([0-9.]+)", stdout):
        cost = float(match.group(1))
    requests = None
    for match in re.finditer(r"Total Requests:\s*(\d+)", stdout):
        requests = int(match.group(1))
    return {
        "seconds": round(time.time() - started, 1),
        "returncode": result.returncode,
        "cost_usd": cost,
        "requests": requests,
        "stdout_tail": stdout[-6000:],
        "stderr_tail": stderr[-3000:],
    }


def docstring_map(source_path: Path) -> dict:
    """entity name -> docstring, for every definition in a module."""
    try:
        tree = ast.parse(source_path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return {}
    found: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node) or ""
            if doc.strip():
                found.setdefault(node.name, []).append(doc)
    return found


def adapt(repo: str, by_file: dict, work: Path) -> dict:
    out_dir = OUT / repo
    out_dir.mkdir(parents=True, exist_ok=True)
    written, missing = 0, []
    for rel, entities in by_file.items():
        path = work / rel
        found = docstring_map(path) if path.exists() else {}
        for entity in entities:
            docs = found.get(entity["name"]) or []
            body = max(docs, key=len) if docs else ""
            if not body.strip():
                missing.append(entity["qname"])
                continue
            header = f"# `{entity['qname']}`\n\n"
            (out_dir / f"{safe_name(entity['qname'])}.md").write_text(
                header + body.strip() + "\n", encoding="utf-8")
            written += 1
    return {"written": written, "missing": missing}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", nargs="+", default=None)
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--timeout", type=int, default=7200)
    ap.add_argument("--reuse-work", action="store_true")
    args = ap.parse_args()

    if not PYTHON_310.exists():
        print(f"python 3.10 not found at {PYTHON_310}")
        return 2
    repos = args.repos or ["ragflow"]
    summary = []
    for repo in repos:
        by_file = sample_map(repo, args.limit, args.seed)
        if not by_file:
            print(f"skip {repo}: no sampled entities")
            continue
        work = WORK / repo
        if not args.reuse_work:
            # prepare_pruned hardcodes WORK under rawork; point it at dawork instead
            import run_repoagent
            original = run_repoagent.WORK
            run_repoagent.WORK = WORK
            try:
                work = prepare_pruned(repo, by_file)
            finally:
                run_repoagent.WORK = original
        entities = sum(len(v) for v in by_file.values())
        print(f"{repo}: {entities} entities in {len(by_file)} files -> {work}", flush=True)
        result = run_docagent(work, args.timeout)
        print(f"  docagent: rc={result['returncode']} {result['seconds']}s"
              f" cost=${result.get('cost_usd')} requests={result.get('requests')}", flush=True)
        if result["returncode"] != 0:
            print((result["stderr_tail"] or result["stdout_tail"])[-1500:], flush=True)
        adapted = adapt(repo, by_file, work)
        print(f"  adapted: {adapted['written']} documents, "
              f"{len(adapted['missing'])} missing", flush=True)
        summary.append({"repo": repo, "entities": entities, "files": len(by_file),
                        "seconds": result["seconds"], "returncode": result["returncode"],
                        "cost_usd": result.get("cost_usd"),
                        "requests": result.get("requests"),
                        "written": adapted["written"],
                        "missing": adapted["missing"][:50]})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nsummary: {OUT / 'run_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
