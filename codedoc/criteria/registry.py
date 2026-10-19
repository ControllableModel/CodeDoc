"""Loading and validation of criterion sets.

Criterion sets are stored as JSON under ``codedoc/criteria/sets/`` so that a
reviewer can read, diff, and re-use them without executing any code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from codedoc.config import CRITERIA_SETS
from codedoc.criteria.schema import CriterionSet


def available() -> List[str]:
    """Names (without extension) of the criterion sets shipped with the repo."""
    if not CRITERIA_SETS.exists():
        return []
    return sorted(p.stem for p in CRITERIA_SETS.glob("*.json"))


def load(name: str) -> CriterionSet:
    """Load a criterion set by file stem, e.g. ``load('iso_26514')``."""
    path = Path(name)
    if not path.suffix:
        path = CRITERIA_SETS / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Criterion set not found: {path}. Available: {available()}"
        )
    with path.open(encoding="utf-8") as fh:
        return CriterionSet.from_dict(json.load(fh))


def load_all() -> Dict[str, CriterionSet]:
    """Load every shipped criterion set."""
    return {name: load(name) for name in available()}


def audit(set_name: str) -> Dict[str, object]:
    """Summarize gaps in a criterion set (anchors, applicability, provenance)."""
    cs = load(set_name)
    return {
        "id": cs.id,
        "axis_role": cs.axis_role,
        "n_criteria": len(cs),
        "n_categories": len(cs.categories),
        "categories": cs.categories,
        "n_entity_level": len(cs.entity_level()),
        "missing_anchors": cs.audit_anchors(),
        "missing_source": [c.name for c in cs if not c.source],
    }
