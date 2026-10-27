# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 158 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 4.091
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Internationalization & Localization | 2 | 2 | 4.665 | 4.665 | 316 |
| Format & Presentation | 2 | 2 | 4.475 | 4.475 | 316 |
| Content Quality | 5 | 5 | 4.375 | 4.375 | 790 |
| Information Structure | 4 | 4 | 3.543 | 3.543 | 632 |
| Usability & User Experience | 1 | 1 | 2.956 | 2.956 | 158 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Conciseness | 158 | 4.854 | 0.353 |
| Content Quality | Consistency | 158 | 4.576 | 0.531 |
| Content Quality | Correctness | 158 | 4.456 | 0.591 |
| Content Quality | Comprehensibility | 158 | 4.342 | 0.56 |
| Content Quality | Completeness | 158 | 3.646 | 0.804 |
| Format & Presentation | Legibility | 158 | 4.918 | 0.275 |
| Format & Presentation | Consistent Format | 158 | 4.032 | 0.706 |
| Information Structure | Structured by Function | 158 | 4.563 | 0.578 |
| Information Structure | Modularity | 158 | 4.494 | 0.582 |
| Information Structure | Navigability | 158 | 4.076 | 0.768 |
| Information Structure | Metadata | 158 | 1.038 | 0.191 |
| Internationalization & Localization | Cultural Neutrality | 158 | 5.0 | - |
| Internationalization & Localization | Translation-Friendly | 158 | 4.329 | 0.47 |
| Usability & User Experience | User-Centered Design | 158 | 2.956 | 0.588 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| joblib | 840 | 4.143 |
| ragflow | 532 | 4.124 |
| sonnet | 840 | 4.019 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 728 | 4.036 |
| function | 434 | 4.205 |
| method | 1050 | 4.083 |

