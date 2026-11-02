# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 201 (0 returned no parseable verdict)
* dimensions asked: 26, scored: 26
* overall mean: 2.978

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 5 | 5 | 4.633 | 4.633 | 1005 |
| Information Structure | 4 | 4 | 3.945 | 3.945 | 804 |
| Internationalization & Localization | 3 | 3 | 3.489 | 3.489 | 603 |
| Format & Presentation | 4 | 4 | 3.088 | 3.088 | 804 |
| Accessibility | 3 | 3 | 2.179 | 2.179 | 603 |
| Usability & User Experience | 3 | 3 | 1.685 | 1.685 | 603 |
| Safety & Compliance | 2 | 2 | 1.02 | 1.02 | 402 |
| Maintenance & Updates | 2 | 2 | 1.012 | 1.012 | 402 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Accessibility | Device Independence | 201 | 4.299 | 1.308 |
| Accessibility | Multi-modal Support | 201 | 1.239 | 0.438 |
| Accessibility | Accessibility Features | 201 | 1.0 | - |
| Content Quality | Consistency | 201 | 4.97 | 0.17 |
| Content Quality | Correctness | 201 | 4.731 | 0.443 |
| Content Quality | Comprehensibility | 201 | 4.652 | 0.476 |
| Content Quality | Completeness | 201 | 4.592 | 0.609 |
| Content Quality | Conciseness | 201 | 4.219 | 0.459 |
| Format & Presentation | Legibility | 201 | 4.871 | 0.35 |
| Format & Presentation | Consistent Format | 201 | 4.06 | 0.368 |
| Format & Presentation | Illustrations and Media | 201 | 2.214 | 1.261 |
| Format & Presentation | Representation of Interactive Elements | 201 | 1.209 | 0.587 |
| Information Structure | Structured by Function | 201 | 4.955 | 0.207 |
| Information Structure | Modularity | 201 | 4.935 | 0.246 |
| Information Structure | Navigability | 201 | 4.866 | 0.341 |
| Information Structure | Metadata | 201 | 1.025 | 0.156 |
| Internationalization & Localization | Cultural Neutrality | 201 | 4.96 | 0.195 |
| Internationalization & Localization | Translation-Friendly | 201 | 4.269 | 0.476 |
| Internationalization & Localization | Space Consideration | 201 | 1.239 | 0.609 |
| Maintenance & Updates | Version Control | 201 | 1.02 | 0.172 |
| Maintenance & Updates | Change Log | 201 | 1.005 | 0.07 |
| Safety & Compliance | Safety Information | 201 | 1.04 | 0.195 |
| Safety & Compliance | Legal and Copyright | 201 | 1.0 | - |
| Usability & User Experience | User-Centered Design | 201 | 3.045 | 0.54 |
| Usability & User Experience | Search and Indexing | 201 | 1.01 | 0.099 |
| Usability & User Experience | Testing and Feedback | 201 | 1.0 | - |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| flask-main | 1352 | 3.021 |
| joblib | 1508 | 2.963 |
| ragflow | 962 | 2.979 |
| sonnet | 1404 | 2.951 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 1768 | 3.007 |
| function | 884 | 3.08 |
| method | 2574 | 2.922 |

## github_docs_style (GitHub docs style)

* documents judged: 201 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 18
* overall mean: 2.59

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 2 | 2 | 3.522 | 3.522 | 402 |
| Structure & Organization | 3 | 3 | 3.209 | 3.209 | 603 |
| Styling & Formatting | 4 | 4 | 2.96 | 2.96 | 804 |
| Article Content Families | 5 | 5 | 2.304 | 2.303 | 1005 |
| Content Types & Completeness | 4 | 4 | 1.647 | 1.647 | 804 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Reference Content | 201 | 4.826 | 0.405 |
| Article Content Families | Error Reference Content Guidelines | 201 | 2.935 | 0.786 |
| Article Content Families | Conceptual Content Guidelines | 201 | 1.692 | 0.665 |
| Article Content Families | Tutorial Content Guidelines | 201 | 1.05 | 0.217 |
| Article Content Families | Getting Started Content Guidelines | 201 | 1.015 | 0.121 |
| Content Quality | Content Type Consistency | 201 | 3.905 | 0.533 |
| Content Quality | Reuse Instead of Copying | 201 | 3.139 | 0.435 |
| Content Types & Completeness | Prerequisites Standards | 201 | 2.821 | 0.711 |
| Content Types & Completeness | Process Content Standards | 201 | 1.751 | 0.88 |
| Content Types & Completeness | Next Steps Standards | 201 | 1.015 | 0.121 |
| Content Types & Completeness | Further Reading Standards | 201 | 1.0 | - |
| Structure & Organization | Content Order | 201 | 4.07 | 0.338 |
| Structure & Organization | Balanced Hierarchy | 201 | 4.04 | 0.297 |
| Structure & Organization | Category Title Naming | 201 | 1.517 | 0.853 |
| Styling & Formatting | Title Standards | 201 | 3.751 | 0.95 |
| Styling & Formatting | Product Label Standards | 201 | 3.627 | 0.542 |
| Styling & Formatting | Introduction Standards | 201 | 3.463 | 0.798 |
| Styling & Formatting | Permission Declaration Standards | 201 | 1.0 | - |

### Per repository

| repo | verdicts | mean |
|---|---|---|
| flask-main | 936 | 2.66 |
| joblib | 1044 | 2.601 |
| ragflow | 666 | 2.523 |
| sonnet | 972 | 2.557 |

### Per entity kind

| kind | verdicts | mean |
|---|---|---|
| class | 1224 | 2.681 |
| function | 612 | 2.572 |
| method | 1782 | 2.534 |

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 201 | 26 | 2.978 | 8 |
| github_docs_style | 201 | 18 | 2.59 | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|
| flask-main | 3.021 | 2.66 |
| joblib | 2.963 | 2.601 |
| ragflow | 2.979 | 2.523 |
| sonnet | 2.951 | 2.557 |

