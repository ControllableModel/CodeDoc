# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 578 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 4.737
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Format & Presentation | 2 | 2 | 4.955 | 4.955 | 1156 |
| Information Structure | 4 | 4 | 4.952 | 4.952 | 2312 |
| Internationalization & Localization | 2 | 2 | 4.856 | 4.856 | 1156 |
| Content Quality | 5 | 5 | 4.566 | 4.566 | 2890 |
| Usability & User Experience | 1 | 1 | 4.059 | 4.059 | 578 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Consistency | 578 | 4.979 | 0.154 |
| Content Quality | Correctness | 578 | 4.696 | 0.464 |
| Content Quality | Comprehensibility | 578 | 4.682 | 0.466 |
| Content Quality | Completeness | 578 | 4.481 | 0.774 |
| Content Quality | Conciseness | 578 | 3.991 | 0.319 |
| Format & Presentation | Legibility | 578 | 4.995 | 0.072 |
| Format & Presentation | Consistent Format | 578 | 4.915 | 0.279 |
| Information Structure | Metadata | 578 | 4.976 | 0.154 |
| Information Structure | Navigability | 578 | 4.953 | 0.211 |
| Information Structure | Structured by Function | 578 | 4.941 | 0.235 |
| Information Structure | Modularity | 578 | 4.939 | 0.239 |
| Internationalization & Localization | Cultural Neutrality | 578 | 5.0 | - |
| Internationalization & Localization | Translation-Friendly | 578 | 4.711 | 0.453 |
| Usability & User Experience | User-Centered Design | 578 | 4.059 | 0.408 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| dify_api | 840 | 4.758 |
| fairseq | 840 | 4.748 |
| flask-main | 840 | 4.764 |
| joblib | 840 | 4.72 |
| numpy | 840 | 4.733 |
| openui | 840 | 4.671 |
| pyro | 840 | 4.706 |
| ragflow | 532 | 4.805 |
| sonnet | 840 | 4.754 |
| torch | 840 | 4.736 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 3066 | 4.587 |
| function | 1708 | 4.809 |
| method | 3318 | 4.839 |

