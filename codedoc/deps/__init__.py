"""Dependency library: language-agnostic extraction of code-entity relations.

Layout
------
``schema``      :class:`Entity` / :class:`Relation` / :class:`DependencyContext`
``graph``       helpers for closure and lookup over relation records
``relations_index``  lookup seam between extraction and generation
``export_dot``       optional DOT export for figures and manual audit
``analyzer``         legacy pyan3 driver (kept only for the pyan comparison)
``languages``   per-language extractors behind one interface

Why language-agnostic: the paper's contribution is not tied to Python.  A
language only contributes an *extractor*; everything downstream (relation
schema, prompt assembly, judging) is shared.  This is what makes the
multi-language generalisation study possible.
"""

from codedoc.deps.schema import (
    DependencyContext,
    Entity,
    EntityKind,
    Relation,
    RelationKind,
)

__all__ = [
    "Entity",
    "EntityKind",
    "Relation",
    "RelationKind",
    "DependencyContext",
]
