"""Build the shipped criterion-set JSON files from a compact, auditable table.

Run from the repository root::

    python scripts/build_criteria_sets.py

Why a generator instead of hand-written JSON: the tables below are the single
source of truth, so a reviewer can diff *this* file rather than a wall of JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.config import CRITERIA_SETS, RESULTS  # noqa: E402
from codedoc.criteria.schema import Criterion, CriterionSet, DOCUMENT_SET, ENTITY  # noqa: E402

# ---------------------------------------------------------------------------
# Scores actually used by the archived judge prompt. Only the endpoints were
# ever defined; 2/3/4 remain gaps and are reported as such by the audit.
# ---------------------------------------------------------------------------
KNOWN_ANCHORS = {1: "Not Mention", 5: "Excellent"}

ISO_CATEGORIES = [
    ("Content Quality", ["Correctness", "Consistency", "Comprehensibility", "Conciseness", "Completeness"]),
    ("Information Structure", ["Modularity", "Structured by Function", "Navigability", "Metadata"]),
    ("Format & Presentation", ["Consistent Format", "Legibility", "Illustrations and Media",
                              "Representation of Interactive Elements"]),
    ("Accessibility", ["Multi-modal Support", "Device Independence", "Accessibility Features"]),
    ("Internationalization & Localization", ["Cultural Neutrality", "Translation-Friendly", "Space Consideration"]),
    ("Usability & User Experience", ["User-Centered Design", "Testing and Feedback", "Search and Indexing"]),
    ("Safety & Compliance", ["Safety Information", "Legal and Copyright"]),
    ("Maintenance & Updates", ["Version Control", "Change Log"]),
]

#: Requirements that govern a *document set* rather than a single code entity.
#: Mixing these into a docstring rubric is why several dimensions never vary.
ISO_DOCSET = {
    "Illustrations and Media", "Representation of Interactive Elements",
    "Multi-modal Support", "Device Independence", "Accessibility Features",
    "Space Consideration", "Testing and Feedback", "Search and Indexing",
    "Safety Information", "Legal and Copyright", "Version Control", "Change Log",
}

ISO_DEFINITIONS = {
    "Correctness": "The documentation states facts about the entity that match its implementation.",
    "Consistency": "Terminology and claims do not contradict the rest of the documentation.",
    "Comprehensibility": "A reader familiar with the project can understand the description.",
    "Conciseness": "The description avoids redundancy and unnecessary detail.",
    "Completeness": "Core functionality, inputs, outputs, and preconditions are covered.",
    "Modularity": "Information is organised into coherent, self-contained units.",
    "Structured by Function": "Content is grouped by the function it serves rather than arbitrarily.",
    "Navigability": "A reader can locate the relevant information about the entity.",
    "Metadata": "Identifying information (name, path, version, audience) is recorded.",
    "Consistent Format": "Formatting follows a uniform convention across artifacts.",
    "Legibility": "The text is typographically readable (spacing, structure, length).",
    "Illustrations and Media": "Illustrative material is provided where it aids understanding.",
    "Representation of Interactive Elements": "Interactive elements of the software are represented in the documentation.",
    "Multi-modal Support": "Content is available in more than one modality.",
    "Device Independence": "Content is not bound to a specific device or display.",
    "Accessibility Features": "Content meets accessibility requirements.",
    "Cultural Neutrality": "Examples and wording avoid culture-specific assumptions.",
    "Translation-Friendly": "Wording supports later translation.",
    "Space Consideration": "Layout reserves room for text expansion in other languages.",
    "User-Centered Design": "Content addresses the reader's task in the software.",
    "Testing and Feedback": "The documentation set is tested and user feedback is collected.",
    "Search and Indexing": "Content is discoverable through search and indexing.",
    "Safety Information": "Hazards and safety-relevant behaviour are documented.",
    "Legal and Copyright": "Legal notices and licensing information are present.",
    "Version Control": "Documentation versions are tracked alongside the software.",
    "Change Log": "Changes to the documentation are recorded.",
}

GITHUB_CATEGORIES = [
    ("Content Quality", ["Content Type Consistency", "Reuse Instead of Copying"]),
    ("Structure & Organization", ["Balanced Hierarchy", "Content Order", "Category Title Naming"]),
    ("Styling & Formatting", ["Title Standards", "Introduction Standards",
                              "Permission Declaration Standards", "Product Label Standards"]),
    ("Content Types & Completeness", ["Process Content Standards", "Next Steps Standards",
                                      "Further Reading Standards", "Prerequisites Standards"]),
    ("Article Content Families", ["Reference Content", "Conceptual Content Guidelines",
                                  "Error Reference Content Guidelines", "Tutorial Content Guidelines",
                                  "Getting Started Content Guidelines"]),
]

PRACTICE_CATEGORIES = [
    ("Signature & Interface", ["Signature Conformance", "Parameter Coverage", "Return Documentation",
                              "Exception Documentation"]),
    ("Behaviour & Contract", ["Side-effect & State Documentation", "Inheritance/Polymorphism Contract",
                              "Dependency Context"]),
    ("Usability", ["Usage Example Validity"]),
    ("Convention Adherence", ["Language Convention Adherence"]),
]

PRACTICE_DEFINITIONS = {
    "Signature Conformance": "The described name, parameter order, and types match the actual signature.",
    "Parameter Coverage": "Every parameter is described, including defaults and constraints.",
    "Return Documentation": "Return values are described, including empty/None/void cases.",
    "Exception Documentation": "Thrown exceptions or error codes are described.",
    "Side-effect & State Documentation": "Side effects, state mutation, and I/O are described.",
    "Inheritance/Polymorphism Contract": "For classes and overridden methods, the inheritance chain, override obligations, and polymorphic contract are described.",
    "Dependency Context": "Relevant callers, callees, or collaborators are described.",
    "Usage Example Validity": "Any example is runnable and consistent with the signature.",
    "Language Convention Adherence": "The artifact follows the target language's docstring convention (Google Style/PEP 257, JSDoc/TSDoc, Javadoc).",
}


def _load_recovered() -> dict:
    path = RESULTS / "judge_criteria_recovered.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if isinstance(data, dict):
        return {str(k): str(v) for k, v in data.items()}
    if isinstance(data, list):
        out = {}
        for item in data:
            if isinstance(item, dict) and "name" in item:
                out[str(item["name"])] = str(item.get("definition", ""))
        return out
    return {}


def _build(set_id, title, version, standards, description, axis_role, categories,
           definitions, docset=(), anchors=None, note=""):
    recovered = _load_recovered()
    criteria = []
    n = 0
    for category, names in categories:
        for name in names:
            n += 1
            definition = recovered.get(name) or definitions.get(name, "")
            criteria.append(
                Criterion(
                    id=f"q{n}",
                    name=name,
                    category=category,
                    definition=definition,
                    level=DOCUMENT_SET if name in docset else ENTITY,
                    source="",
                    anchors=dict(anchors or {}),
                    note=note if name in docset else "",
                )
            )
    return CriterionSet(
        id=set_id, title=title, version=version, standards=list(standards),
        description=description, axis_role=axis_role, criteria=criteria,
    )


def main() -> int:
    CRITERIA_SETS.mkdir(parents=True, exist_ok=True)

    iso = _build(
        "iso_26514",
        "ISO/IEC/IEEE 26514 documentation requirements (code-level projection)",
        "2018",
        ["ISO/IEC/IEEE 26514:2018"],
        "Criterion set used as the primary evaluation axis. Requirements that govern a "
        "document set are marked level=document-set so they can be excluded from the "
        "entity-level rubric; see docs/CRITERIA_ISO.md.",
        "primary",
        ISO_CATEGORIES,
        ISO_DEFINITIONS,
        docset=ISO_DOCSET,
        anchors=KNOWN_ANCHORS,
        note="Governs a document set, not a single code entity; excluded from the entity-level rubric.",
    )

    gh = _build(
        "github_docs_style",
        "GitHub documentation style guide (document-set level)",
        "2024",
        ["GitHub Docs style guide"],
        "Secondary axis, retained for continuity with the published results. It is a "
        "document-set specification, not a general standard for code-level artifacts, "
        "so it is never used as the primary rubric.",
        "secondary",
        GITHUB_CATEGORIES,
        {},
        docset={n for _, ns in GITHUB_CATEGORIES for n in ns},
        note="Document-set level specification; not a normative standard for docstrings.",
    )

    practice = _build(
        "practice_docstring",
        "Entity-level docstring conventions as used in IDE/assistant workflows",
        "draft",
        ["Google Python Style Guide (docstrings)", "PEP 257",
         "JSDoc", "TSDoc", "Oracle Javadoc"],
        "New practice axis. Replaces the vendor document-set style guide with "
        "entity-level conventions that assistant tools follow per language. "
        "Anchors are intentionally left incomplete pending calibration (S5).",
        "primary",
        PRACTICE_CATEGORIES,
        PRACTICE_DEFINITIONS,
    )

    for cs in (iso, gh, practice):
        path = CRITERIA_SETS / f"{cs.id}.json"
        path.write_text(json.dumps(cs.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        miss = cs.audit_anchors()
        print(f"{path.name:<28} {len(cs):>3} criteria  {len(cs.categories)} categories  "
              f"entity-level={len(cs.entity_level()):>2}  missing-anchors={len(miss)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
