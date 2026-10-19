# Rubric scores for the generated documentation sets

* judge: `deepseek-v4-flash`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 578 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 4.661
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Format & Presentation | 2 | 2 | 4.925 | 4.925 | 1156 |
| Information Structure | 4 | 4 | 4.754 | 4.754 | 2312 |
| Internationalization & Localization | 2 | 2 | 4.717 | 4.717 | 1156 |
| Usability & User Experience | 1 | 1 | 4.63 | 4.63 | 578 |
| Content Quality | 5 | 5 | 4.465 | 4.465 | 2890 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Comprehensibility | 578 | 4.877 | 0.333 |
| Content Quality | Consistency | 578 | 4.761 | 0.497 |
| Content Quality | Correctness | 578 | 4.415 | 0.689 |
| Content Quality | Completeness | 578 | 4.282 | 0.872 |
| Content Quality | Conciseness | 578 | 3.988 | 0.405 |
| Format & Presentation | Legibility | 578 | 4.953 | 0.211 |
| Format & Presentation | Consistent Format | 578 | 4.896 | 0.305 |
| Information Structure | Structured by Function | 578 | 4.974 | 0.17 |
| Information Structure | Navigability | 578 | 4.967 | 0.178 |
| Information Structure | Modularity | 578 | 4.965 | 0.183 |
| Information Structure | Metadata | 578 | 4.111 | 0.418 |
| Internationalization & Localization | Cultural Neutrality | 578 | 5.0 | - |
| Internationalization & Localization | Translation-Friendly | 578 | 4.434 | 0.496 |
| Usability & User Experience | User-Centered Design | 578 | 4.63 | 0.531 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| dify_api | 840 | 4.674 |
| fairseq | 840 | 4.685 |
| flask-main | 840 | 4.675 |
| joblib | 840 | 4.633 |
| numpy | 840 | 4.649 |
| openui | 840 | 4.654 |
| pyro | 840 | 4.605 |
| ragflow | 532 | 4.735 |
| sonnet | 840 | 4.682 |
| torch | 840 | 4.646 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 3066 | 4.568 |
| function | 1708 | 4.734 |
| method | 3318 | 4.709 |

## github_docs_style (GitHub docs style)

* documents judged: 578 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 3.084

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Types & Completeness | 4 | 4 | 3.709 | 3.709 | 2312 |
| Article Content Families | 5 | 5 | 3.177 | 3.178 | 2888 |
| Styling & Formatting | 4 | 4 | 3.153 | 3.153 | 2312 |
| Structure & Organization | 3 | 3 | 2.568 | 2.568 | 1734 |
| Content Quality | 2 | 2 | 2.235 | 2.235 | 1156 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Getting Started Content Guidelines | 578 | 4.189 | 0.589 |
| Article Content Families | Reference Content | 578 | 4.182 | 0.631 |
| Article Content Families | Conceptual Content Guidelines | 578 | 3.209 | 0.597 |
| Article Content Families | Tutorial Content Guidelines | 577 | 2.464 | 0.585 |
| Article Content Families | Error Reference Content Guidelines | 577 | 1.842 | 0.604 |
| Content Quality | Reuse Instead of Copying | 578 | 2.408 | 0.652 |
| Content Quality | Content Type Consistency | 578 | 2.062 | 0.357 |
| Content Types & Completeness | Further Reading Standards | 578 | 4.882 | 0.328 |
| Content Types & Completeness | Next Steps Standards | 578 | 3.941 | 0.753 |
| Content Types & Completeness | Process Content Standards | 578 | 3.81 | 0.607 |
| Content Types & Completeness | Prerequisites Standards | 578 | 2.204 | 0.416 |
| Structure & Organization | Balanced Hierarchy | 578 | 3.403 | 0.61 |
| Structure & Organization | Content Order | 578 | 2.384 | 0.493 |
| Structure & Organization | Category Title Naming | 578 | 1.917 | 0.386 |
| Styling & Formatting | Product Label Standards | 578 | 3.881 | 0.504 |
| Styling & Formatting | Title Standards | 578 | 3.254 | 0.911 |
| Styling & Formatting | Introduction Standards | 578 | 2.983 | 0.513 |
| Styling & Formatting | Permission Declaration Standards | 578 | 2.495 | 0.706 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| dify_api | 1080 | 3.101 |
| fairseq | 1080 | 3.218 |
| flask-main | 1080 | 3.131 |
| joblib | 1078 | 3.137 |
| numpy | 1080 | 3.035 |
| openui | 1080 | 2.898 |
| pyro | 1080 | 3.039 |
| ragflow | 684 | 3.184 |
| sonnet | 1080 | 3.021 |
| torch | 1080 | 3.114 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 3942 | 2.98 |
| function | 2196 | 3.074 |
| method | 4264 | 3.186 |

Judge returned dimension names that match no rubric entry (excluded from the tables above, listed so nothing disappears quietly):

* `Overall Quality` x22
* `Overall` x4

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 578 | 14 | 4.661 | 5 |
| github_docs_style | 578 | 18 | 3.084 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| dify_api | 4.674 | 3.101 |
| fairseq | 4.685 | 3.218 |
| flask-main | 4.675 | 3.131 |
| joblib | 4.633 | 3.137 |
| numpy | 4.649 | 3.035 |
| openui | 4.654 | 2.898 |
| pyro | 4.605 | 3.039 |
| ragflow | 4.735 | 3.184 |
| sonnet | 4.682 | 3.021 |
| torch | 4.646 | 3.114 |

