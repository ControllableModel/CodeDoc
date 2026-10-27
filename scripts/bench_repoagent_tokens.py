#!/usr/bin/python3
# _*_ coding: utf-8 _*_
"""Measure RepoAgent's token consumption per repository.

RepoAgent logs its token usage at DEBUG only (``chat_engine.py``), so the runs that produced
the scored documents left no usage trail behind: ``run_repoagent.py`` captures stdout in
memory and keeps the last 4 KB. This driver re-runs RepoAgent on a throwaway copy of each
target with ``-ll DEBUG`` and parses the two debug lines into a per-repository table.

Three deliberate choices:

* **Throwaway workspace.** The documents this run produces are *not* the ones that were
  scored; regenerating them would silently change the comparison. The copy is deleted after
  the tokens are read.
* **Clean state.** ``markdown_docs`` and ``.project_doc_record`` are removed first, because
  RepoAgent skips files it believes are already documented and would report zero usage.
* **Output redirected to a file, never a pipe.** The earlier attempt to read RepoAgent's
  output through ``subprocess`` pipes deadlocked at 64 KB; a log file has no such limit.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOAGENT = ROOT / "third_party" / "RepoAgent"
VENV_PYTHON = ROOT / "third_party" / ".venv-repoagent311" / "Scripts" / "python.exe"
TARGETS = ROOT / "targets"
WORKROOT = ROOT / "third_party" / "rawork_tokenbench"
REPORT = ROOT / "results" / "analysis" / "repoagent_tokens.json"

MODEL = os.environ.get("MODEL", "gpt-6-luna")
BASE_URL = os.environ.get("LLM_URL", "https://apic1.ohmycdn.com/v1")

PROMPT_RE = re.compile(r"LLM Prompt Tokens:\s*(\d+)")
COMPLETION_RE = re.compile(r"LLM Completion Tokens:\s*(\d+)")


def _force_rmtree(path: Path) -> None:
    """Remove a tree even when contained git objects are read-only.

    ``shutil.rmtree(..., ignore_errors=True)`` silently leaves files behind on Windows when
    git marks objects read-only, and the following ``copytree`` then fails with WinError 183.
    Clearing the read-only bit and retrying makes the workspace reusable across runs.
    """
    def on_error(func, target, _exc):
        try:
            os.chmod(target, 0o700)
            func(target)
        except Exception:
            pass
    if path.exists():
        shutil.rmtree(path, onerror=on_error)
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)


def run_one(repo: str, threads: int, timeout: int) -> dict:
    work = WORKROOT / f"{repo}-{int(time.time())}"
    _force_rmtree(work)
    shutil.copytree(TARGETS / repo, work)
    for stale in ("markdown_docs", ".project_doc_record"):
        _force_rmtree(work / stale)

    # RepoAgent's change detector opens the target with GitPython and raises
    # InvalidGitRepositoryError on a plain directory. The pruned target copies are not
    # repositories, so each throwaway copy gets its own one-commit history. ``-q`` and
    # check=False because a repo whose files are already all committed needs no work here.
    for cmd in (
        ["git", "init", "-q"],
        ["git", "-c", "user.name=bench", "-c", "user.email=bench@local", "add", "-A"],
        ["git", "-c", "user.name=bench", "-c", "user.email=bench@local",
         "commit", "-q", "-m", "bench snapshot"],
    ):
        subprocess.run(cmd, cwd=str(work), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")

    env = dict(os.environ)
    env["OPENAI_API_KEY"] = os.environ.get("LLM_KEY", "")
    env["LLM_KEY"] = os.environ.get("LLM_KEY", "")
    env["PYTHONIOENCODING"] = "utf-8"
    log = ROOT / "results" / "analysis" / f"repoagent_tokens_{repo}.log"

    cmd = [
        str(VENV_PYTHON), "-m", "repo_agent", "run",
        "-m", MODEL, "-b", BASE_URL, "-t", "1",
        "-tp", str(work), "-mdp", "markdown_docs",
        "-mtc", str(threads), "-r", str(timeout), "-l", "English",
        "-ll", "DEBUG",
    ]
    started = time.time()
    with log.open("w", encoding="utf-8", errors="replace") as fh:
        proc = subprocess.run(cmd, cwd=str(REPOAGENT), env=env,
                              stdout=fh, stderr=subprocess.STDOUT)
    elapsed = time.time() - started

    text = log.read_text(encoding="utf-8", errors="replace")
    prompt_tokens = [int(x) for x in PROMPT_RE.findall(text)]
    completion_tokens = [int(x) for x in COMPLETION_RE.findall(text)]
    docs = list((work / "markdown_docs").rglob("*.md")) if (work / "markdown_docs").exists() else []

    result = {
        "repo": repo,
        "returncode": proc.returncode,
        "seconds": round(elapsed, 1),
        "calls": len(prompt_tokens),
        "prompt_tokens": sum(prompt_tokens),
        "completion_tokens": sum(completion_tokens),
        "documents": len(docs),
        "log": str(log.relative_to(ROOT)),
    }
    if prompt_tokens:
        result["in_per_call"] = round(sum(prompt_tokens) / len(prompt_tokens), 1)
        result["out_per_call"] = round(sum(completion_tokens) / len(prompt_tokens), 1)
    _force_rmtree(work)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", nargs="+", default=None)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--skip-existing", action="store_true",
                    help="keep repositories already present in the report")
    args = ap.parse_args()

    if not os.environ.get("LLM_KEY"):
        print("no LLM_KEY in the environment")
        return 2

    existing = {}
    if REPORT.exists():
        try:
            existing = json.loads(REPORT.read_text(encoding="utf-8")).get("repos", {})
        except Exception:
            existing = {}

    repos = args.repos or sorted(p.name for p in TARGETS.iterdir() if p.is_dir())
    results = dict(existing)
    for repo in repos:
        if args.skip_existing and repo in results and results[repo].get("calls"):
            print(f"skip {repo}: already measured", flush=True)
            continue
        if not (TARGETS / repo).exists():
            print(f"skip {repo}: not under targets/", flush=True)
            continue
        print(f"{repo}: running (this regenerates documents in a throwaway copy)", flush=True)
        try:
            res = run_one(repo, args.threads, args.timeout)
        except Exception as exc:  # noqa: BLE001 - one repository must not abort the table
            res = {"repo": repo, "error": f"{type(exc).__name__}: {exc}"}
        results[repo] = res
        print(f"  rc={res.get('returncode')} calls={res.get('calls')} "
              f"in={res.get('prompt_tokens')} out={res.get('completion_tokens')} "
              f"{res.get('seconds')}s", flush=True)
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps({
            "model": MODEL,
            "measured_at": datetime.now().isoformat(timespec="seconds"),
            "repos": results,
        }, indent=2, ensure_ascii=False), encoding="utf-8")

    total_in = sum(v.get("prompt_tokens", 0) for v in results.values())
    total_out = sum(v.get("completion_tokens", 0) for v in results.values())
    total_calls = sum(v.get("calls", 0) for v in results.values())
    print(f"\ntotal: {len(results)} repos, {total_calls} calls, "
          f"{total_in:,} in / {total_out:,} out")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
