"""Run the Agentic Doc baseline (ishkapoor2000/agentic-ai) over the sampled entities.

Agentic Doc is a *file-level* generator: it writes one markdown per source file, with a
``## Purpose`` section and nested ``### <symbol>`` subsections. That is the same granularity
as RepoAgent, so the outputs can be cut back to the entity level and scored by the same
judge as the other methods.

Three local patches were required and are recorded in the artifact:

* the OpenAI client had no way to target an OpenAI-compatible gateway;
* ``config_manager.py`` ships with a stray markdown code fence at end of file, which is a
  syntax error (the tool's own config validation fails on a fresh install);
* a failing cache insert (SQLModel rejects the naive datetime default) used to abort the
  document that had just been generated, throwing away paid tokens.

Two upstream limitations that are *not* patched, because they are the tool's design and part
of what the comparison measures:

* the prompt truncates file content to 10,000 characters, so large modules are documented
  from a prefix only;
* all files are documented, not just the sampled entities, so the adapter reports how many
  sampled entities could be recovered from the prose.

Usage::

    python scripts/run_agenticdoc.py --repo flask-main
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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from run_repoagent import prepare as prepare_pruned  # noqa: E402
from run_repoagent import sample_map  # noqa: E402


def safe_name(qname: str) -> str:
    return (qname.replace(".", "_").replace("/", "_").replace("#", "_")
            .replace("<", "_").replace(">", "_"))

WORK = ROOT / "third_party" / "agwork"
OUT = ROOT / "outputs" / "baselines" / "agenticdoc"
CLI = ROOT / "third_party" / ".venv-codewiki" / "Scripts" / "agentic-doc.exe"

CONFIG = """root_path: .
include_globs:
- '**/*.py'
exclude_globs:
- '**/node_modules/**'
- '**/.git/**'
- '**/__pycache__/**'
- '**/.venv/**'
model_provider: openai
openai_model: gpt-6-luna
gemini_model: gemini-2.5-flash
"""


def env_for_run() -> dict:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env["OPENAI_API_KEY"] = os.environ.get("GEN_KEY", "")
    env["OPENAI_BASE_URL"] = os.environ.get("GEN_URL", "https://apic1.ohmycdn.com/v1")
    return env


def run_cli(work: Path, args: list, timeout: int) -> dict:
    started = time.time()
    result = subprocess.run([str(CLI), *args], cwd=str(work), capture_output=True,
                            text=True, encoding="utf-8", errors="replace",
                            env=env_for_run(), timeout=timeout)
    out = (result.stdout or "") + (result.stderr or "")
    requests = None
    for match in re.finditer(r"Total Requests:\s*(\d+)", out):
        requests = int(match.group(1))
    return {"args": args, "seconds": round(time.time() - started, 1),
            "returncode": result.returncode, "requests": requests, "output": out[-4000:]}


# --------------------------------------------------------------------------- markdown

HEADING = re.compile(r"^(#{2,6})\s+(.*)$")


def headings(text: str) -> list:
    found = []
    offset = 0
    for line in text.splitlines(keepends=True):
        match = HEADING.match(line.rstrip("\n"))
        if match:
            found.append((offset, len(match.group(1)), match.group(2).strip()))
        offset += len(line)
    return found


def clean_title(title: str) -> str:
    return title.strip().strip("`").strip()


def block_for(text: str, heads: list, index: int) -> str:
    start_offset, level, _ = heads[index]
    end = len(text)
    for offset, other_level, _ in heads[index + 1:]:
        if other_level <= level:
            end = offset
            break
    return text[start_offset:end].strip()


def extract_entity(text: str, name: str) -> tuple:
    """Return (section_text, strength) for one entity, best effort."""
    heads = headings(text)
    # best heading match: an exact identifier in the title, shallowest depth preferred
    best = None
    for i, (_, level, title) in enumerate(heads):
        plain = clean_title(title)
        token = re.split(r"[\s(:`]", plain)[0].strip("`")
        if token == name or plain.strip("`") == name:
            if best is None or level < heads[best][1]:
                best = i
    if best is not None:
        return block_for(text, heads, best), "heading"

    # Fall back to the deepest section that names the entity. A file-level document often
    # covers several methods inside one subsection ("Lifecycle and messaging" -> start(),
    # stop(), send()), so handing the enclosing section to each of them is a fairer
    # attribution than a single bullet, and the duplication is inherent to the tool's unit.
    token = re.compile(rf"(?<![\w.]){re.escape(name)}(?![\w])")
    candidate = None
    for i, (_, level, _) in enumerate(heads):
        block = block_for(text, heads, i)
        if token.search(block):
            if candidate is None or level > heads[candidate][1]:
                candidate = i
    if candidate is not None:
        return block_for(text, heads, candidate), "enclosing"
    return "", "none"


def adapt(repo: str, by_file: dict, work: Path) -> dict:
    docs_dir = work / "docs" / "files"
    out_dir = OUT / repo
    out_dir.mkdir(parents=True, exist_ok=True)
    cache = {}
    written, weak, missing = 0, [], []
    for rel, entities in by_file.items():
        doc_path = docs_dir / f"{rel}.md"
        text = ""
        if doc_path.exists():
            if doc_path not in cache:
                cache[doc_path] = doc_path.read_text(encoding="utf-8", errors="replace")
            text = cache[doc_path]
        for entity in entities:
            body, strength = extract_entity(text, entity["name"]) if text else ("", "none")
            if strength == "none":
                missing.append({"qname": entity["qname"], "file": rel,
                                "has_file_doc": bool(text)})
                continue
            header = f"# `{entity['qname']}`\n\n"
            (out_dir / f"{safe_name(entity['qname'])}.md").write_text(
                header + body + "\n", encoding="utf-8")
            written += 1
            if strength == "enclosing":
                weak.append(entity["qname"])
    return {"written": written, "weak": weak, "missing": missing}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", nargs="+", default=None)
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--timeout", type=int, default=10800)
    ap.add_argument("--reuse-work", action="store_true")
    args = ap.parse_args()

    if not CLI.exists():
        print(f"agentic-doc CLI not found at {CLI}")
        return 2
    repos = args.repos or sorted({t.name for t in __import__("codedoc.config", fromlist=["x"]).TARGETS})[:10]
    summary = []
    for repo in repos:
        by_file = sample_map(repo, args.limit, args.seed)
        if not by_file:
            print(f"skip {repo}: no sampled entities")
            continue
        work = WORK / repo
        if not args.reuse_work:
            if work.exists():
                shutil.rmtree(work, ignore_errors=True)
            import run_repoagent
            original = run_repoagent.WORK
            run_repoagent.WORK = WORK
            try:
                work = prepare_pruned(repo, by_file)
            finally:
                run_repoagent.WORK = original
        (work / ".agentic-doc.yml").write_text(CONFIG, encoding="utf-8")
        entities = sum(len(v) for v in by_file.values())
        print(f"{repo}: {entities} entities in {len(by_file)} files -> {work}", flush=True)

        scan = run_cli(work, ["scan"], args.timeout)
        print(f"  scan: rc={scan['returncode']} {scan['seconds']}s", flush=True)
        doc = run_cli(work, ["doc", "files", "--limit", "2000", "--enhanced"], args.timeout)
        print(f"  doc:  rc={doc['returncode']} {doc['seconds']}s "
              f"requests={doc['requests']}", flush=True)
        if doc["returncode"] != 0:
            print(doc["output"][-1200:], flush=True)

        adapted = adapt(repo, by_file, work)
        print(f"  adapted: {adapted['written']} documents "
              f"({len(adapted['weak'])} from mention-only), "
              f"{len(adapted['missing'])} missing", flush=True)
        summary.append({"repo": repo, "entities": entities, "files": len(by_file),
                        "scan_seconds": scan["seconds"], "doc_seconds": doc["seconds"],
                        "requests": doc["requests"], "returncode": doc["returncode"],
                        "written": adapted["written"], "weak": adapted["weak"],
                        "missing": adapted["missing"]})
        (OUT).mkdir(parents=True, exist_ok=True)
        (OUT / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    total_written = sum(s["written"] for s in summary)
    total_entities = sum(s["entities"] for s in summary)
    print(f"\ncoverage: {total_written}/{total_entities} entities documented")
    print(f"summary: {OUT / 'run_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
