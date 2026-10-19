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
        for ctx in contexts:
            self._by_key[ctx.entity.qualified_name] = ctx
            self._by_name.setdefault(ctx.entity.name, ctx)
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
        return self._by_key.get(key) or self._by_name.get(name)

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


def get_dep(index: RelationsIndex, display: str, key: str, fpath: str) -> Optional[Dict[str, object]]:
    """Return the writer-facing record for one entity.

    Keeps the historical keys (``real_name``/``source_code``/``uses``/``used_by``)
    so templates keep working, and adds ``relations`` for the new blocks.
    """
    ctx = index.get(key=key, name=display)
    if ctx is None:
        ctx = index.get(key=key) or index.get(name=display.split(".")[-1])
    if ctx is None:
        return None

    uses = [
        {rel.target: rel.detail or rel.path or ""}
        for rel in ctx.get(RelationKind.CALLS)
    ]
    used_by = [{rel.target: rel.path or ""} for rel in ctx.get(RelationKind.CALLED_BY)]
    relations = {
        BLOCK_LABELS[kind]: [rel.target for rel in ctx.get(kind)]
        for kind in BLOCK_LABELS
        if ctx.get(kind)
    }
    return {
        "real_name": ctx.entity.name,
        "display_name": ctx.entity.name,
        "kind": ctx.entity.kind,
        "qualified_name": ctx.entity.qualified_name,
        "path": ctx.entity.path or fpath,
        "source_code": ctx.source,
        "uses": uses,
        "used_by": used_by,
        "relations": relations,
        "is_polymorphic": bool(
            ctx.get(RelationKind.OVERRIDES)
            or ctx.get(RelationKind.OVERRIDDEN_BY)
            or ctx.get(RelationKind.DISPATCH_CANDIDATES)
        ),
    }
