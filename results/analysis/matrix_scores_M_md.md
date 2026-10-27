# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 201 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 4.375
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 5 | 5 | 4.7 | 4.7 | 1005 |
| Internationalization & Localization | 2 | 2 | 4.652 | 4.652 | 402 |
| Format & Presentation | 2 | 2 | 4.53 | 4.53 | 402 |
| Information Structure | 4 | 4 | 3.987 | 3.988 | 804 |
| Usability & User Experience | 1 | 1 | 3.433 | 3.433 | 201 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Consistency | 201 | 4.98 | 0.172 |
| Content Quality | Correctness | 201 | 4.871 | 0.336 |
| Content Quality | Comprehensibility | 201 | 4.761 | 0.426 |
| Content Quality | Completeness | 201 | 4.756 | 0.484 |
| Content Quality | Conciseness | 201 | 4.134 | 0.382 |
| Format & Presentation | Legibility | 201 | 4.97 | 0.17 |
| Format & Presentation | Consistent Format | 201 | 4.09 | 0.302 |
| Information Structure | Structured by Function | 201 | 4.99 | 0.099 |
| Information Structure | Modularity | 201 | 4.985 | 0.121 |
| Information Structure | Navigability | 201 | 4.975 | 0.156 |
| Information Structure | Metadata | 201 | 1.0 | - |
| Internationalization & Localization | Cultural Neutrality | 201 | 5.0 | - |
| Internationalization & Localization | Translation-Friendly | 201 | 4.303 | 0.46 |
| Usability & User Experience | User-Centered Design | 201 | 3.433 | 0.515 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| flask-main | 728 | 4.416 |
| joblib | 812 | 4.347 |
| ragflow | 518 | 4.411 |
| sonnet | 756 | 4.34 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 952 | 4.345 |
| function | 476 | 4.395 |
| method | 1386 | 4.389 |

## github_docs_style (GitHub docs style)

* documents judged: 201 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 2.611

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 2 | 2 | 3.557 | 3.557 | 402 |
| Structure & Organization | 3 | 3 | 3.237 | 3.237 | 603 |
| Styling & Formatting | 4 | 4 | 3.016 | 3.016 | 804 |
| Article Content Families | 5 | 5 | 2.296 | 2.296 | 1005 |
| Content Types & Completeness | 4 | 4 | 1.657 | 1.657 | 804 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Reference Content | 201 | 4.886 | 0.334 |
| Article Content Families | Error Reference Content Guidelines | 201 | 2.915 | 0.833 |
| Article Content Families | Conceptual Content Guidelines | 201 | 1.617 | 0.645 |
| Article Content Families | Tutorial Content Guidelines | 201 | 1.05 | 0.217 |
| Article Content Families | Getting Started Content Guidelines | 201 | 1.01 | 0.099 |
| Content Quality | Content Type Consistency | 201 | 4.005 | 0.494 |
| Content Quality | Reuse Instead of Copying | 201 | 3.109 | 0.409 |
| Content Types & Completeness | Prerequisites Standards | 201 | 2.801 | 0.713 |
| Content Types & Completeness | Process Content Standards | 201 | 1.811 | 0.933 |
| Content Types & Completeness | Next Steps Standards | 201 | 1.015 | 0.121 |
| Content Types & Completeness | Further Reading Standards | 201 | 1.0 | - |
| Structure & Organization | Content Order | 201 | 4.09 | 0.348 |
| Structure & Organization | Balanced Hierarchy | 201 | 4.045 | 0.287 |
| Structure & Organization | Category Title Naming | 201 | 1.577 | 0.884 |
| Styling & Formatting | Title Standards | 201 | 3.856 | 0.927 |
| Styling & Formatting | Product Label Standards | 201 | 3.672 | 0.557 |
| Styling & Formatting | Introduction Standards | 201 | 3.537 | 0.773 |
| Styling & Formatting | Permission Declaration Standards | 201 | 1.0 | - |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| flask-main | 936 | 2.675 |
| joblib | 1044 | 2.586 |
| ragflow | 666 | 2.668 |
| sonnet | 972 | 2.536 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 1224 | 2.714 |
| function | 612 | 2.582 |
| method | 1782 | 2.55 |

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 201 | 14 | 4.375 | 5 |
| github_docs_style | 201 | 18 | 2.611 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| flask-main | 4.416 | 2.675 |
| joblib | 4.347 | 2.586 |
| ragflow | 4.411 | 2.668 |
| sonnet | 4.34 | 2.536 |

