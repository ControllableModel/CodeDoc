"""Compatibility layer for pyan3 1.1.1.

Why this module exists
----------------------
pyan3 1.1.1 crashes on annotated assignments whose right-hand side it cannot
sanitize:

    File ".../pyan/analyzer.py", line 752, in visit_AnnAssign
        get_ast_node_name(value[0]),
    IndexError: list index out of range

``sanitize_exprs(node.value)`` returns an empty list for expressions it does not
model, and the code then indexes element 0.  On the evaluated repositories this
kills the whole DOT export for Flask (4 files: ``ctx.py``, ``sessions.py``,
``testing.py``, ``views.py``) and PyTorch, i.e. the published pipeline cannot
regenerate their dependency graphs with the pinned pyan version.

The upstream bug is patched here instead of in ``site-packages`` so that the fix
travels with the artifact and is reviewable.  pyan is invoked **in-process**
because a subprocess could not see the patch; the previous subprocess call also
swallowed the failure and returned ``None``, which produced a downstream
``TypeError`` far from the real cause.
"""

from __future__ import annotations

import io
import logging
import sys
from typing import List, Sequence

_PATCHED = False
_DEFAULTS = ("--dot", "--no-defines", "--uses")

logger = logging.getLogger(__name__)


def patch_annassign() -> None:
    """Guard pyan's ``visit_AnnAssign`` against empty sanitized values."""
    global _PATCHED
    if _PATCHED:
        return
    import pyan.analyzer as analyzer

    original = analyzer.CallGraphVisitor.visit_AnnAssign
    sanitize_exprs = analyzer.sanitize_exprs

    def visit_AnnAssign(self, node):  # noqa: N802 - mirrors upstream name
        if node.value is not None and not sanitize_exprs(node.value):
            # Upstream would crash here; treat it as a bare type declaration.
            self.last_value = None
            targets = sanitize_exprs(node.target)
            if targets:
                self.visit(targets[0])
            logger.debug(
                "pyan_compat: skipped unsanitizable AnnAssign value at %s:%s",
                getattr(self, "filename", "?"),
                getattr(node, "lineno", "?"),
            )
            return None
        return original(self, node)

    analyzer.CallGraphVisitor.visit_AnnAssign = visit_AnnAssign
    _PATCHED = True


def run_pyan_dot(filenames: Sequence[str]) -> str:
    """Return the DOT graph text for ``filenames``.

    Raises :class:`RuntimeError` when pyan fails, instead of returning ``None``.
    """
    patch_annassign()
    import importlib

    pyan_main_mod = importlib.import_module("pyan.main")
    pyan_main = getattr(pyan_main_mod, "main")

    argv = ["pyan", *filenames, *_DEFAULTS]
    old_argv, old_stdout = sys.argv, sys.stdout
    buffer = io.StringIO()
    try:
        sys.argv = argv
        sys.stdout = buffer
        pyan_main()
    except SystemExit as exc:  # pyan calls sys.exit on argument errors
        raise RuntimeError(f"pyan exited with {exc.code}") from None
    except Exception as exc:
        raise RuntimeError(f"pyan failed: {type(exc).__name__}: {exc}") from exc
    finally:
        sys.argv, sys.stdout = old_argv, old_stdout

    dot = buffer.getvalue()
    if "digraph" not in dot:
        raise RuntimeError(
            "pyan produced no DOT output; the dependency graph cannot be built for this set"
        )
    return dot


def preflight(filenames: Sequence[str], max_report: int = 5) -> List[str]:
    """Report files that pyan cannot analyse on their own.

    Used by ``scripts/probe_relations.py`` so a partially-analysable repository
    is visible instead of silently producing a thin graph.
    """
    import importlib

    pyan_main_mod = importlib.import_module("pyan.main")
    pyan_main = getattr(pyan_main_mod, "main")
    failing: List[str] = []
    for name in filenames:
        argv = ["pyan", name, *_DEFAULTS]
        old_argv, old_stdout = sys.argv, sys.stdout
        try:
            sys.argv = argv
            sys.stdout = io.StringIO()
            pyan_main()
        except BaseException:
            failing.append(name)
        finally:
            sys.argv, sys.stdout = old_argv, old_stdout
        if len(failing) >= max_report:
            break
    return failing
