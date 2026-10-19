# standards/ — source standards and their clause inventories

Working directory for stage 0 of criteria extraction. **Nothing here is
committed**: standards are copyrighted documents and the derived clause
inventories quote them verbatim.

## Convention

| file | produced by |
|---|---|
| `iso_26514.pdf` (or `.txt`/`.md`) | you supply the licensed document |
| `github_style_guide.clauses.json` | `scripts/segment_standard.py --input <url>` |
| `<source>.clauses.md` | section-level inventory produced alongside |

## Commands

```bash
# ISO/IEC/IEEE 26514 (drop the licensed PDF here first)
python scripts/segment_standard.py --input standards/iso_26514.pdf --source iso_26514

# GitHub docs style guide (public web pages)
python scripts/segment_standard.py \
  --input "https://docs.github.com/en/contributing/style-guide-and-content-model/style-guide" \
  --source github_docs_style
```

Each run writes `<source>.clauses.json` (one record per clause: id, section,
quoted text, locator, kind) and `<source>.clauses.md` (section inventory).

## Why this stage exists

Every criterion must be generated from exactly one clause so that it can quote its
anchor, so that coverage is countable, and so that re-running extraction is a fair
comparison. See `docs/DEPENDENCY_BACKENDS.md` for the same principle applied to the
dependency layer.
