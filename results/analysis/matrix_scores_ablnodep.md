# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 158 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 4.735
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Format & Presentation | 2 | 2 | 4.947 | 4.946 | 316 |
| Information Structure | 4 | 4 | 4.937 | 4.937 | 632 |
| Internationalization & Localization | 2 | 2 | 4.877 | 4.877 | 316 |
| Content Quality | 5 | 5 | 4.576 | 4.576 | 790 |
| Usability & User Experience | 1 | 1 | 4.019 | 4.019 | 158 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Consistency | 158 | 4.987 | 0.112 |
| Content Quality | Correctness | 158 | 4.747 | 0.435 |
| Content Quality | Comprehensibility | 158 | 4.703 | 0.457 |
| Content Quality | Completeness | 158 | 4.418 | 0.866 |
| Content Quality | Conciseness | 158 | 4.025 | 0.355 |
| Format & Presentation | Legibility | 158 | 4.994 | 0.079 |
| Format & Presentation | Consistent Format | 158 | 4.899 | 0.302 |
| Information Structure | Metadata | 158 | 4.987 | 0.112 |
| Information Structure | Navigability | 158 | 4.924 | 0.265 |
| Information Structure | Modularity | 158 | 4.918 | 0.275 |
| Information Structure | Structured by Function | 158 | 4.918 | 0.275 |
| Internationalization & Localization | Cultural Neutrality | 158 | 5.0 | - |
| Internationalization & Localization | Translation-Friendly | 158 | 4.753 | 0.431 |
| Usability & User Experience | User-Centered Design | 158 | 4.019 | 0.428 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| joblib | 840 | 4.662 |
| ragflow | 532 | 4.835 |
| sonnet | 840 | 4.745 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 728 | 4.522 |
| function | 434 | 4.825 |
| method | 1050 | 4.846 |

