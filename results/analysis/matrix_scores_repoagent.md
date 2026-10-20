# Rubric scores for the generated documentation sets

* judge: `deepseek-v4-flash`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 38 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 4.363
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 5 | 5 | 4.732 | 4.732 | 190 |
| Format & Presentation | 2 | 2 | 4.54 | 4.539 | 76 |
| Internationalization & Localization | 2 | 2 | 4.5 | 4.5 | 76 |
| Information Structure | 4 | 4 | 3.947 | 3.947 | 152 |
| Usability & User Experience | 1 | 1 | 3.553 | 3.553 | 38 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Consistency | 38 | 4.921 | 0.27 |
| Content Quality | Comprehensibility | 38 | 4.895 | 0.307 |
| Content Quality | Correctness | 38 | 4.816 | 0.388 |
| Content Quality | Completeness | 38 | 4.789 | 0.408 |
| Content Quality | Conciseness | 38 | 4.237 | 0.483 |
| Format & Presentation | Legibility | 38 | 4.658 | 0.474 |
| Format & Presentation | Consistent Format | 38 | 4.421 | 0.494 |
| Information Structure | Structured by Function | 38 | 5.0 | - |
| Information Structure | Modularity | 38 | 4.921 | 0.27 |
| Information Structure | Navigability | 38 | 4.868 | 0.338 |
| Information Structure | Metadata | 38 | 1.0 | - |
| Internationalization & Localization | Cultural Neutrality | 38 | 5.0 | - |
| Internationalization & Localization | Translation-Friendly | 38 | 4.0 | 0.459 |
| Usability & User Experience | User-Centered Design | 38 | 3.553 | 0.594 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| ragflow | 532 | 4.363 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 56 | 4.268 |
| function | 98 | 4.459 |
| method | 378 | 4.352 |

## github_docs_style (GitHub docs style)

* documents judged: 38 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 2.721

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 2 | 2 | 4.636 | 4.64 | 75 |
| Structure & Organization | 3 | 3 | 3.164 | 3.359 | 103 |
| Styling & Formatting | 4 | 4 | 2.861 | 2.957 | 140 |
| Article Content Families | 5 | 5 | 2.044 | 2.23 | 152 |
| Content Types & Completeness | 4 | 4 | 1.382 | 1.376 | 125 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Reference Content | 38 | 4.868 | 0.338 |
| Article Content Families | Error Reference Content Guidelines | 30 | 2.067 | 1.093 |
| Article Content Families | Conceptual Content Guidelines | 28 | 1.143 | 0.44 |
| Article Content Families | Tutorial Content Guidelines | 28 | 1.071 | 0.371 |
| Article Content Families | Getting Started Content Guidelines | 28 | 1.071 | 0.371 |
| Content Quality | Content Type Consistency | 38 | 4.895 | 0.307 |
| Content Quality | Reuse Instead of Copying | 37 | 4.378 | 0.586 |
| Content Types & Completeness | Prerequisites Standards | 31 | 1.935 | 0.801 |
| Content Types & Completeness | Process Content Standards | 28 | 1.321 | 0.658 |
| Content Types & Completeness | Next Steps Standards | 33 | 1.273 | 0.445 |
| Content Types & Completeness | Further Reading Standards | 33 | 1.0 | - |
| Structure & Organization | Content Order | 38 | 4.684 | 0.465 |
| Structure & Organization | Balanced Hierarchy | 38 | 3.474 | 0.678 |
| Structure & Organization | Category Title Naming | 27 | 1.333 | 0.609 |
| Styling & Formatting | Product Label Standards | 35 | 3.743 | 0.905 |
| Styling & Formatting | Title Standards | 38 | 3.658 | 0.619 |
| Styling & Formatting | Introduction Standards | 38 | 2.974 | 0.537 |
| Styling & Formatting | Permission Declaration Standards | 29 | 1.069 | 0.365 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| ragflow | 595 | 2.721 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 71 | 2.437 |
| function | 119 | 2.655 |
| method | 405 | 2.79 |

Judge returned dimension names that match no rubric entry (excluded from the tables above, listed so nothing disappears quietly):

* `Overall Quality` x2

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 38 | 14 | 4.363 | 5 |
| github_docs_style | 38 | 18 | 2.721 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| ragflow | 4.363 | 2.721 |

