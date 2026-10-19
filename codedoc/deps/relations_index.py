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
    RelationKind.ATTRIBUTE_ACCESS: "Attribute access",
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
    snippet_lines: int = 40,
    max_snippets: int = 10,
    relation_snippet_lines: int = 40,
    relation_max_snippets: int = 8,
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

    # Every relation is listed; only the *source snippet* is budgeted. Truncating the
    # list instead (the earlier behaviour, capped at six) hid the structure of the
    # dependency set from the model while saving very little: names are ~30 chars,
    # bodies are ~1 KB each.
    def entries(relations):
        """One entry per relation; extractor snippets win over the target's body.

        For ``called_by`` the extractor supplies the *call site*, which is what shows
        how the entity is used; the caller's whole body buries it.
        """
        out = []
        for i, rel in enumerate(relations):
            if i >= max_snippets:
                out.append({index.label(rel.target): ""})
            elif rel.snippet:
                out.append({index.label(rel.target): rel.snippet})
            else:
                out.append({index.label(rel.target): snippet(rel.target)})
        return out

    uses = entries(ctx.get(RelationKind.CALLS))
    used_by = entries(ctx.get(RelationKind.CALLED_BY))
    # Relation targets also carry source now. Input tokens are cheap and output is
    # not, so the model should see the base class or the overridden method it has to
    # honour rather than only its name. Classes contribute their class view
    # (declaration + __init__ + signatures) so a base class does not flood the prompt
    # with implementation detail; methods and functions contribute a clipped body.
    def relation_entry(rel, index_in_block: int) -> Dict[str, str]:
        # Exact qualified name first: the label can be ambiguous, and an attribute
        # name must never be resolved to an unrelated same-named method.
        target_ctx = index._by_key.get(rel.target_qname) if rel.target_qname else None
        if target_ctx is None:
            target_ctx = index.get(name=rel.target)
        if target_ctx is None:
            candidates = index._by_short.get(rel.target.split(".")[-1], [])
            target_ctx = candidates[0] if len(candidates) == 1 else None
        code = ""
        # An extractor-supplied snippet wins: it is deliberately more precise than
        # "the target's body" (call-site context, attribute assignment).
        if rel.snippet and index_in_block < relation_max_snippets:
            snippet_lines = rel.snippet.splitlines()
            if len(snippet_lines) > relation_snippet_lines:
                snippet_lines = snippet_lines[:relation_snippet_lines]
            snippet_name = (rel.target if rel.kind == RelationKind.ATTRIBUTE_ACCESS
                            else index.label(rel.target))
            return {"name": snippet_name, "code": "\n".join(snippet_lines)}
        if (target_ctx is not None and index_in_block < relation_max_snippets
                and rel.kind != RelationKind.ATTRIBUTE_ACCESS):
            body = target_ctx.source or ""
            if str(target_ctx.entity.kind) == "class":
                from codedoc.writer.classview import class_skeleton
                body = class_skeleton(body)
            lines = body.splitlines()
            if len(lines) > relation_snippet_lines:
                lines = lines[:relation_snippet_lines] + [
                    f"# ... {len(lines) - relation_snippet_lines} more lines ..."
                ]
            code = "\n".join(lines)
        # An attribute name is not an entity: resolving it through the short-name
        # index produced things like "_find_error_handler" -> "App._find_error_handler".
        name = rel.target if rel.kind == RelationKind.ATTRIBUTE_ACCESS else index.label(rel.target)
        return {"name": name, "code": code}

    relations = {
        BLOCK_LABELS[kind]: [relation_entry(rel, i) for i, rel in enumerate(ctx.get(kind))]
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
