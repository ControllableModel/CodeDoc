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

#: Entity kinds a criterion can govern. ``None`` applicability means "all kinds".
KINDS = ("class", "method", "function")

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
    #: Entity kinds this criterion can judge. ``None`` means all of :data:`KINDS`.
    #:
    #: ``level`` alone was not enough. A free function cannot satisfy an
    #: inheritance/polymorphism requirement, yet the judge scored it 1.78 —
    #: reading "not mentioned" as "absent and therefore bad". That is a
    #: measurement artefact: it lowers every function's mean and makes per-kind
    #: comparisons meaningless. Non-applicable pairs are now excluded from both
    #: the question asked and the aggregation.
    applies_to_kinds: Optional[List[str]] = None
    #: Whether the dimension appears in the rubric table printed in the paper
    #: (Table 2: ISO 14 dimensions in 7 categories; Table 3: GitHub 12 dimensions in
    #: 5 categories). The criterion set itself is the *full* set the judge was asked
    #: about — the archived per-dimension scores contain all 26 ISO and all 18 GitHub
    #: dimensions, so the printed tables are a subset, not the measurement rubric.
    #: Both facts are recorded rather than reconciled silently; see
    #: results/analysis/criteria_paper_vs_artifact.md.
    in_paper_table: bool = True
    #: Category as printed in the paper's table. The printed tables regroup the
    #: dimensions (e.g. GitHub's "Further Reading" row does not exist in the full
    #: set), so reproducing the table needs the printed category, not ours.
    paper_category: str = ""
    #: Dimension label as printed in the paper when it differs from the judge's
    #: variable name. The variable names are frozen because the archived per-dimension
    #: scores are keyed by them; the paper's wording is recorded here instead of
    #: renaming and breaking comparability with the published data.
    paper_name: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if self.level not in APPLICABILITY:
            raise ValueError(f"level must be one of {APPLICABILITY}, got {self.level!r}")
        # normalize anchor keys to ints (JSON round-trip yields strings)
        self.anchors = {int(k): v for k, v in (self.anchors or {}).items()}
        if self.applicable_to_entity is None:
            self.applicable_to_entity = self.level == ENTITY
        if self.applies_to_kinds is not None:
            unknown = [k for k in self.applies_to_kinds if k not in KINDS]
            if unknown:
                raise ValueError(
                    f"applies_to_kinds must be drawn from {KINDS}, got {unknown}"
                )

    def applies_to(self, kind: str) -> bool:
        """Whether this criterion can be judged for an entity of ``kind``."""
        if self.applies_to_kinds is None:
            return True
        return kind in self.applies_to_kinds

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

    def table_label(self, criterion: "Criterion") -> tuple:
        """(category, dimension) as printed in the paper."""
        return (criterion.paper_category or criterion.category,
                criterion.paper_name or criterion.name)

    def in_paper_table(self) -> List[Criterion]:
        """Criteria printed in the paper's rubric table (a subset of this set)."""
        return [c for c in self.criteria if c.in_paper_table]

    def table_gap(self) -> Dict[str, List[str]]:
        """Dimensions measured but not printed in the paper's table, and vice versa."""
        return {
            "measured_not_in_table": [c.name for c in self.criteria if not c.in_paper_table],
            "in_table_not_measured": [],  # filled by the audit against archived scores
        }

    def for_kind(self, kind: str) -> List[Criterion]:
        """Entity-level criteria that can be judged for this entity kind."""
        return [c for c in self.criteria if c.applicable_to_entity and c.applies_to(kind)]

    def kind_coverage(self) -> Dict[str, List[str]]:
        """Which criteria apply to each entity kind — the applicability audit table."""
        return {kind: [c.name for c in self.for_kind(kind)] for kind in KINDS}

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
