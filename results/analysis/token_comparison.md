# Token cost: CodeDoc v6 measured against RepoAgent measured

Every number here comes from an API response field, not an estimate:

* CodeDoc: `usage.prompt_tokens` / `usage.completion_tokens` per call, recorded by
  `codedoc/writer/usage.py` and aggregated in `outputs/matrix_v6/manifest.json`.
* RepoAgent: its own `LLM Prompt Tokens` / `LLM Completion Tokens` debug lines
  (`repo_agent/chat_engine.py`), captured by `scripts/bench_repoagent_tokens.py` with
  `-ll DEBUG` and parsed into `results/analysis/repoagent_tokens.json`.

## CodeDoc v6, all ten repositories, both axes

| | documents | calls | input | output | in/doc | out/doc | cost |
|---|---|---|---|---|---|---|---|
| ISO axis | 578 | 578 | — | — | — | — | $0.63 |
| GitHub axis | 578 | 578 | — | — | — | — | $0.59 |
| **total** | **1,156** | **1,156** | **2,603,460** | **2,182,375** | **2,252** | **1,888** | **$1.22** |

One call per document. The input figure is per document, not per entity, and a document is
one entity: there is no retrieval loop to compound it.

## RepoAgent, measured per repository

RepoAgent documents every file in the target, so its call count scales with files rather than
with the sampled entity set. The per-entity columns below divide by the sampled entity count
for comparability, but the honest reading is the absolute columns.

| repository | .py files | documents | calls | input tok | output tok | in/entity | out/entity | wall |
|---|---|---|---|---|---|---|---|---|
| ragflow | 3 | 2 | 36 | 61,270 | 28,827 | 1,612 | 759 | 155 s |
| openui | 30 | 26 | 168 | 208,241 | 112,860 | 3,471 | 1,881 | 412 s |
| flask-main | 24 | 20 | 442 | 863,852 | 329,909 | 14,398 | 5,498 | 1,091 s |
| joblib | 44 | 39 | 775 | 1,109,052 | 564,767 | 18,484 | 9,413 | 2,076 s |

Against CodeDoc's 2,252 input and 1,888 output per document, RepoAgent ranges from 0.7x
(ragflow, a two-file module) to 8.2x (joblib) the input and 0.4x to 5.0x the output. The
calls-per-entity ratio is the striking part: 0.9 for ragflow, 2.8 for openui, 7.4 for
flask-main, 12.9 for joblib, against CodeDoc's 1.0.

That variance is a property of RepoAgent, not of the measurement: it issues one conversation
per file *plus* retries and per-symbol passes, so a repository whose sampled entities cluster
in a few files costs almost nothing, while one where they are spread across many files costs
an order of magnitude more.

## Why four repositories and not ten

RepoAgent's cost is driven by the whole file set of the target, and three targets have file
counts that put a full measurement out of budget:

| repository | .py files | note |
|---|---|---|
| torch | 2,318 | not measured |
| dify_api | 2,243 | not measured |
| fairseq | 442 | not measured |
| pyro | 306 | not measured |
| numpy | 184 | not measured |
| sonnet | 133 | not measured |

The four measured repositories already span 36 to 775 calls and 1,612 to 18,484 input tokens
per entity, which brackets the quantity the token table needs. Measuring the remaining six is
a further cost of roughly USD 2-3 at the observed rates, which the current generation budget
does not cover.

## What the table should claim

`tables/token.tex` in the draft compares CodeDoc against a method it calls "CodeRepo" and
reports changes from -44% to +891%. That method is not in the experiment set, and the
percentages come from numbers this pipeline cannot reproduce. The measured comparison is:

* CodeDoc's token cost per document is **flat**: one call, 2,252 input, 1,888 output, because
  retrieval is static and happens before the call.
* RepoAgent's is **repository-dependent**: 36 to 775 calls per repository, because it
  documents files rather than entities.

The interesting claim is therefore not a percentage but a shape: a standards-guided,
single-call pipeline has a *predictable* cost per entity, which matters when the corpus is
79,745 entities rather than 578.
