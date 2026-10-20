"""Run the RepoAgent baseline over the sampled entities of each repository.

RepoAgent generates documentation file by file, so the fair way to compare it with
CodeDoc on the same entity set is to give it the files those entities live in. The
working tree therefore holds *only* the files that contain at least one sampled entity,
preserving relative paths, and RepoAgent documents every entity inside them. Sections it
produces for entities outside the sample are simply not scored.

Its output is one markdown file per source file, with sections
``## ClassDef X`` / ``### FunctionDef method(...)`` / ``## FunctionDef f(...)``. The
adapter splits those sections into one document per sampled entity so the same judge can
score them.

Usage::

    python scripts/run_repoagent.py --repo ragflow --limit 60 --seed 42
    python scripts/run_repoagent.py --prepare-only --repos ragflow
"""

from __future__ import annotations

import argparse
import ast
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

from codedoc.config import TARGETS  # noqa: E402
from codedoc.deps.relations_index import build_index  # noqa: E402
from codedoc.sampling import pick_entities  # noqa: E402

REPOAGENT = ROOT / "third_party" / "RepoAgent"
VENV_PYTHON = ROOT / "third_party" / ".venv-repoagent311" / "Scripts" / "python.exe"
WORK = ROOT / "third_party" / "rawork"
OUT = ROOT / "outputs" / "baselines" / "repoagent"

BASE_URL = "https://apic1.ohmycdn.com/v1"
MODEL = "gpt-6-luna"
#: gpt-6-luna accepts only its default temperature; RepoAgent's CLI default of 0.2 is
#: rejected outright, which silently turns into endless retries. Pinned to 1 so the
#: baseline runs at the same sampling setting as CodeDoc.
TEMPERATURE = "1"


def sample_map(repo: str, limit: int, seed: int) -> dict:
    """Sampled entities, grouped by the source file they live in."""
    index = build_index(str(TARGETS / repo))
    if index is None:
        return {}
    repo_root = (TARGETS / repo).resolve()
    by_file: dict = {}
    for ctx in pick_entities(index, limit, seed):
        path = Path(ctx.entity.path).resolve()
        try:
            rel = path.relative_to(repo_root)
        except ValueError:
            continue
        by_file.setdefault(str(rel).replace("\\", "/"), []).append({
            "qname": ctx.entity.qualified_name,
            "name": ctx.entity.name.split(".")[-1],
            "kind": str(ctx.entity.kind),
            "owner": ctx.entity.qualified_name.split(".")[-2]
            if "." in ctx.entity.qualified_name and str(ctx.entity.kind) == "method" else "",
        })
    return by_file


def prune_source(text: str, wanted_classes: set, wanted_functions: set,
                 wanted_methods: dict) -> str:
    """Keep only the wanted top-level objects, plus the imports they need.

    RepoAgent documents every object it parses, so handing it a whole file would
    document far more entities than the sample contains (13,019 across the working trees
    against 578 sampled). Pruning keeps the comparison on the same entity set while
    leaving each kept object's source exactly as written: slices are taken from the
    original text, not re-generated.
    """
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text

    # A sampled entity may be nested (a closure inside a decorator, a class built inside
    # a factory). RepoAgent walks the whole AST, so it *can* document those, but only if
    # the enclosing definition is present: map every wanted name to its outermost
    # enclosing module-level statement and keep that.
    wanted_all = set(wanted_classes) | set(wanted_functions) | {
        name for names in wanted_methods.values() for name in names}
    outer_by_name: dict = {}

    def note_outer(node, outer):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            outer_by_name.setdefault(node.name, outer)
            for child in ast.iter_child_nodes(node):
                note_outer(child, outer)
        else:
            for child in ast.iter_child_nodes(node):
                note_outer(child, outer)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            note_outer(node, node)

    def outer_names_for(name: str) -> list:
        outer = outer_by_name.get(name)
        return [outer.name] if outer is not None else [name]

    # names whose outermost container must be kept whole (nested entities)
    extended_classes = set(wanted_classes)
    extended_functions = set(wanted_functions)
    for name in wanted_all:
        outer = outer_by_name.get(name)
        if outer is None or outer.name == name:
            continue
        if isinstance(outer, ast.ClassDef):
            extended_classes.add(outer.name)
        else:
            extended_functions.add(outer.name)
    wanted_classes, wanted_functions = extended_classes, extended_functions

    keep_spans = []
    # module docstring and imports stay, so the pruned file still parses
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            keep_spans.append((node.lineno, getattr(node, "end_lineno", node.lineno)))
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str) and not keep_spans:
            keep_spans.append((node.lineno, getattr(node, "end_lineno", node.lineno)))

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            keep_class = node.name in wanted_classes
            keep_methods = wanted_methods.get(node.name, set())
            if not keep_class and not keep_methods:
                continue
            if keep_class:
                keep_spans.append((node.lineno, getattr(node, "end_lineno", node.lineno)))
                continue
            # keep the class header up to its body, then only the wanted members
            body_nodes = [child for child in node.body
                          if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                          and (child.name in keep_methods or child.name == "__init__")]
            if not body_nodes:
                keep_spans.append((node.lineno, getattr(node, "end_lineno", node.lineno)))
                continue
            first = body_nodes[0]
            keep_spans.append((node.lineno, first.lineno - 1))
            for child in body_nodes:
                keep_spans.append((child.lineno, getattr(child, "end_lineno", child.lineno)))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in wanted_functions:
                keep_spans.append((node.lineno, getattr(node, "end_lineno", node.lineno)))

    keep_spans.sort()
    merged = []
    for start, end in keep_spans:
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    out = []
    for start, end in merged:
        out.extend(lines[start - 1:end])
        out.append("")
    return "\n".join(out) + "\n"


def prepare(repo: str, by_file: dict) -> Path:
    """Copy the sampled entities' source files into a pristine working tree."""
    work = WORK / repo
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    # RepoAgent falls back to its *own* .gitignore when the target has none, and that
    # file ignores lib/, build/, dist/ and more -- which silently dropped every sampled
    # entity living under such a directory (numpy lost 9 files that way). A permissive
    # .gitignore in the working tree keeps the baseline's own filter out of the sample.
    (work / ".gitignore").write_text(
        "# intentionally permissive: the baseline must see every sampled file\n"
        "__pycache__/\n*.py[cod]\n",
        encoding="utf-8")

    for rel, entities in by_file.items():
        src = TARGETS / repo / rel
        dst = work / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        wanted_classes = {e["name"] for e in entities if e["kind"] == "class"}
        wanted_functions = {e["name"] for e in entities if e["kind"] == "function"}
        wanted_methods: dict = {}
        for entity in entities:
            if entity["kind"] == "method" and entity["owner"]:
                wanted_methods.setdefault(entity["owner"], set()).add(entity["name"])
        text = src.read_text(encoding="utf-8", errors="replace")
        dst.write_text(prune_source(text, wanted_classes, wanted_functions, wanted_methods),
                       encoding="utf-8")
    # RepoAgent's ChangeDetector drives everything through GitPython, so the target must
    # be a git repository; a plain directory fails with InvalidGitRepositoryError.
    env = dict(os.environ, GIT_AUTHOR_NAME="baseline", GIT_AUTHOR_EMAIL="baseline@local",
               GIT_COMMITTER_NAME="baseline", GIT_COMMITTER_EMAIL="baseline@local")
    for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                ["git", "-c", "user.name=baseline", "-c", "user.email=baseline@local",
                 "commit", "-qm", "baseline snapshot"]):
        subprocess.run(cmd, cwd=str(work), env=env, capture_output=True)
    return work


def run_repoagent(work: Path, threads: int, timeout: int, extra_args: list) -> dict:
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = os.environ.get("LLM_KEY", "")
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [
        str(VENV_PYTHON), "-m", "repo_agent", "run",
        "-m", MODEL,
        "-b", BASE_URL,
        "-t", TEMPERATURE,
        "-tp", str(work),
        "-mdp", "markdown_docs",
        "-mtc", str(threads),
        "-r", str(timeout),
        "-l", "English",
    ] + extra_args
    started = time.time()
    result = subprocess.run(cmd, cwd=str(REPOAGENT), capture_output=True,
                            text=True, encoding="utf-8", errors="replace", env=env)
    return {
        "seconds": round(time.time() - started, 1),
        "returncode": result.returncode,
        "stdout_tail": (result.stdout or "")[-4000:],
        "stderr_tail": (result.stderr or "")[-4000:],
    }


SECTION = re.compile(r"^(#{2,6})\s+(ClassDef|FunctionDef)\s+([A-Za-z_][A-Za-z0-9_]*)")


def split_sections(md_text: str) -> list:
    """Split a RepoAgent markdown file into (level, kind, name, body) blocks."""
    sections = []
    current = None
    for line in md_text.splitlines():
        match = SECTION.match(line)
        if match:
            if current is not None:
                sections.append(current)
            level = len(match.group(1))
            current = {
                "level": level,
                "kind": match.group(2),
                "name": match.group(3),
                "header": line.rstrip(),
                "lines": [line.rstrip()],
            }
        elif current is not None:
            current["lines"].append(line.rstrip())
    if current is not None:
        sections.append(current)
    for section in sections:
        section["body"] = "\n".join(section["lines"]).strip() + "\n"
    return sections


def adapt(repo: str, by_file: dict, work: Path) -> dict:
    """Emit one markdown document per sampled entity from RepoAgent's per-file output."""
    out_dir = OUT / repo
    out_dir.mkdir(parents=True, exist_ok=True)
    docs_root = work / "markdown_docs"
    written, missing = 0, []
    for rel, entities in by_file.items():
        md_path = docs_root / (rel[:-3] + ".md") if rel.endswith(".py") else None
        if md_path is None or not md_path.exists():
            missing.extend(entity["qname"] for entity in entities)
            continue
        sections = split_sections(md_path.read_text(encoding="utf-8", errors="replace"))
        # Headings deepen with nesting, so keep a stack of enclosing definitions instead
        # of assuming methods are exactly one level below their class. Nested entities
        # (closures, classes built inside factories) appear at depth 3 or more.
        index: dict = {}
        stack: list = []
        for section in sections:
            while stack and stack[-1]["level"] >= section["level"]:
                stack.pop()
            parents = list(stack)
            stack.append(section)
            chain = [p["name"] for p in parents]
            if not parents:
                key = ("class" if section["kind"] == "ClassDef" else "function",
                       section["name"])
            elif parents[0]["kind"] == "ClassDef":
                key = ("method", parents[0]["name"], section["name"])
            else:
                key = ("nested", tuple(chain), section["name"])
            index[key] = section["body"]
            index.setdefault(("byname", section["name"]), section["body"])

        for entity in entities:
            if entity["kind"] == "class":
                body = index.get(("class", entity["name"])) or index.get(("byname", entity["name"]))
            elif entity["kind"] == "method":
                body = (index.get(("method", entity["owner"], entity["name"]))
                        or index.get(("byname", entity["name"]))
                        or next((v for k, v in index.items()
                                 if k[0] in ("method", "nested") and k[-1] == entity["name"]), None))
            else:
                body = index.get(("function", entity["name"])) or index.get(("byname", entity["name"]))
            if not body:
                missing.append(entity["qname"])
                continue
            safe = (entity["qname"].replace(".", "_").replace("/", "_")
                    .replace("#", "_").replace("<", "_").replace(">", "_"))
            (out_dir / f"{safe}.md").write_text(body, encoding="utf-8")
            written += 1
    return {"written": written, "missing": missing, "docs_root": str(docs_root)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repos", nargs="+", default=None)
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--prepare-only", action="store_true")
    ap.add_argument("--reuse-work", action="store_true",
                    help="keep the pruned working tree from a previous run")
    ap.add_argument("--extra", default="", help="extra CLI args passed to repo_agent run")
    ap.add_argument("--repair", action="store_true",
                    help="re-run only the files whose sampled entities produced no document")
    args = ap.parse_args()

    repos = args.repos or sorted(p.name for p in TARGETS.iterdir() if p.is_dir())
    summary = []

    def safe(qname: str) -> str:
        return (qname.replace(".", "_").replace("/", "_").replace("#", "_")
                .replace("<", "_").replace(">", "_"))
    for repo in repos:
        by_file = sample_map(repo, args.limit, args.seed)
        if not by_file:
            print(f"skip {repo}: no sampled entities")
            continue
        if args.repair:
            have = {f.stem for f in (OUT / repo).glob("*.md")} if (OUT / repo).is_dir() else set()
            missing = [e for entities in by_file.values() for e in entities
                       if safe(e["qname"]) not in have]
            if not missing:
                print(f"{repo}: nothing to repair", flush=True)
                continue
            missing_q = {e["qname"] for e in missing}
            by_file = {rel: [e for e in entities if e["qname"] in missing_q]
                       for rel, entities in by_file.items()}
            by_file = {rel: entities for rel, entities in by_file.items() if entities}
            print(f"{repo}: repairing {len(missing)} entities in {len(by_file)} files",
                  flush=True)

        work = WORK / repo
        if args.repair or not args.reuse_work:
            work = prepare(repo, by_file)
        print(f"{repo}: {sum(len(v) for v in by_file.values())} entities in "
              f"{len(by_file)} files -> {work}", flush=True)
        record = {"repo": repo, "files": len(by_file),
                  "entities": sum(len(v) for v in by_file.values())}
        if not args.prepare_only:
            if not VENV_PYTHON.exists():
                print("RepoAgent venv missing: third_party/.venv-repoagent311")
                return 2
            extra = [a for a in args.extra.split() if a]
            result = run_repoagent(work, args.threads, args.timeout, extra)
            record.update(result)
            print(f"  repoagent: rc={result['returncode']} {result['seconds']}s", flush=True)
            if result["returncode"] != 0:
                print((result["stderr_tail"] or result["stdout_tail"])[-1200:], flush=True)
            adapted = adapt(repo, by_file, work)
            record.update({"written": adapted["written"], "missing": len(adapted["missing"])})
            print(f"  adapted: {adapted['written']} documents, "
                  f"{len(adapted['missing'])} missing", flush=True)
        summary.append(record)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nsummary: {OUT / 'run_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
