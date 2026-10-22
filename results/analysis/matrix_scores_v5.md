# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 158 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 4.762
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Information Structure | 4 | 4 | 4.953 | 4.953 | 632 |
| Format & Presentation | 2 | 2 | 4.952 | 4.953 | 316 |
| Internationalization & Localization | 2 | 2 | 4.877 | 4.877 | 316 |
| Content Quality | 5 | 5 | 4.605 | 4.605 | 790 |
| Usability & User Experience | 1 | 1 | 4.171 | 4.171 | 158 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Consistency | 158 | 4.981 | 0.177 |
| Content Quality | Correctness | 158 | 4.747 | 0.435 |
| Content Quality | Comprehensibility | 158 | 4.734 | 0.442 |
| Content Quality | Completeness | 158 | 4.5 | 0.777 |
| Content Quality | Conciseness | 158 | 4.063 | 0.332 |
| Format & Presentation | Legibility | 158 | 4.994 | 0.079 |
| Format & Presentation | Consistent Format | 158 | 4.911 | 0.284 |
| Information Structure | Metadata | 158 | 4.994 | 0.079 |
| Information Structure | Navigability | 158 | 4.943 | 0.232 |
| Information Structure | Modularity | 158 | 4.937 | 0.243 |
| Information Structure | Structured by Function | 158 | 4.937 | 0.243 |
| Internationalization & Localization | Cultural Neutrality | 158 | 5.0 | - |
| Internationalization & Localization | Translation-Friendly | 158 | 4.753 | 0.431 |
| Usability & User Experience | User-Centered Design | 158 | 4.171 | 0.467 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| joblib | 840 | 4.732 |
| ragflow | 532 | 4.848 |
| sonnet | 840 | 4.737 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 728 | 4.57 |
| function | 434 | 4.853 |
| method | 1050 | 4.857 |

## github_docs_style (GitHub docs style)

* documents judged: 158 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 4.191

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Styling & Formatting | 4 | 4 | 4.699 | 4.699 | 632 |
| Content Quality | 2 | 2 | 4.459 | 4.459 | 316 |
| Content Types & Completeness | 4 | 4 | 4.442 | 4.441 | 632 |
| Structure & Organization | 3 | 3 | 4.342 | 4.342 | 474 |
| Article Content Families | 5 | 5 | 3.385 | 3.385 | 790 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Reference Content | 158 | 5.0 | - |
| Article Content Families | Error Reference Content Guidelines | 158 | 4.323 | 0.609 |
| Article Content Families | Conceptual Content Guidelines | 158 | 3.481 | 1.679 |
| Article Content Families | Getting Started Content Guidelines | 158 | 3.07 | 1.191 |
| Article Content Families | Tutorial Content Guidelines | 158 | 1.051 | 0.314 |
| Content Quality | Content Type Consistency | 158 | 4.962 | 0.191 |
| Content Quality | Reuse Instead of Copying | 158 | 3.956 | 0.235 |
| Content Types & Completeness | Next Steps Standards | 158 | 4.684 | 0.479 |
| Content Types & Completeness | Further Reading Standards | 158 | 4.646 | 0.478 |
| Content Types & Completeness | Process Content Standards | 158 | 4.557 | 0.497 |
| Content Types & Completeness | Prerequisites Standards | 158 | 3.88 | 0.599 |
| Structure & Organization | Content Order | 158 | 4.899 | 0.302 |
| Structure & Organization | Balanced Hierarchy | 158 | 4.886 | 0.318 |
| Structure & Organization | Category Title Naming | 158 | 3.241 | 0.442 |
| Styling & Formatting | Introduction Standards | 158 | 4.956 | 0.206 |
| Styling & Formatting | Title Standards | 158 | 4.892 | 0.31 |
| Styling & Formatting | Product Label Standards | 158 | 4.797 | 0.402 |
| Styling & Formatting | Permission Declaration Standards | 158 | 4.152 | 0.781 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| joblib | 1080 | 4.211 |
| ragflow | 684 | 4.164 |
| sonnet | 1080 | 4.187 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 936 | 4.234 |
| function | 558 | 4.281 |
| method | 1350 | 4.123 |

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 158 | 14 | 4.762 | 5 |
| github_docs_style | 158 | 18 | 4.191 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| joblib | 4.732 | 4.211 |
| ragflow | 4.848 | 4.164 |
| sonnet | 4.737 | 4.187 |

