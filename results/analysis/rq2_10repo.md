# RQ2 on ten repositories: Long-Context vs RepoAgent vs CodeDoc v6

Judge `deepseek-chat`, temperature 0, single-round (S) interaction for every column.
Identical entity set per repository (shared sampler, seed 42). Unit of analysis is the
repository (n=10); a repository score is the mean over its sampled entities of the mean over
dimensions.

## ISO/IEC 26514 (14 entity-level dimensions)

| Repository | Long-Context | RepoAgent | **CodeDoc v6** | v6 − RepoAgent |
|---|---|---|---|---|
| dify_api | 4.14 | 4.39 | **4.76** | +0.37 |
| fairseq | 4.16 | 4.11 | **4.75** | +0.64 |
| flask-main | 4.33 | 4.32 | **4.76** | +0.45 |
| joblib | 4.14 | 4.31 | **4.72** | +0.41 |
| numpy | 4.26 | 4.22 | **4.73** | +0.51 |
| openui | 4.13 | 4.34 | **4.67** | +0.33 |
| pyro | 4.11 | 4.24 | **4.71** | +0.46 |
| ragflow | 4.05 | 4.32 | **4.80** | +0.48 |
| sonnet | 4.23 | 4.33 | **4.75** | +0.42 |
| torch | 4.08 | 4.11 | **4.74** | +0.62 |
| **Mean** | **4.164** | **4.269** | **4.739** | **+0.470** |

Per dimension (pooled over the ten repositories):

| Dimension | Category | Long-Context | RepoAgent | **CodeDoc v6** | v6 − best baseline |
|---|---|---|---|---|---|
| Conciseness | Content Quality | 4.76 | 4.26 | **3.99** | **-0.77** ◀ |
| Completeness | Content Quality | 3.94 | 4.68 | **4.49** | **-0.19** ◀ |
| Correctness | Content Quality | 4.62 | 4.87 | **4.70** | **-0.17** ◀ |
| Comprehensibility | Content Quality | 4.48 | 4.70 | **4.69** | **-0.01** ◀ |
| Cultural Neutrality | Internationalization & Localization | 4.99 | 4.95 | **5.00** | **+0.01** |
| Legibility | Format & Presentation | 4.91 | 4.82 | **5.00** | **+0.08** |
| Consistency | Content Quality | 4.72 | 4.89 | **4.98** | **+0.09** |
| Structured by Function | Information Structure | 4.62 | 4.79 | **4.94** | **+0.16** |
| Modularity | Information Structure | 4.58 | 4.71 | **4.94** | **+0.23** |
| Translation-Friendly | Internationalization & Localization | 4.38 | 4.27 | **4.72** | **+0.33** |
| Navigability | Information Structure | 4.12 | 4.62 | **4.95** | **+0.34** |
| User-Centered Design | Usability & User Experience | 3.06 | 3.27 | **4.06** | **+0.79** |
| Consistent Format | Format & Presentation | 4.00 | 3.88 | **4.92** | **+0.91** |
| Metadata | Information Structure | 1.11 | 1.05 | **4.98** | **+3.87** |

## GitHub documentation style (18 dimensions)

| Repository | Long-Context | RepoAgent | **CodeDoc v6** | v6 − RepoAgent |
|---|---|---|---|---|
| dify_api | 2.05 | 2.31 | **4.28** | +1.96 |
| fairseq | 2.13 | 2.20 | **4.26** | +2.06 |
| flask-main | 2.21 | 2.30 | **4.27** | +1.98 |
| joblib | 2.07 | 2.25 | **4.34** | +2.08 |
| numpy | 2.27 | 2.24 | **4.30** | +2.06 |
| openui | 2.04 | 2.32 | **4.25** | +1.94 |
| pyro | 2.23 | 2.28 | **4.28** | +2.00 |
| ragflow | 1.88 | 2.26 | **4.20** | +1.93 |
| sonnet | 2.05 | 2.26 | **4.31** | +2.05 |
| torch | 2.12 | 2.20 | **4.36** | +2.15 |
| **Mean** | **2.107** | **2.263** | **4.284** | **+2.021** |

Per dimension (pooled over the ten repositories):

| Dimension | Category | Long-Context | RepoAgent | **CodeDoc v6** | v6 − best baseline |
|---|---|---|---|---|---|
| Tutorial Content Guidelines | Article Content Families | 1.02 | 1.00 | **1.06** | **+0.04** |
| Reference Content | Article Content Families | 3.82 | 4.49 | **4.99** | **+0.51** |
| Content Order | Structure & Organization | 3.92 | 4.19 | **4.89** | **+0.71** |
| Content Type Consistency | Content Quality | 4.11 | 3.95 | **4.97** | **+0.87** |
| Reuse Instead of Copying | Content Quality | 3.04 | 3.00 | **3.95** | **+0.91** |
| Balanced Hierarchy | Structure & Organization | 2.82 | 3.44 | **4.87** | **+1.43** |
| Product Label Standards | Styling & Formatting | 3.12 | 3.30 | **4.81** | **+1.51** |
| Introduction Standards | Styling & Formatting | 2.86 | 3.10 | **4.96** | **+1.86** |
| Title Standards | Styling & Formatting | 1.94 | 2.98 | **4.91** | **+1.93** |
| Getting Started Content Guidelines | Article Content Families | 1.03 | 1.00 | **3.18** | **+2.14** |
| Category Title Naming | Structure & Organization | 1.20 | 1.14 | **3.34** | **+2.14** |
| Conceptual Content Guidelines | Article Content Families | 1.42 | 1.21 | **3.72** | **+2.29** |
| Error Reference Content Guidelines | Article Content Families | 1.55 | 1.40 | **4.34** | **+2.79** |
| Process Content Standards | Content Types & Completeness | 1.44 | 1.58 | **4.49** | **+2.91** |
| Prerequisites Standards | Content Types & Completeness | 1.54 | 1.95 | **4.97** | **+3.03** |
| Permission Declaration Standards | Styling & Formatting | 1.00 | 1.00 | **4.27** | **+3.27** |
| Further Reading Standards | Content Types & Completeness | 1.04 | 1.00 | **4.65** | **+3.61** |
| Next Steps Standards | Content Types & Completeness | 1.04 | 1.01 | **4.72** | **+3.68** |

## Paired statistics (n = 10 repositories)

Two-sided Wilcoxon signed-rank on the ten repository pairs, Cliff's delta as effect size.
This is the test the paper claims (`Wilcoxon p<0.05`, `Cliff's delta>0.6 in every setting`),
so it is reported for every comparison the table makes.

| axis | comparison | mean difference | Wilcoxon p | Cliff's delta |
|---|---|---|---|---|
| ISO | CodeDoc v6 − RepoAgent | +0.470 | 0.0020 | +1.00 |
| ISO | CodeDoc v6 − Long-Context | +0.576 | 0.0020 | +1.00 |
| ISO | RepoAgent − Long-Context | +0.106 | 0.0488 | +0.52 |
| GitHub | CodeDoc v6 − RepoAgent | +2.021 | 0.0020 | +1.00 |
| GitHub | CodeDoc v6 − Long-Context | +2.177 | 0.0020 | +1.00 |
| GitHub | RepoAgent − Long-Context | +0.156 | 0.0039 | +0.80 |

Every comparison against a baseline clears the claimed thresholds, and the win is unanimous
across repositories: Cliff's delta of +1.00 means CodeDoc v6 outscores the baseline in all ten
paired repositories on both standards, not on average only.

Note that RepoAgent beats Long-Context on both standards (+0.106 ISO, +0.156 GitHub), which
matters for the paper's framing: the second baseline is a floor, not a straw man, and the
difference between the two baselines is itself small. Almost the entire margin over both comes
from the standards-derived structure, which is what the ablation needs to confirm.

## Token cost of the three methods on the same ten repositories

| method | entities | input tok | output tok | in/entity | out/entity | cost |
|---|---|---|---|---|---|---|
| Long-Context | 578 | 191,314 | 264,254 | 331 | 457 | $0.14 |
| CodeDoc v6 | 1,156 docs (578 x 2 axes) | measured per repo in `matrix_run.md` | | | | $1.22 |

The Long-Context baseline is cheap because its prompt is one sentence plus at most 9,000
characters of source, and it produces the shortest documents of any method. That is exactly
why it is a useful floor: it holds the backbone and roughly the source budget constant while
removing the structure, and it loses 0.58 on ISO and 2.18 on GitHub.
