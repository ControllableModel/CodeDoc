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

