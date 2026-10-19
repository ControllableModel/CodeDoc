"""Audit whether every extracted relation actually reaches the prompt.

The published artifact claimed to inject dependency information but injected a
single relation family, and nothing verified the claim. This script answers the
question directly and per entity kind:

* how many relations of each kind the extractor found;
* how many of them appear in the record handed to the prompt builder;
* how many appear in the *rendered prompt text* (so nothing is lost between the
  record and the template);
* and for classes, how much of the class skeleton survives budgeting.

Recall is reported per kind. A kind at 0% means the extractor produces relations the
writer never sees — exactly the defect that made class documentation possible on
paper and impossible in practice.

Usage::

    python scripts/audit_prompt_injection.py --repo flask-main
    python scripts/audit_prompt_injection.py --repo flask-main --prompt-check 20
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.config import TARGETS, TEMPLATES  # noqa: E402
from codedoc.deps.relations_index import BLOCK_LABELS, build_index, get_dep  # noqa: E402
from codedoc.deps.schema import EntityKind, RelationKind  # noqa: E402
from codedoc.writer.prompt import build_prompt  # noqa: E402

#: Every relation kind the extractor can emit, mapped to how it is rendered.
KIND_TO_BLOCK = {
    RelationKind.CALLS: "Uses",
    RelationKind.CALLED_BY: "Used by",
    RelationKind.INHERITS: "Inherits",
    RelationKind.SUBCLASSED_BY: "Subclassed by",
    RelationKind.INSTANTIATED_AT: "Instantiated at",
    RelationKind.OVERRIDES: "Overrides",
    RelationKind.OVERRIDDEN_BY: "Overridden by",
    RelationKind.DISPATCH_CANDIDATES: "Dispatch candidates",
    RelationKind.ATTRIBUTE_ACCESS: "Attribute access",
}


def _defines_init(source: str) -> bool:
    """True only when the class actually defines ``__init__`` (not merely mentions it)."""
    import ast
    import textwrap

    try:
        tree = ast.parse(textwrap.dedent(source))
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            return any(
                isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == "__init__"
                for child in node.body
            )
    return False


class _Args:
    relevant = True
    language = "English"
    max_tokens = 40000
    source_budget = 8000
    prompt_template = str(TEMPLATES / "iso_26514.txt")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default="flask-main")
    ap.add_argument("--prompt-check", type=int, default=10,
                    help="render this many prompts and verify each relation name appears")
    ap.add_argument("--model-kind", default=None, help="restrict to one entity kind")
    args = ap.parse_args()

    index = build_index(str(TARGETS / args.repo))
    if index is None:
        print(f"no entities in {args.repo}", file=sys.stderr)
        return 1

    entities = index.contexts
    if args.model_kind:
        entities = [c for c in entities if str(c.entity.kind) == args.model_kind]
    print(f"repository: {args.repo}   entities: {len(entities)}")

    available = collections.Counter()
    injected = collections.Counter()
    entities_with_relation = collections.Counter()
    entities_with_injection = collections.Counter()
    per_kind = collections.defaultdict(collections.Counter)

    for ctx in entities:
        kind = str(ctx.entity.kind)
        dep = get_dep(index, ctx.entity.name, ctx.entity.qualified_name, ctx.entity.path)
        if dep is None:
            continue
        injected_names = set()
        for entries in (dep.get("relations") or {}).values():
            for entry in entries:
                injected_names.add(entry.get("name") if isinstance(entry, dict) else str(entry))
        injected_names |= {name for item in dep["uses"] for name in item}
        injected_names |= {name for item in dep["used_by"] for name in item}

        for relation_kind in KIND_TO_BLOCK:
            relations = ctx.get(relation_kind)
            if not relations:
                continue
            available[relation_kind] += len(relations)
            entities_with_relation[relation_kind] += 1
            per_kind[kind][relation_kind] += len(relations)
            hits = sum(1 for r in relations if r.target in injected_names
                       or index.label(r.target) in injected_names)
            injected[relation_kind] += hits
            if hits:
                entities_with_injection[relation_kind] += 1

    print()
    print("INJECTION RECALL PER RELATION KIND")
    print("-" * 92)
    print(f"{'relation':<22}{'rendered as':<22}{'found':>8}{'injected':>9}{'recall':>8}"
          f"{'entities':>10}{'covered':>9}")
    print("-" * 92)
    problems = []
    for relation_kind, block in KIND_TO_BLOCK.items():
        total = available[relation_kind]
        hit = injected[relation_kind]
        n_ent = entities_with_relation[relation_kind]
        covered = entities_with_injection[relation_kind]
        recall = (hit / total) if total else float("nan")
        flag = ""
        if total and recall < 1.0:
            problems.append((relation_kind, total, hit, recall))
            flag = "  <-- LOSS"
        print(f"{relation_kind:<22}{block:<22}{total:>8}{hit:>9}"
              f"{(f'{recall:.1%}' if total else '—'):>8}{n_ent:>10}{covered:>9}{flag}")

    # ---- prompt-level verification ------------------------------------------
    if args.prompt_check:
        print()
        print(f"PROMPT-LEVEL VERIFICATION (first {args.prompt_check} entities)")
        print("-" * 92)
        writer_args = _Args()
        checked = 0
        failures = 0
        for ctx in entities[: args.prompt_check]:
            dep = get_dep(index, ctx.entity.name, ctx.entity.qualified_name, ctx.entity.path)
            if dep is None:
                continue
            prompt = build_prompt(dep, writer_args)
            missing = []
            for relation_kind in KIND_TO_BLOCK:
                for relation in ctx.get(relation_kind):
                    label = index.label(relation.target)
                    if relation.target not in prompt and label not in prompt:
                        missing.append(f"{relation_kind}:{relation.target}")
            checked += 1
            status = "OK" if not missing else f"MISSING {len(missing)}: {missing[:3]}"
            if missing:
                failures += 1
            print(f"  {ctx.entity.qualified_name[:46]:<48}{str(ctx.entity.kind):<9}"
                  f"{len(prompt):>7} chars  {status}")
        print(f"  checked={checked}  entities_with_missing_relations={failures}")

    # ---- class skeleton completeness ----------------------------------------
    classes = [c for c in entities if c.entity.kind == EntityKind.CLASS]
    if classes:
        print()
        print("CLASS VIEW COMPLETENESS")
        print("-" * 92)
        omitted = 0
        no_init = 0
        for ctx in classes:
            dep = get_dep(index, ctx.entity.name, ctx.entity.qualified_name, ctx.entity.path)
            if dep is None:
                continue
            view = dep.get("prompt_source") or ""
            if "further method signature(s) omitted" in view:
                omitted += 1
            if "__init__" not in view and _defines_init(ctx.source or ""):
                no_init += 1
        print(f"  classes: {len(classes)}")
        print(f"  skeleton dropped method signatures for : {omitted} classes")
        print(f"  skeleton missing an existing __init__ : {no_init} classes")

    print()
    if problems:
        print("DEFECTS: relation kinds below full recall ->", ", ".join(
            f"{k}({r:.1%})" for k, _t, _h, r in problems))
        return 1
    print("OK: every extracted relation appears in the injected record.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
