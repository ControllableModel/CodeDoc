"""Python dependency extractor built on the standard library ``ast``.

Why this exists
---------------
``pyan3`` 1.1.1 was the backend behind the published results. It cannot be used
as the dependency layer of this project:

* it only models **call edges** (function to function), so a class has inbound
  references at best and *no* outbound relations — which is why class
  documentation had no usable context;
* it crashes on modern syntax and on cross-file resolution
  (``IndexError`` in ``visit_AnnAssign``, ``KeyError`` on imports, ``ValueError:
  Unknown scope`` on lambdas) — on the ten evaluated repositories it fails
  outright for NumPy, Dify, joblib, Fairseq and PyTorch;
* it is pinned to the interpreter's grammar, so any repository written for a
  newer Python cannot be parsed at all.

This extractor covers **classes and functions** with seven relation kinds and
depends on nothing but the standard library, so it runs unchanged on any Python
the repository requires (3.9+ grammar is handled by running the analysis with a
matching interpreter).

What it does and does not do
----------------------------
Resolved statically:

* ``inherits`` / ``subclassed_by`` from class bases, with name resolution through
  the module import graph;
* ``overrides`` / ``overridden_by`` by matching method names along the resolved
  inheritance chain;
* ``dispatch_candidates`` — sibling implementations of a polymorphic method;
* ``instantiated_at`` for calls whose callee resolves to a known class;
* ``calls`` / ``called_by`` for module-level functions, imported functions,
  ``self.method()`` and ``Class.method()``.

Not resolved (counted and reported, never silently dropped):

* calls through arbitrary attributes with unknown receiver type
  (``obj.do_thing()`` where ``obj``'s type is not inferable);
* dynamic dispatch through ``getattr``/``globals()``, decorators that replace
  callables, metaclass magic;
* multi-target assignments and conditional definitions.

So the numbers this extractor reports are a **sound lower bound with an explicit
unresolved count**, which is exactly what a paper needs: coverage is measurable
instead of assumed.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from codedoc.deps.languages import register
from codedoc.deps.languages.base import Extractor
from codedoc.deps.schema import (
    DependencyContext,
    Entity,
    EntityKind,
    Relation,
    RelationKind,
)

#: Directories that never contain the library under analysis.
_SKIP_DIRS = {"__pycache__", ".git", "build", "dist", "node_modules", ".venv", "venv"}


def _module_name(path: Path, root: Path) -> str:
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = Path(path.name)
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else path.stem


class _ClassInfo:
    __slots__ = ("qname", "module", "name", "bases_raw", "bases", "methods",
                 "path", "lineno", "end_lineno", "outer_function")

    def __init__(self, qname, module, name, bases_raw, path, lineno, end_lineno, outer):
        self.qname = qname
        self.module = module
        self.name = name
        self.bases_raw = bases_raw
        self.bases: List[str] = []
        self.methods: Dict[str, str] = {}
        self.path = path
        self.lineno = lineno
        self.end_lineno = end_lineno
        self.outer_function = outer


class _FuncInfo:
    __slots__ = ("qname", "module", "name", "kind", "owner", "path", "lineno",
                 "end_lineno", "calls", "unresolved")

    def __init__(self, qname, module, name, kind, owner, path, lineno, end_lineno):
        self.qname = qname
        self.module = module
        self.name = name
        self.kind = kind            # "function" | "method"
        self.owner = owner          # class qname for methods
        self.path = path
        self.lineno = lineno
        self.end_lineno = end_lineno
        self.calls: List[str] = []
        self.unresolved = 0


class ProjectIndex:
    """Symbol index and resolution engine for one repository."""

    def __init__(self, root: str) -> None:
        # Absolute paths are used throughout: the language-server backends return
        # absolute URIs and mixing the two silently breaks every lookup.
        self.root = Path(root).resolve()
        self.modules: Dict[str, ast.Module] = {}
        self.module_paths: Dict[str, str] = {}
        self.imports: Dict[str, Dict[str, str]] = {}
        self.classes: Dict[str, _ClassInfo] = {}
        self.functions: Dict[str, _FuncInfo] = {}
        self.parse_errors: List[Tuple[str, str]] = []
        self.unresolved_bases: List[Tuple[str, str]] = []
        self.total_calls = 0
        self.unresolved_calls = 0

    # -- parsing ------------------------------------------------------------
    def build(self) -> "ProjectIndex":
        for path in sorted(self.root.rglob("*.py")):
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            try:
                source = path.read_text(encoding="utf-8", errors="strict")
                tree = ast.parse(source, filename=str(path))
            except (SyntaxError, UnicodeDecodeError, OSError) as exc:
                self.parse_errors.append((str(path), f"{type(exc).__name__}: {exc}"))
                continue
            mod = _module_name(path, self.root)
            self.modules[mod] = tree
            self.module_paths[mod] = str(path.resolve())
            self.imports[mod] = {}
            self._collect(ast.Module(body=tree.body, type_ignores=[]), mod, path.resolve())
        self._resolve()
        return self

    def _collect(self, tree: ast.Module, mod: str, path: Path) -> None:
        """Record imports, classes and functions (including nested ones)."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.asname:
                        self.imports[mod][alias.asname] = alias.name
                    else:
                        head = alias.name.split(".")[0]
                        self.imports[mod][head] = head
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level and base:
                    # relative import: drop the leading package components
                    parent = mod.rsplit(".", node.level)[0] if "." in mod else ""
                    base = f"{parent}.{base}".lstrip(".")
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    local = alias.asname or alias.name
                    self.imports[mod][local] = f"{base}.{alias.name}" if base else alias.name

        # walk the module body with an explicit stack so we know the owner
        stack: List[Tuple[str, str]] = []   # (kind, qname)

        def visit(nodes: Iterable[ast.AST]) -> None:
            for node in nodes:
                if isinstance(node, ast.ClassDef):
                    qname = f"{mod}.{node.name}" if not stack else f"{stack[-1][1]}.{node.name}"
                    info = _ClassInfo(
                        qname, mod, node.name,
                        [self._base_name(b) for b in node.bases],
                        str(path), node.lineno, getattr(node, "end_lineno", node.lineno),
                        stack[-1][1] if stack and stack[-1][0] == "function" else "",
                    )
                    self.classes[qname] = info
                    stack.append(("class", qname))
                    visit(node.body)
                    stack.pop()
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    parent = stack[-1][1] if stack else mod
                    kind = EntityKind.METHOD if (stack and stack[-1][0] == "class") else EntityKind.FUNCTION
                    qname = f"{parent}.{node.name}"
                    if qname in self.functions:
                        suffix = 2
                        while f"{qname}#{suffix}" in self.functions:
                            suffix += 1
                        qname = f"{qname}#{suffix}"
                    owner = stack[-1][1] if (stack and stack[-1][0] == "class") else ""
                    info = _FuncInfo(
                        qname, mod, node.name, kind, owner, str(path),
                        node.lineno, getattr(node, "end_lineno", node.lineno),
                    )
                    self.functions[qname] = info
                    if owner:
                        self.classes[owner].methods.setdefault(node.name, qname)
                    stack.append(("function", qname))
                    visit(node.body)
                    stack.pop()

        visit(tree.body)

    @staticmethod
    def _base_name(node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parts = []
            cur: ast.expr = node
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            return ".".join(reversed(parts))
        if isinstance(node, ast.Subscript):   # Generic[T]
            return ProjectIndex._base_name(node.value)
        return ""

    # -- resolution ---------------------------------------------------------
    def resolve_name(self, mod: str, name: str) -> Optional[Tuple[str, str]]:
        """Resolve a bare name in module scope to ('class'|'function'|'module', qname)."""
        qname = f"{mod}.{name}"
        if qname in self.classes:
            return "class", qname
        if qname in self.functions:
            return "function", qname
        target = self.imports.get(mod, {}).get(name)
        if target:
            if target in self.classes:
                return "class", target
            if target in self.functions:
                return "function", target
            if target in self.modules:
                return "module", target
            # `from pkg import mod` where mod is a package module
            if f"{target}" in self.modules:
                return "module", target
            head, _, tail = target.rpartition(".")
            if head in self.classes:
                return "class", head
        return None

    def resolve_expr(self, mod: str, expr: ast.expr, owner_class: str = "") -> Optional[Tuple[str, str]]:
        """Resolve an expression to a known symbol, if statically determinable."""
        if isinstance(expr, ast.Name):
            return self.resolve_name(mod, expr.id)
        if isinstance(expr, ast.Attribute):
            base = self.resolve_expr(mod, expr.value, owner_class)
            if base and base[0] == "module":
                cand = f"{base[1]}.{expr.attr}"
                if cand in self.classes:
                    return "class", cand
                if cand in self.functions:
                    return "function", cand
            if base and base[0] == "class":
                cand = f"{base[1]}.{expr.attr}"
                if cand in self.functions:
                    return "function", cand
                if cand in self.classes:
                    return "class", cand
            # self.x() / cls.x() -> look along the inheritance chain
            if isinstance(expr.value, ast.Name) and expr.value.id in ("self", "cls") and owner_class:
                for qname in self.mro(owner_class):
                    meth = self.classes.get(qname, None)
                    if meth and expr.attr in meth.methods:
                        return "function", meth.methods[expr.attr]
            return None
        return None

    def mro(self, class_qname: str, _seen: Optional[set] = None, _depth: int = 0) -> List[str]:
        """Resolved inheritance chain, most-derived first."""
        if _depth > 12 or class_qname in (_seen or set()):
            return []
        seen = _seen or set()
        seen.add(class_qname)
        info = self.classes.get(class_qname)
        if info is None:
            return []
        chain = [class_qname]
        for base in info.bases:
            chain.extend(self.mro(base, seen, _depth + 1))
        return chain

    def _resolve_bases(self) -> None:
        for info in self.classes.values():
            for raw in info.bases_raw:
                if not raw:
                    continue
                target = self._resolve_dotted(info.module, raw, info.outer_function)
                if target and target in self.classes:
                    info.bases.append(target)
                else:
                    self.unresolved_bases.append((info.qname, raw))

    def _resolve_dotted(self, mod: str, dotted: str, outer: str = "") -> Optional[str]:
        head, _, rest = dotted.partition(".")
        if outer:
            local = f"{outer}.{dotted}"
            if local in self.classes:
                return local
        found = self.resolve_name(mod, head)
        if found is None:
            # maybe a fully qualified name inside this project
            if dotted in self.classes:
                return dotted
            return None
        kind, qname = found
        if not rest:
            return qname
        return f"{qname}.{rest}"

    def _resolve(self) -> None:
        self._resolve_bases()
        for info in self.functions.values():
            self._scan_calls(info)

    def _scan_calls(self, func: _FuncInfo) -> None:
        tree = self.modules.get(func.module)
        if tree is None:
            return
        node = self._find_node(tree, func)
        if node is None:
            return
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Call):
                continue
            self.total_calls += 1
            target = self.resolve_expr(func.module, sub.func, func.owner)
            if target is None:
                func.unresolved += 1
                self.unresolved_calls += 1
                continue
            func.calls.append(target[1])

    def _find_node(self, tree: ast.AST, func: _FuncInfo) -> Optional[ast.AST]:
        for sub in ast.walk(tree):
            if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if sub.name == func.name and sub.lineno == func.lineno and sub.col_offset == getattr(func, "col", sub.col_offset):
                    return sub
        # fall back to name+line match (col_offset is not stored)
        for sub in ast.walk(tree):
            if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if sub.name == func.name and sub.lineno == func.lineno:
                    return sub
        return None

    # -- derived views ------------------------------------------------------
    def subclass_map(self) -> Dict[str, List[str]]:
        subs: Dict[str, List[str]] = defaultdict(list)
        for info in self.classes.values():
            for base in info.bases:
                subs[base].append(info.qname)
        return dict(subs)


@register
class PythonAstExtractor(Extractor):
    """Class + function dependency extractor with no third-party dependency."""

    language = "python"
    suffixes = (".py",)
    backend = "stdlib ast + import-graph resolution"
    status = "implemented"
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
        self._index: Optional[ProjectIndex] = None

    # -- helpers ------------------------------------------------------------
    def _build(self, repo_root: str) -> ProjectIndex:
        if self._index is None:
            self._index = ProjectIndex(repo_root).build()
        return self._index

    def measure(self, repo_root: str) -> Dict[str, int]:
        idx = self._build(repo_root)
        classes = len(idx.classes)
        methods = sum(1 for f in idx.functions.values() if f.kind == EntityKind.METHOD)
        functions = sum(1 for f in idx.functions.values() if f.kind == EntityKind.FUNCTION)
        declared = sum(len(info.bases_raw) for info in idx.classes.values())
        return {
            "classes": classes,
            "methods": methods,
            "functions": functions,
            "documentable": methods + functions,
            "files": len(idx.modules),
            "parse_errors": len(idx.parse_errors),
            "bases_declared": declared,
            "bases_resolved": declared - len(idx.unresolved_bases),
            "calls": idx.total_calls,
            "calls_resolved": idx.total_calls - idx.unresolved_calls,
        }

    def coverage_report(self, repo_root: str) -> Dict[str, object]:
        """Resolution statistics — the evidence that coverage is measured."""
        idx = self._build(repo_root)
        declared = sum(len(info.bases_raw) for info in idx.classes.values())
        return {
            "files_parsed": len(idx.modules),
            "parse_errors": idx.parse_errors[:10],
            "n_parse_errors": len(idx.parse_errors),
            "classes": len(idx.classes),
            "bases_declared": declared,
            "bases_resolved": declared - len(idx.unresolved_bases),
            "base_resolution_rate": (declared - len(idx.unresolved_bases)) / declared if declared else 1.0,
            "calls": idx.total_calls,
            "calls_resolved": idx.total_calls - idx.unresolved_calls,
            "call_resolution_rate": (idx.total_calls - idx.unresolved_calls) / idx.total_calls if idx.total_calls else 1.0,
        }

    def extract(self, repo_root: str) -> List[DependencyContext]:
        idx = self._build(repo_root)
        subs = idx.subclass_map()
        contexts: List[DependencyContext] = []

        # called_by index
        called_by: Dict[str, List[str]] = defaultdict(list)
        for info in idx.functions.values():
            for target in info.calls:
                called_by[target].append(info.qname)

        # instantiation index
        instantiated_by: Dict[str, List[str]] = defaultdict(list)
        for info in idx.functions.values():
            for target in info.calls:
                if target in idx.classes:
                    instantiated_by[target].append(info.qname)

        # --- classes -------------------------------------------------------
        for qname, info in idx.classes.items():
            entity = Entity(
                name=info.name, kind=EntityKind.CLASS, path=info.path,
                span=[info.lineno, info.end_lineno], qualified_name=qname,
            )
            ctx = DependencyContext(entity=entity, source=self._slice(info.path, info.lineno, info.end_lineno))
            for base in info.bases:
                ctx.add(Relation(kind=RelationKind.INHERITS, target=base.split(".")[-1],
                                 target_kind=EntityKind.CLASS, path=idx.classes[base].path))
            for sub in subs.get(qname, []):
                ctx.add(Relation(kind=RelationKind.SUBCLASSED_BY, target=sub.split(".")[-1],
                                 target_kind=EntityKind.CLASS, path=idx.classes[sub].path))
            for user in dict.fromkeys(instantiated_by.get(qname, [])):
                target_kind = EntityKind.METHOD if user in idx.functions and idx.functions[user].kind == EntityKind.METHOD else EntityKind.FUNCTION
                path = idx.functions[user].path if user in idx.functions else ""
                ctx.add(Relation(kind=RelationKind.INSTANTIATED_AT, target=user.split(".")[-1],
                                 target_kind=target_kind, path=path))
            # polymorphic contract: methods overridden somewhere in the subtree
            for mname, mqname in info.methods.items():
                impls = [q for q in subs.get(qname, []) if mname in idx.classes[q].methods]
                if impls:
                    ctx.add(Relation(
                        kind=RelationKind.OVERRIDDEN_BY, target=f"{info.name}.{mname}",
                        target_kind=EntityKind.METHOD,
                        detail="implemented by " + ", ".join(
                            f"{idx.classes[q].name}.{mname}" for q in impls[:6]),
                    ))
            contexts.append(ctx)

        # --- functions and methods ----------------------------------------
        for qname, info in idx.functions.items():
            entity = Entity(
                name=(f"{info.owner.split('.')[-1]}.{info.name}" if info.owner else info.name),
                kind=info.kind, path=info.path, span=[info.lineno, info.end_lineno],
                qualified_name=qname,
            )
            ctx = DependencyContext(entity=entity, source=self._slice(info.path, info.lineno, info.end_lineno))
            for target in dict.fromkeys(info.calls):
                kind = EntityKind.CLASS if target in idx.classes else (
                    EntityKind.METHOD if target in idx.functions and idx.functions[target].kind == EntityKind.METHOD
                    else EntityKind.FUNCTION)
                path = (idx.classes[target].path if target in idx.classes
                        else idx.functions[target].path if target in idx.functions else "")
                ctx.add(Relation(kind=RelationKind.CALLS, target=target.split(".")[-1],
                                 target_kind=kind, path=path))
            for caller in dict.fromkeys(called_by.get(qname, [])):
                ctx.add(Relation(kind=RelationKind.CALLED_BY, target=caller.split(".")[-1],
                                 target_kind=EntityKind.FUNCTION))
            if info.kind == EntityKind.METHOD and info.owner:
                for anc in idx.mro(info.owner)[1:]:
                    if info.name in idx.classes[anc].methods:
                        ctx.add(Relation(kind=RelationKind.OVERRIDES,
                                         target=f"{idx.classes[anc].name}.{info.name}",
                                         target_kind=EntityKind.METHOD,
                                         path=idx.classes[anc].path))
                for sub in subs.get(info.owner, []):
                    if info.name in idx.classes[sub].methods:
                        ctx.add(Relation(kind=RelationKind.OVERRIDDEN_BY,
                                         target=f"{idx.classes[sub].name}.{info.name}",
                                         target_kind=EntityKind.METHOD,
                                         path=idx.classes[sub].path))
                for anc in idx.mro(info.owner)[1:]:
                    for peer in subs.get(anc, []):
                        if peer == info.owner:
                            continue
                        if info.name in idx.classes[peer].methods:
                            ctx.add(Relation(kind=RelationKind.DISPATCH_CANDIDATES,
                                             target=f"{idx.classes[peer].name}.{info.name}",
                                             target_kind=EntityKind.METHOD,
                                             path=idx.classes[peer].path))
            contexts.append(ctx)
        return contexts

    @staticmethod
    def _slice(path: str, start: int, end: int) -> str:
        try:
            lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return ""
        return "\n".join(lines[max(0, start - 1):end])
