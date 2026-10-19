"""Shared LSP-backed extractor.

Language servers expose exactly the relations pyan3 cannot give us:

======================  ==============================================  ==================
Relation                LSP request                                     Server support
======================  ==============================================  ==================
``inherits``            ``textDocument/prepareTypeHierarchy`` (supertypes)  jdtls, tsserver, pyright
``subclassed_by``       ``textDocument/prepareTypeHierarchy`` (subtypes)    jdtls, tsserver, pyright
``instantiated_at``     ``textDocument/references`` on the class symbol      all
``overrides``           ``textDocument/typeHierarchy/supertypes`` + match    jdtls, tsserver
``dispatch_candidates`` subclasses + same-named member                       jdtls, tsserver
``calls``/``called_by`` ``textDocument/prepareCallHierarchy``                jdtls, tsserver, clangd
======================  ==============================================  ==================

Status: **skeleton**.  The per-language subclasses only configure a server;
the request sequence above still has to be implemented and validated against
the acceptance thresholds in ``EXPERIMENT_SEQUENCE.md`` (S1).  Nothing here
silently falls back to function-only analysis: an unimplemented path raises.
"""

from __future__ import annotations

from typing import Dict, List

from codedoc.deps.languages.base import Extractor
from codedoc.deps.schema import DependencyContext, RelationKind

_INSTALL_HINT = (
    "Install a language server client first, e.g. `pip install multilspy` "
    "(each language also needs its own server binary, see docs/DEPENDENCIES.md)."
)


def ensure_client() -> object:
    """Return a language-server client, or explain precisely what is missing."""
    try:
        import multilspy  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(f"multilspy is unavailable ({exc}). {_INSTALL_HINT}") from exc
    return multilspy


class LspExtractor(Extractor):
    """Base class for language-server-backed extractors."""

    language = ""
    language_id = ""
    backend = "LSP"
    server_command: tuple = ()

    status = "skeleton"
    supported_relations = (
        RelationKind.CALLS,
        RelationKind.CALLED_BY,
        RelationKind.INHERITS,
        RelationKind.SUBCLASSED_BY,
        RelationKind.INSTANTIATED_AT,
        RelationKind.OVERRIDES,
        RelationKind.OVERRIDDEN_BY,
        RelationKind.DISPATCH_CANDIDATES,
    )

    def __init__(self) -> None:
        self.backend = f"LSP ({self.language_id or self.language})"

    # -- to implement -------------------------------------------------------
    def measure(self, repo_root: str) -> Dict[str, int]:
        raise NotImplementedError(
            f"{type(self).__name__}.measure is not implemented yet. "
            "Required: start the language server, list document symbols, and count "
            "classes / methods / functions resolved."
        )

    def extract(self, repo_root: str) -> List[DependencyContext]:
        raise NotImplementedError(
            f"{type(self).__name__}.extract is not implemented yet. "
            "Required: for every entity emit relations from prepareTypeHierarchy, "
            "prepareCallHierarchy and references (see module docstring)."
        )
