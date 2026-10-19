"""Prompt and audit-document assembly for documentation generation.

Two consumers:

``build_prompt``  assembles the generation prompt for one entity
``format_dep``    renders the human-readable ``.info`` audit trail

Both take the dict produced by :func:`codedoc.deps.relations_index.get_dep`, which
keeps the historical keys (``real_name``/``source_code``/``uses``/``used_by``) and
adds ``relations`` — the class and polymorphism blocks the pyan3-era prompt could
not express, because a class has no callers/callees of its own.
"""

from __future__ import annotations

from typing import Dict, List

from codedoc.deps.schema import DependencyContext, RelationKind

__all__ = ["build_prompt", "format_dep", "build_context_blocks", "render_relations"]


def _build_section(items: List[Dict[str, str]], title: str) -> str:
    if not items:
        return ""
    lines = [f"## {title}\n"]
    for item in items:
        for name, code in item.items():
            if code:
                lines.append(f"### {name}\n```python\n{code}\n```\n")
            else:
                lines.append(f"### {name}\n")
    return "".join(lines)


def render_relations(info: Dict[str, object]) -> str:
    """Render inheritance / instantiation / override blocks as markdown."""
    relations = info.get("relations") or {}
    if not relations:
        return ""
    lines: List[str] = []
    for label, targets in relations.items():  # type: ignore[union-attr]
        if not targets:
            continue
        lines.append(f"## {label}\n")
        for target in targets:  # type: ignore[union-attr]
            lines.append(f"- `{target}`")
        lines.append("\n")
    return "".join(lines)


def format_dep(info: Dict[str, object], include_deps: bool = True) -> str:
    """The ``.info`` audit record: what exactly reached the prompt."""
    uses = _build_section(info["uses"], "Uses") if include_deps else ""          # type: ignore[arg-type]
    used_by = _build_section(info["used_by"], "Used by") if include_deps else ""  # type: ignore[arg-type]
    relations = render_relations(info) if include_deps else ""
    return f"""# {info["real_name"]}
## Path
`{info["path"]}`

## Definition
```python
{info["source_code"]}
```

{uses}
{used_by}
{relations}"""


def build_prompt(info: Dict[str, object], args) -> str:
    """Assemble the generation prompt for one entity."""
    uses = _build_section(info["uses"], "Dependencies") if args.relevant else ""      # type: ignore[arg-type]
    used_by = _build_section(info["used_by"], "Dependents") if args.relevant else ""  # type: ignore[arg-type]
    relations = render_relations(info) if args.relevant else ""

    # Ablation / IDE-style baseline: no criteria template.
    if args.prompt_template is None:
        return f"""Generate documentation for the following code in {args.language}.

Code to document:
```python
{info["source_code"]}
```
uses:
{uses}

used_by:
{used_by}
{relations}

Provide clear and concise documentation."""

    try:
        with open(args.prompt_template, "r", encoding="utf-8") as fh:
            template = fh.read()
    except FileNotFoundError:
        return (
            f"Generate docs for {info['real_name']}\n\n{info['source_code']}\n\n"
            f"{uses}\n{used_by}\n{relations}"
        )
    try:
        return template.format(
            real_name=info["real_name"],
            path=info["path"],
            source_code=info["source_code"],
            uses=uses,
            used_by=used_by,
            relations=relations,
            language=args.language,
        )
    except KeyError:
        # Template predates the ``relations`` placeholder; still usable.
        return template.format(
            real_name=info["real_name"],
            path=info["path"],
            source_code=info["source_code"],
            uses=uses,
            used_by=used_by,
            language=args.language,
        )


def build_context_blocks(context: DependencyContext) -> Dict[str, str]:
    """Relation blocks for a :class:`DependencyContext` (used by reports/tests)."""
    blocks: Dict[str, str] = {}
    for kind, label in (
        (RelationKind.INHERITS, "Inheritance"),
        (RelationKind.SUBCLASSED_BY, "Subclassed by"),
        (RelationKind.INSTANTIATED_AT, "Instantiated at"),
        (RelationKind.OVERRIDES, "Overrides"),
        (RelationKind.OVERRIDDEN_BY, "Overridden by"),
        (RelationKind.DISPATCH_CANDIDATES, "Dispatch candidates"),
        (RelationKind.CALLS, "Calls"),
        (RelationKind.CALLED_BY, "Called by"),
    ):
        relations = context.get(kind)
        if relations:
            blocks[label] = (
                f"## {label}\n" + "\n".join(f"- `{r.target}`" for r in relations) + "\n"
            )
    return blocks
