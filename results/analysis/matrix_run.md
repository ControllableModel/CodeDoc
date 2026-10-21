# Matrix run: ISO and GitHub documentation sets

* model: `gpt-6-luna` at `https://apic1.ohmycdn.com/v1`
* sampling: relation-stratified, limit 60, seed 42
* the two axes are generated from different templates and written to different
  directories, so no document is shared between rubrics
* 314 documents in 19.3 min, 2 failed, USD 0.3166

| repo | entities in repo | sampled | relation links in sample |
|---|---|---|---|
| ragflow | 38 | 38 | 72 |
| joblib | 749 | 60 | 127 |
| sonnet | 1605 | 60 | 94 |

| axis | template | documents | chars | cost (USD) | failed |
|---|---|---|---|---|---|
| iso_26514 | iso_26514.txt | 156 | 579,926 | 0.1610 | 2 |
| github_docs_style | github.txt | 158 | 568,421 | 0.1556 | 0 |

Output: `outputs\tokenbench_v4/<axis>/<repo>/<entity>.md`

## Failures

* joblib / iso_26514 / hashing.Hasher: APIConnectionError: Connection error.
* sonnet / iso_26514 / src.recurrent.Conv3DLSTM: APIConnectionError: Connection error.
