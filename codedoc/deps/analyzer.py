"""Repository scanning: source parsing and dependency-graph construction.

Extracted from ``codedoc/cli.py`` so that dependency analysis has no dependency
on the LLM stack. Before this split, importing the analyzer pulled in ``openai``
(via the writer module), which meant the analysis stage could not run in an
interpreter where only the static-analysis dependencies were installed.

Responsibilities:

``Analyzer.scan``      walk ``*.py``, parse members with :mod:`ast`, build DOT
``Analyzer._run_pyan`` call pyan3 in-process with the compatibility patch applied
``Analyzer._parse``    collect top-level functions and class methods

Known limitations (see ``docs/PROVENANCE.md``):

* only top-level functions and class methods are collected — nested functions and
  module-level lambdas are not entities;
* a file that fails to parse contributes no members, and pyan may then reject the
  whole graph, in which case offending files are excluded iteratively and the
  exclusion is reported.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Optional


class Analyzer:
    """Parse a repository and produce its pyan3 DOT graph."""

    def __init__(self, target) -> None:
        self.target = Path(target)
        #: stem -> {"path": str, "members": {...}}
        self.files: Dict[str, Dict[str, object]] = {}

    # -- public API ---------------------------------------------------------
    def scan(self) -> Optional[str]:
        """Parse every ``*.py`` file and return the DOT graph (``None`` if empty)."""
        for f in self.target.rglob("*.py"):
            self.files[f.stem] = {"path": str(f), "members": self._parse(f)}
        if not self.files:
            return None
        return self._run_pyan()

    def measure(self) -> Dict[str, int]:
        """Entity counts without building the dependency graph."""
        for f in self.target.rglob("*.py"):
            self.files[f.stem] = {"path": str(f), "members": self._parse(f)}
        classes = methods = functions = 0
        for info in self.files.values():
            members = info["members"]  # type: ignore[index]
            classes += len(members["classes"])          # type: ignore[index]
            functions += len(members["functions"])      # type: ignore[index]
            for cls in members["classes"].values():     # type: ignore[index]
                methods += len(cls["methods"])
        return {
            "classes": classes,
            "methods": methods,
            "functions": functions,
            "documentable": methods + functions,
            "files": len(self.files),
        }

    # -- internals ----------------------------------------------------------
    def _run_pyan(self) -> str:
        paths = [f["path"] for f in self.files.values()]  # type: ignore[misc]
        # pyan runs in-process so the compatibility patch for pyan3's
        # visit_AnnAssign crash applies; a subprocess could not see it.
        # Failures are excluded iteratively: on a modern code base pyan rejects
        # more than a handful of files, so a single pass is not enough.
        from codedoc.deps.pyan_compat import preflight, run_pyan_dot

        keep: List[str] = list(paths)
        excluded: List[str] = []
        last_error: Optional[Exception] = None
        for _round in range(8):
            try:
                dot = run_pyan_dot(keep)
                if excluded:
                    print(
                        f"  pyan: excluded {len(excluded)} unparsable file(s) "
                        f"({len(keep)}/{len(paths)} analysed)"
                    )
                return dot
            except RuntimeError as exc:
                last_error = exc
                print(f"pyan error: {exc}")
                bad = set(preflight(keep, max_report=len(keep))) - set(excluded)
                if not bad:
                    break
                excluded.extend(sorted(bad))
                keep = [p for p in keep if p not in bad]
                print(f"  excluding {len(bad)} more file(s); {len(keep)} remain")
        raise RuntimeError(
            f"pyan cannot analyse this repository even after excluding "
            f"{len(excluded)} file(s); last error: {last_error}"
        )

    @staticmethod
    def _parse(fpath) -> Dict[str, object]:
        """Collect top-level functions and class methods from one file."""
        result: Dict[str, object] = {"classes": {}, "functions": []}
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError, OSError):
            return result

        fname = Path(fpath).stem
        functions = result["functions"]
        classes = result["classes"]
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({"key": f"{fname}__{node.name}", "name": node.name})  # type: ignore[union-attr]
            elif isinstance(node, ast.ClassDef):
                cls = {"key": f"{fname}__{node.name}", "name": node.name, "methods": []}
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        cls["methods"].append(
                            {
                                "key": f"{fname}__{node.name}__{item.name}",
                                "name": f"{node.name}.{item.name}",
                            }
                        )
                classes[node.name] = cls  # type: ignore[index]
        return result
