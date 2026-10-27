# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 158 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 3.987
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Internationalization & Localization | 2 | 2 | 4.671 | 4.671 | 316 |
| Format & Presentation | 2 | 2 | 4.415 | 4.415 | 316 |
| Content Quality | 5 | 5 | 4.263 | 4.263 | 790 |
| Information Structure | 4 | 4 | 3.4 | 3.4 | 632 |
| Usability & User Experience | 1 | 1 | 2.728 | 2.728 | 158 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Conciseness | 158 | 4.886 | 0.318 |
| Content Quality | Consistency | 158 | 4.462 | 0.547 |
| Content Quality | Correctness | 158 | 4.342 | 0.582 |
| Content Quality | Comprehensibility | 158 | 4.291 | 0.531 |
| Content Quality | Completeness | 158 | 3.335 | 0.808 |
| Format & Presentation | Legibility | 158 | 4.899 | 0.302 |
| Format & Presentation | Consistent Format | 158 | 3.93 | 0.657 |
| Information Structure | Structured by Function | 158 | 4.367 | 0.63 |
| Information Structure | Modularity | 158 | 4.335 | 0.569 |
| Information Structure | Navigability | 158 | 3.88 | 0.741 |
| Information Structure | Metadata | 158 | 1.019 | 0.136 |
| Internationalization & Localization | Cultural Neutrality | 158 | 5.0 | - |
| Internationalization & Localization | Translation-Friendly | 158 | 4.342 | 0.474 |
| Usability & User Experience | User-Centered Design | 158 | 2.728 | 0.592 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| joblib | 840 | 4.021 |
| ragflow | 532 | 4.009 |
| sonnet | 840 | 3.938 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 728 | 3.894 |
| function | 434 | 4.129 |
| method | 1050 | 3.992 |

