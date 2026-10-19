# Cost and latency benchmark (DeepSeek, measured)

Every figure below comes from `usage.prompt_tokens` / `usage.completion_tokens` in
the API responses (`codedoc/writer/usage.py`), not from character estimates.

* model: `deepseek-chat` (endpoint `https://api.deepseek.com/v1`)
* criteria: `practice_docstring` (9 entity-level dimensions, multi-judge mode = 1 call per document)
* date: measured on the current pipeline (relations + class view + prompt budget)

## 1. Smoke test — one entity

Entity `Flask.__init__` in `targets/flask-main`.

| phase | calls | in tok | out tok | API sec |
|---|---|---|---|---|
| generation | 1 | 1,724 | 2,369 | 10.71 |
| judge (9 dims) | 1 | 2,665 | 799 | 3.64 |
| **total** | **2** | **4,389** | **3,168** | **14.35** |

Result: prompt 7,634 chars accepted; 9,843 chars generated with all 12 required
sections present; 9/9 dimensions parsed; no truncation (`finish_reason=stop`).

## 2. Small repository — `ragflow` (38 entities: 4 classes, 27 methods, 7 functions)

Workers: 4 for generation, 3 for judging. Extraction (AST) is free and local.

| phase | calls | in tok | out tok | tok/call | API sec | wall sec |
|---|---|---|---|---|---|---|
| extraction (AST) | — | — | — | — | — | ~0 |
| generation | 38 | 51,167 | 70,050 | 3,189 | 316.4 | 98.0 |
| judging | 38 | 81,298 | 28,990 | 2,902 | 147.3 | 91.3 |
| **total** | **76** | **132,465** | **99,040** | **3,046** | **463.7** | **189.2** |

* throughput: **5.0 s wall per entity** (generate + judge), 0.20 entities/s
* per entity: **3,486 input / 2,606 output** tokens
* judging costs more input than generation (81k vs 51k): the document is fed in
  together with the criterion specification, and the document is longer than the prompt.
* judging wall time includes a fixed 2 s sleep per call in `solo_query`.

## 3. Extrapolation to the experiment plan

Linear in documents, using the measured per-document unit above.
Prices are DeepSeek list prices (¥2 / 1M input, ¥8 / 1M output) and are
**orientation only** — re-check at order time.

| scale | docs | in tok | out tok | CNY≈ | hours≈ |
|---|---|---|---|---|---|
| RQ2.1 main table (5 config × 3 repos × 60) | 900 | 3,137,329 | 2,345,684 | 25.04 | 1.25 |
| RQ2.2 fairness (2 × 3 × 60) | 360 | 1,254,932 | 938,274 | 10.02 | 0.50 |
| RQ3 ablation (4 × 1 × 60) | 240 | 836,621 | 625,516 | 6.68 | 0.33 |
| RQ4.1 class entities (3 × 60) | 180 | 627,466 | 469,137 | 5.01 | 0.25 |
| RQ4.2 multi-language (2 × 60) | 120 | 418,311 | 312,758 | 3.34 | 0.17 |
| **all RQs** | **1,800** | **6,274,658** | **4,691,368** | **50.08** | **2.49** |

**Reading**: the full planned matrix costs ≈ ¥50 and ≈ 2.5 wall-clock hours at the
current concurrency. Consequences:

1. Cost is not the binding constraint — **the binding constraint is the human
   annotation work** (RQ1.3, D3) and the multi-language extractor work (RQ4.2).
2. There is room to afford the expensive judging mode where it matters: one
   per-dimension table (14 single-dimension calls per document) on 30 documents
   costs ≈ 420 calls ≈ ¥12, well within budget.

## 4. Quality signal from this run (not a result, a sanity check)

Mean dimension scores over 38 entities (all parsed, 342 verdicts):

| dimension | n | mean | sd |
|---|---|---|---|
| Dependency Context | 38 | 4.82 | 0.51 |
| Return Documentation | 38 | 4.71 | 0.82 |
| Side-effect & State Documentation | 38 | 4.68 | 0.73 |
| Parameter Coverage | 38 | 4.61 | 0.93 |
| Signature Conformance | 38 | 4.47 | 1.02 |
| Usage Example Validity | 38 | 4.39 | 0.87 |
| Exception Documentation | 38 | 3.79 | 1.13 |
| Language Convention Adherence | 38 | 2.89 | 1.12 |
| Inheritance/Polymorphism Contract | 38 | 1.92 | 1.13 |
| **all** | **342** | **4.03** | — |

Three observations worth carrying into the paper:

* `Dependency Context` is the **highest** dimension — consistent with the relation
  blocks actually being in the prompt (previously they were silently dropped by the
  missing `{relations}` placeholder).
* `Inheritance/Polymorphism Contract` is the **lowest** — expected: only 4 of 38
  entities are classes, and most ragflow classes have no project-internal base.
  Per-kind reporting (RQ4.1) is therefore required, not optional.
* `Language Convention Adherence` is low (2.89) — the retained 12-section ISO output
  structure conflicts with in-language docstring conventions. This is a **real design
  tension**, not a bug: it should be reported honestly and examined per criterion set
  (`practice_docstring` vs `iso_26514`), because it is exactly the axis the review
  questioned when it said the dimensions are not specific to code.

## 5. Two defects found by this benchmark and fixed

| # | defect | evidence | fix |
|---|---|---|---|
| 1 | judging at `temperature=1` intermittently emits unparseable JSON | 2/38 documents (5.3%) returned no verdict, with `finish_reason=stop` and no API error; both parsed on the first retry | `judge_temperature` is now configurable and defaults to **0**; `judge_with_retry()` retries up to 3 times and reports the attempt count |
| 2 | a failed parse silently dropped the document from the analysis | the first run reported "0 failed calls" while 2 documents had no scores | the drivers warn on an unparseable verdict instead of recording an empty one |

Consequence for RQ1.4 (stability): with a temperature of 0 the repeated-run check
becomes trivially deterministic, so stability must be measured by an explicit
variance experiment (repeat at a small non-zero temperature, or repeat with a
different judge model) rather than by re-running the same configuration.

## 6. Reproduce

```powershell
$env:LLM_KEY="..."; $env:LLM_URL="https://api.deepseek.com/v1"
python scripts/smoke_llm.py --repo targets/flask-main --entity Flask.__init__
python scripts/bench_small_repo.py --repo ragflow --limit 38 --workers 4 --judge_workers 3 `
       --model deepseek-chat --criteria practice_docstring
```

Artifacts per run: `outputs/bench_<repo>/{docs,scores.json,cost_report.json,run_meta.json}`.
