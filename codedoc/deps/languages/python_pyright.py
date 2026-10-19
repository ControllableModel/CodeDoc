"""Python dependency extractor backed by the Pyright language server.

Why Pyright
-----------
The static AST extractor (:mod:`codedoc.deps.languages.python_ast`) resolves a
call only when the callee's name is statically determinable, which on real
repositories covers a minority of call sites (7-22 % observed). Pyright performs
type inference, so ``obj.method()`` resolves when the receiver's type is
inferable, and ``definition`` resolves a base class to the file and line that
declares it — including bases imported from other modules.

What Pyright does **not** give us
---------------------------------
Its capabilities do not include ``typeHierarchyProvider`` (only
``callHierarchyProvider``, ``referencesProvider``, ``definitionProvider``,
``documentSymbolProvider``, ``workspaceSymbolProvider``). Class hierarchies are
therefore reconstructed from:

* ``textDocument/definition`` on every base-class expression → the declaring
  class, mapped back to a project entity by ``(path, line)``;
* the reverse of those edges for ``subclassed_by``;
* ``textDocument/references`` on a class → reference sites, mapped to the
  enclosing entity → ``instantiated_at`` and general usage.

So the extractor is a **hybrid**: the AST index supplies structure and precise
ranges, the language server supplies resolution. That division is deliberate —
it keeps the structural claims auditable and confines the type-aware part to the
steps that actually need it.
"""

from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from codedoc.deps.languages import register
from codedoc.deps.languages.base import Extractor
from codedoc.deps.languages.lsp_client import LspClient
from codedoc.deps.languages.python_ast import ProjectIndex
from codedoc.deps.schema import (
    DependencyContext,
    Entity,
    EntityKind,
    Relation,
    RelationKind,
)

#: Analysis scope pushed to Pyright. Without it every query triggers a
#: whole-workspace analysis (measured: 2 GB RSS / 600 s CPU on 24 files).
PYRIGHT_SETTINGS = {
    "python": {
        "analysis": {
            "diagnosticMode": "openFilesOnly",
            "indexing": False,
            "useLibraryCodeForTypes": False,
            "autoSearchPaths": False,
            "autoImportCompletions": False,
            "exclude": ["**/node_modules", "**/__pycache__", "**/.*"],
        }
    }
}

#: Node executable and pyright's language-server entry (installed via npm).
NODE_CANDIDATES = (
    r"C:\Program Files\nodejs\node.exe",
    "node",
)
LANGSERVER_CANDIDATES = (
    os.path.expandvars(r"%APPDATA%\npm\node_modules\pyright\langserver.index.js"),
    os.path.expandvars(r"%APPDATA%\npm\node_modules\pyright\langserver.index.js"),
)


def _find_node() -> Optional[str]:
    for candidate in NODE_CANDIDATES:
        if candidate == "node" or Path(candidate).exists():
            return candidate
    return None


def _find_langserver() -> Optional[str]:
    for candidate in LANGSERVER_CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _norm(path: str) -> str:
    """Normalize a path for comparisons.

    The language server returns lower-case drive letters (``file:///e:/...``)
    while the AST index stores ``E:\...``; comparing raw strings silently
    classifies every internal relation as external.
    """
    return os.path.normcase(str(Path(path).resolve()))


class _IntervalIndex:
    """Map ``(path, line)`` to the innermost enclosing entity."""

    def __init__(self, index: ProjectIndex) -> None:
        self.by_path: Dict[str, List[Tuple[int, int, str, str]]] = defaultdict(list)
        for qname, info in index.classes.items():
            self.by_path[_norm(info.path)].append((info.lineno, info.end_lineno, qname, EntityKind.CLASS))
        for qname, info in index.functions.items():
            self.by_path[_norm(info.path)].append((info.lineno, info.end_lineno, qname, info.kind))
        for spans in self.by_path.values():
            spans.sort(key=lambda s: (s[0], -(s[1])))

    def at(self, path: str, line: int) -> Optional[Tuple[str, str]]:
        best = None
        for start, end, qname, kind in self.by_path.get(_norm(path), []):
            if start <= line <= end:
                if best is None or (start >= best[0] and end <= best[1]):
                    best = (start, end, qname, kind)
            elif start > line:
                break
        return (best[2], best[3]) if best else None


@register
class PythonPyrightExtractor(Extractor):
    """Class + function dependencies resolved by Pyright, structure by ``ast``."""

    language = "python"
    suffixes = (".py",)
    backend = "pyright LSP + stdlib ast"
    status = "implemented"
    supported_relations = (
        RelationKind.CALLS,
        RelationKind.CALLED_BY,
        RelationKind.INHERITS,
        RelationKind.SUBCLASSED_BY,
        RelationKind.INSTANTIATED_AT,
        RelationKind.OVERRIDES,
        RelationKind.OVERRIDDEN_BY,
        RelationKind.DISPATCH_CANDIDATES,
    )

    def __init__(
        self,
        timeout: float = 30.0,
        max_entities: Optional[int] = None,
        max_requests: Optional[int] = None,
        use_references: bool = False,
    ) -> None:
        self.timeout = timeout
        #: Cap on entities queried per run; large repositories are sampled and the
        #: sample size is reported instead of silently truncating.
        self.max_entities = max_entities
        self.max_requests = max_requests
        #: Pyright's ``references`` adds little over the AST call index for
        #: *internal* sites and is expensive, so it is off by default.
        self.use_references = use_references
        self._index: Optional[ProjectIndex] = None
        self._intervals: Optional[_IntervalIndex] = None
        self.stats: Dict[str, int] = defaultdict(int)

    # -- setup --------------------------------------------------------------
    def _prepare(self, repo_root: str) -> ProjectIndex:
        if self._index is None:
            self._index = ProjectIndex(repo_root).build()
            self._intervals = _IntervalIndex(self._index)
        return self._index

    def _client(self, repo_root: str) -> LspClient:
        node = _find_node()
        server = _find_langserver()
        if not node or not server:
            raise RuntimeError(
                "pyright language server not found. Install with `npm i -g pyright`; "
                f"looked for node in {NODE_CANDIDATES} and server in {LANGSERVER_CANDIDATES}"
            )
        return LspClient(
            [node, server, "--stdio"],
            repo_root,
            timeout=self.timeout,
            settings=PYRIGHT_SETTINGS,
            max_requests=self.max_requests,
        )

    def _path_of(self, uri: str, root: Path) -> str:
        from urllib.parse import unquote, urlparse

        parsed = urlparse(uri)
        p = Path(unquote(parsed.path.lstrip("/")))
        return str(p)

    def _in_project(self, path: str, repo_root: str) -> bool:
        root = _norm(repo_root)
        target = _norm(path)
        return target == root or target.startswith(root.rstrip(os.sep) + os.sep)

    # -- measure ------------------------------------------------------------
    def measure(self, repo_root: str) -> Dict[str, int]:
        idx = self._prepare(repo_root)
        methods = sum(1 for f in idx.functions.values() if f.kind == EntityKind.METHOD)
        functions = sum(1 for f in idx.functions.values() if f.kind == EntityKind.FUNCTION)
        return {
            "classes": len(idx.classes),
            "methods": methods,
            "functions": functions,
            "documentable": methods + functions,
            "files": len(idx.modules),
            "bases_declared": sum(len(i.bases_raw) for i in idx.classes.values()),
        }

    # -- extraction ---------------------------------------------------------
    def extract(self, repo_root: str) -> List[DependencyContext]:
        idx = self._prepare(repo_root)
        assert self._intervals is not None
        root = Path(repo_root).resolve()
        client = self._client(repo_root)
        contexts: List[DependencyContext] = []
        client.start()
        try:
            # 1. internal inheritance edges via definition resolution
            base_edges, external_bases = self._resolve_bases(client, idx, repo_root, root)
            subs: Dict[str, List[str]] = defaultdict(list)
            for child, parents in base_edges.items():
                for parent in parents:
                    subs[parent].append(child)

            # 2. class contexts
            for qname, info in idx.classes.items():
                ctx = DependencyContext(
                    entity=Entity(
                        name=info.name, kind=EntityKind.CLASS, path=info.path,
                        span=[info.lineno, info.end_lineno], qualified_name=qname,
                    ),
                    source=self._slice(info.path, info.lineno, info.end_lineno),
                )
                for parent in base_edges.get(qname, []):
                    ctx.add(Relation(kind=RelationKind.INHERITS,
                                     target=idx.display_name(parent),
                                     target_kind=EntityKind.CLASS,
                                     path=idx.classes[parent].path))
                for child in subs.get(qname, []):
                    ctx.add(Relation(kind=RelationKind.SUBCLASSED_BY,
                                     target=idx.display_name(child),
                                     target_kind=EntityKind.CLASS,
                                     path=idx.classes[child].path))
                # references -> instantiation / usage sites (optional)
                refs = []
                if self.use_references:
                    refs = client.references(
                        info.path, info.lineno,
                        self._name_column(info.path, info.lineno, info.name))
                    self.stats["class_references"] += len(refs)
                for ref in refs:
                    ref_path = self._path_of(ref["uri"], root)
                    line = ref["range"]["start"]["line"] + 1
                    if not self._in_project(ref_path, repo_root):
                        continue
                    enclosing = self._intervals.at(ref_path, line)
                    if not enclosing or enclosing[0] == qname:
                        continue
                    ctx.add(Relation(
                        kind=RelationKind.INSTANTIATED_AT,
                        target=enclosing[0].split(".")[-1],
                        target_kind=enclosing[1], path=ref_path, line=line,
                    ))
                for mname, mqname in info.methods.items():
                    impls = [c for c in subs.get(qname, []) if mname in idx.classes[c].methods]
                    if impls:
                        ctx.add(Relation(
                            kind=RelationKind.OVERRIDDEN_BY,
                            target=f"{info.name}.{mname}",
                            target_kind=EntityKind.METHOD,
                            detail="implemented by " + ", ".join(
                                f"{idx.classes[c].name}.{mname}" for c in impls[:6]),
                        ))
                contexts.append(ctx)

            # 3. function / method contexts via call hierarchy
            entities = list(idx.functions.items())
            sampled = False
            if self.max_entities and len(entities) > self.max_entities:
                entities = entities[: self.max_entities]
                sampled = True
            called_by: Dict[str, List[str]] = defaultdict(list)
            for qname, info in entities:
                ctx = DependencyContext(
                    entity=Entity(
                        name=(f"{info.owner.split('.')[-1]}.{info.name}" if info.owner else info.name),
                        kind=info.kind, path=info.path, span=[info.lineno, info.end_lineno],
                        qualified_name=qname,
                    ),
                    source=self._slice(info.path, info.lineno, info.end_lineno),
                )
                column = self._name_column(info.path, info.lineno, info.name)
                items = client.prepare_call_hierarchy(info.path, info.lineno, column)
                if items:
                    self.stats["hierarchy_items"] += 1
                    item = items[0]
                    for call in client.outgoing_calls(item):
                        target = call.get("to", {})
                        resolved = self._entity_of_item(target, root, repo_root)
                        if resolved:
                            ctx.add(Relation(kind=RelationKind.CALLS,
                                             target=resolved[0].split(".")[-1],
                                             target_kind=resolved[1],
                                             path=target.get("uri", "")))
                        else:
                            name = (target.get("name") or "").split(".")[-1]
                            ctx.add(Relation(kind=RelationKind.CALLS, target=name,
                                             target_kind=EntityKind.FUNCTION, detail="external"))
                            self.stats["external_calls"] += 1
                    for call in client.incoming_calls(item):
                        source = call.get("from", {})
                        resolved = self._entity_of_item(source, root, repo_root)
                        name = (resolved[0] if resolved else (source.get("name") or "")).split(".")[-1]
                        ctx.add(Relation(kind=RelationKind.CALLED_BY, target=name,
                                         target_kind=EntityKind.FUNCTION))
                        if resolved:
                            called_by[resolved[0]].append(qname)
                else:
                    self.stats["hierarchy_missing"] += 1
                # override relations from resolved inheritance
                if info.kind == EntityKind.METHOD and info.owner:
                    for parent in base_edges.get(info.owner, []):
                        if info.name in idx.classes[parent].methods:
                            ctx.add(Relation(kind=RelationKind.OVERRIDES,
                                             target=f"{idx.classes[parent].name}.{info.name}",
                                             target_kind=EntityKind.METHOD,
                                             path=idx.classes[parent].path))
                    for child in subs.get(info.owner, []):
                        if info.name in idx.classes[child].methods:
                            ctx.add(Relation(kind=RelationKind.OVERRIDDEN_BY,
                                             target=f"{idx.classes[child].name}.{info.name}",
                                             target_kind=EntityKind.METHOD,
                                             path=idx.classes[child].path))
                    for parent in base_edges.get(info.owner, []):
                        for peer in subs.get(parent, []):
                            if peer != info.owner and info.name in idx.classes[peer].methods:
                                ctx.add(Relation(kind=RelationKind.DISPATCH_CANDIDATES,
                                                 target=f"{idx.classes[peer].name}.{info.name}",
                                                 target_kind=EntityKind.METHOD,
                                                 path=idx.classes[peer].path))
                contexts.append(ctx)
            self.stats["entities_queried"] = len(entities)
            self.stats["entities_total"] = len(idx.functions)
            self.stats["sampled"] = int(sampled)
            self.stats["external_bases"] = external_bases
        finally:
            client.stop()
        return contexts

    # -- helpers ------------------------------------------------------------
    def _resolve_bases(self, client: Optional[LspClient], idx: ProjectIndex, repo_root: str, root: Path) -> Tuple[Dict[str, List[str]], int]:
        """Map class -> resolved internal parents.

        Resolution is done on the AST index (module scope + import graph), which
        is cheap and sufficient for *internal* inheritance. Asking the language
        server for ``definition`` of every base turned out to be the single
        most expensive operation in the pipeline and resolved no additional
        internal edge, so it is not used.
        """
        edges: Dict[str, List[str]] = defaultdict(list)
        external = 0
        for qname, info in idx.classes.items():
            for raw in info.bases_raw:
                if not raw:
                    continue
                target = idx._resolve_dotted(info.module, raw, info.outer_function)
                if target and target in idx.classes and target != qname:
                    edges[qname].append(target)
                    self.stats["bases_resolved_internal"] += 1
                else:
                    external += 1
        return dict(edges), external

    def _entity_of_item(self, item: Dict, root: Path, repo_root: str) -> Optional[Tuple[str, str]]:
        uri = item.get("uri") or ""
        if not uri:
            return None
        path = self._path_of(uri, root)
        if not self._in_project(path, repo_root):
            return None
        line = item.get("selectionRange", {}).get("start", {}).get("line", 0) + 1
        assert self._intervals is not None
        return self._intervals.at(path, line)

    @staticmethod
    def _name_column(path: str, lineno: int, name: str) -> int:
        try:
            line = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()[lineno - 1]
        except (OSError, IndexError):
            return 0
        idx = line.find(name)
        return idx if idx >= 0 else 0

    @staticmethod
    def _slice(path: str, start: int, end: int) -> str:
        try:
            lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return ""
        return "\n".join(lines[max(0, start - 1):end])
