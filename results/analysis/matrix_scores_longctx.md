# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 578 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 14
* overall mean: 4.168
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Internationalization & Localization | 2 | 2 | 4.688 | 4.689 | 1156 |
| Content Quality | 5 | 5 | 4.504 | 4.504 | 2890 |
| Format & Presentation | 2 | 2 | 4.463 | 4.463 | 1156 |
| Information Structure | 4 | 4 | 3.615 | 3.615 | 2312 |
| Usability & User Experience | 1 | 1 | 3.067 | 3.067 | 578 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Conciseness | 578 | 4.756 | 0.433 |
| Content Quality | Consistency | 578 | 4.718 | 0.49 |
| Content Quality | Correctness | 578 | 4.623 | 0.564 |
| Content Quality | Comprehensibility | 578 | 4.481 | 0.562 |
| Content Quality | Completeness | 578 | 3.943 | 0.831 |
| Format & Presentation | Legibility | 578 | 4.912 | 0.296 |
| Format & Presentation | Consistent Format | 578 | 4.014 | 0.737 |
| Information Structure | Structured by Function | 578 | 4.628 | 0.59 |
| Information Structure | Modularity | 578 | 4.583 | 0.592 |
| Information Structure | Navigability | 578 | 4.135 | 0.771 |
| Information Structure | Metadata | 578 | 1.112 | 0.367 |
| Internationalization & Localization | Cultural Neutrality | 578 | 4.991 | 0.11 |
| Internationalization & Localization | Translation-Friendly | 578 | 4.386 | 0.504 |
| Usability & User Experience | User-Centered Design | 578 | 3.067 | 0.606 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| dify_api | 840 | 4.14 |
| fairseq | 840 | 4.16 |
| flask-main | 840 | 4.33 |
| joblib | 840 | 4.144 |
| numpy | 840 | 4.256 |
| openui | 840 | 4.13 |
| pyro | 840 | 4.114 |
| ragflow | 532 | 4.051 |
| sonnet | 840 | 4.227 |
| torch | 840 | 4.083 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 3066 | 4.289 |
| function | 1708 | 4.21 |
| method | 3318 | 4.034 |

## github_docs_style (GitHub docs style)

* documents judged: 578 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 2.115

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 2 | 2 | 3.585 | 3.585 | 1156 |
| Structure & Organization | 3 | 3 | 2.667 | 2.667 | 1734 |
| Styling & Formatting | 4 | 4 | 2.242 | 2.242 | 2312 |
| Article Content Families | 5 | 5 | 1.775 | 1.775 | 2890 |
| Content Types & Completeness | 4 | 4 | 1.265 | 1.265 | 2312 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Reference Content | 578 | 3.844 | 1.16 |
| Article Content Families | Error Reference Content Guidelines | 578 | 1.55 | 0.927 |
| Article Content Families | Conceptual Content Guidelines | 578 | 1.429 | 0.619 |
| Article Content Families | Getting Started Content Guidelines | 578 | 1.031 | 0.183 |
| Article Content Families | Tutorial Content Guidelines | 578 | 1.021 | 0.165 |
| Content Quality | Content Type Consistency | 578 | 4.121 | 1.02 |
| Content Quality | Reuse Instead of Copying | 578 | 3.048 | 0.841 |
| Content Types & Completeness | Prerequisites Standards | 578 | 1.538 | 0.681 |
| Content Types & Completeness | Process Content Standards | 578 | 1.436 | 0.701 |
| Content Types & Completeness | Next Steps Standards | 578 | 1.043 | 0.235 |
| Content Types & Completeness | Further Reading Standards | 578 | 1.043 | 0.249 |
| Structure & Organization | Content Order | 578 | 3.939 | 1.058 |
| Structure & Organization | Balanced Hierarchy | 578 | 2.855 | 1.15 |
| Structure & Organization | Category Title Naming | 578 | 1.206 | 0.606 |
| Styling & Formatting | Product Label Standards | 578 | 3.135 | 1.0 |
| Styling & Formatting | Introduction Standards | 578 | 2.874 | 1.059 |
| Styling & Formatting | Title Standards | 578 | 1.958 | 1.098 |
| Styling & Formatting | Permission Declaration Standards | 578 | 1.002 | 0.042 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| dify_api | 1080 | 2.047 |
| fairseq | 1080 | 2.128 |
| flask-main | 1080 | 2.215 |
| joblib | 1080 | 2.073 |
| numpy | 1080 | 2.275 |
| openui | 1080 | 2.043 |
| pyro | 1080 | 2.233 |
| ragflow | 684 | 1.882 |
| sonnet | 1080 | 2.053 |
| torch | 1080 | 2.119 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 3942 | 2.367 |
| function | 2196 | 2.126 |
| method | 4266 | 1.877 |

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 578 | 14 | 4.168 | 5 |
| github_docs_style | 578 | 18 | 2.115 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| dify_api | 4.14 | 2.047 |
| fairseq | 4.16 | 2.128 |
| flask-main | 4.33 | 2.215 |
| joblib | 4.144 | 2.073 |
| numpy | 4.256 | 2.275 |
| openui | 4.13 | 2.043 |
| pyro | 4.114 | 2.233 |
| ragflow | 4.051 | 1.882 |
| sonnet | 4.227 | 2.053 |
| torch | 4.083 | 2.119 |

