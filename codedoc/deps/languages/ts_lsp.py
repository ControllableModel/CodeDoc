"""TypeScript / JavaScript relations via ``tsserver``.

Uses ``typescript-language-server --stdio`` (an npm package) on top of the
TypeScript compiler's own language service, so class hierarchies and interface
implementations resolve without a build.
"""

from __future__ import annotations

from codedoc.deps.languages import register
from codedoc.deps.languages.lsp import LspExtractor


@register
class TypeScriptLspExtractor(LspExtractor):
    language = "typescript"
    language_id = "typescript"
    suffixes = (".ts", ".tsx", ".mts", ".cts")

    server_command = ("typescript-language-server", "--stdio")

    notes = (
        "Install with `npm i -g typescript typescript-language-server`. "
        "Interfaces plus `implements` clauses give polymorphism relations "
        "comparable to Java's."
    )
