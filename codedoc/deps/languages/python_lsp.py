"""Python class/hierarchy relations via a language server.

Complements :mod:`codedoc.deps.languages.python_pyan`, which only sees call
edges.  Recommended server: ``pyright-langserver --stdio`` (or
``jedi-language-server``), installed through npm/pip respectively.
"""

from __future__ import annotations

from codedoc.deps.languages import register
from codedoc.deps.languages.lsp import LspExtractor


@register
class PythonLspExtractor(LspExtractor):
    language = "python"
    language_id = "python"
    suffixes = (".py",)
    server_command = ("pyright-langserver", "--stdio")

    notes = (
        "Adds inherits / subclassed_by / instantiated_at / overrides for classes "
        "and methods, which pyan3 cannot provide."
    )
