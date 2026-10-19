# Paper rubric vs artifact rubric: the ISO and GitHub criteria sets

Checked against `_TSE_2026_Code_Document/tables/standards.tex` and
`sections/methodology.tex`, and against the archived per-dimension scores.

## 1. What the paper says

| claim | location |
|---|---|
| "the final ISO rubric contains **7 categories and 14 dimensions**" | `methodology.tex` §Phase (a) |
| "the final GitHub rubric contains **5 categories and 12 dimensions**" | `methodology.tex` §Phase (a) |
| `tab:iso_dimensions` and `tab:github_dimensions` "list both rubrics" — described as **the full rubrics** | `experiment_revised.tex` §Evaluation rubric |
| ISO standards "cover **correctness, completeness, consistency**, modular organisation, maintainability, **accessibility**, internationalisation, safety, and update discipline" | `methodology.tex` §Source standards |

## 2. What the artifact and the archived data contain

| set | artifact (full) | archived judge output | paper table |
|---|---|---|---|
| ISO | **26 dimensions / 8 categories** | **26 dimensions** (all present) | 14 / 7 |
| GitHub | **18 dimensions / 5 categories** | **18 dimensions** (all present) | 12 / 5 |

The per-dimension scores behind the published numbers (224 non-empty
`*quality*.jsonl` files) key on **all 26 ISO and all 18 GitHub dimensions**. So the
printed tables are a **subset of the measurement rubric**, not the rubric itself.

## 3. The 12 ISO dimensions measured but not printed

`Correctness`, `Consistency`, `Comprehensibility`, `Completeness`,
`Structured by Function`, `Illustrations and Media`, `Multi-modal Support`,
`Device Independence`, `Accessibility Features`, `User-Centered Design`,
`Testing and Feedback`, `Version Control`.

**This is the most damaging part of the discrepancy**, because:

1. `methodology.tex` explicitly advertises correctness, completeness, consistency and
   accessibility as covered by the ISO rubric — **none of the four appears in the
   printed table**, and the "Accessibility" category is absent from it entirely.
2. They are the dimensions most relevant to code-level documentation. The printed
   table instead shows `Legibility` ("font size and color contrast"), `Space
   Consideration` ("reserve space for text expansion"), `Search and Indexing`,
   `Legal and Copyright`, `Change Log` — all document-set properties. A reviewer
   complaining that "the dimensions are not specific to code" (§R1-10) reads this
   table as *evidence*.

## 4. The 6 GitHub dimensions measured but not printed

`Content Type Consistency`, `Reuse Instead of Copying`, `Balanced Hierarchy`,
`Content Order`, `Introduction Standards`, `Product Label Standards`.

The other 12 match the paper exactly.

## 5. A deeper problem with the GitHub axis

All 18 GitHub dimensions are **document-set level** in the artifact's classification,
so **0 of 12** printed GitHub dimensions can be judged on a single entity. Running the
entity-level judging path with `github_docs_style` yields *no criteria*, yet
`experiment_revised.tex` reports GitHub rubric scores per generated entity.

Two coherent readings, and the paper must pick one:

* **document-set reading** — the GitHub axis scores *assembled file-level documents*
  (our pipeline already emits one `.md` per source file). Then the rubric applies, and
  the evaluation unit must be stated as "file-level document set", not "entity".
* **entity reading** — the GitHub axis is not applicable at entity level at all, and
  reporting it as such was a unit-of-analysis error.

## 6. What was changed in the artifact

The artifact now reproduces both printed tables **exactly** and keeps the full sets:

| field | meaning |
|---|---|
| `in_paper_table` | dimension appears in the printed table (ISO 14, GitHub 12) |
| `paper_category` | category **as printed** (the tables regroup: paper uses `i18n & Localization` and `Usability & UX`, and GitHub's `Further Reading` row does not exist as a category in the full set) |
| `paper_name` | printed label where it differs from the judge variable (`Interactive Element Representation` vs `Representation of Interactive Elements`, `Translation Friendly` vs `Translation-Friendly`) |
| `CriterionSet.table_label()` / `in_paper_table()` | reproduce the printed table row by row |

Judge variable names were deliberately **not** renamed: the archived scores are keyed by
them, so renaming would break comparability with the published data.

Verified: `iso_26514` 14/14 and `github_docs_style` 12/12 reproduce the paper's tables
row for row, while the full sets remain 26 and 18.

Also fixed: the GitHub criteria set shipped with **empty definitions** (the recovered
definitions file only covers ISO dimensions), so the judge prompt read
`- Title Standards:` with nothing after the colon. All 18 GitHub dimensions now carry
the paper's Table 3 descriptions.

## 7. Recommendation for the resubmission

1. **Print the full rubrics** (26 ISO / 18 GitHub) in the appendix and keep the 14/12
   as a *primary subset* with an explicit note — the tables currently under-describe the
   measurement, and the omitted ISO dimensions are precisely the ones the review says
   are missing.
2. **Fix the `Source standards` sentence** in `methodology.tex` so it does not claim
   dimensions the rubric does not print.
3. **Declare the evaluation unit per axis**: entity-level for the ISO entity-applicable
   subset and the practice axis; file-level document set for the GitHub axis and the
   document-set ISO dimensions. This also converts the R1-10 criticism into a measured
   finding (the applicability audit in `results/analysis/cost_benchmark.md` §8 already
   quantifies what non-applicable pairs cost when left in the aggregate).
4. Keep reporting both columns (full set / printed subset) so the earlier numbers stay
   audit-able.

## 8. Open question for the team

The archived files cannot regenerate the reported aggregates: computing repository
means over the 26-dimension set and over the 14-dimension table gives different values,
and **neither matches the published 3.72/3.79 (ISO) and 3.68/3.74 (GitHub)** for the
same repositories. Either the published numbers came from a run whose raw scores are not
in the repository, or they were aggregated with a rule that is not written down. This
needs to be resolved before the resubmission claims reproducibility.
