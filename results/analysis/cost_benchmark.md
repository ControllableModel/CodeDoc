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


## 7. Large repository — `flask-main` (431 entities: 47 classes, 287 methods, 97 functions)

Workers: 6 generation, 5 judging. Full repository, no sampling.

| phase | calls | in tok | out tok | tok/call | API sec | wall sec |
|---|---|---|---|---|---|---|
| extraction (AST, local) | — | — | — | — | — | 0.1 |
| generation | 431 | 522,561 | 802,019 | 3,073 | 3,762.8 | 733.6 |
| judging | 454 | 988,296 | 345,954 | 2,938 | 1,632.6 | 645.0 |
| **total** | **885** | **1,510,857** | **1,147,973** | **3,004** | **5,395.5** | **1,378.7** |

* **23.0 minutes wall**, **2.66M tokens**, **≈ CNY 12.21** at list price
* **CNY 0.028 per entity**, 3.2 s wall per entity
* judging needed 454 calls for 431 documents: **23 retries (5.3%)**, i.e. the
  unparseable-verdict rate observed in section 5 reproduces at scale, and is **not**
  eliminated by temperature 0. Two documents still ended with no verdict after the
  retries (0.46%), which is reported rather than dropped.

### Scale table

| documents | in tok | out tok | CNY≈ | hours≈ |
|---|---|---|---|---|
| 900 (RQ2.1) | 3,154,922 | 2,397,159 | 25.49 | 0.80 |
| 1,800 (all RQs) | 6,309,844 | 4,794,319 | 50.97 | 1.60 |
| 3,600 (doubled) | 12,619,687 | 9,588,638 | 101.95 | 3.20 |

### Per-entity-kind scores (9 dimensions, 3,866 verdicts)

| dimension | all | class (n=47) | method (n=287) | function (n=97) |
|---|---|---|---|---|
| Return Documentation | 4.93 | 4.60 | 4.98 | 4.93 |
| Dependency Context | 4.93 | 4.74 | 4.94 | 4.97 |
| Parameter Coverage | 4.83 | 4.53 | 4.88 | 4.81 |
| Usage Example Validity | 4.74 | 4.66 | 4.76 | 4.72 |
| Signature Conformance | 4.72 | 4.30 | 4.83 | 4.60 |
| Side-effect & State Documentation | 4.65 | 4.15 | 4.71 | 4.72 |
| Exception Documentation | 4.15 | 3.81 | 4.19 | 4.22 |
| Language Convention Adherence | 3.63 | 3.06 | 3.79 | 3.43 |
| Inheritance/Polymorphism Contract | 3.16 | **4.00** | 3.48 | **1.78** |
| **all** | **4.41** | **4.21** | **4.51** | **4.24** |

Three findings that change the analysis plan:

1. **`Inheritance/Polymorphism Contract` is not applicable to functions and the judge
   charges for it anyway.** A free function has no inheritance contract, yet it scores
   1.78 — the judge reads "not mentioned" as "absent and therefore bad". This is a
   *measurement* artefact, not a quality difference. Non-applicable
   (criterion, entity-kind) pairs must be excluded from aggregation, which is exactly
   the `applicable_to_entity` field already present in the criterion schema. Until
   that is wired into scoring, per-kind means are all biased downward by the
   dimension count.
2. **Classes score lower than methods on six of nine dimensions** (all: 4.21 vs 4.51).
   A class document must cover everything the class does, and the retained 12-section
   structure fits a single callable better than a whole class. This is a real
   difficulty of the new capability, and it belongs in RQ4.1 as a reported result,
   not as a footnote.
3. **`Language Convention Adherence` is the weakest applicable dimension** (3.63; 3.06
   for classes). The 12-section ISO output structure conflicts with in-language
   docstring conventions. Reporting it per criterion set is mandatory, since this is
   the axis the review questioned when it said the dimensions are not specific to code.
