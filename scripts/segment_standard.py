"""Segment a standards document into clauses (stage 0 of criteria extraction).

Produces the clause inventory that every later stage depends on: each candidate
criterion is generated from exactly one clause, so it can quote its anchor, and
coverage can be counted.

Supported inputs
----------------
* ``.txt`` / ``.md`` — plain text or Markdown (an ISO PDF converted with any tool)
* ``.pdf``           — read directly with PyMuPDF
* ``.html`` / ``.htm`` — documentation sites such as a vendor style guide

Usage::

    python scripts/segment_standard.py --input standards/iso_26514.pdf --source iso_26514
    python scripts/segment_standard.py --input https://docs.github.com/... --source github_docs_style
    python scripts/segment_standard.py --input standards/notes.md --source iso_26514 --include-non-requirements
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.criteria.clauses import (  # noqa: E402
    segment_html,
    segment_pdf,
    segment_text,
    summarize,
)

STANDARDS_DIR = ROOT / "standards"


def fetch(url: str, tries: int = 4) -> str:
    """Fetch a URL with retries; this network resets connections intermittently."""
    last: Exception | None = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                return resp.read().decode("utf-8", "ignore")
        except Exception as exc:  # noqa: BLE001 - network layer
            last = exc
    raise RuntimeError(f"cannot fetch {url}: {last}")


def load(input_path: str, include_non_requirements: bool):
    lowered = input_path.lower()
    if lowered.startswith(("http://", "https://")):
        html = fetch(input_path)
        return segment_html(html, source="", locator=input_path,
                            include_non_requirements=include_non_requirements), input_path
    path = Path(input_path)
    if not path.exists():
        raise SystemExit(f"input not found: {path}")
    if path.suffix.lower() == ".pdf":
        return segment_pdf(str(path), source="", include_non_requirements=include_non_requirements), str(path)
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() in (".html", ".htm"):
        return segment_html(text, source="", locator=str(path),
                            include_non_requirements=include_non_requirements), str(path)
    return segment_text(text, source="", include_non_requirements=include_non_requirements), str(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--source", required=True, help="criterion-set id, e.g. iso_26514")
    ap.add_argument("--include-non-requirements", action="store_true",
                    help="also keep sentences without a directive verb (measures how much of "
                         "the document is not an assessable requirement)")
    ap.add_argument("--out-dir", default=str(STANDARDS_DIR))
    args = ap.parse_args()

    clauses, origin = load(args.input, args.include_non_requirements)
    # The segmenter is source-agnostic; stamp the requested source id here.
    for clause in clauses:
        clause.source = args.source
        clause.id = f"{args.source}:{clause.id.split(':', 1)[-1]}"

    summary = summarize(clauses)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{args.source}.clauses.json"
    json_path.write_text(
        json.dumps([c.to_dict() for c in clauses], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    md = [
        f"# Clause inventory: {args.source}",
        "",
        f"* origin: `{origin}`",
        f"* clauses: **{summary['n_clauses']}** (requirements: {summary['n_requirements']})",
        f"* sections: **{summary['n_sections']}**",
        "",
        "| section | requirements | total |",
        "|---|---|---|",
    ]
    for section, counts in summary["sections"].items():
        md.append(f"| {section[:70]} | {counts['requirements']} | {counts['total']} |")
    (out_dir / f"{args.source}.clauses.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"{json_path}")
    print(f"clauses={summary['n_clauses']} requirements={summary['n_requirements']} "
          f"sections={summary['n_sections']}")
    print("first clauses:")
    for clause in clauses[:5]:
        print(f"  [{clause.id}] ({clause.section[:28]}) {clause.text[:80]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
