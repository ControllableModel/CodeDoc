# Per-dimension comparison, every tool (CodeDoc v5)

Pooled over ragflow + joblib + sonnet. One judge (`deepseek-chat`, temperature 0) for every
column, identical entity set and criteria files. v5 is the template revision that restores the
GitHub-standard section names and never omits the Errors or Permissions sections; see
`prompt_variants.md` for the revision history.

### ISO/IEC 26514（14 实体级维度）

| 维度 | 主维度 | CodeDoc v1 | **CodeDoc v5** | RepoAgent | MemDocAgent | v5−最佳基线 |
|---|---|---|---|---|---|---|
| Completeness | Content Quality | 4.58 | **4.54** | 4.80 | 4.72 | **-0.27** ◀ |
| Conciseness | Content Quality | 4.01 | **4.07** | 4.32 | 4.17 | **-0.24** ◀ |
| Correctness | Content Quality | 4.75 | **4.76** | 4.92 | 4.86 | **-0.16** ◀ |
| Comprehensibility | Content Quality | 4.86 | **4.75** | 4.80 | 4.74 | **-0.04** ◀ |
| Structured by Function | Information Structure | 4.98 | **4.94** | 4.86 | 4.98 | **-0.04** ◀ |
| Modularity | Information Structure | 4.98 | **4.94** | 4.77 | 4.98 | **-0.04** ◀ |
| Navigability | Information Structure | 4.98 | **4.95** | 4.68 | 4.97 | **-0.02** ◀ |
| Cultural Neutrality | Internationalization & Localization | 5.00 | **5.00** | 5.00 | 5.00 | **+0.00** |
| Consistency | Content Quality | 4.98 | **4.98** | 4.96 | 4.97 | **+0.01** |
| Legibility | Format & Presentation | 5.00 | **4.99** | 4.85 | 4.95 | **+0.04** |
| Translation-Friendly | Internationalization & Localization | 4.59 | **4.78** | 4.31 | 4.30 | **+0.47** |
| User-Centered Design | Usability & User Experience | 4.10 | **4.19** | 3.27 | 3.39 | **+0.80** |
| Consistent Format | Format & Presentation | 4.90 | **4.92** | 3.91 | 4.09 | **+0.83** |
| Metadata | Information Structure | 4.88 | **4.99** | 1.04 | 1.00 | **+3.95** |

总均分：**CodeDoc v5 4.772** ｜ CodeDoc v1 4.757 ｜ RepoAgent 4.321 ｜ MemDocAgent 4.366

| 主维度 | CodeDoc v1 | **CodeDoc v5** | RepoAgent | MemDocAgent |
|---|---|---|---|---|
| Content Quality | 4.64 | **4.62** | 4.76 | 4.69 |
| Information Structure | 4.96 | **4.96** | 3.84 | 3.98 |
| Format & Presentation | 4.95 | **4.96** | 4.38 | 4.52 |
| Internationalization & Localization | 4.79 | **4.89** | 4.66 | 4.65 |
| Usability & User Experience | 4.10 | **4.19** | 3.27 | 3.39 |

### GitHub 文档风格（18 维度）

| 维度 | 主维度 | CodeDoc v1 | **CodeDoc v5** | RepoAgent | MemDocAgent | v5−最佳基线 |
|---|---|---|---|---|---|---|
| Tutorial Content Guidelines | Article Content Families | 2.58 | **1.05** | 1.01 | 1.05 | **-0.00** ◀ |
| Reference Content | Article Content Families | 3.69 | **5.00** | 4.44 | 4.88 | **+0.12** |
| Content Order | Structure & Organization | 3.26 | **4.91** | 4.18 | 4.10 | **+0.73** |
| Balanced Hierarchy | Structure & Organization | 3.94 | **4.90** | 3.34 | 4.04 | **+0.86** |
| Reuse Instead of Copying | Content Quality | 3.23 | **3.96** | 3.01 | 3.09 | **+0.88** |
| Content Type Consistency | Content Quality | 2.38 | **4.97** | 3.95 | 4.02 | **+0.95** |
| Prerequisites Standards | Content Types & Completeness | 2.89 | **3.89** | 1.90 | 2.88 | **+1.01** |
| Title Standards | Styling & Formatting | 3.58 | **4.89** | 2.96 | 3.71 | **+1.18** |
| Product Label Standards | Styling & Formatting | 3.91 | **4.81** | 3.29 | 3.58 | **+1.23** |
| Introduction Standards | Styling & Formatting | 3.79 | **4.96** | 3.13 | 3.58 | **+1.38** |
| Error Reference Content Guidelines | Article Content Families | 1.72 | **4.33** | 1.39 | 2.85 | **+1.48** |
| Category Title Naming | Structure & Organization | 2.05 | **3.22** | 1.15 | 1.58 | **+1.64** |
| Conceptual Content Guidelines | Article Content Families | 3.69 | **3.42** | 1.24 | 1.54 | **+1.88** |
| Getting Started Content Guidelines | Article Content Families | 3.51 | **3.04** | 1.00 | 1.02 | **+2.02** |
| Process Content Standards | Content Types & Completeness | 4.02 | **4.56** | 1.65 | 1.80 | **+2.76** |
| Permission Declaration Standards | Styling & Formatting | 2.86 | **4.14** | 1.00 | 1.00 | **+3.14** |
| Further Reading Standards | Content Types & Completeness | 4.98 | **4.64** | 1.00 | 1.00 | **+3.64** |
| Next Steps Standards | Content Types & Completeness | 4.39 | **4.69** | 1.01 | 1.02 | **+3.67** |

总均分：**CodeDoc v5 4.187** ｜ CodeDoc v1 3.360 ｜ RepoAgent 2.259 ｜ MemDocAgent 2.597

| 主维度 | CodeDoc v1 | **CodeDoc v5** | RepoAgent | MemDocAgent |
|---|---|---|---|---|
| Content Quality | 2.80 | **4.46** | 3.48 | 3.55 |
| Structure & Organization | 3.09 | **4.34** | 2.89 | 3.24 |
| Styling & Formatting | 3.53 | **4.70** | 2.60 | 2.97 |
| Content Types & Completeness | 4.07 | **4.44** | 1.39 | 1.68 |
| Article Content Families | 3.04 | **3.37** | 1.82 | 2.27 |
