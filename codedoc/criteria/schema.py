"""Data model for standards-derived documentation criteria.

A criterion is the bridge between a normative clause (ISO/IEC/IEEE 26514, a
language docstring convention, a vendor style guide) and a machine-checkable
expectation.  Three properties matter for construct validity:

``level``
    Whether the requirement governs a *single code entity* (a docstring) or a
    *document set* (an article/page collection).  Mixing the two is the main
    reason several rubric dimensions never vary on code-level artifacts.
``anchors``
    The scoring rubric.  A 1--5 scale is unusable unless every level is
    defined, so anchors are first-class data here.
``source``
    A resolvable pointer to the clause the criterion was derived from.  Without
    it the criterion set cannot be audited, which is what reviewers asked for.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

ENTITY = "entity"          # governed per code entity (docstring level)
DOCUMENT_SET = "document-set"  # governed over a collection of documents

APPLICABILITY = (ENTITY, DOCUMENT_SET)


@dataclass
class Criterion:
    """A single assessable requirement."""

    id: str
    name: str
    category: str
    definition: str
    level: str = ENTITY
    source: str = ""
    #: Scoring anchors, keyed by integer score (1..S). Missing levels are
    #: exactly the gap reviewers flagged: only the endpoints were ever defined.
    anchors: Dict[int, str] = field(default_factory=dict)
    applicable_to_entity: Optional[bool] = None
    note: str = ""

    def __post_init__(self) -> None:
        if self.level not in APPLICABILITY:
            raise ValueError(f"level must be one of {APPLICABILITY}, got {self.level!r}")
        # normalize anchor keys to ints (JSON round-trip yields strings)
        self.anchors = {int(k): v for k, v in (self.anchors or {}).items()}
        if self.applicable_to_entity is None:
            self.applicable_to_entity = self.level == ENTITY

    @property
    def has_full_anchors(self) -> bool:
        """True when every score level of the scale is defined."""
        return bool(self.anchors) and sorted(self.anchors) == list(
            range(min(self.anchors), max(self.anchors) + 1)
        )

    @property
    def missing_anchors(self) -> List[int]:
        if not self.anchors:
            return list(range(1, 6))
        lo, hi = min(self.anchors), max(self.anchors)
        return [i for i in range(lo, hi + 1) if i not in self.anchors]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["anchors"] = {str(k): v for k, v in self.anchors.items()}
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Criterion":
        return cls(**data)


@dataclass
class CriterionSet:
    """A named collection of criteria plus provenance."""

    id: str
    title: str
    version: str
    standards: List[str] = field(default_factory=list)
    description: str = ""
    #: Role of this axis in the evaluation design, e.g. "primary" / "secondary"
    #: / "sanity-check".  Recorded so no axis is silently promoted.
    axis_role: str = "primary"
    criteria: List[Criterion] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.criteria)

    def __iter__(self):
        return iter(self.criteria)

    @property
    def names(self) -> List[str]:
        return [c.name for c in self.criteria]

    @property
    def categories(self) -> List[str]:
        seen: List[str] = []
        for c in self.criteria:
            if c.category not in seen:
                seen.append(c.category)
        return seen

    def by_category(self) -> Dict[str, List[Criterion]]:
        out: Dict[str, List[Criterion]] = {}
        for c in self.criteria:
            out.setdefault(c.category, []).append(c)
        return out

    def get(self, key: str) -> Criterion:
        for c in self.criteria:
            if c.id == key or c.name == key:
                return c
        raise KeyError(key)

    def entity_level(self) -> List[Criterion]:
        """Criteria that govern a single code entity (usable as a docstring rubric)."""
        return [c for c in self.criteria if c.applicable_to_entity]

    def audit_anchors(self) -> Dict[str, List[int]]:
        """Report which criteria are missing scoring anchors (reviewer item)."""
        return {c.name: c.missing_anchors for c in self.criteria if not c.has_full_anchors}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "version": self.version,
            "standards": self.standards,
            "description": self.description,
            "axis_role": self.axis_role,
            "criteria": [c.to_dict() for c in self.criteria],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriterionSet":
        payload = dict(data)
        payload["criteria"] = [Criterion.from_dict(c) for c in data.get("criteria", [])]
        return cls(**payload)
