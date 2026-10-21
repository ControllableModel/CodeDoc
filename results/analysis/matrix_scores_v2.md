# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 38 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 4.872
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Format & Presentation | 2 | 2 | 4.987 | 4.987 | 76 |
| Internationalization & Localization | 2 | 2 | 4.96 | 4.961 | 76 |
| Information Structure | 4 | 4 | 4.947 | 4.947 | 152 |
| Content Quality | 5 | 5 | 4.816 | 4.816 | 190 |
| Usability & User Experience | 1 | 1 | 4.447 | 4.447 | 38 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Consistency | 38 | 5.0 | - |
| Content Quality | Conciseness | 38 | 4.921 | 0.27 |
| Content Quality | Comprehensibility | 38 | 4.816 | 0.388 |
| Content Quality | Correctness | 38 | 4.763 | 0.425 |
| Content Quality | Completeness | 38 | 4.579 | 0.815 |
| Format & Presentation | Legibility | 38 | 5.0 | - |
| Format & Presentation | Consistent Format | 38 | 4.974 | 0.16 |
| Information Structure | Metadata | 38 | 5.0 | - |
| Information Structure | Navigability | 38 | 4.947 | 0.223 |
| Information Structure | Modularity | 38 | 4.921 | 0.27 |
| Information Structure | Structured by Function | 38 | 4.921 | 0.27 |
| Internationalization & Localization | Cultural Neutrality | 38 | 5.0 | - |
| Internationalization & Localization | Translation-Friendly | 38 | 4.921 | 0.27 |
| Usability & User Experience | User-Centered Design | 38 | 4.447 | 0.594 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| ragflow | 532 | 4.872 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 56 | 4.375 |
| function | 98 | 4.969 |
| method | 378 | 4.921 |

## github_docs_style (GitHub docs style)

* documents judged: 38 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 2.993

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 2 | 2 | 4.487 | 4.487 | 76 |
| Structure & Organization | 3 | 3 | 4.298 | 4.298 | 114 |
| Styling & Formatting | 4 | 4 | 3.868 | 3.868 | 152 |
| Article Content Families | 5 | 5 | 1.995 | 1.995 | 190 |
| Content Types & Completeness | 4 | 4 | 1.638 | 1.638 | 152 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Reference Content | 38 | 5.0 | - |
| Article Content Families | Error Reference Content Guidelines | 38 | 1.974 | 1.614 |
| Article Content Families | Conceptual Content Guidelines | 38 | 1.0 | - |
| Article Content Families | Tutorial Content Guidelines | 38 | 1.0 | - |
| Article Content Families | Getting Started Content Guidelines | 38 | 1.0 | - |
| Content Quality | Content Type Consistency | 38 | 5.0 | - |
| Content Quality | Reuse Instead of Copying | 38 | 3.974 | 0.16 |
| Content Types & Completeness | Prerequisites Standards | 38 | 2.816 | 1.904 |
| Content Types & Completeness | Process Content Standards | 38 | 1.395 | 0.844 |
| Content Types & Completeness | Next Steps Standards | 38 | 1.342 | 0.575 |
| Content Types & Completeness | Further Reading Standards | 38 | 1.0 | - |
| Structure & Organization | Balanced Hierarchy | 38 | 4.974 | 0.16 |
| Structure & Organization | Content Order | 38 | 4.974 | 0.16 |
| Structure & Organization | Category Title Naming | 38 | 2.947 | 0.32 |
| Styling & Formatting | Introduction Standards | 38 | 4.868 | 0.338 |
| Styling & Formatting | Title Standards | 38 | 4.816 | 0.388 |
| Styling & Formatting | Product Label Standards | 38 | 4.789 | 0.408 |
| Styling & Formatting | Permission Declaration Standards | 38 | 1.0 | - |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| ragflow | 684 | 2.993 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 72 | 2.903 |
| function | 126 | 2.889 |
| method | 486 | 3.033 |

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 38 | 14 | 4.872 | 5 |
| github_docs_style | 38 | 18 | 2.993 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| ragflow | 4.872 | 2.993 |

