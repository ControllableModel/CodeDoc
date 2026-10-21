# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 156 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 4.763
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Format & Presentation | 2 | 2 | 4.958 | 4.958 | 312 |
| Information Structure | 4 | 4 | 4.95 | 4.95 | 624 |
| Internationalization & Localization | 2 | 2 | 4.862 | 4.862 | 312 |
| Content Quality | 5 | 5 | 4.608 | 4.608 | 780 |
| Usability & User Experience | 1 | 1 | 4.199 | 4.199 | 156 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Consistency | 156 | 4.987 | 0.112 |
| Content Quality | Correctness | 156 | 4.744 | 0.437 |
| Content Quality | Comprehensibility | 156 | 4.718 | 0.45 |
| Content Quality | Completeness | 156 | 4.468 | 0.737 |
| Content Quality | Conciseness | 156 | 4.122 | 0.429 |
| Format & Presentation | Legibility | 156 | 5.0 | - |
| Format & Presentation | Consistent Format | 156 | 4.917 | 0.276 |
| Information Structure | Metadata | 156 | 4.974 | 0.158 |
| Information Structure | Navigability | 156 | 4.955 | 0.207 |
| Information Structure | Modularity | 156 | 4.936 | 0.245 |
| Information Structure | Structured by Function | 156 | 4.936 | 0.245 |
| Internationalization & Localization | Cultural Neutrality | 156 | 5.0 | - |
| Internationalization & Localization | Translation-Friendly | 156 | 4.724 | 0.447 |
| Usability & User Experience | User-Centered Design | 156 | 4.199 | 0.486 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| joblib | 826 | 4.713 |
| ragflow | 532 | 4.88 |
| sonnet | 826 | 4.737 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 700 | 4.597 |
| function | 434 | 4.827 |
| method | 1050 | 4.847 |

## github_docs_style (GitHub docs style)

* documents judged: 158 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 3.693

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Types & Completeness | 4 | 4 | 4.29 | 4.29 | 632 |
| Content Quality | 2 | 2 | 4.253 | 4.253 | 316 |
| Structure & Organization | 3 | 3 | 4.129 | 4.129 | 474 |
| Styling & Formatting | 4 | 4 | 3.908 | 3.908 | 632 |
| Article Content Families | 5 | 5 | 2.56 | 2.559 | 790 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Reference Content | 158 | 4.975 | 0.157 |
| Article Content Families | Getting Started Content Guidelines | 158 | 3.728 | 0.847 |
| Article Content Families | Error Reference Content Guidelines | 158 | 2.038 | 1.587 |
| Article Content Families | Conceptual Content Guidelines | 158 | 1.044 | 0.26 |
| Article Content Families | Tutorial Content Guidelines | 158 | 1.013 | 0.112 |
| Content Quality | Content Type Consistency | 158 | 4.658 | 0.487 |
| Content Quality | Reuse Instead of Copying | 158 | 3.848 | 0.466 |
| Content Types & Completeness | Next Steps Standards | 158 | 4.424 | 0.566 |
| Content Types & Completeness | Prerequisites Standards | 158 | 4.405 | 0.772 |
| Content Types & Completeness | Further Reading Standards | 158 | 4.335 | 0.523 |
| Content Types & Completeness | Process Content Standards | 158 | 3.994 | 0.725 |
| Structure & Organization | Balanced Hierarchy | 158 | 4.747 | 0.435 |
| Structure & Organization | Content Order | 158 | 4.627 | 0.509 |
| Structure & Organization | Category Title Naming | 158 | 3.013 | 0.373 |
| Styling & Formatting | Title Standards | 158 | 4.88 | 0.362 |
| Styling & Formatting | Introduction Standards | 158 | 4.772 | 0.419 |
| Styling & Formatting | Product Label Standards | 158 | 4.373 | 0.579 |
| Styling & Formatting | Permission Declaration Standards | 158 | 1.608 | 1.168 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| joblib | 1080 | 3.723 |
| ragflow | 684 | 3.806 |
| sonnet | 1080 | 3.593 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 936 | 3.567 |
| function | 558 | 3.677 |
| method | 1350 | 3.787 |

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 156 | 14 | 4.763 | 5 |
| github_docs_style | 158 | 18 | 3.693 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| joblib | 4.713 | 3.723 |
| ragflow | 4.88 | 3.806 |
| sonnet | 4.737 | 3.593 |

