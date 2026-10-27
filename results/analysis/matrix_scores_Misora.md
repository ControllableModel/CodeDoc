# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 578 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 4.267
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 5 | 5 | 4.679 | 4.679 | 2890 |
| Internationalization & Localization | 2 | 2 | 4.609 | 4.609 | 1156 |
| Format & Presentation | 2 | 2 | 4.346 | 4.346 | 1156 |
| Information Structure | 4 | 4 | 3.79 | 3.79 | 2312 |
| Usability & User Experience | 1 | 1 | 3.277 | 3.277 | 578 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Consistency | 578 | 4.889 | 0.514 |
| Content Quality | Correctness | 578 | 4.87 | 0.531 |
| Content Quality | Comprehensibility | 578 | 4.692 | 0.621 |
| Content Quality | Completeness | 578 | 4.675 | 0.646 |
| Content Quality | Conciseness | 578 | 4.27 | 0.633 |
| Format & Presentation | Legibility | 578 | 4.813 | 0.564 |
| Format & Presentation | Consistent Format | 578 | 3.879 | 0.512 |
| Information Structure | Structured by Function | 578 | 4.78 | 0.584 |
| Information Structure | Modularity | 578 | 4.713 | 0.615 |
| Information Structure | Navigability | 578 | 4.614 | 0.646 |
| Information Structure | Metadata | 578 | 1.054 | 0.225 |
| Internationalization & Localization | Cultural Neutrality | 578 | 4.945 | 0.467 |
| Internationalization & Localization | Translation-Friendly | 578 | 4.273 | 0.618 |
| Usability & User Experience | User-Centered Design | 578 | 3.277 | 0.548 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| dify_api | 840 | 4.387 |
| fairseq | 840 | 4.106 |
| flask-main | 840 | 4.317 |
| joblib | 840 | 4.31 |
| numpy | 840 | 4.221 |
| openui | 840 | 4.342 |
| pyro | 840 | 4.244 |
| ragflow | 532 | 4.321 |
| sonnet | 840 | 4.333 |
| torch | 840 | 4.113 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 3066 | 4.256 |
| function | 1708 | 4.329 |
| method | 3318 | 4.246 |

