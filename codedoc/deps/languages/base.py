"""Interface every per-language dependency extractor must satisfy.

Adding a language must mean adding *one* file that fills this interface; the
relation schema, prompt assembly and judging stay untouched.  That constraint is
what makes the multi-language study meaningful rather than a rewrite per
language.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Sequence

from codedoc.deps.schema import DependencyContext, RelationKind


class Extractor(ABC):
    """Produces dependency contexts for one programming language."""

    #: Language identifier, e.g. ``"python"``.
    language: str = ""
    #: Source file suffixes handled by this extractor, e.g. ``(".py",)``.
    suffixes: Sequence[str] = ()
    #: Human-readable name of the underlying analysis backend.
    backend: str = ""
    #: ``"implemented"`` when the backend actually returns relations,
    #: ``"skeleton"`` when the interface exists but the requests are not wired
    #: up yet. Reported verbatim so a capability matrix cannot overclaim.
    status: str = "implemented"
    #: Relation kinds this extractor can actually produce.  Declared explicitly
    #: so the paper never claims a relation the tooling does not deliver.
    supported_relations: Sequence[str] = ()

    @abstractmethod
    def measure(self, repo_root: str) -> Dict[str, int]:
        """Return entity/relation counts without building full contexts.

        Used by the coverage report (how much of the repository the extractor can
        actually resolve), so a language cannot be claimed working on the basis
        of a single example.
        """

    @abstractmethod
    def extract(self, repo_root: str) -> List[DependencyContext]:
        """Return one :class:`DependencyContext` per documentable entity."""

    def supports(self, relation_kind: str) -> bool:
        return relation_kind in self.supported_relations

    def missing_relations(self) -> List[str]:
        """Relation kinds defined in the schema but not produced by this backend."""
        return [rk for rk in RelationKind.ALL if rk not in self.supported_relations]

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<{type(self).__name__} language={self.language!r} backend={self.backend!r}>"
