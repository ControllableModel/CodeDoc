"""Language-agnostic schema for code entities and the relations among them.

The published version of CodeDoc modelled a single relation, `call`/`called_by`,
which is a *function-level* notion.  That is precisely why class documentation
had no usable context: a class has no callees.  The schema below adds the
relations needed to describe classes and polymorphism, so the same downstream
prompt machinery can document every entity kind.

Relation kinds
--------------
``calls`` / ``called_by``      R1  function <-> function call edge
``inherits`` / ``subclassed_by`` R2/R3 class hierarchy, including interfaces
``instantiated_at``            R4  where a class is instantiated (missing before)
``overrides`` / ``overridden_by`` R5 method override pairs
``dispatch_candidates``        R6  same-named implementations across subclasses
``attribute_access``           R7  attribute reads/writes (optional)
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


class EntityKind:
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    MODULE = "module"
    #: An attribute observed on a class (``self.x`` inside its methods). The schema
    #: declared ``attribute_access`` as a relation kind, but until now no extractor
    #: emitted it — nine relation families were promised and eight were delivered.
    ATTRIBUTE = "attribute"

    ALL = (FUNCTION, METHOD, CLASS, MODULE, ATTRIBUTE)
    #: Kinds that can be documented as an entity of their own. Attributes carry
    #: relations but are not documented standalone.
    DOCUMENTABLE = (FUNCTION, METHOD, CLASS)


class RelationKind:
    CALLS = "calls"
    CALLED_BY = "called_by"
    INHERITS = "inherits"
    SUBCLASSED_BY = "subclassed_by"
    INSTANTIATED_AT = "instantiated_at"
    OVERRIDES = "overrides"
    OVERRIDDEN_BY = "overridden_by"
    DISPATCH_CANDIDATES = "dispatch_candidates"
    ATTRIBUTE_ACCESS = "attribute_access"

    ALL = (
        CALLS, CALLED_BY, INHERITS, SUBCLASSED_BY, INSTANTIATED_AT,
        OVERRIDES, OVERRIDDEN_BY, DISPATCH_CANDIDATES, ATTRIBUTE_ACCESS,
    )

    #: Relations whose target is another code entity (carries a name + path).
    ENTITY_TARGETED = ALL

    LABELS = {
        CALLS: "Calls",
        CALLED_BY: "Called by",
        INHERITS: "Inherits",
        SUBCLASSED_BY: "Subclassed by",
        INSTANTIATED_AT: "Instantiated at",
        OVERRIDES: "Overrides",
        OVERRIDDEN_BY: "Overridden by",
        DISPATCH_CANDIDATES: "Dispatch candidates",
        ATTRIBUTE_ACCESS: "Attribute access",
    }


@dataclass
class Entity:
    """A code entity that documentation can be produced for."""

    name: str
    kind: str
    path: str = ""
    span: Optional[List[int]] = None      # [start_line, end_line], 1-based
    qualified_name: str = ""

    def __post_init__(self) -> None:
        if self.kind not in EntityKind.ALL:
            raise ValueError(f"kind must be one of {EntityKind.ALL}, got {self.kind!r}")
        if not self.qualified_name:
            self.qualified_name = self.name

    @property
    def documentable(self) -> bool:
        return self.kind in EntityKind.DOCUMENTABLE

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class Relation:
    """A directed edge from the documented entity to another element."""

    kind: str
    target: str
    target_kind: str = EntityKind.FUNCTION
    path: str = ""
    line: Optional[int] = None
    detail: str = ""
    #: Fully qualified name of the target entity, when it is one inside the project.
    #: ``target`` is a human label and can be ambiguous (two classes named
    #: Blueprint in different packages); source injection needs the exact entity.
    target_qname: str = ""
    #: Source text the extractor wants injected for this relation, overriding what the
    #: writer would derive from the target entity. Used for call-site context (the
    #: caller's call expression, not the caller's body) and for attribute assignments.
    snippet: str = ""

    def __post_init__(self) -> None:
        if self.kind not in RelationKind.ALL:
            raise ValueError(f"unknown relation kind: {self.kind!r}")

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class DependencyContext:
    """Everything the writer needs to know about one entity's surroundings."""

    entity: Entity
    source: str = ""
    relations: Dict[str, List[Relation]] = field(default_factory=dict)

    def add(self, relation: Relation) -> None:
        self.relations.setdefault(relation.kind, []).append(relation)

    def get(self, kind: str) -> List[Relation]:
        return self.relations.get(kind, [])

    def count(self, kind: str) -> int:
        return len(self.relations.get(kind, []))

    @property
    def is_empty(self) -> bool:
        return not any(self.relations.values())

    def summary(self) -> Dict[str, int]:
        """Relation counts, used by the coverage reports in the experiments."""
        return {k: len(v) for k, v in self.relations.items() if v}

    def to_dict(self) -> Dict[str, object]:
        return {
            "entity": self.entity.to_dict(),
            "source": self.source,
            "relations": {k: [r.to_dict() for r in v] for k, v in self.relations.items() if v},
        }
