# ISO-based documentation criteria

This document collects **every ISO-oriented criterion artifact that exists in this
repository**, states where each one comes from, and marks explicitly what could not be
recovered. Nothing here is paraphrased from memory: each item cites the file it was extracted
from.

> **Why this file exists.** The manuscript refers to a criterion set `Q` in several places and
> promises its full listing (including the 1–5 scoring anchors and a clause-to-dimension
> traceability table) in supplementary material. That material was not shipped with the
> submission. This file is the machine-checkable part of that promise; the remaining gaps are
> listed in §6.

---

## 1. The two roles of `Q`

The same criterion set is used twice:

| Role | Where it enters the pipeline | Artifact |
|---|---|---|
| **Generation** (Phase (b), Stage 2) | The criteria are embedded in the generation prompt, which also prescribes the required output structure. | `prompts/ISO.txt` |
| **Evaluation** (LLM-as-a-judge) | One judge call per dimension; the judge returns a score and textual evidence. | `5Score/`, `3Score/` |

## 2. Generation-time criteria — 8 categories / 26 requirement-level items

Verbatim from [`prompts/ISO.txt`](../prompts/ISO.txt) (heading: *"ISO Documentation Standards
(8 Dimensions, 26 Requirements)"*), and declared there as following **ISO/IEC 26514** and
**ISO/IEC 82079**.

| # | Category | Requirement-level items |
|---|---|---|
| 1 | Content Quality | Correctness; Consistency; Comprehensibility; Conciseness; Completeness |
| 2 | Information Structure | Modularity; Structured by Function; Navigability; Metadata |
| 3 | Format & Presentation | Consistent Format; Legibility; Illustrations & Media; Interactive Elements |
| 4 | Accessibility | Multi-modal Support; Device Independence; Accessibility Features |
| 5 | Internationalization & Localization | Cultural Neutrality; Translation-Friendly; Space Consideration |
| 6 | Usability & User Experience | User-Centered Design; Testing & Feedback; Search & Indexing |
| 7 | Safety & Compliance | Safety Information; Legal & Copyright |
| 8 | Maintenance & Updates | Version Control; Change Log |

These 26 items are exactly the 26 dimensions scored under the three-level protocol in
`3Score/` (§5).

## 3. The evaluation rubric reported in the paper — 7 categories / 14 dimensions

This is the reduced rubric used for the reported quality scores (source: the manuscript's
rubric table, reproduced here so the criteria are readable from the artifact alone).

| Category | Dimension | Definition |
|---|---|---|
| Content Quality | Conciseness | Avoid redundancy and repetition, and include only necessary information. |
| Content Quality | Legibility | Font size and color contrast should be suitable for the reading environment. |
| Information Structure | Modularity | Content should be divided into independent, reusable topics. |
| Information Structure | Navigability | Provide table of contents, index, and search functionality. |
| Information Structure | Metadata | Each topic should include metadata for content management and retrieval. |
| Format & Presentation | Consistent Format | Use unified style guides, including fonts, colors, icons, and warning formats. |
| Format & Presentation | Interactive Element Representation | Use consistent graphics or formats to represent keyboard shortcuts. |
| i18n & Localization | Cultural Neutrality | Avoid culture-specific examples, humor, or images. |
| i18n & Localization | Translation Friendly | Use simple sentences and consistent terminology. |
| i18n & Localization | Space Consideration | Reserve space for text expansion in different languages. |
| Usability & UX | Search and Indexing | Provide full-text search, Boolean search, and filtering functions. |
| Safety & Compliance | Safety Information | Danger, warning, and caution information should be prominent. |
| Safety & Compliance | Legal and Copyright | Include copyright notices, trademark information, and license terms. |
| Maintenance & Updates | Change Log | Clearly identify new or modified content, and provide update notes. |

## 4. Judge-facing definitions — 18 dimensions recovered verbatim

The archived judging transcripts in `5Score/` contain the **exact per-dimension definitions
that were sent to the judge**, in the sentence pattern
`"A good document should have the quality of <dimension>, which means to <definition>."`

The table below is extracted mechanically into
[`results/judge_criteria_recovered.json`](../results/judge_criteria_recovered.json)
(source column = the log the definition was recovered from).

| Dimension (judge variable) | Definition sent to the judge |
|---|---|
| Metadata | Each topic should include metadata (e.g., audience, product version, information type) to facilitate content management and retrieval. |
| Consistent Format | Uses a unified style guide (fonts, colors, icons, warning formats, etc.); maintains consistent formatting for both print and electronic documents. |
| Legibility | Font size and color contrast are suitable for the reading environment; avoids all-caps text, excessive italics, or underlining. |
| Illustrations and Media | Graphics should be clear and consistent, placed adjacent to relevant text; avoids culturally sensitive images; videos and animations should be brief and have control options. |
| Representation of Interactive Elements | Uses consistent graphics or formats to represent keyboard shortcuts, mouse actions, touch gestures, etc.; uses symbols or graphics to distinguish literal values from variables. |
| Multi-modal Support | Provides text alternatives for non-text content (images, videos, audio); supports screen readers, high-contrast modes, etc. |
| Device Independence | Avoids dependencies on specific devices (e.g., 'click the green button'); provides instructions for multiple operation methods (keyboard, voice, touch, etc.). |
| Accessibility Features | Clearly explains the software's accessibility features and how to use them. |
| Cultural Neutrality | Avoids culture-specific examples, humor, and images; uses internationally recognized date, currency, and measurement unit formats. |
| Translation-Friendly | Uses simple sentences, consistent terminology, and avoids abbreviations and slang; text in graphics should be separable to facilitate translation. |
| Space Consideration | Reserves space for text expansion (e.g., German and Finnish text is typically longer than English). |
| User-Centered Design | Designs content based on user tasks and roles; provides context-sensitive help. |
| Testing and Feedback | Conducts usability testing to ensure information is easy to find, use, and understand; collects user feedback for continuous improvement. |
| Search and Indexing | Provides full-text search, Boolean search, and filtering capabilities; indexes should include synonyms and user-friendly terms. |
| Safety Information | Safety information (e.g., danger, warning, caution) should be prominent and consistent; uses standard signal words (Danger, Warning, Caution). |
| Legal and Copyright | Includes copyright notices, trademark information, and license terms; complies with relevant laws and regulations (e.g., Section 508, ISO standards). |
| Version Control | Documentation should be updated in sync with software versions; uses configuration management (CM) systems to manage changes. |
| Change Log | Clearly identifies new or modified content; provides release notes and compatibility information. |

## 5. Scoring scales and anchors

Two judge protocols exist in this repository. Both are documented here exactly as the
archived artifacts define them.

**Three-level protocol (`3Score/`)** — categorical labels, observed value set
`bad` | `good` | `excellent` (e.g. `DOTquality_mul_Eval.jsonl`: 13 `good`, 10 `bad`,
3 `excellent`). The label semantics are not defined in the archived prompts.

**1–5 protocol (`5Score/`)** — integer scores. The judge prompt states the scale endpoints
verbatim:

> *"you can choose from 1 score(Not Mention) to 5 score (excellent)"*

So the **only anchored points are the endpoints**:

| Score | Anchor (as documented) |
|---|---|
| 1 | Not mentioned |
| 5 | Excellent |
| 2, 3, 4 | **Not defined in the archived artifacts** (see §6) |

Observed values in `5Score/DOTquality_mul_Eval.jsonl`: `1`×1, `2`×6, `3`×6, `4`×6
(the log file is truncated mid-stream, so it does not contain the full score distribution).

## 6. Known gaps (to be closed before resubmission)

These are stated plainly rather than papered over:

1. **Intermediate anchors (2–4) are not defined anywhere in the artifacts.** Only
   "1 = not mentioned" and "5 = excellent" were ever specified to the judge. Any published
   anchor table for scores 2–4 must be authored and re-validated, not described as "used in
   the reported experiments".
2. **The clause-to-dimension traceability table does not exist in this repository.** The
   generation prompt names ISO/IEC 26514 and ISO/IEC 82079 but does not map individual
   clauses to dimensions. A genuine traceability table requires working from the standard
   text clause by clause.
3. **The 14-dimension reportable rubric vs. the 26 requirement-level items.** The 26 items
   are what the generation prompt and the 3-level judging use; the reported 1–5 scores use
   the 14-dimension rubric. The exact reduction (26 → 14) is not recorded as an artifact and
   must be reconstructed and documented.
4. **Recovered definitions cover the ISO rubric only.** No GitHub-named dimension prompt was
   found in the archived logs — see [`CRITERIA_GITHUB.md`](CRITERIA_GITHUB.md) §3.
