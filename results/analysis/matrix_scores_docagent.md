# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 36 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 3.544
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Internationalization & Localization | 2 | 2 | 3.931 | 3.931 | 72 |
| Content Quality | 5 | 5 | 3.817 | 3.817 | 180 |
| Format & Presentation | 2 | 2 | 3.695 | 3.694 | 72 |
| Information Structure | 4 | 4 | 3.125 | 3.125 | 144 |
| Usability & User Experience | 1 | 1 | 2.778 | 2.778 | 36 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Conciseness | 36 | 4.056 | 1.666 |
| Content Quality | Consistency | 36 | 4.028 | 1.691 |
| Content Quality | Comprehensibility | 36 | 3.861 | 1.636 |
| Content Quality | Correctness | 36 | 3.667 | 1.546 |
| Content Quality | Completeness | 36 | 3.472 | 1.443 |
| Format & Presentation | Legibility | 36 | 4.056 | 1.666 |
| Format & Presentation | Consistent Format | 36 | 3.333 | 1.414 |
| Information Structure | Structured by Function | 36 | 3.972 | 1.724 |
| Information Structure | Modularity | 36 | 3.944 | 1.715 |
| Information Structure | Navigability | 36 | 3.583 | 1.552 |
| Information Structure | Metadata | 36 | 1.0 | - |
| Internationalization & Localization | Cultural Neutrality | 36 | 4.056 | 1.666 |
| Internationalization & Localization | Translation-Friendly | 36 | 3.806 | 1.613 |
| Usability & User Experience | User-Centered Design | 36 | 2.778 | 1.108 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| ragflow | 504 | 3.544 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 56 | 3.429 |
| function | 98 | 2.99 |
| method | 350 | 3.717 |

## github_docs_style (GitHub docs style)

* documents judged: 36 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 1.907

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 2 | 2 | 2.944 | 2.944 | 72 |
| Styling & Formatting | 4 | 4 | 2.236 | 2.236 | 144 |
| Structure & Organization | 3 | 3 | 2.195 | 2.194 | 108 |
| Article Content Families | 5 | 5 | 1.667 | 1.667 | 180 |
| Content Types & Completeness | 4 | 4 | 1.146 | 1.146 | 144 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Reference Content | 36 | 3.556 | 1.554 |
| Article Content Families | Error Reference Content Guidelines | 36 | 1.75 | 1.064 |
| Article Content Families | Conceptual Content Guidelines | 36 | 1.028 | 0.164 |
| Article Content Families | Tutorial Content Guidelines | 36 | 1.0 | - |
| Article Content Families | Getting Started Content Guidelines | 36 | 1.0 | - |
| Content Quality | Content Type Consistency | 36 | 3.389 | 1.42 |
| Content Quality | Reuse Instead of Copying | 36 | 2.5 | 0.866 |
| Content Types & Completeness | Prerequisites Standards | 36 | 1.306 | 0.461 |
| Content Types & Completeness | Process Content Standards | 36 | 1.278 | 0.448 |
| Content Types & Completeness | Next Steps Standards | 36 | 1.0 | - |
| Content Types & Completeness | Further Reading Standards | 36 | 1.0 | - |
| Structure & Organization | Content Order | 36 | 3.306 | 1.43 |
| Structure & Organization | Balanced Hierarchy | 36 | 2.278 | 1.017 |
| Structure & Organization | Category Title Naming | 36 | 1.0 | - |
| Styling & Formatting | Product Label Standards | 36 | 2.806 | 1.15 |
| Styling & Formatting | Title Standards | 36 | 2.778 | 0.975 |
| Styling & Formatting | Introduction Standards | 36 | 2.361 | 1.032 |
| Styling & Formatting | Permission Declaration Standards | 36 | 1.0 | - |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| ragflow | 648 | 1.907 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 72 | 1.861 |
| function | 126 | 1.714 |
| method | 450 | 1.969 |

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 36 | 14 | 3.544 | 5 |
| github_docs_style | 36 | 18 | 1.907 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| ragflow | 3.544 | 1.907 |

