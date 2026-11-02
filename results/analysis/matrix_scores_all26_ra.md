# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 578 (0 returned no parseable verdict)
* dimensions asked: 26, scored: 26
* overall mean: 2.791

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 5 | 5 | 4.633 | 4.634 | 2890 |
| Information Structure | 4 | 4 | 3.607 | 3.608 | 2312 |
| Internationalization & Localization | 3 | 3 | 3.34 | 3.34 | 1734 |
| Format & Presentation | 4 | 4 | 2.611 | 2.611 | 2312 |
| Accessibility | 3 | 3 | 1.86 | 1.86 | 1734 |
| Usability & User Experience | 3 | 3 | 1.617 | 1.616 | 1734 |
| Maintenance & Updates | 2 | 2 | 1.027 | 1.028 | 1156 |
| Safety & Compliance | 2 | 2 | 1.007 | 1.007 | 1156 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Accessibility | Device Independence | 578 | 3.576 | 1.785 |
| Accessibility | Multi-modal Support | 578 | 1.005 | 0.072 |
| Accessibility | Accessibility Features | 578 | 1.0 | - |
| Content Quality | Consistency | 578 | 4.839 | 0.549 |
| Content Quality | Correctness | 578 | 4.801 | 0.58 |
| Content Quality | Comprehensibility | 578 | 4.661 | 0.63 |
| Content Quality | Completeness | 578 | 4.522 | 0.709 |
| Content Quality | Conciseness | 578 | 4.344 | 0.645 |
| Format & Presentation | Legibility | 578 | 4.673 | 0.627 |
| Format & Presentation | Consistent Format | 578 | 3.716 | 0.563 |
| Format & Presentation | Illustrations and Media | 578 | 1.043 | 0.282 |
| Format & Presentation | Representation of Interactive Elements | 578 | 1.012 | 0.161 |
| Information Structure | Structured by Function | 578 | 4.645 | 0.634 |
| Information Structure | Modularity | 578 | 4.543 | 0.649 |
| Information Structure | Navigability | 578 | 4.199 | 0.623 |
| Information Structure | Metadata | 578 | 1.043 | 0.203 |
| Internationalization & Localization | Cultural Neutrality | 578 | 4.782 | 0.601 |
| Internationalization & Localization | Translation-Friendly | 578 | 4.209 | 0.66 |
| Internationalization & Localization | Space Consideration | 578 | 1.029 | 0.206 |
| Maintenance & Updates | Version Control | 578 | 1.036 | 0.243 |
| Maintenance & Updates | Change Log | 578 | 1.019 | 0.17 |
| Safety & Compliance | Safety Information | 578 | 1.014 | 0.143 |
| Safety & Compliance | Legal and Copyright | 578 | 1.0 | - |
| Usability & User Experience | User-Centered Design | 578 | 2.846 | 0.528 |
| Usability & User Experience | Testing and Feedback | 578 | 1.002 | 0.042 |
| Usability & User Experience | Search and Indexing | 578 | 1.002 | 0.042 |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| dify_api | 1560 | 2.856 |
| fairseq | 1560 | 2.704 |
| flask-main | 1560 | 2.831 |
| joblib | 1560 | 2.831 |
| numpy | 1560 | 2.76 |
| openui | 1560 | 2.797 |
| pyro | 1560 | 2.752 |
| ragflow | 988 | 2.838 |
| sonnet | 1560 | 2.864 |
| torch | 1560 | 2.693 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 5694 | 2.781 |
| function | 3172 | 2.851 |
| method | 6162 | 2.769 |

## github_docs_style (GitHub docs style)

* documents judged: 578 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 2.272

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 2 | 2 | 3.505 | 3.505 | 1156 |
| Structure & Organization | 3 | 3 | 2.937 | 2.938 | 1734 |
| Styling & Formatting | 4 | 4 | 2.606 | 2.606 | 2312 |
| Article Content Families | 5 | 5 | 1.823 | 1.823 | 2890 |
| Content Types & Completeness | 4 | 4 | 1.385 | 1.385 | 2312 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Reference Content | 578 | 4.514 | 0.676 |
| Article Content Families | Error Reference Content Guidelines | 578 | 1.384 | 0.752 |
| Article Content Families | Conceptual Content Guidelines | 578 | 1.204 | 0.412 |
| Article Content Families | Tutorial Content Guidelines | 578 | 1.01 | 0.101 |
| Article Content Families | Getting Started Content Guidelines | 578 | 1.002 | 0.042 |
| Content Quality | Content Type Consistency | 578 | 3.993 | 0.552 |
| Content Quality | Reuse Instead of Copying | 578 | 3.017 | 0.348 |
| Content Types & Completeness | Prerequisites Standards | 578 | 1.955 | 0.659 |
| Content Types & Completeness | Process Content Standards | 578 | 1.574 | 0.764 |
| Content Types & Completeness | Next Steps Standards | 578 | 1.007 | 0.083 |
| Content Types & Completeness | Further Reading Standards | 578 | 1.005 | 0.072 |
| Structure & Organization | Content Order | 578 | 4.176 | 0.644 |
| Structure & Organization | Balanced Hierarchy | 578 | 3.465 | 0.811 |
| Structure & Organization | Category Title Naming | 578 | 1.171 | 0.478 |
| Styling & Formatting | Product Label Standards | 578 | 3.311 | 0.561 |
| Styling & Formatting | Introduction Standards | 578 | 3.121 | 0.971 |
| Styling & Formatting | Title Standards | 578 | 2.993 | 0.614 |
| Styling & Formatting | Permission Declaration Standards | 578 | 1.0 | - |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| dify_api | 1080 | 2.337 |
| fairseq | 1080 | 2.252 |
| flask-main | 1080 | 2.329 |
| joblib | 1080 | 2.253 |
| numpy | 1080 | 2.28 |
| openui | 1080 | 2.257 |
| pyro | 1080 | 2.274 |
| ragflow | 684 | 2.268 |
| sonnet | 1080 | 2.241 |
| torch | 1080 | 2.233 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 3942 | 2.277 |
| function | 2196 | 2.307 |
| method | 4266 | 2.25 |

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 578 | 26 | 2.791 | 8 |
| github_docs_style | 578 | 18 | 2.272 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| dify_api | 2.856 | 2.337 |
| fairseq | 2.704 | 2.252 |
| flask-main | 2.831 | 2.329 |
| joblib | 2.831 | 2.253 |
| numpy | 2.76 | 2.28 |
| openui | 2.797 | 2.257 |
| pyro | 2.752 | 2.274 |
| ragflow | 2.838 | 2.268 |
| sonnet | 2.864 | 2.241 |
| torch | 2.693 | 2.233 |

