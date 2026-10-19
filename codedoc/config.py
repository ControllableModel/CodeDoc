"""Central path and runtime configuration for CodeDoc.

All filesystem locations live here so that no module hard-codes a path.
"""

from pathlib import Path

# --- package roots -----------------------------------------------------------
PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent

# --- libraries ---------------------------------------------------------------
TEMPLATES = PACKAGE_ROOT / "writer" / "templates"
CRITERIA_SETS = PACKAGE_ROOT / "criteria" / "sets"

# --- data locations ----------------------------------------------------------
#: Target repositories under analysis (third-party code, never committed).
TARGETS = REPO_ROOT / "targets"
#: Generated documentation artifacts (never committed).
OUTPUTS = REPO_ROOT / "outputs"
#: Archived evaluation evidence (committed, small).
RESULTS = REPO_ROOT / "results"

DEFAULT_PROMPT_TEMPLATE = "iso_26514.txt"


def default_template() -> str:
    """Absolute path of the default generation template (ISO/IEC/IEEE 26514)."""
    return str(TEMPLATES / DEFAULT_PROMPT_TEMPLATE)


def resolve_target(path: str) -> Path:
    """Resolve a target repository path.

    Accepts an absolute path, a path relative to the current working directory,
    or a bare repository name that exists under ``targets/``.
    """
    p = Path(path).expanduser()
    if p.is_absolute():
        return p.resolve()
    if p.exists():
        return p.resolve()
    candidate = TARGETS / path
    if candidate.exists():
        return candidate.resolve()
    return p.resolve()
