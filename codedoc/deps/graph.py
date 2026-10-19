"""Graph helpers over :class:`~codedoc.deps.schema.Relation` records.

Kept deliberately small: traversals needed by prompt assembly and by the
coverage reports (how many relations were recovered per entity kind).
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Set

from codedoc.deps.schema import DependencyContext, EntityKind, Relation, RelationKind


def ancestors(context: DependencyContext, depth: int = 1) -> List[str]:
    """Inheritance chain names, nearest first."""
    chain: List[str] = []
    frontier = [r.target for r in context.get(RelationKind.INHERITS)]
    while frontier and len(chain) < depth:
        chain.extend(frontier)
        # Only local hops are resolvable without querying the extractor again.
        frontier = []
    return chain


def override_chain(context: DependencyContext) -> Dict[str, List[str]]:
    """Map each overridden/overriding pair for a method."""
    return {
        "overrides": [r.target for r in context.get(RelationKind.OVERRIDES)],
        "overridden_by": [r.target for r in context.get(RelationKind.OVERRIDDEN_BY)],
        "dispatch": [r.target for r in context.get(RelationKind.DISPATCH_CANDIDATES)],
    }


def is_polymorphic(context: DependencyContext) -> bool:
    """True when the entity participates in override or dynamic dispatch."""
    return bool(
        context.get(RelationKind.OVERRIDES)
        or context.get(RelationKind.OVERRIDDEN_BY)
        or context.get(RelationKind.DISPATCH_CANDIDATES)
    )


def merge(*contexts: DependencyContext) -> DependencyContext:
    """Merge relation sets that describe the same entity."""
    if not contexts:
        raise ValueError("merge() requires at least one context")
    base = contexts[0]
    seen: Set[str] = set()
    for ctx in contexts:
        for kind, relations in ctx.relations.items():
            for rel in relations:
                key = f"{kind}|{rel.target}|{rel.path}"
                if key in seen:
                    continue
                seen.add(key)
                if kind not in base.relations:
                    base.relations[kind] = []
                base.relations[kind].append(rel)
    return base


def coverage(contexts: Iterable[DependencyContext]) -> Dict[str, Dict[str, float]]:
    """Relation coverage per entity kind.

    Reported in the paper as evidence that class-level context is actually
    recovered rather than merely claimed.
    """
    stats: Dict[str, Dict[str, List[int]]] = {}
    for ctx in contexts:
        kind = ctx.entity.kind
        bucket = stats.setdefault(
            kind, {rk: [0, 0] for rk in RelationKind.ALL}
        )
        for rk in RelationKind.ALL:
            bucket[rk][0] += ctx.count(rk)
            bucket[rk][1] += 1
    out: Dict[str, Dict[str, float]] = {}
    for kind, bucket in stats.items():
        n = next(iter(bucket.values()))[1] or 1
        out[kind] = {rk: v[0] / n for rk, v in bucket.items()}
    return out


def entities_without_context(contexts: Iterable[DependencyContext]) -> List[str]:
    """Entities whose dependency context is empty (a documentation-quality risk)."""
    return [ctx.entity.qualified_name for ctx in contexts if ctx.is_empty]
