"""Prompt assembly for documentation generation.

Two layers live here:

1. The **legacy single-relation assembly** (:func:`format_dep`,
   :func:`build_prompt`) is re-exported unchanged from ``codedoc.deps.dot`` so
   that previously published behaviour stays reproducible.
2. The **entity-aware assembly** (:func:`build_context_blocks`) renders the
   richer relation set from :mod:`codedoc.deps.schema`.  This is what makes
   class and method documentation possible: a class gets its inheritance chain,
   its instantiation sites and its override obligations, none of which a
   caller/callee-only prompt can express.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from codedoc.deps.dot import build_prompt, format_dep  # noqa: F401  (re-export)
from codedoc.deps.schema import DependencyContext, EntityKind, RelationKind

#: Relations that carry source snippets into the prompt, per entity kind.
_SNIPPET_RELATIONS = (RelationKind.CALLS, RelationKind.CALLED_BY)

__all__ = ["build_prompt", "format_dep", "build_context_blocks", "render_blocks"]


def _section(title: str, lines: List[str]) -> str:
    body = "\n".join(f"- {line}" for line in lines if line)
    return f"## {title}\n{body}\n" if body else ""


def build_context_blocks(context: DependencyContext) -> Dict[str, str]:
    """Render relation blocks keyed by section name.

    Kept as data (not a single string) so the same context can feed different
    templates, and so tests can assert on individual blocks.
    """
    blocks: Dict[str, str] = {}
    kind = context.entity.kind

    if kind == EntityKind.CLASS:
        blocks["Inheritance"] = _section(
            "Inheritance",
            [
                f"Inherits `{r.target}`" + (f" ({r.path})" if r.path else "")
                for r in context.get(RelationKind.INHERITS)
            ]
            + [
                f"Subclassed by `{r.target}`" + (f" ({r.path})" if r.path else "")
                for r in context.get(RelationKind.SUBCLASSED_BY)
            ],
        )
        blocks["Instantiation"] = _section(
            "Instantiated at",
            [
                f"`{r.target}`" + (f" in {r.path}:{r.line}" if r.path else "")
                for r in context.get(RelationKind.INSTANTIATED_AT)
            ],
        )
        blocks["Contract"] = _section(
            "Contract",
            [
                f"`{r.target}` is overridden in subclasses; document the contract "
                f"subclasses must satisfy"
                for r in context.get(RelationKind.OVERRIDDEN_BY)
            ],
        )
    else:
        blocks["Calls"] = _section(
            "Calls", [f"`{r.target}`" + (f" ({r.path})" if r.path else "")
                      for r in context.get(RelationKind.CALLS)]
        )
        blocks["CalledBy"] = _section(
            "Called by", [f"`{r.target}`" + (f" ({r.path})" if r.path else "")
                          for r in context.get(RelationKind.CALLED_BY)]
        )
        blocks["Override"] = _section(
            "Override relations",
            [
                f"Overrides `{r.target}`" + (f" ({r.path})" if r.path else "")
                for r in context.get(RelationKind.OVERRIDES)
            ]
            + [
                f"Overridden by `{r.target}`" + (f" ({r.path})" if r.path else "")
                for r in context.get(RelationKind.OVERRIDDEN_BY)
            ]
            + [
                f"Dispatch candidate `{r.target}`"
                for r in context.get(RelationKind.DISPATCH_CANDIDATES)
            ],
        )

    return {name: text for name, text in blocks.items() if text}


def render_blocks(blocks: Dict[str, str], order: Optional[List[str]] = None) -> str:
    """Join blocks in a stable order, for deterministic prompts."""
    if order is None:
        order = sorted(blocks)
    return "\n".join(blocks[name] for name in order if name in blocks)


def source_with_dependencies(context: DependencyContext) -> str:
    """Target source followed by the source of directly related entities."""
    parts = [context.source] if context.source else []
    for relation_kind in _SNIPPET_RELATIONS:
        for relation in context.get(relation_kind):
            if relation.detail:
                parts.append(f"# {relation_kind}: {relation.target}\n{relation.detail}")
    return "\n\n".join(parts)
