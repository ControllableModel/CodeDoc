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

__all__ = [
    "build_prompt", "format_dep", "build_context_blocks", "render_relations",
    "clip_source",
]

#: Default budget for the source section, in characters.
#:
#: The previous pipeline truncated the *whole* message to 10,000 characters in
#: ``call_llm``. For a 1,500-line class that meant the dependency blocks, the
#: required output structure and even the tail of the source were silently
#: dropped. Clipping the source section explicitly keeps every other section
#: intact and makes the elision visible in the prompt and in the audit record.
DEFAULT_SOURCE_BUDGET = 8000


def clip_source(code: str, budget: int = DEFAULT_SOURCE_BUDGET) -> str:
    """Trim a source section to ``budget`` characters, keeping head and tail.

    The signature and the trailing code (imports, returns, decorators) are the
    parts a documentation writer needs most, so both ends are kept and the middle
    is elided with an explicit marker that states how many lines were removed.
    """
    if budget <= 0 or len(code) <= budget:
        return code
    lines = code.splitlines()
    marker_reserve = 120
    head_budget = int((budget - marker_reserve) * 0.6)
    tail_budget = budget - marker_reserve - head_budget

    head, used = [], 0
    for line in lines:
        if used + len(line) + 1 > head_budget:
            break
        head.append(line)
        used += len(line) + 1

    tail, used = [], 0
    for line in reversed(lines[len(head):]):
        if used + len(line) + 1 > tail_budget:
            break
        tail.append(line)
        used += len(line) + 1
    tail.reverse()

    elided = len(lines) - len(head) - len(tail)
    marker = f"# ... {elided} lines elided (source exceeds the {budget}-char budget) ..."
    return "\n".join(head + [marker] + tail)


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
    """Render inheritance / instantiation / override blocks as markdown.

    Entries are either plain names (older records) or ``{name, code}`` dicts. When a
    source snippet is present it is rendered as a fenced block: the model needs the
    base class or the overridden method itself, not just its name, and input tokens
    are the cheap side of the bill.
    """
    relations = info.get("relations") or {}
    if not relations:
        return ""
    lines: List[str] = []
    for label, entries in relations.items():  # type: ignore[union-attr]
        if not entries:
            continue
        lines.append(f"## {label}\n")
        for entry in entries:  # type: ignore[union-attr]
            if isinstance(entry, dict):
                name = entry.get("name") or ""
                code = entry.get("code") or ""
            else:
                name, code = str(entry), ""
            if code:
                lines.append(f"### {name}\n```python\n{code}\n```\n")
            else:
                lines.append(f"- `{name}`")
        lines.append("\n")
    return "".join(lines)


def format_dep(info: Dict[str, object], include_deps: bool = True) -> str:
    """The ``.info`` audit record: what exactly reached the prompt."""
    source = clip_source(str(info.get("prompt_source") or info["source_code"]))
    uses = _build_section(info["uses"], "Uses") if include_deps else ""          # type: ignore[arg-type]
    used_by = _build_section(info["used_by"], "Used by") if include_deps else ""  # type: ignore[arg-type]
    relations = render_relations(info) if include_deps else ""
    return f"""# {info["real_name"]}
## Path
`{info["path"]}`

## Definition
```python
{source}
```

{uses}
{used_by}
{relations}"""


def render_evidence(info: Dict[str, object]) -> str:
    """Mechanical evidence block for the ``{evidence}`` placeholder.

    The criteria CodeDoc scores worst on ask for facts that are decidable from the AST but
    were previously left to the model to infer: every return path (Completeness), every
    exception the body can raise (GitHub "Error Reference Content"), and the exact
    signature (GitHub "Reference Content"). Handing them over as evidence costs a few
    hundred input tokens and removes the guesswork.

    Line numbers are relative to the source excerpt in the prompt, which is why the block
    says so: quoting file line numbers here would be wrong after clipping.
    """
    signals = info.get("signals") or {}
    if not isinstance(signals, dict):
        return ""
    blocks = []

    signature = str(signals.get("signature") or "").strip()
    if signature:
        blocks.append("### Signature\n```python\n" + signature + "\n```")
    elif str(info.get("kind") or "") == "class":
        blocks.append("### Signature\n(class declaration — see the source below)")

    returns = signals.get("returns") or []
    if isinstance(returns, list) and returns:
        rows = [f"- excerpt line {r['line']}: `return {r['value']}`" for r in returns[:12]]
        if len(returns) > 12:
            rows.append(f"- ... {len(returns) - 12} more return statements")
        blocks.append("### Return statements in the body\n" + "\n".join(rows))

    raises = signals.get("raises") or []
    if isinstance(raises, list) and raises:
        rows = [f"- excerpt line {r['line']}: `raise {r['name']}`" for r in raises[:12]]
        if len(raises) > 12:
            rows.append(f"- ... {len(raises) - 12} more raise statements")
        blocks.append("### Raise statements in the body\n" + "\n".join(rows))

    if not blocks:
        return ""
    return "## Evidence extracted from the source (mechanical, not inferred)\n\n" + "\n\n".join(blocks)


def build_prompt(info: Dict[str, object], args) -> str:
    """Assemble the generation prompt for one entity.

    The source section is budgeted *from the total prompt cap*, not from a fixed
    constant: the criteria template alone is ~4 KB, so a fixed 8 KB source budget
    still overflowed the 10 KB guard and the overflow truncated the tail of the
    prompt (the required output structure). Everything except the source section is
    mandatory, so it gets whatever budget remains, split between head and tail with
    an explicit elision marker.
    """
    uses = _build_section(info["uses"], "Dependencies") if args.relevant else ""      # type: ignore[arg-type]
    used_by = _build_section(info["used_by"], "Dependents") if args.relevant else ""  # type: ignore[arg-type]
    relations = render_relations(info) if args.relevant else ""
    evidence = render_evidence(info)
    source_text = str(info.get("prompt_source") or info["source_code"])
    cap = int(getattr(args, "max_tokens", 0) or 0)
    configured = int(getattr(args, "source_budget", 0) or DEFAULT_SOURCE_BUDGET)

    # Ablation / IDE-style baseline: no criteria template.
    if args.prompt_template is None:
        scaffold = (
            f"Generate documentation for the following code in {args.language}.\n\n"
            f"Code to document:\n```python\n\n```\nuses:\n{uses}\n\n"
            f"used_by:\n{used_by}\n{relations}\n\nProvide clear and concise documentation."
        )
        budget = configured if not cap else max(400, min(configured, cap - len(scaffold) - 100))
        return scaffold.replace(
            "```python\n\n```", "```python\n" + clip_source(source_text, budget) + "\n```"
        )

    try:
        with open(args.prompt_template, "r", encoding="utf-8") as fh:
            template = fh.read()
    except FileNotFoundError:
        template = "Generate docs for {real_name}\n\n{source_code}\n\n{uses}\n{used_by}\n{relations}"

    # Budget the source from what the template and the other sections leave over.
    overhead = len(template) + len(uses) + len(used_by) + len(relations) + len(evidence) + 200
    budget = configured if not cap else max(400, min(configured, cap - overhead))
    source = clip_source(source_text, budget)

    values = dict(
        real_name=info["real_name"],
        path=info["path"],
        source_code=source,
        uses=uses,
        used_by=used_by,
        relations=relations,
        evidence=evidence,
        # Older templates spell this {signals}; both names carry the same block so a
        # template written either way keeps working.
        signals=evidence,
        kind=str(info.get("kind") or ""),
        qname=str(info.get("qualified_name") or info["real_name"]),
        language=args.language,
    )
    try:
        return template.format(**values)
    except KeyError:
        # Template predates one of the placeholders (e.g. ``relations``).
        for optional in ("relations", "evidence", "signals", "kind", "qname"):
            values.pop(optional, None)
        return template.format(**values)


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
