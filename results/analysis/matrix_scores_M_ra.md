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

## github_docs_style (GitHub docs style)

* documents judged: 578 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 2.263

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 2 | 2 | 3.478 | 3.478 | 1156 |
| Structure & Organization | 3 | 3 | 2.921 | 2.922 | 1734 |
| Styling & Formatting | 4 | 4 | 2.599 | 2.599 | 2312 |
| Article Content Families | 5 | 5 | 1.818 | 1.818 | 2890 |
| Content Types & Completeness | 4 | 4 | 1.38 | 1.38 | 2312 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Reference Content | 578 | 4.491 | 0.671 |
| Article Content Families | Error Reference Content Guidelines | 578 | 1.391 | 0.744 |
| Article Content Families | Conceptual Content Guidelines | 578 | 1.208 | 0.41 |
| Article Content Families | Tutorial Content Guidelines | 578 | 1.002 | 0.042 |
| Article Content Families | Getting Started Content Guidelines | 578 | 1.0 | - |
| Content Quality | Content Type Consistency | 578 | 3.96 | 0.503 |
| Content Quality | Reuse Instead of Copying | 578 | 2.997 | 0.311 |
| Content Types & Completeness | Prerequisites Standards | 578 | 1.943 | 0.662 |
| Content Types & Completeness | Process Content Standards | 578 | 1.566 | 0.749 |
| Content Types & Completeness | Next Steps Standards | 578 | 1.009 | 0.093 |
| Content Types & Completeness | Further Reading Standards | 578 | 1.003 | 0.059 |
| Structure & Organization | Content Order | 578 | 4.183 | 0.64 |
| Structure & Organization | Balanced Hierarchy | 578 | 3.443 | 0.807 |
| Structure & Organization | Category Title Naming | 578 | 1.138 | 0.418 |
| Styling & Formatting | Product Label Standards | 578 | 3.311 | 0.567 |
| Styling & Formatting | Introduction Standards | 578 | 3.104 | 0.986 |
| Styling & Formatting | Title Standards | 578 | 2.981 | 0.604 |
| Styling & Formatting | Permission Declaration Standards | 578 | 1.0 | - |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| dify_api | 1080 | 2.313 |
| fairseq | 1080 | 2.198 |
| flask-main | 1080 | 2.296 |
| joblib | 1080 | 2.253 |
| numpy | 1080 | 2.244 |
| openui | 1080 | 2.316 |
| pyro | 1080 | 2.28 |
| ragflow | 684 | 2.265 |
| sonnet | 1080 | 2.26 |
| torch | 1080 | 2.204 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 3942 | 2.243 |
| function | 2196 | 2.327 |
| method | 4266 | 2.248 |

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 578 | 14 | 4.267 | 5 |
| github_docs_style | 578 | 18 | 2.263 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| dify_api | 4.387 | 2.313 |
| fairseq | 4.106 | 2.198 |
| flask-main | 4.317 | 2.296 |
| joblib | 4.31 | 2.253 |
| numpy | 4.221 | 2.244 |
| openui | 4.342 | 2.316 |
| pyro | 4.244 | 2.28 |
| ragflow | 4.321 | 2.265 |
| sonnet | 4.333 | 2.26 |
| torch | 4.113 | 2.204 |

