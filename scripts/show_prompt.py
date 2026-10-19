"""Print the exact prompt that would be sent for one entity.

Reviewers could not tell what actually reached the model, and the published
description of the injected information was contradicted by the artifact (it
claimed AST-derived structure while only raw source lines were passed). This tool
makes the prompt inspectable: no API key, no model call.

Usage::

    python scripts/show_prompt.py --repo targets/flask-main --entity Flask
    python scripts/show_prompt.py --repo targets/flask-main --entity Flask.__init__
    python scripts/show_prompt.py --repo targets/flask-main --entity Flask --criteria practice_docstring
    python scripts/show_prompt.py --repo targets/flask-main --entity Flask --raw   # prompt text only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.config import CRITERIA_SETS, TEMPLATES  # noqa: E402
from codedoc.deps.relations_index import build_index, get_dep  # noqa: E402
from codedoc.writer.prompt import build_prompt, format_dep  # noqa: E402


class _Args:
    """Minimal stand-in for the CLI namespace used by the writer."""

    relevant = True
    language = "English"
    prompt_template = None
    process = False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--entity", required=True, help="class or function/method name, e.g. Flask or Flask.__init__")
    ap.add_argument("--criteria", default="iso_26514",
                    help=f"criterion set: one of {sorted(p.stem for p in CRITERIA_SETS.glob('*.json'))}")
    ap.add_argument("--template", default=None, help="template file (default: the criteria set's ISO template)")
    ap.add_argument("--no-deps", action="store_true", help="leave the dependency blocks out (ablation view)")
    ap.add_argument("--raw", action="store_true", help="print only the prompt, no section banners")
    ap.add_argument("--show-info", action="store_true", help="also print the .info audit record")
    args = ap.parse_args()

    index = build_index(args.repo)
    if index is None:
        print(f"no entities extracted from {args.repo}", file=sys.stderr)
        return 1

    dep = get_dep(index, args.entity, "", "")
    if dep is None:
        candidates = [c.entity.name for c in index.contexts if args.entity.lower() in c.entity.name.lower()]
        print(f"entity {args.entity!r} not found. Similar: {candidates[:10]}", file=sys.stderr)
        return 1

    writer_args = _Args()
    writer_args.relevant = not args.no_deps
    template = args.template or str(TEMPLATES / ("iso_26514.txt" if args.criteria == "iso_26514" else "github.txt"))
    writer_args.prompt_template = None if args.no_deps else template

    prompt = build_prompt(dep, writer_args)

    if args.raw:
        print(prompt)
        return 0

    print("=" * 78)
    print(f"ENTITY      {dep['qualified_name']}  (kind={dep['kind']})")
    print(f"BACKEND     {index.backend}")
    print(f"PATH        {dep['path']}")
    print(f"CRITERIA    {args.criteria}")
    print(f"TEMPLATE    {writer_args.prompt_template or '(none: IDE-style baseline prompt)'}")
    print(f"RELATIONS   {dep['relations'] or '(none)'}")
    print(f"POLYMORPHIC {dep['is_polymorphic']}")
    print(f"SOURCE      {len(dep['source_code'].splitlines())} lines")
    print(f"PROMPT      {len(prompt)} chars")
    print("=" * 78)
    print()
    print(prompt)
    if args.show_info:
        print()
        print("=" * 78)
        print(".info AUDIT RECORD")
        print("=" * 78)
        print(format_dep(dep, True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
