"""CodeDoc console — a local dashboard for the documentation pipeline.

Design constraints
------------------
* **No build step, no third-party server**: stdlib ``http.server`` and static
  HTML/CSS/JS only. The artifact has to run on a reviewer's machine, and a
  ``pip install`` wall is a reproduction barrier.
* **Localhost only.** The console can hold an API key, so it binds to 127.0.0.1 and
  keeps the key in a gitignored local file, never in the served HTML.
* **Long work is a job.** Building the dependency index takes milliseconds on a small
  repository and about a minute on torch, so analysis returns a job id and the page
  polls it instead of holding a request open.

Run::

    python webapp/server.py --port 8765
    # then open http://127.0.0.1:8765/
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.config import CRITERIA_SETS, TARGETS, TEMPLATES  # noqa: E402
from codedoc.criteria import registry  # noqa: E402
from codedoc.deps.relations_index import BLOCK_LABELS, build_index, get_dep  # noqa: E402
from codedoc.deps.schema import RelationKind  # noqa: E402
from codedoc.writer.prompt import build_prompt  # noqa: E402

WEBAPP = Path(__file__).resolve().parent
STATIC = WEBAPP / "static"
CONFIG_PATH = WEBAPP / "config.local.json"

DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "https://apic1.ohmycdn.com/v1",
    "model": "gpt-6-luna",
    "use_max_completion_tokens": True,
    "max_completion_tokens": 8000,
    #: Price list of the configured endpoint, per million tokens, in USD.
    #: Two context tiers x four service modes, plus cached-input and cache-creation
    #: rates, because providers charge all of these differently.
    "pricing": {
        "currency": "USD",
        "long_context_threshold": 272000,
        "mode": "standard",
        "tiers": {
            "short": {
                "standard": {"input": 0.09, "cached_input": 0.009, "cache_creation": 0.1125, "output": 0.45},
                "flex":     {"input": 0.045, "cached_input": 0.0045, "cache_creation": 0.05625, "output": 0.225},
                "batch":    {"input": 0.045, "cached_input": 0.0045, "cache_creation": 0.05625, "output": 0.225},
                "priority": {"input": 0.18, "cached_input": 0.018, "cache_creation": 0.225, "output": 0.90},
            },
            "long": {
                "standard": {"input": 0.18, "cached_input": 0.018, "cache_creation": 0.225, "output": 0.675},
                "flex":     {"input": 0.09, "cached_input": 0.009, "cache_creation": 0.1125, "output": 0.3375},
                "batch":    {"input": 0.09, "cached_input": 0.009, "cache_creation": 0.1125, "output": 0.3375},
                "priority": {"input": 0.36, "cached_input": 0.036, "cache_creation": 0.45, "output": 1.35},
            },
        },
    },
    "temperature": 1.0,
    "judge_temperature": 0.0,
    "max_tokens": 40000,
    "source_budget": 8000,
    "template": "iso_26514.txt",
    "criteria": ["practice_docstring"],
    "language": "English",
    "relevant": True,
    #: Concurrent generations. The endpoint latency dominates (about 25 s per entity on
    #: gpt-6-luna), so throughput scales with this until the proxy starts throttling.
    "workers": 6,
}

#: Analysis results and their dependency indices, keyed by request signature.
_INDEX_CACHE: dict = {}
_JOBS: dict = {}
_LOCK = threading.Lock()


# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------
def load_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            config.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
    # Environment wins so a shell session does not have to paste the key into a form.
    if os.getenv("LLM_KEY"):
        config["api_key"] = os.environ["LLM_KEY"]
    if os.getenv("LLM_URL"):
        config["base_url"] = os.environ["LLM_URL"]
    if os.getenv("MODEL"):
        config["model"] = os.environ["MODEL"]
    return config


def save_config(config: dict) -> dict:
    merged = load_config()
    for key in DEFAULT_CONFIG:
        if key in config and config[key] not in (None, ""):
            merged[key] = config[key]
    CONFIG_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged


def compute_cost(prompt_tokens: int, completion_tokens: int, cached_tokens: int,
                 config: dict) -> dict:
    """Cost of one call under the configured tier and mode.

    The tier is chosen by prompt length (a long-context call is priced per its whole
    prompt), and cached prompt tokens are billed at the cached-input rate. Returns the
    amount plus the breakdown, so the UI can show why a number is what it is.
    """
    pricing = config.get("pricing") or DEFAULT_CONFIG["pricing"]
    tier_name = "long" if prompt_tokens > int(pricing.get("long_context_threshold", 272000)) else "short"
    mode = pricing.get("mode", "standard")
    rates = (pricing.get("tiers", {}).get(tier_name, {}) or {}).get(mode) or {}
    if not rates:  # unknown mode: fall back to standard of the same tier
        rates = (pricing.get("tiers", {}).get(tier_name, {}) or {}).get("standard", {})

    cached = min(max(0, int(cached_tokens or 0)), max(0, int(prompt_tokens or 0)))
    fresh = max(0, int(prompt_tokens or 0) - cached)
    amount = (
        fresh / 1e6 * float(rates.get("input", 0))
        + cached / 1e6 * float(rates.get("cached_input", rates.get("input", 0)))
        + int(completion_tokens or 0) / 1e6 * float(rates.get("output", 0))
    )
    return {
        "amount": round(amount, 6),
        "currency": pricing.get("currency", "USD"),
        "tier": tier_name,
        "mode": mode,
        "cached_tokens": cached,
        "rates": rates,
    }


def public_config(config: dict) -> dict:
    """Never send the key back to the browser; only whether one is present."""
    view = {k: v for k, v in config.items() if k != "api_key"}
    key = config.get("api_key") or ""
    view["api_key_present"] = bool(key)
    view["api_key_hint"] = (key[:6] + "…" + key[-4:]) if len(key) > 12 else ""
    return view


# ---------------------------------------------------------------------------
# repository access
# ---------------------------------------------------------------------------
def list_repositories() -> list:
    repos = []
    if TARGETS.exists():
        for path in sorted(TARGETS.iterdir()):
            if not path.is_dir():
                continue
            try:
                n_py = sum(1 for _ in path.rglob("*.py"))
            except OSError:
                continue
            if n_py:
                repos.append({"name": path.name, "path": str(path), "py_files": n_py})
    return repos


def resolve_repo(repo: str, custom_path: str = "") -> Path:
    if custom_path:
        candidate = Path(custom_path)
    else:
        candidate = TARGETS / repo
    candidate = candidate.expanduser()
    if not candidate.is_absolute():
        candidate = (ROOT / candidate).resolve()
    if not candidate.exists():
        raise FileNotFoundError(f"repository not found: {candidate}")
    return candidate


class _PromptArgs:
    """The namespace ``writer.prompt.build_prompt`` expects."""

    def __init__(self, config: dict) -> None:
        self.relevant = bool(config.get("relevant", True))
        self.language = config.get("language", "English")
        self.max_tokens = int(config.get("max_tokens", 16000))
        self.source_budget = int(config.get("source_budget", 8000))
        template = config.get("template") or ""
        self.prompt_template = str(TEMPLATES / template) if template and template != "none" else None


# ---------------------------------------------------------------------------
# analysis
# ---------------------------------------------------------------------------
def analyse(repo_name: str, custom_path: str, mode: str, limit: int, seed: int) -> dict:
    """Build the index and the entity list the console displays."""
    signature = (repo_name, custom_path, mode, limit, seed)
    with _LOCK:
        cached = _INDEX_CACHE.get(signature)
    if cached is not None:
        return cached

    repo_path = resolve_repo(repo_name, custom_path)
    index = build_index(str(repo_path))
    if index is None:
        raise RuntimeError("no Python entities extracted from this path")

    if mode == "sample" and limit > 0:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "codedoc_bench", ROOT / "scripts" / "bench_small_repo.py"
        )
        module = importlib.util.module_from_spec(spec)
        namespace = {"__name__": "codedoc_bench", "__file__": str(ROOT / "scripts" / "bench_small_repo.py")}
        exec(compile((ROOT / "scripts" / "bench_small_repo.py").read_text(encoding="utf-8"),
                     "bench_small_repo.py", "exec"), namespace)
        selected = namespace["pick_entities"](index, limit, seed)
    else:
        selected = list(index.contexts)

    files: dict = {}
    entities = []
    for ctx in selected:
        rel_path = os.path.relpath(ctx.entity.path, repo_path) if ctx.entity.path else ""
        entry = files.setdefault(rel_path, {"path": rel_path, "abs_path": ctx.entity.path,
                                            "entities": []})
        relations = {
            BLOCK_LABELS[kind]: len(ctx.get(kind))
            for kind in BLOCK_LABELS
            if ctx.get(kind)
        }
        calls = len(ctx.get(RelationKind.CALLS))
        called_by = len(ctx.get(RelationKind.CALLED_BY))
        if calls:
            relations["Uses"] = calls
        if called_by:
            relations["Used by"] = called_by
        record = {
            "qname": ctx.entity.qualified_name,
            "name": ctx.entity.name,
            "kind": str(ctx.entity.kind),
            "path": rel_path,
            "span": ctx.entity.span,
            "source_lines": len((ctx.source or "").splitlines()),
            "relations": relations,
        }
        entry["entities"].append(record)
        entities.append(record)

    for entry in files.values():
        entry["entities"].sort(key=lambda e: (e["kind"], e["name"]))

    result = {
        "repo": repo_name or str(repo_path),
        "repo_path": str(repo_path),
        "mode": mode,
        "limit": limit,
        "seed": seed,
        "files": [files[k] for k in sorted(files)],
        "entities": sorted(entities, key=lambda e: (e["path"], e["kind"], e["name"])),
        "counts": {
            "entities": len(entities),
            "files": len(files),
            "classes": sum(1 for e in entities if e["kind"] == "class"),
            "methods": sum(1 for e in entities if e["kind"] == "method"),
            "functions": sum(1 for e in entities if e["kind"] == "function"),
        },
    }
    with _LOCK:
        _INDEX_CACHE[signature] = {"result": result, "index": index, "repo_path": str(repo_path)}
    return _INDEX_CACHE[signature]


def entity_detail(repo_name: str, custom_path: str, mode: str, limit: int, seed: int,
                  qname: str, config: dict) -> dict:
    """Everything the console shows for one entity: source, prompt, relations, params."""
    entry = analyse(repo_name, custom_path, mode, limit, seed)
    index = entry["index"]
    dep = get_dep(index, qname.split(".")[-1], qname, "")
    if dep is None:
        raise KeyError(f"entity not found: {qname}")

    writer_args = _PromptArgs(config)
    prompt = build_prompt(dep, writer_args)
    # dep["relations"] is already {block label: [target, ...]} — do not re-resolve it
    # against RelationKind, which held Relation objects only inside the extractor.
    relations_all = {
        label: [
            {"name": entry.get("name"), "code": entry.get("code") or "",
             "has_code": bool(entry.get("code"))}
            if isinstance(entry, dict) else {"name": str(entry), "code": "", "has_code": False}
            for entry in targets
        ]
        for label, targets in (dep.get("relations") or {}).items()
    }
    template_used = writer_args.prompt_template or "(IDE-style baseline: no criteria template)"

    return {
        "qname": dep["qualified_name"],
        "name": dep["real_name"],
        "kind": dep["kind"],
        "path": dep["path"],
        "source": dep["source_code"],
        "prompt_source": dep.get("prompt_source") or dep["source_code"],
        "prompt": prompt,
        "prompt_chars": len(prompt),
        "prompt_clipped": "lines elided" in prompt,
        "relations": dep.get("relations") or {},
        "relation_counts": {label: len(entries) for label, entries in relations_all.items()},
        "is_polymorphic": dep.get("is_polymorphic", False),
        "uses": [list(item.keys())[0] for item in dep["uses"]],
        "used_by": [list(item.keys())[0] for item in dep["used_by"]],
        "template": template_used,
        "params": {
            "model": config.get("model"),
            "base_url": config.get("base_url"),
            "temperature": config.get("temperature"),
            "max_tokens": config.get("max_tokens"),
            "source_budget": config.get("source_budget"),
            "language": config.get("language"),
            "relevant": config.get("relevant"),
        },
    }


# ---------------------------------------------------------------------------
# generation
# ---------------------------------------------------------------------------
def generate_document(repo_name: str, custom_path: str, mode: str, limit: int, seed: int,
                      qname: str, config: dict) -> dict:
    key = config.get("api_key") or ""
    if not key:
        raise RuntimeError("no API key configured")

    from codedoc.writer.llm import LinguisticCore
    from codedoc.writer.usage import RECORDER

    detail = entity_detail(repo_name, custom_path, mode, limit, seed, qname, config)
    core = LinguisticCore()
    core.LLM_key = key
    core.LLM_url = config.get("base_url") or DEFAULT_CONFIG["base_url"]
    core.model = config.get("model") or DEFAULT_CONFIG["model"]
    core.temperature = float(config.get("temperature", 1.0))
    core.max_output_tokens = int(config.get("max_completion_tokens") or 8000)
    core.max_retries = int(config.get("max_retries") or 3)
    core.use_max_completion_tokens = bool(config.get("use_max_completion_tokens", True))
    # The writers record into the process-wide RECORDER. Tagging this call and
    # filtering by the tag is required under concurrency: a positional snapshot also
    # captures records written by sibling threads, which inflated batch accounting
    # by roughly the worker count.
    call_tag = f"console-{uuid.uuid4()}"
    core.label = call_tag
    core.create_socket()

    started = time.time()
    document = core.process(detail["prompt"])
    seconds = time.time() - started
    mine = [r for r in RECORDER.records if r.get("label") == call_tag]
    usage = {
        "prompt_tokens": sum(r["prompt_tokens"] for r in mine),
        "completion_tokens": sum(r["completion_tokens"] for r in mine),
        "cached_tokens": sum(r.get("cached_tokens", 0) for r in mine),
    }

    out_dir = ROOT / "outputs" / "console" / (repo_name or "custom")
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = qname.replace(".", "_").replace("/", "_").replace("#", "_")
    (out_dir / f"{safe}.md").write_text(document or "", encoding="utf-8")
    (out_dir / f"{safe}.prompt.txt").write_text(detail["prompt"], encoding="utf-8")

    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    cost_info = compute_cost(prompt_tokens, completion_tokens,
                             usage.get("cached_tokens", 0), config)
    return {
        "qname": qname,
        "document": document or "",
        "chars": len(document or ""),
        "seconds": round(seconds, 2),
        "tokens": {"prompt": prompt_tokens, "completion": completion_tokens,
                   "cached": usage.get("cached_tokens", 0)},
        "cost": cost_info["amount"],
        "currency": cost_info["currency"],
        "cost_detail": cost_info,
        #: kept for the earlier callers that read cost_cny
        "cost_cny": cost_info["amount"],
        "model": core.model,
        "saved_to": str(out_dir),
    }


GRAPH_KINDS = {
    "inherits": "inherits",
    "subclassed_by": "subclassed_by",
    "instantiated_at": "instantiated_at",
    "overrides": "overrides",
    "overridden_by": "overridden_by",
    "dispatch_candidates": "dispatch_candidates",
    "attribute_access": "attribute_access",
    "calls": "calls",
    "called_by": "called_by",
}


def graph_data(repo_name: str, custom_path: str, mode: str, limit: int, seed: int,
               focus: str = "", depth: int = 1, kinds: str = "") -> dict:
    """Nodes and edges for the dependency graph view.

    Defaults to the class-level skeleton (inheritance, instantiation, overriding,
    dispatch) because a call graph on a whole repository is unreadable; call edges
    are included when explicitly requested or when the view is focused on an entity.
    """
    entry = analyse(repo_name, custom_path, mode, limit, seed)
    index = entry["index"]
    wanted = [k.strip() for k in kinds.split(",") if k.strip()] or [
        "inherits", "subclassed_by", "instantiated_at", "overrides",
        "overridden_by", "dispatch_candidates",
    ]
    if focus:
        wanted = list(dict.fromkeys(wanted + ["calls", "called_by", "attribute_access"]))

    by_qname = {ctx.entity.qualified_name: ctx for ctx in index.contexts}
    by_short: dict = {}
    for ctx in index.contexts:
        by_short.setdefault(ctx.entity.name.split(".")[-1], []).append(ctx)

    def resolve(target: str, exclude: str = ""):
        hit = by_qname.get(target)
        if hit is not None:
            return hit
        candidates = [c for c in by_short.get(target.split(".")[-1], [])
                      if c.entity.qualified_name != exclude]
        if len(candidates) == 1:
            return candidates[0]
        return None

    # ---- focus neighbourhood -------------------------------------------------
    allowed = None
    if focus:
        allowed = set()
        frontier = [by_qname.get(focus)] if focus in by_qname else []
        if not frontier:
            candidates = by_short.get(focus.split(".")[-1], [])
            frontier = candidates[:1]
        # depth 1 must include the neighbours themselves, so expand depth+1 times:
        # the first pass admits the focus, each further pass admits one hop.
        for _ in range(max(1, depth) + 1):
            nxt = []
            for ctx in frontier:
                if ctx is None:
                    continue
                key = ctx.entity.qualified_name
                if key in allowed:
                    continue
                allowed.add(key)
                for relation_kind in wanted:
                    for relation in ctx.get(relation_kind):
                        target = resolve(relation.target, exclude=key)
                        if target is not None:
                            allowed.add(target.entity.qualified_name)
                            nxt.append(target)
            frontier = nxt
        allowed.add(focus)

    nodes: dict = {}
    edges: list = []
    seen_edges = set()

    # Disambiguate labels: two modules can define the same class name (Flask defines
    # Blueprint and imports sansio.blueprints.Blueprint), and a two-part suffix is not
    # always enough, so fall back to the full qualified name.
    short_counts: dict = {}
    for ctx in index.contexts:
        short = ctx.entity.name.split(".")[-1]
        short_counts[short] = short_counts.get(short, 0) + 1
    suffix_counts: dict = {}
    for ctx in index.contexts:
        parts = ctx.entity.qualified_name.split(".")
        suffix_counts[".".join(parts[-2:])] = suffix_counts.get(".".join(parts[-2:]), 0) + 1

    def label_of(ctx) -> str:
        short = ctx.entity.name.split(".")[-1]
        if short_counts.get(short, 0) <= 1:
            return short
        parts = ctx.entity.qualified_name.split(".")
        suffix = ".".join(parts[-2:])
        if suffix_counts.get(suffix, 0) <= 1:
            return suffix
        return ctx.entity.qualified_name

    def node_of(ctx) -> dict:
        key = ctx.entity.qualified_name
        if key not in nodes:
            nodes[key] = {
                "id": key,
                "name": label_of(ctx),
                "kind": str(ctx.entity.kind),
                "path": ctx.entity.path,
                "qname": key,
            }
        return nodes[key]

    for ctx in index.contexts:
        key = ctx.entity.qualified_name
        if allowed is not None and key not in allowed:
            continue
        for relation_kind in wanted:
            for relation in ctx.get(relation_kind):
                target_ctx = resolve(relation.target, exclude=key)
                if allowed is not None and (
                        target_ctx is None or target_ctx.entity.qualified_name not in allowed):
                    continue
                node_of(ctx)
                target_id = (target_ctx.entity.qualified_name if target_ctx is not None
                             else f"ext:{relation.target}")
                if target_ctx is None:
                    nodes.setdefault(target_id, {
                        "id": target_id, "name": relation.target,
                        "kind": "external", "path": "", "qname": "",
                    })
                signature = (key, target_id, relation_kind)
                if signature in seen_edges:
                    continue
                seen_edges.add(signature)
                edges.append({"source": key, "target": target_id, "kind": relation_kind})

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "kinds": wanted,
        "focus": focus,
        "depth": depth,
        "counts": {"nodes": len(nodes), "edges": len(edges)},
    }


def start_batch(spec: dict, config: dict, workers: int = 0) -> str:
    """Generate documentation for every entity in the current selection.

    Entities are independent, so the batch runs concurrently: sequentially, a
    38-entity repository took 7.5 minutes and a 431-entity one would take over an
    hour. Progress is updated under the job lock after each completion.
    """
    job_id = str(uuid.uuid4())
    entry = analyse(**{k: spec[k] for k in ("repo_name", "custom_path", "mode", "limit", "seed")})
    targets = [e["qname"] for e in entry["result"]["entities"]]
    workers = int(workers or config.get("workers") or 6)
    with _LOCK:
        _JOBS[job_id] = {
            "status": "running",
            "started": time.time(),
            "kind": "batch",
            "progress": {"done": 0, "total": len(targets), "failed": 0,
                         "prompt_tokens": 0, "completion_tokens": 0,
                         "cached_tokens": 0, "cost": 0.0, "cost_cny": 0.0,
                         "workers": workers,
                         "currency": (config.get("pricing") or {}).get("currency", "USD"),
                         "current": ""},
            "cancel": False,
        }

    def one(qname):
        with _LOCK:
            job = _JOBS[job_id]
            if job.get("cancel"):
                return
            job["progress"]["current"] = qname
        try:
            result = generate_document(
                spec["repo_name"], spec["custom_path"], spec["mode"],
                spec["limit"], spec["seed"], qname, config,
            )
            with _LOCK:
                progress = _JOBS[job_id]["progress"]
                progress["done"] += 1
                progress["prompt_tokens"] += result["tokens"]["prompt"]
                progress["completion_tokens"] += result["tokens"]["completion"]
                progress["cached_tokens"] += result["tokens"].get("cached", 0)
                progress["cost"] = round(progress["cost"] + result["cost"], 6)
                progress["cost_cny"] = progress["cost"]
        except Exception as exc:  # noqa: BLE001 - one failure must not stop the batch
            with _LOCK:
                progress = _JOBS[job_id]["progress"]
                progress["done"] += 1
                progress["failed"] += 1
                progress["last_error"] = f"{type(exc).__name__}: {exc}"

    def work():
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            list(pool.map(one, targets))
        with _LOCK:
            job = _JOBS[job_id]
            if job.get("cancel"):
                job["status"] = "cancelled"
            else:
                job["status"] = "done"
            job["finished"] = time.time()

    threading.Thread(target=work, daemon=True).start()
    return job_id


def existing_document(repo_name: str, qname: str) -> str:
    safe = qname.replace(".", "_").replace("/", "_").replace("#", "_")
    path = ROOT / "outputs" / "console" / (repo_name or "custom") / f"{safe}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    server_version = "CodeDocConsole/1.0"

    def log_message(self, fmt, *args):  # keep the terminal readable
        sys.stderr.write("  %s\n" % (fmt % args))

    # -- helpers -----------------------------------------------------------
    def _json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path):
        if not path.exists() or not path.is_file():
            self._json({"error": f"not found: {path.name}"}, 404)
            return
        suffix = path.suffix.lower()
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".svg": "image/svg+xml",
        }.get(suffix, "application/octet-stream")
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # No caching: the console is edited during use, and a stale bundle looks
        # exactly like a bug in the page.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except ValueError:
            return {}

    # -- routes ------------------------------------------------------------
    def do_GET(self):
        parsed = urlparse(self.path)
        route = parsed.path
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        try:
            if route in ("/", "/index.html"):
                self._file(STATIC / "index.html")
            elif route.startswith("/static/"):
                self._file(STATIC / route[len("/static/"):])
            elif route == "/api/bootstrap":
                config = load_config()
                self._json({
                    "config": public_config(config),
                    "repositories": list_repositories(),
                    "criteria_sets": [
                        {"id": p.stem, "path": str(p)} for p in sorted(CRITERIA_SETS.glob("*.json"))
                    ],
                    "templates": [
                        {"name": p.name, "path": str(p)} for p in sorted(TEMPLATES.glob("*.txt"))
                    ],
                    "relation_blocks": list(BLOCK_LABELS.values()),
                })
            elif route == "/api/criteria":
                set_id = query.get("id") or "practice_docstring"
                criterion_set = registry.load(set_id)
                self._json({
                    "id": set_id,
                    "axis_role": criterion_set.axis_role,
                    "criteria": [
                        {
                            "name": c.name,
                            "category": c.category,
                            "definition": c.definition,
                            "level": c.level,
                            "applies_to": [k for k in ("class", "method", "function") if c.applies_to(k)],
                            "missing_anchors": c.missing_anchors,
                        }
                        for c in criterion_set
                    ],
                })
            elif route == "/api/analyze":
                job_id = str(uuid.uuid4())
                spec = dict(
                    repo_name=query.get("repo", ""),
                    custom_path=query.get("path", ""),
                    mode=query.get("mode", "full"),
                    limit=int(query.get("limit") or 0),
                    seed=int(query.get("seed") or 42),
                )
                with _LOCK:
                    _JOBS[job_id] = {"status": "running", "started": time.time(), "result": None,
                                     "error": None}

                def work():
                    try:
                        entry = analyse(**spec)
                        with _LOCK:
                            _JOBS[job_id].update(status="done", result=entry["result"])
                    except Exception as exc:  # noqa: BLE001 - reported to the page
                        with _LOCK:
                            _JOBS[job_id].update(status="error", error=f"{type(exc).__name__}: {exc}",
                                                 traceback=traceback.format_exc(limit=4))

                threading.Thread(target=work, daemon=True).start()
                self._json({"job": job_id})
            elif route == "/api/job":
                with _LOCK:
                    job = _JOBS.get(query.get("id", ""))
                if job is None:
                    self._json({"error": "unknown job"}, 404)
                else:
                    self._json(job)
            elif route == "/api/entity":
                config = load_config()
                self._json(entity_detail(
                    query.get("repo", ""), query.get("path", ""),
                    query.get("mode", "full"), int(query.get("limit") or 0),
                    int(query.get("seed") or 42), query.get("qname", ""), config,
                ))
            elif route == "/api/graph":
                self._json(graph_data(
                    query.get("repo", ""), query.get("path", ""),
                    query.get("mode", "full"), int(query.get("limit") or 0),
                    int(query.get("seed") or 42), query.get("focus", ""),
                    int(query.get("depth") or 1), query.get("kinds", ""),
                ))
            elif route == "/api/document":
                self._json({"document": existing_document(query.get("repo", ""),
                                                          query.get("qname", ""))})
            else:
                self._json({"error": "unknown route"}, 404)
        except FileNotFoundError as exc:
            self._json({"error": str(exc)}, 404)
        except KeyError as exc:
            self._json({"error": str(exc)}, 404)
        except Exception as exc:  # noqa: BLE001
            self._json({"error": f"{type(exc).__name__}: {exc}",
                        "traceback": traceback.format_exc(limit=4)}, 500)

    def do_POST(self):
        route = urlparse(self.path).path
        body = self._body()
        try:
            if route == "/api/config":
                self._json({"config": public_config(save_config(body))})
            elif route == "/api/generate_all":
                config = load_config()
                for key in DEFAULT_CONFIG:
                    if key in body:
                        config[key] = body[key]
                if not config.get("api_key"):
                    raise RuntimeError("no API key configured")
                job_id = start_batch({
                    "repo_name": body.get("repo", ""),
                    "custom_path": body.get("path", ""),
                    "mode": body.get("mode", "full"),
                    "limit": int(body.get("limit") or 0),
                    "seed": int(body.get("seed") or 42),
                }, config, workers=int(body.get("workers") or 0))
                self._json({"job": job_id})
            elif route == "/api/job_cancel":
                with _LOCK:
                    job = _JOBS.get(body.get("id", ""))
                    if job is None:
                        self._json({"error": "unknown job"}, 404)
                        return
                    job["cancel"] = True
                self._json({"ok": True})
            elif route == "/api/generate":
                config = load_config()
                for key in DEFAULT_CONFIG:
                    if key in body:
                        config[key] = body[key]
                self._json(generate_document(
                    body.get("repo", ""), body.get("path", ""), body.get("mode", "full"),
                    int(body.get("limit") or 0), int(body.get("seed") or 42),
                    body.get("qname", ""), config,
                ))
            else:
                self._json({"error": "unknown route"}, 404)
        except Exception as exc:  # noqa: BLE001
            self._json({"error": f"{type(exc).__name__}: {exc}",
                        "traceback": traceback.format_exc(limit=4)}, 500)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    if not STATIC.exists():
        print(f"missing static assets: {STATIC}", file=sys.stderr)
        return 2

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"CodeDoc console: http://{args.host}:{args.port}/")
    print(f"  repositories: {TARGETS}")
    print(f"  config file : {CONFIG_PATH}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
