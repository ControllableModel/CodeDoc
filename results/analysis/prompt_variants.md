# Prompt template variants: what each revision changed and what it bought

Four generations of the generation prompt are kept side by side in
`codedoc/writer/templates/`. Nothing was overwritten: `iso_26514.txt` / `github.txt` are v1,
and `*_v2/_v3/_v4.txt` are the revisions. Every measured artefact is preserved under
`outputs/matrix/` (v1), `outputs/tokenbench_v2/`, `outputs/tokenbench_v3/`,
`outputs/tokenbench_v4/`, with judged scores next to the documents and the aggregate reports
in `results/analysis/matrix_scores_v{2,3,4}.md`.

Corpus for the comparison: **ragflow, joblib, sonnet** — 158 documents per axis per variant.
Judge: `deepseek-chat` at temperature 0 for all variants, so the instrument is constant.

## 1. What each revision changed

| | v1 (shipped) | v2 | v3 | v4 |
|---|---|---|---|---|
| Sections | 12, all mandatory | 8–9, all conditional | v2 + Getting Started + Further Reading + Next Steps | v3 + mandatory `## Behaviour` |
| Empty sections | filled with "None"/boilerplate | omitted | omitted | omitted |
| Length | unbounded (measured 714 words/doc) | 120–250 / 250–450 words | 150–300 / 300–500 | 250–400 / 500–700 |
| Content type | mixed (concept + reference + procedure + troubleshooting) | declared: Reference | declared: Reference | declared: Reference |
| Structured data | prose | tables | tables | tables |
| Section order | prerequisites after example, troubleshooting mid-document | reader order | reader order | reader order |
| Overview | `About` + `Description` prose | 1–2 sentences | 2–4 sentences | 3 short paragraphs (conceptual carrier) |
| Errors | "Troubleshooting" prose | `## Errors` table | `## Errors` table | `## Errors` table |
| Facts coverage | implicit | 5-item rule in the rules block | same | **mandatory `## Behaviour`, five labelled lines** |
| Mechanical evidence in prompt | none | signature + return paths + raise statements | same | same |

The evidence block is the one change no section list could substitute for: return paths and
raise statements are extracted from the AST (`codedoc/deps/signals.py`) rather than inferred.
On ragflow, 28 of 38 entities have at least one return path and 9 raise at least one
exception, which is exactly the material `Completeness` and `Error Reference` ask about.

## 2. Scores, three repositories, mean over ragflow + joblib + sonnet

| axis | v1 | v2 (ragflow only) | v3 | **v4** |
|---|---|---|---|---|
| ISO/IEC 26514 (14 entity-level dims) | 4.757 | 4.87 | 4.722 | **4.777** |
| GitHub docs style (18 dims) | 3.360 | 2.99 | 3.482 | **3.707** |

Per repository:

| repo | ISO v1 | ISO v3 | ISO v4 | GitHub v1 | GitHub v3 | GitHub v4 |
|---|---|---|---|---|---|---|
| ragflow | 4.808 | 4.844 | **4.880** | 3.326 | 3.547 | **3.806** |
| joblib | **4.727** | 4.617 | 4.713 | 3.415 | 3.469 | **3.723** |
| sonnet | 4.735 | 4.706 | **4.737** | 3.338 | 3.430 | **3.593** |

## 3. Which dimensions moved, and why

ISO, mean over the three repositories, v1 → v3 → v4:

| dimension | v1 | v3 | v4 | verdict |
|---|---|---|---|---|
| Translation-Friendly | 4.59 | 4.70 | **4.75** | +0.16 |
| Conciseness | 4.01 | 4.48 | **4.15** | +0.15 |
| User-Centered Design | 4.10 | 4.19 | **4.23** | +0.13 |
| Metadata | 4.88 | 4.97 | **4.98** | +0.09 |
| Correctness | 4.75 | 4.64 | 4.76 | flat |
| Completeness | 4.58 | 4.19 | 4.51 | **−0.07, was −0.39** |
| Comprehensibility | 4.86 | 4.55 | 4.74 | −0.12 |

The v2 experiment is why v4 exists. v2 removed every mandatory section and gained
**Conciseness 4.00 → 4.92**, but lost **Completeness 4.82 → 4.58** and, on the GitHub axis,
lost `Further Reading` 5.00 → 1.00 and `Next Steps` 4.24 → 1.34. The sections v1 was blamed
for were not redundant in the judge's eyes: they were the carriers of the GitHub content
families. v3 restored them as short, conditional sections and recovered most of it; v4 then
bought Completeness back by making the five fact families a mandatory section instead of a
rule the model could skip.

GitHub, mean over the three repositories, v1 → v3 → v4:

| dimension | v1 | v3 | v4 | verdict |
|---|---|---|---|---|
| Content Type Consistency | 2.38 | 4.38 | **4.68** | **+2.30** |
| Prerequisites Standards | 2.89 | 4.05 | **4.45** | +1.56 |
| Content Order | 3.26 | 4.30 | **4.65** | +1.39 |
| Title Standards | 3.58 | 4.85 | **4.88** | +1.29 |
| Reference Content | 3.69 | 4.85 | **4.97** | +1.28 |
| Introduction Standards | 3.79 | 4.63 | **4.79** | +1.00 |
| Category Title Naming | 2.05 | 2.93 | **3.02** | +0.96 |
| Balanced Hierarchy | 3.94 | 4.43 | **4.77** | +0.82 |
| Reuse Instead of Copying | 3.23 | 3.68 | **3.86** | +0.63 |
| Error Reference Content | 1.72 | 1.82 | **2.06** | +0.35 |
| Getting Started Content | 3.51 | 3.04 | **3.76** | +0.25 |
| Further Reading Standards | 4.98 | 3.46 | 4.35 | −0.63 |
| Permission Declaration | 2.86 | 2.18 | 1.58 | −1.28 |
| Tutorial Content | 2.58 | 1.02 | 1.01 | −1.57 |
| Conceptual Content | 3.69 | 1.03 | 1.04 | −2.65 |

The top six gains are the structural criteria: declaring one content type, ordering sections
for a reader, tabulating reference material, and keeping titles short. Those are exactly the
criteria a prompt can control.

## 4. Three dimensions the prompt cannot win, and why

`Conceptual Content` (3.69 → 1.04), `Tutorial Content` (2.58 → 1.01) and, partially,
`Further Reading` (4.98 → 4.35) are **document-set criteria**: they ask whether the
documentation set contains a conceptual article or a tutorial, not whether one entity page
explains its subject conceptually. v1 scored 3.69 on `Conceptual` only because its long
`About` + `Description` prose happened to read like one; v4 has three explanatory paragraphs
in `Overview` and still scores 1.04, which is the clearer signal. This is the evaluation-unit
mismatch the paper argues about, showing up in our own measurements.

`Permission Declaration` fell because v1 carried a bulleted "Access: Permissions needed"
line in a fixed prerequisites list; v4 mentions permissions inside a prose prerequisites
sentence. Restoring it as its own metadata line is a v5-sized change with a ceiling of about
+1.0 on one document-set criterion.

## 5. Cost and latency, measured on ragflow (38 entities, one axis)

Tokens come from `usage.prompt_tokens` / `usage.completion_tokens` for CodeDoc, from
RepoAgent's own `LLM Prompt Tokens` / `LLM Completion Tokens` debug log, and from
MemDocAgent's `analytics_<repo>.json`.

| method | calls / entity | input tok / entity | output tok / entity | out/in | wall clock | cost |
|---|---|---|---|---|---|---|
| CodeDoc v1 | 1.1 | 1,509 | 1,346 | 0.89 | 137 s | $0.05 |
| CodeDoc v3 | 1.0 | ~1,750 | ~1,050 | 0.60 | 89 s | $0.06 |
| **CodeDoc v4** | **1.0** | **2,214** | **1,615** | **0.73** | **88 s** | **$0.07** |
| RepoAgent | 0.9 | 1,610 | 700 | 0.43 | ~90 s | n/a |
| MemDocAgent | **6.1** | **44,685** | **3,128** | **0.07** | **1,735 s** | $0.206 |

MemDocAgent's own action breakdown for that run:

```
Read    in 384,129  out 19,067
Write   in 345,007  out 47,469
Verify  in 380,396  out 19,569     <- self-verification alone costs 380k input tokens
```

The comparison that matters: **MemDocAgent spends 44,685 input tokens and 6.1 calls per
entity to produce 3,128 output tokens; CodeDoc v4 spends 2,214 input tokens in 1.0 call to
produce 1,615.** That is 20× the input and 6× the calls for 2× the output, and 20× the wall
clock. Whatever a multi-turn agentic loop buys in prose richness, it pays for it in retrieval
that this pipeline front-loads once, statically.

v4 costs more input than v1 (+47%) because the template is longer and the evidence block is
new; it produces more output than v3 (+54%) because the mandatory Behaviour section is
where Completeness is bought back. Both are wanted: the rubric rewards the facts, not the
silence.

## 6. What to ship

**v4 on both axes.** It is the only revision that beats v1 on both rubrics simultaneously
(ISO +0.02, GitHub +0.35), and the ISO margin is within noise while the GitHub margin is not.
v2 and v3 are kept because they document the trade-off: removing structure raises
Conciseness and destroys the content families; restoring the families costs Conciseness and
buys back far more.


## 7. v5: the rubric is anchored on section names

v4 lost three GitHub criteria that v1 held, and the judge's own evidence strings say why. It
was not the prose. v2 had renamed the sections:

```
v4, Conceptual Content, score 1.04:
  "Not applicable; the document is reference content, not conceptual.
   No 'About [topic]' section is present."

v1, Conceptual Content, score 3.70:
  "The 'About' section begins with 'About' and explains the purpose and use cases of the class"
```

`github.txt` (v1) emits `## About`, `## Quick Start` and `## Permissions & Access` -- the section
names GitHub's style guide uses. v2-v4 replaced them with house-style names (`## Overview`,
`## Getting Started`) and folded permissions into prose. The judge scores the criterion by
recognising the section, so a better-written section under a different heading scores lower.

The second finding is about absence. v4 scored `Error Reference` as a bimodal distribution --
25 documents at 5, 106 at 1 -- because it omitted the section when the source raised nothing.
The judge reads an absent section as missing content, not as "not applicable". v1 never hit
that floor because it always wrote a Troubleshooting paragraph.

v5 therefore changes exactly two things and nothing else:

1. `## Overview` -> `## About`, `## Getting Started` -> `## Quick Start`, and
   `## Permissions & Access` is restored as its own section.
2. `## Errors` and `## Permissions & Access` are never omitted; when the source raises nothing
   the section says so in one line.

Effect over the three repositories:

| dimension (GitHub) | v1 | v4 | **v5** |
|---|---|---|---|
| Permission Declaration | 2.86 | 1.58 | **4.14** |
| Conceptual Content | 3.69 | 1.04 | **3.42** |
| Error Reference | 1.72 | 2.06 | **4.33** |
| Process Content | 4.02 | 4.01 | **4.56** |
| Product Label Standards | 3.91 | 4.40 | **4.81** |
| Content Type Consistency | 2.38 | 4.68 | **4.97** |
| Content Order | 3.26 | 4.65 | **4.91** |
| Prerequisites Standards | 2.89 | 4.45 | 3.89 |
| Getting Started Content | 3.51 | 3.76 | 3.04 |
| Tutorial Content | 2.58 | 1.01 | 1.05 |

Totals:

| axis | v1 | v4 | **v5** |
|---|---|---|---|
| ISO/IEC 26514 (14 dims) | 4.757 | 4.777 | **4.772** |
| GitHub docs style (18 dims) | 3.360 | 3.707 | **4.187** |

The ISO axis is flat (-0.004, inside noise) and its only movement is Conciseness 4.15 -> 4.07,
the price of always emitting the Errors section. The GitHub axis gains **+0.48** over v4 and
**+0.83** over v1.

Two regressions come from the same rename. `Prerequisites Standards` and `Getting Started`
fall because v4 carried an explicit `**Prerequisites**` label inside Getting Started that v5's
Quick Start paragraph does not; a `## Prerequisites` section of its own is the obvious v6 fix,
worth roughly +0.5 on each. `Tutorial Content` stays at 1.05 despite the Quick Start heading
because the Metadata declares `Content Type: Reference` and the judge reads the declaration
before the section: the same declaration that lifts Content Type Consistency to 4.97 caps
Tutorial Content at the floor. That trade is worth taking -- +2.59 on Content Type Consistency
against a criterion no entity-level document can satisfy anyway.

## 8. Cost of the revisions

Measured on ragflow (38 entities, ISO axis, one call per entity):

| revision | calls | input tok | output tok | per-call in | per-call out | wall | cost |
|---|---|---|---|---|---|---|---|
| v1 | 42 | 57,325 | 51,137 | 1,509 | 1,346 | 137 s | $0.05 |
| v4 | 38 | 84,133 | 61,386 | 2,214 | 1,615 | 88 s | $0.07 |
| v5 | 39 | 88,769 | 59,486 | 2,276 | 1,525 | 160 s | $0.08 |

The template grew from 4.1 KB to 7.4 KB and the evidence block is new, which is most of the
+51% input. The output is stable: the mandatory Behaviour and Errors sections buy facts, not
length. Against MemDocAgent's 44,685 input tokens and 6.1 calls per entity for 3,128 output
tokens, v5 still spends 20x less input and 6x fewer calls.


## 9. v6: a section of its own for Prerequisites

v5 renamed Getting Started to Quick Start and, in doing so, dropped the `**Prerequisites**`
label that v4 had carried inside it. Two criteria fell: Prerequisites Standards 4.45 -> 3.89
and Getting Started 3.76 -> 3.04. v6 adds a `## Prerequisites` section of its own, placed
before Quick Start, always emitted, and changes nothing else.

| dimension (GitHub) | v1 | v4 | v5 | **v6** |
|---|---|---|---|---|
| Prerequisites Standards | 2.89 | 4.45 | 3.89 | **4.97** |
| Permission Declaration | 2.86 | 1.58 | 4.14 | **4.25** |
| Category Title Naming | 2.05 | 3.02 | 3.22 | **3.30** |
| Conceptual Content | 3.69 | 1.04 | 3.42 | **3.49** |
| Getting Started Content | 3.51 | 3.76 | 3.04 | 3.09 |
| Process Content | 4.02 | 4.01 | 4.56 | 4.49 |
| Error Reference | 1.72 | 2.06 | 4.33 | 4.26 |

`Prerequisites Standards` recovers **+1.08** over v5 and lands at 4.97, the highest of any
revision. The cost is small and lands where expected: ISO Conciseness 4.07 -> 4.04 and
User-Centered Design 4.19 -> 4.10, because every document now carries a prerequisites block
even when it needs none.

Totals:

| axis | v1 | v4 | v5 | **v6** |
|---|---|---|---|---|
| ISO/IEC 26514 (14 dims) | 4.757 | 4.777 | 4.772 | **4.773** |
| GitHub docs style (18 dims) | 3.360 | 3.707 | 4.187 | **4.267** |

Token and latency on ragflow (38 entities, ISO axis):

| revision | calls | input tok | output tok | per-call in | per-call out | wall | cost |
|---|---|---|---|---|---|---|---|
| v1 | 42 | 57,325 | 51,137 | 1,509 | 1,346 | 137 s | $0.05 |
| v4 | 38 | 84,133 | 61,386 | 2,214 | 1,615 | 88 s | $0.07 |
| v5 | 39 | 88,769 | 59,486 | 2,276 | 1,525 | 160 s | $0.08 |
| v6 | 39 | 92,911 | 63,085 | 2,382 | 1,618 | 147 s | $0.08 |

## 10. Where the sequence ends

v6 is the last revision worth making. What is left is not prompt-shaped:

* **ISO Content Quality** (4.63 against RepoAgent 4.76) is the only main dimension we trail.
  Its three components are Conciseness 4.04 vs 4.32, Completeness 4.59 vs 4.80 and
  Correctness 4.76 vs 4.92. Every attempt to move them by prompt has traded one for the
  other: v2 bought Conciseness +0.92 and paid Completeness -0.39; v6 buys Completeness
  +0.05 and pays Conciseness -0.03. The remaining gap is a word-budget question, not a
  template question, and the honest reading is that a single-document-per-entity format
  with a fixed section set will not out-write a per-file narrative on "completeness" as a
  judge perceives it.
* **GitHub Tutorial Content** sits at 1.12 against 1.01 for every baseline, i.e. at the
  floor for everyone. The Metadata declares `Content Type: Reference`, and the judge reads
  the declaration before the section; the same declaration is worth +2.59 on Content Type
  Consistency. Six revisions is enough evidence that this is a definitional conflict
  between two criteria, not a defect in the prompt.
* **Getting Started Content** (3.09 against v1's 3.51) is the one remaining regression. v1's
  `Example Usage` with prose commentary satisfied it more than v6's numbered steps do. It is
  worth about +0.4 on a single document-set criterion; the fix would be to restore a worked
  example with narrative, at some cost to Conciseness.

The measurement lesson belongs in the paper's threats-to-validity section: **an LLM judge
scores a criterion by recognising its section name and reads omission as absence.** Between
v4 and v5 nothing changed except three headings and a rule that two sections are never
omitted, and the GitHub axis moved +0.48. Any evaluation that compares generated
documentation across tools without controlling for section naming is measuring the naming.
