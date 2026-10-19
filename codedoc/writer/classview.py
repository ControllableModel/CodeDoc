"""Class-level prompt view: ``__init__`` in full, other methods as signatures.

A class body is a poor prompt. Flask's class is 1,517 lines, so injecting it whole
either overflows the budget or gets clipped to a fragment — and the fragment is
mostly implementation detail that a class-level document should *not* restate.

The agreed view for a class entity is:

* the class declaration (name and bases, which is where inheritance is visible);
* the ``__init__`` body **in full** — constructor behaviour is what a class
  document describes (parameters, defaults, setup, side effects);
* every other method as a **signature only**: decorators dropped, body dropped,
  parameter list and return annotation kept.

Method-level detail is not lost: each method is documented as its own entity, one
level below the class in the generated artifact.
"""

from __future__ import annotations

import ast
import textwrap
from typing import List, Optional

#: Lines a single signature may span before it is truncated.
MAX_SIGNATURE_LINES = 12


def _class_node(source: str) -> Optional[ast.ClassDef]:
    try:
        tree = ast.parse(textwrap.dedent(source))
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            return node
    return None


def _signature(lines: List[str], node: ast.AST) -> str:
    """Join the ``def`` header of a function, dropping decorators and the body."""
    start = node.lineno - 1
    collected: List[str] = []
    for line in lines[start:start + MAX_SIGNATURE_LINES]:
        collected.append(line.rstrip())
        if line.rstrip().endswith(":"):
            break
    header = "\n".join(collected) or f"    def {getattr(node, 'name', '?')}(...):"
    indent = len(header) - len(header.lstrip())
    return " " * indent + header.lstrip()


def _body(lines: List[str], node: ast.AST) -> str:
    start = node.lineno - 1
    end = getattr(node, "end_lineno", start + 1)
    return "\n".join(lines[start:end])


def class_skeleton(source: str, budget: Optional[int] = None) -> str:
    """Render the class-level prompt view.

    ``budget`` caps the rendered characters. ``__init__`` is always kept in full;
    remaining methods are added in declaration order until the budget is reached,
    and the number of omitted methods is stated explicitly instead of being
    silently dropped.
    """
    node = _class_node(source)
    if node is None:
        return source

    lines = textwrap.dedent(source).splitlines()
    parts: List[str] = []

    # 1. class declaration (first line up to the closing colon)
    header: List[str] = []
    for line in lines[node.lineno - 1:]:
        header.append(line.rstrip())
        if line.rstrip().endswith(":"):
            break
    parts.append("\n".join(header))

    members = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    init = next((n for n in members if n.name == "__init__"), None)
    others = [n for n in members if n is not init]

    # 2. __init__ in full — the constructor is what a class document explains
    if init is not None:
        parts.append(_body(lines, init))

    # 3. remaining methods: signatures only
    rendered = 0
    used = len("\n".join(parts))
    for member in others:
        signature = _signature(lines, member)
        if budget is not None and used + len(signature) + 1 > budget:
            break
        parts.append(signature)
        used += len(signature) + 1
        rendered += 1

    omitted = len(others) - rendered
    if omitted > 0:
        parts.append(f"    # ... {omitted} further method signature(s) omitted (prompt budget) ...")

    return "\n".join(parts)


def class_member_summary(source: str) -> List[str]:
    """Names of the methods declared by a class, in declaration order."""
    node = _class_node(source)
    if node is None:
        return []
    return [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
