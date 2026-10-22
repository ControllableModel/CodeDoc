# Per-dimension comparison, every tool (CodeDoc v6)

Pooled over ragflow + joblib + sonnet. One judge (`deepseek-chat`, temperature 0) for every
column, identical entity set and criteria files. v6 is the current template: v5 plus a
dedicated Prerequisites section. Revision history and the failed hypotheses are in
`prompt_variants.md`.

### ISO/IEC 26514（14 个实体级维度）

| 维度 | 主维度 | CodeDoc v6 | CodeDoc v1 | RepoAgent | MemDocAgent | v6−最佳基线 |
|---|---|---|---|---|---|---|
| Conciseness | Content Quality | **4.04** | 4.01 | 4.32 | 4.17 | **-0.28** ◀ |
| Completeness | Content Quality | **4.59** | 4.58 | 4.80 | 4.72 | **-0.21** ◀ |
| Correctness | Content Quality | **4.76** | 4.75 | 4.92 | 4.86 | **-0.16** ◀ |
| Comprehensibility | Content Quality | **4.76** | 4.86 | 4.80 | 4.74 | **-0.03** ◀ |
| Structured by Function | Information Structure | **4.95** | 4.98 | 4.86 | 4.98 | **-0.03** ◀ |
| Modularity | Information Structure | **4.95** | 4.98 | 4.77 | 4.98 | **-0.02** ◀ |
| Navigability | Information Structure | **4.97** | 4.98 | 4.68 | 4.97 | **-0.00** ◀ |
| Cultural Neutrality | Internationalization & Localization | **5.00** | 5.00 | 5.00 | 5.00 | **+0.00** |
| Consistency | Content Quality | **4.98** | 4.98 | 4.96 | 4.97 | **+0.01** |
| Legibility | Format & Presentation | **4.99** | 5.00 | 4.85 | 4.95 | **+0.04** |
| Translation-Friendly | Internationalization & Localization | **4.78** | 4.59 | 4.31 | 4.30 | **+0.47** |
| User-Centered Design | Usability & User Experience | **4.10** | 4.10 | 3.27 | 3.39 | **+0.72** |
| Consistent Format | Format & Presentation | **4.95** | 4.90 | 3.91 | 4.09 | **+0.87** |
| Metadata | Information Structure | **4.98** | 4.88 | 1.04 | 1.00 | **+3.94** |

总均分：**CodeDoc v6 4.773** ｜ CodeDoc v1 4.757 ｜ RepoAgent 4.321 ｜ MemDocAgent 4.366

| 主维度 | CodeDoc v6 | CodeDoc v1 | RepoAgent | MemDocAgent |
|---|---|---|---|---|
| Content Quality | **4.63** | 4.64 | 4.76 | 4.69 |
| Information Structure | **4.96** | 4.96 | 3.84 | 3.98 |
| Format & Presentation | **4.97** | 4.95 | 4.38 | 4.52 |
| Internationalization & Localization | **4.89** | 4.79 | 4.66 | 4.65 |
| Usability & User Experience | **4.10** | 4.10 | 3.27 | 3.39 |

### GitHub 文档风格（18 个维度）

| 维度 | 主维度 | CodeDoc v6 | CodeDoc v1 | RepoAgent | MemDocAgent | v6−最佳基线 |
|---|---|---|---|---|---|---|
| Tutorial Content Guidelines | Article Content Families | **1.12** | 2.58 | 1.01 | 1.05 | **+0.06** |
| Reference Content | Article Content Families | **4.99** | 3.69 | 4.44 | 4.88 | **+0.11** |
| Content Order | Structure & Organization | **4.94** | 3.26 | 4.18 | 4.10 | **+0.76** |
| Balanced Hierarchy | Structure & Organization | **4.91** | 3.94 | 3.34 | 4.04 | **+0.87** |
| Reuse Instead of Copying | Content Quality | **3.97** | 3.23 | 3.01 | 3.09 | **+0.89** |
| Content Type Consistency | Content Quality | **4.97** | 2.38 | 3.95 | 4.02 | **+0.96** |
| Title Standards | Styling & Formatting | **4.89** | 3.58 | 2.96 | 3.71 | **+1.18** |
| Product Label Standards | Styling & Formatting | **4.85** | 3.91 | 3.29 | 3.58 | **+1.27** |
| Introduction Standards | Styling & Formatting | **4.96** | 3.79 | 3.13 | 3.58 | **+1.38** |
| Error Reference Content Guidelines | Article Content Families | **4.26** | 1.72 | 1.39 | 2.85 | **+1.41** |
| Category Title Naming | Structure & Organization | **3.30** | 2.05 | 1.15 | 1.58 | **+1.72** |
| Conceptual Content Guidelines | Article Content Families | **3.49** | 3.69 | 1.24 | 1.54 | **+1.95** |
| Getting Started Content Guidelines | Article Content Families | **3.09** | 3.51 | 1.00 | 1.02 | **+2.07** |
| Prerequisites Standards | Content Types & Completeness | **4.97** | 2.89 | 1.90 | 2.88 | **+2.09** |
| Process Content Standards | Content Types & Completeness | **4.49** | 4.02 | 1.65 | 1.80 | **+2.69** |
| Permission Declaration Standards | Styling & Formatting | **4.25** | 2.86 | 1.00 | 1.00 | **+3.25** |
| Further Reading Standards | Content Types & Completeness | **4.64** | 4.98 | 1.00 | 1.00 | **+3.64** |
| Next Steps Standards | Content Types & Completeness | **4.68** | 4.39 | 1.01 | 1.02 | **+3.67** |

总均分：**CodeDoc v6 4.267** ｜ CodeDoc v1 3.360 ｜ RepoAgent 2.259 ｜ MemDocAgent 2.597

| 主维度 | CodeDoc v6 | CodeDoc v1 | RepoAgent | MemDocAgent |
|---|---|---|---|---|
| Content Quality | **4.47** | 2.80 | 3.48 | 3.55 |
| Structure & Organization | **4.39** | 3.09 | 2.89 | 3.24 |
| Styling & Formatting | **4.74** | 3.53 | 2.60 | 2.97 |
| Content Types & Completeness | **4.70** | 4.07 | 1.39 | 1.68 |
| Article Content Families | **3.39** | 3.04 | 1.82 | 2.27 |
