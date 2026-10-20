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
| Information Structure | 4 | 4 | 4.957 | 4.958 | 2312 |
| Format & Presentation | 2 | 2 | 4.946 | 4.946 | 1156 |
| Internationalization & Localization | 2 | 2 | 4.764 | 4.764 | 1156 |
| Content Quality | 5 | 5 | 4.591 | 4.591 | 2890 |
| Usability & User Experience | 1 | 1 | 4.112 | 4.112 | 578 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Consistency | 578 | 4.972 | 0.174 |
| Content Quality | Comprehensibility | 578 | 4.808 | 0.394 |
| Content Quality | Correctness | 578 | 4.732 | 0.447 |
| Content Quality | Completeness | 578 | 4.45 | 0.786 |
| Content Quality | Conciseness | 578 | 3.995 | 0.208 |
| Format & Presentation | Legibility | 578 | 4.998 | 0.042 |
| Format & Presentation | Consistent Format | 578 | 4.893 | 0.309 |
| Information Structure | Navigability | 578 | 4.986 | 0.117 |
| Information Structure | Modularity | 578 | 4.984 | 0.124 |
| Information Structure | Structured by Function | 578 | 4.984 | 0.124 |
| Information Structure | Metadata | 578 | 4.875 | 0.33 |
| Internationalization & Localization | Cultural Neutrality | 578 | 5.0 | - |
| Internationalization & Localization | Translation-Friendly | 578 | 4.528 | 0.499 |
| Usability & User Experience | User-Centered Design | 578 | 4.112 | 0.381 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| dify_api | 840 | 4.74 |
| fairseq | 840 | 4.746 |
| flask-main | 840 | 4.789 |
| joblib | 840 | 4.727 |
| numpy | 840 | 4.767 |
| openui | 840 | 4.739 |
| pyro | 840 | 4.655 |
| ragflow | 532 | 4.808 |
| sonnet | 840 | 4.735 |
| torch | 840 | 4.689 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 3066 | 4.608 |
| function | 1708 | 4.797 |
| method | 3318 | 4.825 |

## github_docs_style (GitHub docs style)

* documents judged: 578 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 3.44

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Types & Completeness | 4 | 4 | 4.15 | 4.15 | 2312 |
| Styling & Formatting | 4 | 4 | 3.622 | 3.622 | 2312 |
| Structure & Organization | 3 | 3 | 3.175 | 3.175 | 1734 |
| Article Content Families | 5 | 5 | 3.093 | 3.093 | 2890 |
| Content Quality | 2 | 2 | 2.918 | 2.919 | 1156 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Conceptual Content Guidelines | 578 | 3.758 | 0.686 |
| Article Content Families | Reference Content | 578 | 3.753 | 0.519 |
| Article Content Families | Getting Started Content Guidelines | 578 | 3.578 | 0.553 |
| Article Content Families | Tutorial Content Guidelines | 578 | 2.607 | 0.65 |
| Article Content Families | Error Reference Content Guidelines | 578 | 1.77 | 0.822 |
| Content Quality | Reuse Instead of Copying | 578 | 3.313 | 0.603 |
| Content Quality | Content Type Consistency | 578 | 2.524 | 0.586 |
| Content Types & Completeness | Further Reading Standards | 578 | 4.984 | 0.124 |
| Content Types & Completeness | Next Steps Standards | 578 | 4.524 | 0.53 |
| Content Types & Completeness | Process Content Standards | 578 | 4.05 | 0.362 |
| Content Types & Completeness | Prerequisites Standards | 578 | 3.042 | 0.604 |
| Structure & Organization | Balanced Hierarchy | 578 | 3.948 | 0.244 |
| Structure & Organization | Content Order | 578 | 3.369 | 0.565 |
| Structure & Organization | Category Title Naming | 578 | 2.209 | 0.746 |
| Styling & Formatting | Product Label Standards | 578 | 3.983 | 0.444 |
| Styling & Formatting | Introduction Standards | 578 | 3.804 | 0.563 |
| Styling & Formatting | Title Standards | 578 | 3.768 | 1.04 |
| Styling & Formatting | Permission Declaration Standards | 578 | 2.933 | 0.781 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| dify_api | 1080 | 3.494 |
| fairseq | 1080 | 3.6 |
| flask-main | 1080 | 3.583 |
| joblib | 1080 | 3.415 |
| numpy | 1080 | 3.41 |
| openui | 1080 | 3.415 |
| pyro | 1080 | 3.392 |
| ragflow | 684 | 3.326 |
| sonnet | 1080 | 3.338 |
| torch | 1080 | 3.384 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 3942 | 3.374 |
| function | 2196 | 3.566 |
| method | 4266 | 3.436 |

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 578 | 14 | 4.737 | 5 |
| github_docs_style | 578 | 18 | 3.44 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| dify_api | 4.74 | 3.494 |
| fairseq | 4.746 | 3.6 |
| flask-main | 4.789 | 3.583 |
| joblib | 4.727 | 3.415 |
| numpy | 4.767 | 3.41 |
| openui | 4.739 | 3.415 |
| pyro | 4.655 | 3.392 |
| ragflow | 4.808 | 3.326 |
| sonnet | 4.735 | 3.338 |
| torch | 4.689 | 3.384 |

