# Matrix run: ISO and GitHub documentation sets

* model: `gpt-6-luna` at `https://apic1.ohmycdn.com/v1`
* sampling: relation-stratified, limit 60, seed 42
* the two axes are generated from different templates and written to different
  directories, so no document is shared between rubrics
* 316 documents in 13.9 min, 0 failed, USD 0.3185

| repo | entities in repo | sampled | relation links in sample |
|---|---|---|---|
| ragflow | 38 | 38 | 72 |
| joblib | 749 | 60 | 127 |
| sonnet | 1605 | 60 | 94 |

| axis | template | documents | chars | cost (USD) | failed |
|---|---|---|---|---|---|
| iso_26514 | iso_26514.txt | 158 | 599,443 | 0.1643 | 0 |
| github_docs_style | github.txt | 158 | 584,394 | 0.1541 | 0 |

Output: `outputs\tokenbench_v5/<axis>/<repo>/<entity>.md`
