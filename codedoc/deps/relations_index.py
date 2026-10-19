"""Relationship index used by the generation pipeline.

This module is the seam between *dependency extraction* and *documentation
generation*. It replaces the pyan3/DOT path:

======================  ====================================================
before                  after
======================  ====================================================
``Analyzer.scan()``     :func:`build_index` (default extractor, AST-based)
→ ``pyan3 --dot``       (no DOT in the pipeline; ``export_dot`` writes DOT out)
``DotParser``/``Navigator``  :class:`RelationsIndex` over ``DependencyContext``
``dot.get_dep()``       :func:`get_dep` → the dict shape the writer expects
======================  ====================================================

The dict returned by :func:`get_dep` keeps the keys the writer already used
(``real_name``, ``path``, ``source_code``, ``uses``, ``used_by``) and adds the
class/polymorphism relations, so prompt building gains them without breaking
existing templates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from codedoc.deps import languages
from codedoc.deps.schema import DependencyContext, EntityKind, RelationKind
from codedoc.writer.classview import class_skeleton

#: Relation kinds rendered as their own labelled block in prompts and audits.
BLOCK_LABELS = {
    RelationKind.INHERITS: "Inherits",
    RelationKind.SUBCLASSED_BY: "Subclassed by",
    RelationKind.INSTANTIATED_AT: "Instantiated at",
    RelationKind.OVERRIDES: "Overrides",
    RelationKind.OVERRIDDEN_BY: "Overridden by",
    RelationKind.DISPATCH_CANDIDATES: "Dispatch candidates",
}


class RelationsIndex:
    """Lookup structure over the extracted relation set."""

    def __init__(self, contexts: List[DependencyContext], backend: str) -> None:
        self.backend = backend
        self.contexts = contexts
        self._by_key: Dict[str, DependencyContext] = {}
        self._by_name: Dict[str, DependencyContext] = {}
        #: short name ("method") -> contexts. Relation targets are recorded with
        #: short names for readability, so lookups must tolerate them.
        self._by_short: Dict[str, List[DependencyContext]] = {}
        for ctx in contexts:
            self._by_key[ctx.entity.qualified_name] = ctx
            self._by_name.setdefault(ctx.entity.name, ctx)
            short = ctx.entity.name.split(".")[-1]
            self._by_short.setdefault(short, []).append(ctx)
        #: stem -> {"path": str, "members": {...}} — the shape ``cli.py`` iterates
        self.files: Dict[str, Dict[str, object]] = self._build_files()

    # -- views --------------------------------------------------------------
    def _build_files(self) -> Dict[str, Dict[str, object]]:
        files: Dict[str, Dict[str, object]] = {}
        for ctx in self.contexts:
            path = Path(ctx.entity.path)
            stem = path.stem
            entry = files.setdefault(stem, {"path": ctx.entity.path, "members": {"classes": {}, "functions": []}})
            members = entry["members"]  # type: ignore[index]
            if ctx.entity.kind == EntityKind.CLASS:
                members["classes"].setdefault(  # type: ignore[index]
                    ctx.entity.name,
                    {"key": ctx.entity.qualified_name, "name": ctx.entity.name, "methods": []},
                )
            elif ctx.entity.kind == EntityKind.METHOD:
                owner = ctx.entity.name.split(".")[0]
                cls = members["classes"].setdefault(  # type: ignore[index]
                    owner,
                    {"key": f"{ctx.entity.qualified_name.rsplit('.', 2)[0]}.{owner}",
                     "name": owner, "methods": []},
                )
                cls["methods"].append({"key": ctx.entity.qualified_name, "name": ctx.entity.name})
            else:
                members["functions"].append(  # type: ignore[index]
                    {"key": ctx.entity.qualified_name, "name": ctx.entity.name}
                )
        return files

    def get(self, key: str = "", name: str = "") -> Optional[DependencyContext]:
        found = self._by_key.get(key) or self._by_name.get(name)
        if found is not None:
            return found
        # fall back to a unique short-name match
        candidates = self._by_short.get((name or key).split(".")[-1], [])
        return candidates[0] if len(candidates) == 1 else None

    def label(self, short: str) -> str:
        """Qualified label for a relation target, when it is unambiguous."""
        candidates = self._by_short.get(short.split(".")[-1], [])
        if len(candidates) == 1:
            return candidates[0].entity.name
        return short

    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for ctx in self.contexts:
            for kind, rels in ctx.relations.items():
                counts[kind] = counts.get(kind, 0) + len(rels)
        return counts


def build_index(target: str, backend: Optional[str] = None) -> Optional[RelationsIndex]:
    """Extract relations for a repository.

    ``backend`` selects a registered extractor backend (see
    ``languages.describe()``); the default is the language's implemented default,
    which for Python is the dependency-free AST backend.
    """
    detected = languages.detect(str(target))
    if not detected:
        return None
    language = detected[0]
    extractor = languages.get(language, backend)
    contexts = extractor.extract(str(target))
    if not contexts:
        return None
    return RelationsIndex(contexts, backend=f"{extractor.backend}")


def get_dep(
    index: RelationsIndex,
    display: str,
    key: str,
    fpath: str,
    snippet_lines: int = 20,
    max_deps: int = 6,
) -> Optional[Dict[str, object]]:
    """Return the writer-facing record for one entity.

    Keeps the historical keys (``real_name``/``source_code``/``uses``/``used_by``)
    so templates keep working, and adds ``relations`` for the new blocks.
    """
    ctx = index.get(key=key, name=display)
    if ctx is None:
        ctx = index.get(key=key) or index.get(name=display.split(".")[-1])
    if ctx is None:
        return None

    # Inject the dependency's *source*, not its path. The earlier pipeline put a
    # path into a ```python fence, which told the model it was looking at code when
    # it was looking at a filename.
    def snippet(target: str) -> str:
        dep_ctx = index.get(name=target)
        if dep_ctx is None:
            candidates = index._by_short.get(target.split(".")[-1], [])
            dep_ctx = candidates[0] if len(candidates) == 1 else None
        if dep_ctx is None or not dep_ctx.source:
            return ""
        lines = dep_ctx.source.splitlines()
        if len(lines) > snippet_lines:
            lines = lines[:snippet_lines] + [
                f"# ... {len(lines) - snippet_lines} more lines ..."
            ]
        return "\n".join(lines)

    # Dependency snippets are the bulk of the prompt, so both the per-dependency
    # length and the number of rendered dependencies are bounded: uncapped, four
    # dependency bodies left no budget for the entity itself.
    calls = ctx.get(RelationKind.CALLS)[:max_deps]
    callers = ctx.get(RelationKind.CALLED_BY)[:max_deps]
    uses = [{index.label(rel.target): snippet(rel.target)} for rel in calls]
    used_by = [{index.label(rel.target): snippet(rel.target)} for rel in callers]
    relations = {
        BLOCK_LABELS[kind]: [rel.target for rel in ctx.get(kind)]
        for kind in BLOCK_LABELS
        if ctx.get(kind)
    }
    source = ctx.source
    # A class body is a poor prompt: implementation detail that the class document
    # should not restate, and long enough to crowd out everything else. The agreed
    # view keeps the declaration, __init__ in full, and the remaining method
    # signatures; method bodies are documented by their own entities.
    prompt_source = class_skeleton(source) if ctx.entity.kind == EntityKind.CLASS else source

    return {
        "real_name": ctx.entity.name,
        "display_name": ctx.entity.name,
        "kind": ctx.entity.kind,
        "qualified_name": ctx.entity.qualified_name,
        "path": ctx.entity.path or fpath,
        "source_code": source,
        "prompt_source": prompt_source,
        "uses": uses,
        "used_by": used_by,
        "relations": relations,
        "is_polymorphic": bool(
            ctx.get(RelationKind.OVERRIDES)
            or ctx.get(RelationKind.OVERRIDDEN_BY)
            or ctx.get(RelationKind.DISPATCH_CANDIDATES)
        ),
    }
