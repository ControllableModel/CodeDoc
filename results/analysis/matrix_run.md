# Matrix run: ISO and GitHub documentation sets

* model: `gpt-6-luna` at `https://apic1.ohmycdn.com/v1`
* sampling: relation-stratified, limit 60, seed 42
* the two axes are generated from different templates and written to different
  directories, so no document is shared between rubrics
* 1156 documents in 36.6 min, 0 failed, USD 1.2164

| repo | entities in repo | sampled | relation links in sample |
|---|---|---|---|
| dify_api | 15813 | 60 | 95 |
| fairseq | 5229 | 60 | 108 |
| flask-main | 431 | 60 | 103 |
| joblib | 749 | 60 | 127 |
| numpy | 2868 | 60 | 91 |
| openui | 165 | 60 | 57 |
| pyro | 3396 | 60 | 126 |
| ragflow | 38 | 38 | 72 |
| sonnet | 1605 | 60 | 94 |
| torch | 49451 | 60 | 115 |

| axis | template | documents | chars | cost (USD) | failed |
|---|---|---|---|---|---|
| iso_26514 | iso_26514_v6.txt | 578 | 2,441,276 | 0.6289 | 0 |
| github_docs_style | github_v6.txt | 578 | 2,380,866 | 0.5875 | 0 |

Output: `outputs\matrix_v6/<axis>/<repo>/<entity>.md`
