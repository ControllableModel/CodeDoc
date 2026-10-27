# Matrix run: ISO and GitHub documentation sets

* model: `gpt-6-luna` at `https://apic1.ohmycdn.com/v1`
* sampling: relation-stratified, limit 60, seed 42
* the two axes are generated from different templates and written to different
  directories, so no document is shared between rubrics
* 158 documents in 3.1 min, 0 failed, USD 0.0255

| repo | entities in repo | sampled | relation links in sample |
|---|---|---|---|
| ragflow | 38 | 38 | 72 |
| joblib | 749 | 60 | 127 |
| sonnet | 1605 | 60 | 94 |

| axis | template | documents | chars | cost (USD) | failed |
|---|---|---|---|---|---|
| iso_26514 | iso_26514_v6.txt | 158 | 97,986 | 0.0255 | 0 |

Output: `outputs\ablation_baseline/<axis>/<repo>/<entity>.md`
