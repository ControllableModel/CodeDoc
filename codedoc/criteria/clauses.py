"""Segment a standards document into individual requirement clauses.

Why segmentation is the foundation of the structured extraction
--------------------------------------------------------------
The published procedure pasted a whole standard into a model and accepted free
text. That makes three review questions unanswerable: which clause a criterion
came from, whether every clause was considered, and whether the result is
reproducible.

Segmentation fixes all three at the source: every candidate criterion is produced
from exactly one clause, so it can carry a quoted anchor, coverage is countable,
and re-running the extraction on the same clause set is a fair comparison.

Supported inputs: plain text / Markdown (ISO PDFs converted to text, or any
vendor style guide), HTML (documentation sites) and PDF (via PyMuPDF when
available).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from html.parser import HTMLParser
from typing import Iterable, List, Optional

#: Modal / directive verbs that mark an assessable requirement.
REQUIREMENT_PATTERN = re.compile(
    r"\b(must|shall|should|required?|mandatory|avoid|do not|don't|never|always|"
    r"use|prefer|ensure|include|provide)\b",
    re.IGNORECASE,
)

#: Heading markers recognised in text input (Markdown style).
_HEADING = re.compile(r"^(#{1,4})\s+(.*)$")

#: A sentence that *illustrates* a rule rather than stating one. GitHub's style
#: guide is full of "Use: …" / "Avoid: …" pairs; counting each pair as its own
#: clause inflates the inventory and hides that they belong to one rule.
EXAMPLE_PATTERN = re.compile(r"^(use|avoid|don't|do|example[s]?)\b\s*[:：]", re.IGNORECASE)

#: Clause numbering such as "5.2", "5.2.1", "A.3".
_NUMBERED = re.compile(r"^\s*(\d+(?:\.\d+)*|[A-Z]\.\d+(?:\.\d+)*)\s+\S")


@dataclass
class Clause:
    """One extractable unit of a standard."""

    id: str
    source: str
    section: str
    text: str
    #: Page or URL the clause came from — the anchor a criterion quotes.
    locator: str = ""
    kind: str = "requirement"
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def split_sentences(text: str) -> List[str]:
    """Split prose into sentences, tolerating abbreviations and list markers."""
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    # Split at sentence ends *and* before a leading clause number. Standards text
    # from a PDF frequently reads "… information product. 4.2 Documentation …";
    # without the numeric lookahead the two clauses merge into one.
    parts = re.split(r"(?<=[.!?:;])\s+(?=(?:[A-Z(\[]|\d+(?:\.\d+)*\s))", text)
    return [p.strip() for p in parts if p.strip()]


def _slug(section: str, index: int) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", section.lower()).strip("-") or "clause"
    return f"{base}-{index}"


def segment_text(
    text: str,
    source: str,
    locator_prefix: str = "",
    include_non_requirements: bool = False,
    min_chars: int = 25,
) -> List[Clause]:
    """Segment Markdown-like or plain standards text into clauses.

    A clause is one requirement-bearing sentence within one heading section. With
    ``include_non_requirements`` every sentence becomes a clause, which is useful
    for measuring how much of a standard is *not* an assessable requirement.
    """
    clauses: List[Clause] = []
    section = ""
    counter = 0
    buffer: List[str] = []
    locator = locator_prefix

    def flush() -> None:
        nonlocal counter, buffer
        if not buffer:
            return
        paragraph = " ".join(buffer).strip()
        buffer = []
        if len(paragraph) < min_chars:
            return
        for sentence in split_sentences(paragraph):
            if len(sentence) < min_chars:
                continue
            if EXAMPLE_PATTERN.match(sentence):
                # attach to the preceding clause instead of inventing a new one
                if clauses and clauses[-1].section == (section or "(preamble)"):
                    clauses[-1].extra.setdefault("examples", []).append(sentence)
                    continue
            is_requirement = bool(REQUIREMENT_PATTERN.search(sentence))
            if not is_requirement and not include_non_requirements:
                continue
            counter += 1
            clauses.append(
                Clause(
                    id=f"{source}:{_slug(section, counter)}",
                    source=source,
                    section=section or "(preamble)",
                    text=sentence,
                    locator=locator,
                    kind="requirement" if is_requirement else "guidance",
                )
            )

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        heading = _HEADING.match(line)
        numbered = _NUMBERED.match(line)
        if heading:
            flush()
            section = heading.group(2).strip()
            continue
        if (
            numbered
            and len(line) < 100
            and not line.rstrip().endswith((".", ":", ";", ","))
            and not REQUIREMENT_PATTERN.search(line)
        ):
            # A numbered *section title* in a PDF-to-text conversion. The length,
            # punctuation and directive-verb guards matter: without them numbered
            # requirement sentences such as "4.1 The documentation shall …" were
            # swallowed as headings and the clause inventory came out empty.
            flush()
            section = line.strip()
            continue
        if not line.strip():
            flush()
            continue
        if line.strip().startswith(("|", "---", "```")):
            continue
        buffer.append(line.strip())
    flush()
    return clauses


class _HtmlToText(HTMLParser):
    """Convert documentation HTML into Markdown-ish text with headings kept."""

    BLOCK = {"p", "div", "br", "li", "tr", "section", "article"}
    HEADINGS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####"}

    def __init__(self) -> None:
        super().__init__()
        self.out: List[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer"):
            self._skip += 1
        if tag in self.HEADINGS:
            self.out.append("\n\n" + self.HEADINGS[tag] + " ")
        elif tag in self.BLOCK:
            self.out.append("\n")
        elif tag == "li":
            self.out.append("\n- ")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer") and self._skip:
            self._skip -= 1
        if tag in self.HEADINGS or tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if self._skip:
            return
        text = data.strip()
        if text:
            self.out.append(text + " ")

    def text(self) -> str:
        joined = "".join(self.out)
        return re.sub(r"\n{3,}", "\n\n", joined)


def html_to_text(html: str) -> str:
    parser = _HtmlToText()
    parser.feed(html)
    return parser.text()


def segment_html(html: str, source: str, locator: str = "", **kwargs) -> List[Clause]:
    return segment_text(html_to_text(html), source, locator_prefix=locator, **kwargs)


def segment_pdf(path: str, source: str, **kwargs) -> List[Clause]:
    """Segment a PDF standards document (requires PyMuPDF)."""
    try:
        import fitz  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "PDF segmentation needs PyMuPDF (`import fitz`): " f"{exc}"
        ) from exc
    clauses: List[Clause] = []
    with fitz.open(path) as doc:
        for page_no, page in enumerate(doc, start=1):
            text = page.get_text("text")
            for clause in segment_text(text, source, **kwargs):
                clause.locator = f"{path}#page={page_no}"
                clauses.append(clause)
    for i, clause in enumerate(clauses, start=1):
        clause.id = f"{source}:clause-{i}"
    return clauses


def summarize(clauses: Iterable[Clause]) -> dict:
    """Section-level counts — the first audit table a reviewer expects."""
    by_section: dict = {}
    for clause in clauses:
        entry = by_section.setdefault(clause.section, {"requirements": 0, "total": 0})
        entry["total"] += 1
        if clause.kind == "requirement":
            entry["requirements"] += 1
    return {
        "n_clauses": sum(v["total"] for v in by_section.values()),
        "n_requirements": sum(v["requirements"] for v in by_section.values()),
        "n_sections": len(by_section),
        "sections": by_section,
    }
