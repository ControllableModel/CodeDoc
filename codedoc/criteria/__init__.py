"""Criteria library: standards-derived documentation criteria.

Public surface::

    from codedoc.criteria import registry
    registry.available()          # ['github_docs_style', 'iso_26514', 'practice_docstring']
    cs = registry.load('iso_26514')
    cs.entity_level()             # criteria usable as a docstring rubric
    cs.audit_anchors()            # criteria whose 1-5 anchors are incomplete
"""

from codedoc.criteria.schema import Criterion, CriterionSet, ENTITY, DOCUMENT_SET

__all__ = ["Criterion", "CriterionSet", "ENTITY", "DOCUMENT_SET", "registry", "extract"]
