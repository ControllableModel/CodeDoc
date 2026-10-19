"""Java class hierarchy and call relations via ``jdtls``.

Java is the strongest case for the hierarchy-aware pipeline: interfaces,
abstract classes and overrides are first-class, so ``inherits``,
``subclassed_by`` and ``overrides`` are reliably resolvable.
"""

from __future__ import annotations

from codedoc.deps.languages import register
from codedoc.deps.languages.lsp import LspExtractor


@register
class JavaLspExtractor(LspExtractor):
    language = "java"
    language_id = "java"
    suffixes = (".java",)
    server_command = ("jdtls",)

    notes = (
        "Requires a JDK on PATH. Interfaces and abstract classes make this the "
        "best language to demonstrate polymorphism-aware documentation."
    )
