"""Export the relation set as Graphviz DOT.

DOT is **no longer the pipeline's intermediate representation** — relations are
extracted directly (stdlib AST, or a language server) and stored as typed
records. This module exists so that DOT survives as an *export* format, which is
all it was ever good for here:

* figures and manual inspection of a dependency neighbourhood;
* diffing two extraction runs (a DOT file is easy to eyeball);
* reproducing the shape of the previously published graphs for comparison.

Usage::

    from codedoc.deps.export_dot import to_dot
    dot = to_dot(index.contexts, focus="Flask")
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence

from codedoc.deps.schema import DependencyContext, RelationKind

#: Relations rendered as edges. ``inherits``/``calls`` dominate an inspection graph.
DEFAULT_KINDS: Sequence[str] = (
    RelationKind.INHERITS,
    RelationKind.CALLS,
)

_EDGE_STYLE = {
    RelationKind.INHERITS: 'arrowhead="onormal", color="#1f77b4"',
    RelationKind.CALLS: 'arrowhead="normal", color="#888888"',
    RelationKind.INSTANTIATED_AT: 'style="dashed", arrowhead="normal", color="#2ca02c"',
    RelationKind.OVERRIDES: 'style="dashed", arrowhead="empty", color="#d62728"',
    RelationKind.SUBCLASSED_BY: 'arrowhead="onormal", color="#17becf"',
    RelationKind.CALLED_BY: 'arrowhead="normal", color="#bbbbbb"',
}


def _quote(name: str) -> str:
    return '"' + name.replace('"', '\\"') + '"'


def to_dot(
    contexts: Iterable[DependencyContext],
    focus: Optional[str] = None,
    depth: int = 1,
    kinds: Sequence[str] = DEFAULT_KINDS,
    rankdir: str = "LR",
) -> str:
    """Render a DOT digraph.

    With ``focus`` only the neighbourhood of that entity is emitted (the entity
    itself plus its relations up to ``depth`` hops), which keeps figures readable.
    """
    contexts = list(contexts)
    by_name = {c.entity.name: c for c in contexts}
    by_qname = {c.entity.qualified_name: c for c in contexts}

    selected: List[DependencyContext] = []
    if focus is None:
        selected = contexts
    else:
        frontier = [by_name.get(focus) or by_qname.get(focus)]
        seen = set()
        for _ in range(max(1, depth) + 1):
            next_frontier = []
            for ctx in [f for f in frontier if f is not None]:
                key = ctx.entity.qualified_name
                if key in seen:
                    continue
                seen.add(key)
                selected.append(ctx)
                for kind in kinds:
                    for relation in ctx.get(kind):
                        target = by_name.get(relation.target)
                        if target is not None:
                            next_frontier.append(target)
            frontier = next_frontier

    lines = [f"digraph dependencies {{", f'  rankdir="{rankdir}";',
             '  node [shape="box", fontsize=10, style="rounded"];']
    emitted_nodes = set()
    emitted_edges = set()
    for ctx in selected:
        name = ctx.entity.name
        if name not in emitted_nodes:
            shape = "box3d" if ctx.entity.kind == "class" else "box"
            lines.append(f"  {_quote(name)} [shape={shape}];")
            emitted_nodes.add(name)
        for kind in kinds:
            for relation in ctx.get(kind):
                edge = (name, relation.target, kind)
                if edge in emitted_edges:
                    continue
                emitted_edges.add(edge)
                if relation.target not in emitted_nodes:
                    lines.append(f"  {_quote(relation.target)};")
                    emitted_nodes.add(relation.target)
                style = _EDGE_STYLE.get(kind, "")
                label = f'label="{kind}", {style}' if style else f'label="{kind}"'
                lines.append(f"  {_quote(name)} -> {_quote(relation.target)} [{label}];")
    lines.append("}")
    return "\n".join(lines) + "\n"
