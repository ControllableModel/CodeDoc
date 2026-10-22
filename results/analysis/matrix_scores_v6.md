# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 158 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 4.767
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Format & Presentation | 2 | 2 | 4.975 | 4.975 | 316 |
| Information Structure | 4 | 4 | 4.965 | 4.965 | 632 |
| Internationalization & Localization | 2 | 2 | 4.88 | 4.88 | 316 |
| Content Quality | 5 | 5 | 4.614 | 4.614 | 790 |
| Usability & User Experience | 1 | 1 | 4.101 | 4.101 | 158 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Consistency | 158 | 4.981 | 0.136 |
| Content Quality | Correctness | 158 | 4.747 | 0.435 |
| Content Quality | Comprehensibility | 158 | 4.747 | 0.435 |
| Content Quality | Completeness | 158 | 4.563 | 0.707 |
| Content Quality | Conciseness | 158 | 4.032 | 0.38 |
| Format & Presentation | Legibility | 158 | 4.994 | 0.079 |
| Format & Presentation | Consistent Format | 158 | 4.956 | 0.206 |
| Information Structure | Metadata | 158 | 4.981 | 0.136 |
| Information Structure | Navigability | 158 | 4.968 | 0.175 |
| Information Structure | Modularity | 158 | 4.956 | 0.206 |
| Information Structure | Structured by Function | 158 | 4.956 | 0.206 |
| Internationalization & Localization | Cultural Neutrality | 158 | 5.0 | - |
| Internationalization & Localization | Translation-Friendly | 158 | 4.759 | 0.427 |
| Usability & User Experience | User-Centered Design | 158 | 4.101 | 0.409 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| joblib | 840 | 4.721 |
| ragflow | 532 | 4.816 |
| sonnet | 840 | 4.782 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 728 | 4.591 |
| function | 434 | 4.866 |
| method | 1050 | 4.849 |

## github_docs_style (GitHub docs style)

* documents judged: 156 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 4.271

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Styling & Formatting | 4 | 4 | 4.731 | 4.731 | 624 |
| Content Types & Completeness | 4 | 4 | 4.692 | 4.692 | 624 |
| Content Quality | 2 | 2 | 4.474 | 4.474 | 312 |
| Structure & Organization | 3 | 3 | 4.389 | 4.389 | 468 |
| Article Content Families | 5 | 5 | 3.413 | 3.413 | 780 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Reference Content | 156 | 4.987 | 0.112 |
| Article Content Families | Error Reference Content Guidelines | 156 | 4.269 | 0.683 |
| Article Content Families | Conceptual Content Guidelines | 156 | 3.538 | 1.719 |
| Article Content Families | Getting Started Content Guidelines | 156 | 3.147 | 1.28 |
| Article Content Families | Tutorial Content Guidelines | 156 | 1.122 | 0.57 |
| Content Quality | Content Type Consistency | 156 | 4.974 | 0.158 |
| Content Quality | Reuse Instead of Copying | 156 | 3.974 | 0.158 |
| Content Types & Completeness | Prerequisites Standards | 156 | 4.974 | 0.158 |
| Content Types & Completeness | Next Steps Standards | 156 | 4.673 | 0.469 |
| Content Types & Completeness | Further Reading Standards | 156 | 4.628 | 0.483 |
| Content Types & Completeness | Process Content Standards | 156 | 4.494 | 0.635 |
| Structure & Organization | Content Order | 156 | 4.942 | 0.233 |
| Structure & Organization | Balanced Hierarchy | 156 | 4.904 | 0.295 |
| Structure & Organization | Category Title Naming | 156 | 3.321 | 0.467 |
| Styling & Formatting | Introduction Standards | 156 | 4.962 | 0.192 |
| Styling & Formatting | Title Standards | 156 | 4.885 | 0.339 |
| Styling & Formatting | Product Label Standards | 156 | 4.827 | 0.411 |
| Styling & Formatting | Permission Declaration Standards | 156 | 4.25 | 0.765 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| joblib | 1044 | 4.31 |
| ragflow | 684 | 4.235 |
| sonnet | 1080 | 4.255 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 900 | 4.352 |
| function | 558 | 4.301 |
| method | 1350 | 4.204 |

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 158 | 14 | 4.767 | 5 |
| github_docs_style | 156 | 18 | 4.271 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| joblib | 4.721 | 4.31 |
| ragflow | 4.816 | 4.235 |
| sonnet | 4.782 | 4.255 |

