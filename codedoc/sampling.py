"""Deterministic, relation-stratified entity sampling.

Kept in the package rather than in a script because three callers need the same
selection: the console, the small-repo benchmark, and the experiment matrix driver.
Any divergence between them would silently make runs incomparable.
"""

from __future__ import annotations

import random


def pick_entities(index, limit: int, seed: int = 42) -> list:
    """Relation-stratified, deterministic entity selection.

    A plain kind-balanced sample can miss the relation families that make the
    experiment meaningful: a repository may have hundreds of methods and only a
    handful of classes that override anything. The sample therefore reserves a
    quota per relation family first, then fills the rest kind-balanced, so a 60
    entity sample still exercises inheritance, instantiation, overriding, dispatch
    and attribute access.

    Selection is deterministic for a given seed, which the reproduction protocol
    requires.
    """
    from codedoc.deps.schema import RelationKind

    rng = random.Random(seed)
    all_ctx = sorted(index.contexts, key=lambda c: str(c.entity.qualified_name))
    if limit <= 0 or limit >= len(all_ctx):
        return all_ctx

    # relation families that must be represented, hardest first
    families = [
        (RelationKind.SUBCLASSED_BY, 4),
        (RelationKind.INSTANTIATED_AT, 4),
        (RelationKind.OVERRIDES, 6),
        (RelationKind.DISPATCH_CANDIDATES, 4),
        (RelationKind.INHERITS, 4),
        (RelationKind.ATTRIBUTE_ACCESS, 3),
        (RelationKind.CALLED_BY, 3),
    ]

    picked = []
    seen = set()

    def take(candidates, count):
        taken = 0
        pool = [c for c in candidates if c.entity.qualified_name not in seen]
        rng.shuffle(pool)
        for ctx in pool:
            if taken >= count or len(picked) >= limit:
                break
            picked.append(ctx)
            seen.add(ctx.entity.qualified_name)
            taken += 1

    for relation_kind, quota in families:
        take([c for c in all_ctx if c.get(relation_kind)], quota)

    # fill kind-balanced
    by_kind: dict = {}
    for ctx in all_ctx:
        if ctx.entity.qualified_name in seen:
            continue
        by_kind.setdefault(str(ctx.entity.kind), []).append(ctx)
    kinds = sorted(by_kind)
    while len(picked) < limit and any(by_kind.values()):
        for kind in kinds:
            if len(picked) >= limit:
                break
            bucket = by_kind[kind]
            while bucket:
                ctx = bucket.pop(rng.randrange(len(bucket)))
                if ctx.entity.qualified_name in seen:
                    continue
                picked.append(ctx)
                seen.add(ctx.entity.qualified_name)
                break

    return picked


def coverage(index, selected) -> dict:
    """Relation-family coverage of a sample, for the experiment write-up."""
    from codedoc.deps.schema import RelationKind

    full = {str(kind): sum(1 for c in index.contexts if c.get(kind))
            for kind in RelationKind.ALL}
    sampled = {str(kind): sum(1 for c in selected if c.get(kind))
               for kind in RelationKind.ALL}
    return {"full": full, "sampled": sampled}
