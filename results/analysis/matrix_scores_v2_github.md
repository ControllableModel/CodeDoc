# Rubric scores for the generated documentation sets

* judge: `deepseek-chat`, temperature 0.0
* two levels are reported: the rubric's main dimensions (ISO: 8 categories, GitHub: 5) and every individual dimension
* a main dimension is the mean of its dimensions' means, so a category with more dimensions does not dominate by weight
* ISO scores only its entity-applicable dimensions; GitHub scores its full set

## iso_26514 (ISO/IEC 26514)

* documents judged: 0 (0 returned no parseable verdict)
* dimensions asked: 14, scored: 0
* overall mean: None
* main dimensions with no entity-applicable dimension at all: Accessibility, Maintenance & Updates, Safety & Compliance -- these govern a document set and cannot be scored on a single entity, which is the paper's evaluation-unit argument in concrete numbers

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 5 | 0 | None | None | 0 |
| Information Structure | 4 | 0 | None | None | 0 |
| Format & Presentation | 2 | 0 | None | None | 0 |
| Internationalization & Localization | 2 | 0 | None | None | 0 |
| Usability & User Experience | 1 | 0 | None | None | 0 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Content Quality | Correctness | 0 | **missing** | - |
| Content Quality | Consistency | 0 | **missing** | - |
| Content Quality | Comprehensibility | 0 | **missing** | - |
| Content Quality | Conciseness | 0 | **missing** | - |
| Content Quality | Completeness | 0 | **missing** | - |
| Format & Presentation | Consistent Format | 0 | **missing** | - |
| Format & Presentation | Legibility | 0 | **missing** | - |
| Information Structure | Modularity | 0 | **missing** | - |
| Information Structure | Structured by Function | 0 | **missing** | - |
| Information Structure | Navigability | 0 | **missing** | - |
| Information Structure | Metadata | 0 | **missing** | - |
| Internationalization & Localization | Cultural Neutrality | 0 | **missing** | - |
| Internationalization & Localization | Translation-Friendly | 0 | **missing** | - |
| Usability & User Experience | User-Centered Design | 0 | **missing** | - |

### Per repository

| repo | verdicts | mean |
|---|---|---|

### Per entity kind

| kind | verdicts | mean |
|---|---|---|

## github_docs_style (GitHub docs style)

* documents judged: 0 (0 returned no parseable verdict)
* dimensions asked: 18, scored: 0
* overall mean: None

### Main dimensions

| main dimension | dims | scored | mean | pooled | verdicts |
|---|---|---|---|---|---|
| Content Quality | 2 | 0 | None | None | 0 |
| Structure & Organization | 3 | 0 | None | None | 0 |
| Styling & Formatting | 4 | 0 | None | None | 0 |
| Content Types & Completeness | 4 | 0 | None | None | 0 |
| Article Content Families | 5 | 0 | None | None | 0 |

### Dimensions

| main dimension | dimension | n | mean | sd |
|---|---|---|---|---|
| Article Content Families | Reference Content | 0 | **missing** | - |
| Article Content Families | Conceptual Content Guidelines | 0 | **missing** | - |
| Article Content Families | Error Reference Content Guidelines | 0 | **missing** | - |
| Article Content Families | Tutorial Content Guidelines | 0 | **missing** | - |
| Article Content Families | Getting Started Content Guidelines | 0 | **missing** | - |
| Content Quality | Content Type Consistency | 0 | **missing** | - |
| Content Quality | Reuse Instead of Copying | 0 | **missing** | - |
| Content Types & Completeness | Process Content Standards | 0 | **missing** | - |
| Content Types & Completeness | Next Steps Standards | 0 | **missing** | - |
| Content Types & Completeness | Further Reading Standards | 0 | **missing** | - |
| Content Types & Completeness | Prerequisites Standards | 0 | **missing** | - |
| Structure & Organization | Balanced Hierarchy | 0 | **missing** | - |
| Structure & Organization | Content Order | 0 | **missing** | - |
| Structure & Organization | Category Title Naming | 0 | **missing** | - |
| Styling & Formatting | Title Standards | 0 | **missing** | - |
| Styling & Formatting | Introduction Standards | 0 | **missing** | - |
| Styling & Formatting | Permission Declaration Standards | 0 | **missing** | - |
| Styling & Formatting | Product Label Standards | 0 | **missing** | - |

### Per repository

| repo | verdicts | mean |
|---|---|---|

### Per entity kind

| kind | verdicts | mean |
|---|---|---|

## Axis comparison

Each axis grades its own document set against its own rubric, so these are
rubric-fit scores rather than a head-to-head grade of one text.

| axis | documents | dimensions | overall mean | main dimensions |
|---|---|---|---|---|
| iso_26514 | 0 | 14 | None | 5 |
| github_docs_style | 0 | 18 | None | 5 |

| repo | iso_26514 | github_docs_style |
|---|---|---|

