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

## github_docs_style (GitHub docs style)

* documents judged: 578 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 4.287

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Styling & Formatting | 4 | 4 | 4.737 | 4.737 | 2312 |
| Content Types & Completeness | 4 | 4 | 4.706 | 4.706 | 2312 |
| Content Quality | 2 | 2 | 4.46 | 4.46 | 1156 |
| Structure & Organization | 3 | 3 | 4.371 | 4.371 | 1734 |
| Article Content Families | 5 | 5 | 3.471 | 3.471 | 2890 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Reference Content | 578 | 4.993 | 0.083 |
| Article Content Families | Error Reference Content Guidelines | 578 | 4.343 | 0.694 |
| Article Content Families | Conceptual Content Guidelines | 578 | 3.761 | 1.562 |
| Article Content Families | Getting Started Content Guidelines | 578 | 3.194 | 1.266 |
| Article Content Families | Tutorial Content Guidelines | 578 | 1.066 | 0.406 |
| Content Quality | Content Type Consistency | 578 | 4.974 | 0.159 |
| Content Quality | Reuse Instead of Copying | 578 | 3.946 | 0.225 |
| Content Types & Completeness | Prerequisites Standards | 578 | 4.971 | 0.169 |
| Content Types & Completeness | Next Steps Standards | 578 | 4.715 | 0.455 |
| Content Types & Completeness | Further Reading Standards | 578 | 4.645 | 0.482 |
| Content Types & Completeness | Process Content Standards | 578 | 4.493 | 0.595 |
| Structure & Organization | Content Order | 578 | 4.891 | 0.323 |
| Structure & Organization | Balanced Hierarchy | 578 | 4.869 | 0.338 |
| Structure & Organization | Category Title Naming | 578 | 3.353 | 0.478 |
| Styling & Formatting | Introduction Standards | 578 | 4.962 | 0.191 |
| Styling & Formatting | Title Standards | 578 | 4.91 | 0.286 |
| Styling & Formatting | Product Label Standards | 578 | 4.806 | 0.4 |
| Styling & Formatting | Permission Declaration Standards | 578 | 4.272 | 0.763 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| dify_api | 1080 | 4.276 |
| fairseq | 1080 | 4.256 |
| flask-main | 1080 | 4.272 |
| joblib | 1080 | 4.336 |
| numpy | 1080 | 4.302 |
| openui | 1080 | 4.252 |
| pyro | 1080 | 4.276 |
| ragflow | 684 | 4.199 |
| sonnet | 1080 | 4.312 |
| torch | 1080 | 4.356 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 3942 | 4.308 |
| function | 2196 | 4.332 |
| method | 4266 | 4.244 |

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 578 | 14 | 4.737 | 5 |
| github_docs_style | 578 | 18 | 4.287 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| dify_api | 4.758 | 4.276 |
| fairseq | 4.748 | 4.256 |
| flask-main | 4.764 | 4.272 |
| joblib | 4.72 | 4.336 |
| numpy | 4.733 | 4.302 |
| openui | 4.671 | 4.252 |
| pyro | 4.706 | 4.276 |
| ragflow | 4.805 | 4.199 |
| sonnet | 4.754 | 4.312 |
| torch | 4.736 | 4.356 |

