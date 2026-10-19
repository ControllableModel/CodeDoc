"""Registry of per-language extractors.

A language may have **several** backends (e.g. Python has a working pyan3
extractor for call relations and a language-server extractor for class
hierarchy).  The registry therefore keys on ``(language, backend)`` and the
default backend is always an ``implemented`` one — a skeleton must never shadow a
working extractor, which is exactly the kind of silent degradation this refactor
exists to prevent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Type

from codedoc.deps.languages.base import Extractor

#: language -> backend -> extractor class (insertion order preserved)
_REGISTRY: Dict[str, Dict[str, Type[Extractor]]] = {}


def register(cls: Type[Extractor]) -> Type[Extractor]:
    """Register an extractor class (usable as a decorator)."""
    if not cls.language:
        raise ValueError(f"{cls.__name__} must declare a language")
    if not cls.backend:
        raise ValueError(f"{cls.__name__} must declare a backend")
    _REGISTRY.setdefault(cls.language, {})[cls.backend] = cls
    return cls


def _registry() -> Dict[str, Dict[str, Type[Extractor]]]:
    """Populate the registry lazily to avoid import cycles."""
    if _REGISTRY:
        return _REGISTRY
    from codedoc.deps.languages import (  # noqa: F401  (import for side effects)
        python_pyan,
        python_lsp,
        java_lsp,
        ts_lsp,
    )
    return _REGISTRY


def available() -> List[str]:
    return sorted(_registry())


def backends(language: str) -> List[str]:
    return list(_registry().get(language.strip().lower(), {}))


def _default_backend(language: str) -> Optional[str]:
    """First implemented backend, falling back to the first registered one."""
    table = _registry().get(language, {})
    for name, cls in table.items():
        if cls.status == "implemented":
            return name
    return next(iter(table), None)


def get(language: str, backend: Optional[str] = None) -> Extractor:
    """Instantiate an extractor.

    With no ``backend`` the default is the first implemented backend, so callers
    never accidentally receive a skeleton.
    """
    key = language.strip().lower()
    table = _registry().get(key)
    if not table:
        raise KeyError(
            f"No extractor for language {language!r}. Available: {sorted(_registry())}"
        )
    name = backend or _default_backend(key)
    if name not in table:
        raise KeyError(
            f"No backend {backend!r} for {key!r}. Available: {list(table)}"
        )
    return table[name]()


def for_suffix(suffix: str) -> Optional[str]:
    """Language that handles a file suffix, if any."""
    s = suffix if suffix.startswith(".") else f".{suffix}"
    for language, table in _registry().items():
        if any(s in cls.suffixes for cls in table.values()):
            return language
    return None


def detect(repo_root: str) -> List[str]:
    """Languages present in a repository, ordered by file count (desc)."""
    counts: Dict[str, int] = {}
    root = Path(repo_root)
    if not root.exists():
        return []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        lang = for_suffix(path.suffix)
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    return [lang for lang, _ in sorted(counts.items(), key=lambda kv: -kv[1])]


def describe() -> List[Dict[str, object]]:
    """Capability matrix used in docs and in the paper's setup table."""
    rows: List[Dict[str, object]] = []
    for language in sorted(_registry()):
        for backend, cls in _registry()[language].items():
            inst = cls()
            rows.append(
                {
                    "language": language,
                    "backend": backend,
                    "status": inst.status,
                    "suffixes": list(inst.suffixes),
                    "supported_relations": list(inst.supported_relations),
                    "missing_relations": inst.missing_relations(),
                }
            )
    return rows


__all__ = [
    "Extractor", "register", "available", "backends", "get", "for_suffix", "detect", "describe",
]
