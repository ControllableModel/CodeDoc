"""Phase (a): criteria extraction from standards documents.

Reviewers objected that the original procedure pasted a whole standard into a
model and accepted free-text output, so the result could not be audited or
reproduced.  This module replaces it with a *schema-constrained* extraction and
adds the stability check that was missing.

Planned capabilities (S5 in the experiment sequence):

``extract``
    Ask the model for strictly-typed JSON matching :data:`CRITERION_SCHEMA`.
``stability``
    Run the extraction N times and report set-level agreement (Jaccard over
    criterion names) plus per-item alignment.
``diff``
    Compare two extractions so drift between runs is visible rather than
    silently averaged away.

The LLM transport is injected so this module stays testable without a key.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence

from codedoc.criteria.schema import Criterion, CriterionSet, DOCUMENT_SET, ENTITY

#: JSON Schema handed to the model.  Kept to the subset of keywords that
#: structured-output implementations reliably support.
CRITERION_SCHEMA: Dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["criteria"],
    "properties": {
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "category", "definition", "level", "source_clause"],
                "properties": {
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "definition": {"type": "string"},
                    "level": {"type": "string", "enum": [ENTITY, DOCUMENT_SET]},
                    "source_clause": {"type": "string"},
                    "anchors": {
                        "type": "object",
                        "additionalProperties": True,
                    },
                },
            },
        }
    },
}

EXTRACTION_INSTRUCTION = """\
You extract documentation quality criteria from a standards document.

Rules:
1. Emit one criterion per *assessable requirement* stated in the document.
2. `level` is "entity" when the requirement governs a single documentation
   artifact for one code entity (a docstring or comment block), and
   "document-set" when it governs a collection of documents (chapters, pages,
   articles, navigation, illustrations, publishing workflow).
3. `source_clause` must quote or cite the clause the criterion comes from.
4. Do not invent requirements that are not present in the document.
Return JSON matching the provided schema and nothing else."""


@dataclass
class ExtractionResult:
    """One extraction run."""

    criteria: List[Criterion]
    raw: str = ""

    @property
    def names(self) -> List[str]:
        return [c.name for c in self.criteria]


def _coerce_set(result: ExtractionResult, set_id: str, title: str) -> CriterionSet:
    return CriterionSet(
        id=set_id,
        title=title,
        version="extracted",
        description="Extracted by schema-constrained prompting.",
        axis_role="primary",
        criteria=result.criteria,
    )


def parse_response(raw: str) -> ExtractionResult:
    """Parse a JSON response into criteria, rejecting non-conforming payloads."""
    payload = json.loads(raw)
    items = payload.get("criteria", [])
    criteria: List[Criterion] = []
    for i, item in enumerate(items, start=1):
        criteria.append(
            Criterion(
                id=f"q{i}",
                name=item["name"],
                category=item.get("category", "Uncategorized"),
                definition=item.get("definition", ""),
                level=item.get("level", ENTITY),
                source=item.get("source_clause", ""),
                anchors=item.get("anchors", {}) or {},
            )
        )
    return ExtractionResult(criteria=criteria, raw=raw)


def extract(
    document: str,
    query: Callable[[str, str], str],
    set_id: str = "extracted",
    title: str = "Extracted criterion set",
) -> CriterionSet:
    """Run one schema-constrained extraction.

    ``query`` receives ``(instruction, document)`` and must return JSON text.
    """
    raw = query(EXTRACTION_INSTRUCTION, document)
    return _coerce_set(parse_response(raw), set_id, title)


def jaccard(a: Sequence[str], b: Sequence[str]) -> float:
    """Set-level agreement between two extractions, case-insensitive."""
    sa = {x.strip().lower() for x in a}
    sb = {x.strip().lower() for x in b}
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def stability(runs: Sequence[CriterionSet]) -> Dict[str, object]:
    """Report agreement across repeated extraction runs.

    This is the evidence the review asked for: re-running the extraction must
    reproduce substantially the same criterion set.
    """
    if len(runs) < 2:
        raise ValueError("Stability requires at least two runs.")
    names = [run.names for run in runs]
    pairwise: List[float] = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            pairwise.append(jaccard(names[i], names[j]))
    union = {n.strip().lower() for ns in names for n in ns}
    always = {n for n in union if all(n in {x.strip().lower() for x in ns} for ns in names)}
    return {
        "n_runs": len(runs),
        "mean_pairwise_jaccard": sum(pairwise) / len(pairwise),
        "min_pairwise_jaccard": min(pairwise),
        "n_union": len(union),
        "n_stable": len(always),
        "stable_ratio": len(always) / len(union) if union else 1.0,
        "per_run_sizes": [len(ns) for ns in names],
    }


def diff(a: CriterionSet, b: CriterionSet) -> Dict[str, List[str]]:
    """Criteria present in only one of the two sets."""
    na = {c.name.strip().lower(): c.name for c in a}
    nb = {c.name.strip().lower(): c.name for c in b}
    return {
        "only_in_first": [na[k] for k in na.keys() - nb.keys()],
        "only_in_second": [nb[k] for k in nb.keys() - na.keys()],
        "shared": [na[k] for k in na.keys() & nb.keys()],
    }
