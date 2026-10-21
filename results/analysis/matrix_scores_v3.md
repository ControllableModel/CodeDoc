# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 158 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 4.705
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Format & Presentation | 2 | 2 | 4.918 | 4.918 | 316 |
| Information Structure | 4 | 4 | 4.878 | 4.878 | 632 |
| Internationalization & Localization | 2 | 2 | 4.838 | 4.839 | 316 |
| Content Quality | 5 | 5 | 4.538 | 4.538 | 790 |
| Usability & User Experience | 1 | 1 | 4.158 | 4.158 | 158 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Consistency | 158 | 4.962 | 0.191 |
| Content Quality | Correctness | 158 | 4.614 | 0.5 |
| Content Quality | Comprehensibility | 158 | 4.519 | 0.512 |
| Content Quality | Conciseness | 158 | 4.468 | 0.512 |
| Content Quality | Completeness | 158 | 4.127 | 0.809 |
| Format & Presentation | Legibility | 158 | 4.981 | 0.136 |
| Format & Presentation | Consistent Format | 158 | 4.854 | 0.353 |
| Information Structure | Metadata | 158 | 4.968 | 0.175 |
| Information Structure | Navigability | 158 | 4.867 | 0.339 |
| Information Structure | Structured by Function | 158 | 4.854 | 0.353 |
| Information Structure | Modularity | 158 | 4.823 | 0.382 |
| Internationalization & Localization | Cultural Neutrality | 158 | 5.0 | - |
| Internationalization & Localization | Translation-Friendly | 158 | 4.677 | 0.468 |
| Usability & User Experience | User-Centered Design | 158 | 4.158 | 0.546 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| joblib | 840 | 4.617 |
| ragflow | 532 | 4.844 |
| sonnet | 840 | 4.706 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 728 | 4.54 |
| function | 434 | 4.77 |
| method | 1050 | 4.793 |

## github_docs_style (GitHub docs style)

* documents judged: 158 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 3.473

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 2 | 2 | 3.99 | 3.991 | 316 |
| Styling & Formatting | 4 | 4 | 3.987 | 3.987 | 632 |
| Structure & Organization | 3 | 3 | 3.863 | 3.863 | 474 |
| Content Types & Completeness | 4 | 4 | 3.805 | 3.805 | 632 |
| Article Content Families | 5 | 5 | 2.354 | 2.354 | 790 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Reference Content | 158 | 4.835 | 0.387 |
| Article Content Families | Getting Started Content Guidelines | 158 | 3.076 | 0.875 |
| Article Content Families | Error Reference Content Guidelines | 158 | 1.804 | 1.456 |
| Article Content Families | Conceptual Content Guidelines | 158 | 1.032 | 0.237 |
| Article Content Families | Tutorial Content Guidelines | 158 | 1.025 | 0.157 |
| Content Quality | Content Type Consistency | 158 | 4.329 | 0.533 |
| Content Quality | Reuse Instead of Copying | 158 | 3.652 | 0.605 |
| Content Types & Completeness | Prerequisites Standards | 158 | 4.082 | 1.037 |
| Content Types & Completeness | Next Steps Standards | 158 | 3.987 | 0.646 |
| Content Types & Completeness | Process Content Standards | 158 | 3.715 | 0.872 |
| Content Types & Completeness | Further Reading Standards | 158 | 3.437 | 0.61 |
| Structure & Organization | Balanced Hierarchy | 158 | 4.399 | 0.49 |
| Structure & Organization | Content Order | 158 | 4.259 | 0.505 |
| Structure & Organization | Category Title Naming | 158 | 2.93 | 0.34 |
| Styling & Formatting | Title Standards | 158 | 4.842 | 0.382 |
| Styling & Formatting | Introduction Standards | 158 | 4.589 | 0.492 |
| Styling & Formatting | Product Label Standards | 158 | 4.316 | 0.541 |
| Styling & Formatting | Permission Declaration Standards | 158 | 2.203 | 1.267 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| joblib | 1080 | 3.469 |
| ragflow | 684 | 3.547 |
| sonnet | 1080 | 3.43 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 936 | 3.473 |
| function | 558 | 3.43 |
| method | 1350 | 3.49 |

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 158 | 14 | 4.705 | 5 |
| github_docs_style | 158 | 18 | 3.473 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| joblib | 4.617 | 3.469 |
| ragflow | 4.844 | 3.547 |
| sonnet | 4.706 | 3.43 |

