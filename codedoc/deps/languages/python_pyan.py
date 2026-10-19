"""Python dependency extractor backed by pyan3 (the backend used in the paper).

Capabilities and limits, stated honestly because reviewers asked exactly this:

* The DOT graph pyan3 emits carries **call edges between functions/methods**.
* A class node therefore has inbound references (who uses/instantiates it in the
  graph pyan3 could resolve) but **no outbound call edges** — classes do not
  call anything.  Class hierarchy (`inherits` / `subclassed_by`) and method
  override pairs are *not* recovered here.
* For those relations, register :mod:`codedoc.deps.languages.python_lsp`, which
  queries a language server instead.
"""

from __future__ import annotations

from typing import Dict, List

from codedoc.deps.languages import register
from codedoc.deps.languages.base import Extractor
from codedoc.deps.schema import (
    DependencyContext,
    Entity,
    EntityKind,
    Relation,
    RelationKind,
)


@register
class PythonPyanExtractor(Extractor):
    language = "python"
    suffixes = (".py",)
    backend = "pyan3 + ast"
    supported_relations = (RelationKind.CALLS, RelationKind.CALLED_BY)

    def __init__(self) -> None:
        self._nav = None
        self._files: Dict[str, Dict[str, object]] = {}

    # -- helpers ------------------------------------------------------------
    def _scan(self, repo_root: str) -> None:
        """Run the existing analyser to obtain a Navigator (lazy import)."""
        if self._nav is not None:
            return
        from codedoc.deps.analyzer import Analyzer  # no LLM dependency

        analyzer = Analyzer(repo_root)
        dot = analyzer.scan()
        file_map = {k: v["path"] for k, v in analyzer.files.items()}
        self._files = analyzer.files
        from codedoc.deps.dot import analyze

        self._nav = analyze(dot, repo_root, file_map)

    @staticmethod
    def _entity_kind(fname: str, is_method: bool) -> str:
        return EntityKind.METHOD if is_method else EntityKind.FUNCTION

    def _context(self, display: str, nid: str, fpath: str, kind: str) -> DependencyContext:
        from codedoc.deps.dot import get_dep

        dep = get_dep(self._nav, display, nid, fpath)
        ctx = DependencyContext(
            entity=Entity(name=display, kind=kind, path=fpath, qualified_name=nid),
            source=getattr(dep, "code", "") or "",
        )
        for target in getattr(dep, "uses", []) or []:
            ctx.add(Relation(kind=RelationKind.CALLS, target=str(target)))
        for target in getattr(dep, "used_by", []) or []:
            ctx.add(Relation(kind=RelationKind.CALLED_BY, target=str(target)))
        return ctx

    # -- Extractor interface ------------------------------------------------
    def measure(self, repo_root: str) -> Dict[str, int]:
        self._scan(repo_root)
        n_cls = n_method = n_func = 0
        for info in self._files.values():
            members = info.get("members", {})
            for cls_info in members.get("classes", {}).values():
                n_cls += 1
                n_method += len(cls_info.get("methods", []))
            n_func += len(members.get("functions", []))
        return {
            "classes": n_cls,
            "methods": n_method,
            "functions": n_func,
            "documentable": n_method + n_func,
        }

    def extract(self, repo_root: str) -> List[DependencyContext]:
        self._scan(repo_root)
        out: List[DependencyContext] = []
        for fname, info in self._files.items():
            fpath = str(info.get("path", ""))
            members = info.get("members", {})
            for cls_name, cls_info in members.get("classes", {}).items():
                for method in cls_info.get("methods", []):
                    out.append(
                        self._context(
                            str(method.get("display_name") or method.get("name")),
                            str(method.get("key")),
                            fpath,
                            EntityKind.METHOD,
                        )
                    )
            for func in members.get("functions", []):
                out.append(
                    self._context(
                        str(func.get("display_name") or func.get("name")),
                        str(func.get("key")),
                        fpath,
                        EntityKind.FUNCTION,
                    )
                )
        return out
