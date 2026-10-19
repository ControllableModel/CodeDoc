"""Fetch the evaluated repositories from upstream, keeping only core library code.

Why not ``git clone``
---------------------
The git transport to github.com is unreliable from this network (repeated
"Recv failure: Connection was reset"), while ``api.github.com`` and
``codeload.github.com`` answer reliably. So the snapshot is obtained as a tarball
**pinned to a resolved commit SHA**, which is actually stricter than
``git clone --depth 1``: the recorded SHA and the extracted tree cannot drift.

Why "core only"
---------------
A full clone drags in the front-end, docs, CI configuration and test suites.
Those are irrelevant to a documentation-generation study and would swamp the
analysis. Each entry below names the package directory that *is* the library, and
extraction drops test/doc/example directories anyway.

Usage::

    python scripts/fetch_core_repos.py --list
    python scripts/fetch_core_repos.py joblib numpy
    python scripts/fetch_core_repos.py --all
"""

from __future__ import annotations

import argparse
import io
import json
import shutil
import sys
import tarfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.config import TARGETS  # noqa: E402

USER_AGENT = "CodeDoc-artifact-fetcher/1.0"

#: name -> (owner/repo, core package directory inside the tarball[, pin path])
#:
#: ``pin path`` exists because a repository can be *restructured* after the
#: evaluated snapshot was taken: RAGFlow no longer ships the Python ``api/``
#: package at HEAD (its core moved to Go-style ``cmd/``/``internal/``). For such
#: repositories the commit is pinned to the last one that still contains the
#: evaluated layout, which is recorded in the manifest.
REPOS: dict = {
    "numpy":      ("numpy/numpy", "numpy"),
    "openui":     ("wandb/openui", "backend/openui"),
    "ragflow":    ("infiniflow/ragflow", "api", "api/ragflow_server.py"),
    "dify_api":   ("langgenius/dify", "api"),
    "flask-main": ("pallets/flask", "src/flask"),
    "joblib":     ("joblib/joblib", "joblib"),
    "pyro":       ("pyro-ppl/pyro", "pyro"),
    "fairseq":    ("facebookresearch/fairseq", "fairseq"),
    "sonnet":     ("google-deepmind/sonnet", "sonnet"),
    "torch":      ("pytorch/pytorch", "torch"),
}

#: Directory names dropped during extraction (tests, docs, packaging noise).
EXCLUDE_DIRS = {
    "tests", "test", "testing", "docs", "doc", "documentation", "examples",
    "example", "benchmarks", "benchmark", "bench", ".github", ".git", "build",
    "dist", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache",
}
#: Never needed by the analysis; keeps the tree small and diffable.
EXCLUDE_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf",
    ".mp4", ".zip", ".whl", ".so", ".dll", ".dylib", ".pyc", ".ipynb",
}

RETRIES = 5
TIMEOUT = 90


def http_get(url: str, retries: int = RETRIES) -> bytes:
    """GET with retries — the network here resets connections intermittently."""
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001 - network layer
            last = exc
            wait = min(2 * attempt, 10)
            print(f"    retry {attempt}/{retries} after {type(exc).__name__}: {str(exc)[:60]}")
            time.sleep(wait)
    raise RuntimeError(f"GET failed after {retries} attempts: {url}") from last


def resolve_commit(owner_repo: str, pin_path: str | None = None) -> tuple:
    """Return (sha, branch, committed_date).

    With ``pin_path`` the commit is the last one that still touched that path,
    i.e. the newest snapshot that still has the evaluated layout.
    """
    if pin_path:
        commits = json.loads(
            http_get(
                f"https://api.github.com/repos/{owner_repo}/commits?path={pin_path}&per_page=1"
            )
        )
        if not commits:
            raise RuntimeError(f"no commit ever touched {pin_path} in {owner_repo}")
        sha = commits[0]["sha"]
        date = commits[0]["commit"]["committer"]["date"]
        return sha, f"pinned@{pin_path}", date
    meta = json.loads(http_get(f"https://api.github.com/repos/{owner_repo}"))
    branch = meta.get("default_branch", "main")
    commit = json.loads(http_get(f"https://api.github.com/repos/{owner_repo}/commits/{branch}"))
    sha = commit["sha"]
    date = commit["commit"]["committer"]["date"]
    return sha, branch, date


def download_tarball(owner_repo: str, sha: str) -> tarfile.TarFile:
    data = http_get(f"https://codeload.github.com/{owner_repo}/tar.gz/{sha}")
    return tarfile.open(fileobj=io.BytesIO(data), mode="r:gz")


def wanted(member_name: str, package: str) -> str | None:
    """Return the destination-relative path, or None to skip the member."""
    parts = member_name.split("/")
    if len(parts) < 2:
        return None
    rel = "/".join(parts[1:])            # strip the "<repo>-<sha>/" prefix
    if not rel:
        return None
    if not (rel == package or rel.startswith(package + "/")):
        return None
    chunks = rel.split("/")
    if any(c in EXCLUDE_DIRS for c in chunks[:-1]):
        return None
    if Path(rel).suffix.lower() in EXCLUDE_SUFFIXES:
        return None
    return rel


def extract(tar: tarfile.TarFile, package: str, dest: Path) -> tuple:
    """Extract the package directory; return (n_files, n_bytes, kept_prefix)."""
    n_files = 0
    n_bytes = 0
    kept_prefix = None
    for member in tar.getmembers():
        rel = wanted(member.name, package)
        if rel is None or not member.isfile():
            continue
        target = dest / Path(rel).relative_to(package)
        target.parent.mkdir(parents=True, exist_ok=True)
        handle = tar.extractfile(member)
        if handle is None:
            continue
        payload = handle.read()
        target.write_bytes(payload)
        n_files += 1
        n_bytes += len(payload)
        kept_prefix = package
    return n_files, n_bytes, kept_prefix


def fetch(name: str, force: bool = False) -> dict:
    spec = REPOS[name]
    owner_repo, package = spec[0], spec[1]
    pin_path = spec[2] if len(spec) > 2 else None
    dest = TARGETS / name
    if dest.exists() and not force:
        print(f"[skip] {name}: already present (use --force to refetch)")
        return {}

    print(f"[{name}] {owner_repo} :: {package}")
    sha, branch, date = resolve_commit(owner_repo, pin_path)
    print(f"    commit {sha[:12]} ({branch}, {date})")
    tar = download_tarball(owner_repo, sha)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    n_files, n_bytes, kept = extract(tar, package, dest)
    tar.close()
    if not n_files:
        print(f"    !! nothing extracted for package '{package}' — check the path")
    record = {
        "name": name,
        "upstream": f"https://github.com/{owner_repo}",
        "commit": sha,
        "branch": branch,
        "committed_date": date,
        "core_package": package,
        "extracted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": n_files,
        "bytes": n_bytes,
        "kept_prefix": kept,
        "pinned_path": pin_path,
    }
    print(f"    extracted {n_files} files, {n_bytes/1048576:.2f} MB")
    return record


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("names", nargs="*", help="repositories to fetch")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.list:
        for name, (repo, pkg) in REPOS.items():
            print(f"{name:<12} {repo:<28} core={pkg}")
        return 0

    names = list(REPOS) if args.all else args.names
    if not names:
        ap.error("specify repository names or --all")
    unknown = [n for n in names if n not in REPOS]
    if unknown:
        ap.error(f"unknown repositories: {unknown}. Known: {list(REPOS)}")

    TARGETS.mkdir(parents=True, exist_ok=True)
    manifest_path = TARGETS / "PROVENANCE.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}

    failed = []
    for name in names:
        try:
            record = fetch(name, force=args.force)
            if record:
                manifest[name] = record
        except Exception as exc:  # noqa: BLE001 - network layer
            print(f"[FAIL] {name}: {type(exc).__name__}: {exc}")
            failed.append(name)

    if manifest:
        manifest_path.write_text(
            json.dumps(dict(sorted(manifest.items())), indent=2) + "\n", encoding="utf-8"
        )
        print(f"\nmanifest: {manifest_path}")
    if failed:
        print(f"failed: {failed}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
