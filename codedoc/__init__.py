"""CodeDoc — standards-guided, dependency-aware code-level documentation generation.

Repository layout (six libraries)
---------------------------------
1. ``codedoc.criteria``  Criteria library   — standards-derived criterion sets (ISO, practice axis).
2. ``codedoc.deps``      Dependency library — language-agnostic entity/relation extraction.
3. ``codedoc.writer``    Writer library     — prompt assembly + LLM generation/refinement.
4. ``codedoc.judge``     Judge library      — criterion-aligned judging, aggregation, statistics.
5. ``targets/``          Target repositories (clone only; never committed).
6. ``outputs/``          Documentation store — generated artifacts (never committed).
"""

__version__ = "0.2.0"

__all__ = ["__version__"]
