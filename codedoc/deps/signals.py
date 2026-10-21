"""Mechanical facts about an entity, read straight from its source.

The criteria CodeDoc scores worst on ask for facts that were previously left to the model
to infer: every return path (ISO "Completeness"), every exception the body can raise
(GitHub "Error Reference Content"), and the exact signature (GitHub "Reference Content").
All three are decidable from the AST, so they are extracted here and handed to the prompt
as evidence instead of being guessed at.

Extraction is deliberately shallow and fail-soft: a source excerpt that does not parse
yields empty lists rather than an exception, because a missing hint only makes the prompt
slightly weaker, while an exception would drop the entity.
"""

from __future__ import annotations

import ast
from typing import Dict, List


def _dedent_lines(text: str) -> List[str]:
    """Dedent a source excerpt so ``ast.parse`` accepts an indented method body."""
    lines = text.splitlines()
    widths = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
    cut = min(widths) if widths else 0
    return [line[cut:] if line.strip() else "" for line in lines]


def entity_signals(source: str) -> Dict[str, object]:
    """Return ``{signature, returns, raises}`` for the first definition in ``source``."""
    signals: Dict[str, object] = {"signature": "", "returns": [], "raises": []}
    body = (source or "").strip()
    if not body:
        return signals
    try:
        tree = ast.parse("\n".join(_dedent_lines(body)))
    except SyntaxError:
        return signals

    node = None
    for child in ast.walk(tree):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            node = child
            break
    if node is None:
        return signals

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        params = [a.arg for a in node.args.posonlyargs + node.args.args]
        n_defaults = len(node.args.defaults)
        rendered = []
        for i, name in enumerate(params):
            if node.args.vararg is not None and name == getattr(node.args.vararg, "arg", None):
                continue
            if n_defaults and i >= len(params) - n_defaults:
                rendered.append(name + "=...")
            else:
                rendered.append(name)
        if node.args.vararg is not None:
            rendered.append("*" + node.args.vararg.arg)
        if node.args.kwarg is not None:
            rendered.append("**" + node.args.kwarg.arg)
        ret = ""
        if getattr(node, "returns", None) is not None:
            ret = " -> " + ast.unparse(node.returns)
        signals["signature"] = f"{node.name}({', '.join(rendered)}){ret}"

    returns: List[Dict[str, object]] = []
    raises: List[Dict[str, object]] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Return):
            value = ast.unparse(child.value) if child.value is not None else "None"
            if len(value) > 90:
                value = value[:87] + "..."
            returns.append({"line": child.lineno, "value": value})
        elif isinstance(child, ast.Raise):
            if child.exc is None:
                name = "re-raise current exception"
            elif isinstance(child.exc, ast.Call):
                name = ast.unparse(child.exc.func)
            else:
                name = ast.unparse(child.exc)
            if len(name) > 60:
                name = name[:57] + "..."
            raises.append({"line": child.lineno, "name": name})
    signals["returns"] = returns
    signals["raises"] = raises
    return signals
