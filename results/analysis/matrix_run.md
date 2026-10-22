# Matrix run: ISO and GitHub documentation sets

* model: `gpt-6-luna` at `https://apic1.ohmycdn.com/v1`
* sampling: relation-stratified, limit 60, seed 42
* the two axes are generated from different templates and written to different
  directories, so no document is shared between rubrics
* 314 documents in 16.0 min, 2 failed, USD 0.3250

| repo | entities in repo | sampled | relation links in sample |
|---|---|---|---|
| ragflow | 38 | 38 | 72 |
| joblib | 749 | 60 | 127 |
| sonnet | 1605 | 60 | 94 |

| axis | template | documents | chars | cost (USD) | failed |
|---|---|---|---|---|---|
| iso_26514 | iso_26514.txt | 158 | 651,517 | 0.1693 | 0 |
| github_docs_style | github.txt | 156 | 625,351 | 0.1557 | 2 |

Output: `outputs\tokenbench_v6/<axis>/<repo>/<entity>.md`

## Failures

* joblib / github_docs_style / externals.loky.backend.popen_loky_posix.Popen: APIConnectionError: Connection error.
* joblib / github_docs_style / _parallel_backends.ParallelBackendBase: APIConnectionError: Connection error.
