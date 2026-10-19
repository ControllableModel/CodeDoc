# Cost projection: ISO axis, full corpus, and the validation suite

Prices: DeepSeek list (CNY 2 / 1M input, CNY 8 / 1M output). Re-check before ordering.
Every unit below is **measured**, not modelled:

| unit | evidence | cost |
|---|---|---|
| generation, per entity | flask-main, 431 docs: 1,213 in / 1,861 out | **¥0.0173** |
| ISO judging (14 entity-level criteria), per document | calibration call on an 11.9k-char doc: 3,488 in / 840 out | ¥0.0137 raw, **¥0.0119** scaled to the corpus mean doc (7,977 chars) |
| practice judging (9 dimensions), per document | flask-main, 454 calls: 2,177 in / 762 out | **¥0.0105** |
| full pipeline, per entity (generate + ISO judge) | derived | **¥0.0292** |
| wall time, per entity (generate + judge, 6/5 workers) | flask-main: 1,378.7 s / 431 | **3.2 s** |

Corpus size, measured locally with the AST extractor (no API cost):

| repository | entities | classes | methods | functions |
|---|---|---|---|---|
| ragflow | 38 | 4 | 27 | 7 |
| openui | 165 | 27 | 66 | 72 |
| flask-main | 431 | 47 | 287 | 97 |
| joblib | 749 | 109 | 459 | 181 |
| sonnet | 1,605 | 321 | 1,021 | 263 |
| numpy | 2,868 | 178 | 878 | 1,812 |
| pyro | 3,396 | 539 | 2,103 | 754 |
| fairseq | 5,229 | 786 | 3,589 | 854 |
| dify_api | 15,813 | 5,386 | 7,991 | 2,436 |
| torch | 49,451 | 5,117 | 23,336 | 20,998 |
| **total** | **79,745** | 12,514 | 39,757 | 27,474 |

## A. Full corpus (not recommended)

| repository | entities | generation | ISO judging | total | wall hours |
|---|---|---|---|---|---|
| ragflow | 38 | 0.7 | 0.5 | 1.1 | 0.0 |
| openui | 165 | 2.9 | 2.0 | 4.8 | 0.1 |
| flask-main | 431 | 7.5 | 5.1 | 12.6 | 0.4 |
| joblib | 749 | 13.0 | 8.9 | 21.8 | 0.7 |
| sonnet | 1,605 | 27.8 | 19.0 | 46.8 | 1.4 |
| numpy | 2,868 | 49.7 | 34.0 | 83.7 | 2.5 |
| pyro | 3,396 | 58.8 | 40.3 | 99.1 | 3.0 |
| fairseq | 5,229 | 90.5 | 62.0 | 152.5 | 4.6 |
| dify_api | 15,813 | 273.8 | 187.4 | 461.2 | 14.1 |
| torch | 49,451 | 856.2 | 586.2 | 1,442.4 | 44.0 |
| **total** | **79,745** | **1,381** | **945** | **≈¥2,326** | **71** |

Cheap ¥2.3k but 71 wall-clock hours, and the large repositories are exactly the ones
where a 60-entity sample is what the protocol calls for anyway. Not recommended.

## B. Re-judge only (documents already generated)

Generation is criteria-independent: the prompt template is the ISO-structure template
in every run, so switching the *judging* criterion set needs no regeneration.

| scope | documents | cost | wall (5 workers) |
|---|---|---|---|
| flask-main | 431 | **¥5.1** | ~6 min |
| all 10 repositories | 79,745 | ¥945 | ~17 h |

This is the cheapest way to obtain the ISO axis for data we already have — and it is
the immediate next step for flask-main.

## C. Sampled corpus (recommended shape)

| plan | entities | generate + ISO judge | wall |
|---|---|---|---|
| 3 repos × 60 | 180 | ¥5.3 | 0.16 h |
| 5 repos × 60 | 300 | ¥8.8 | 0.27 h |
| **10 repos × 60** | **600** | **¥17.5** | **0.53 h** |

Running **both** axes (ISO 14 dimensions + practice 9 dimensions) on the same
documents adds the practice judging pass: 600 × ¥0.0105 ≈ ¥6.3.

## D. Full validation suite

| experiment | documents | cost | wall |
|---|---|---|---|
| RQ1.1 degradation ladder, 7 groups × 30 (judging only) | 210 | 2.5 | 0.19 h |
| RQ1.3 human alignment, 60 pairs (no API) | 0 | 0.0 | — |
| RQ2.1 main table, 5 configs × 3 repos × 60 | 900 | 26.3 | 0.80 h |
| RQ2.2 fairness, 2 baselines × 3 repos × 60 | 360 | 10.5 | 0.32 h |
| RQ3 ablation, 4 configs × 1 repo × 60 | 240 | 7.0 | 0.21 h |
| RQ4.1 class entities (reuses RQ2.1) | 0 | 0.0 | — |
| RQ4.2 multi-language, 2 × 60 | 120 | 3.5 | 0.11 h |
| RQ1.4 judge stability (30 re-runs) | 30 | 0.4 | 0.03 h |
| **total** | **1,860** | **≈¥50** | **1.65 h** |

## E. Tiers

| tier | content | API cost | wall |
|---|---|---|---|
| **T1 最小可信** | flask 431, both axes (reuse docs) + RQ1.1 ladder + RQ1.4 | **≈¥18** | ~1 h |
| **T2 推荐** | 10 repos × 60, both axes + full validation suite | **≈¥65** | ~3 h |
| **T3 全量** | all 79,745 entities, both axes | ≈¥3,300 | ~100 h |

Already spent so far: ragflow ¥1.0 + flask-main ¥12.2 + kind-filter check ¥0.9 + calibration ¥0.02 ≈ **¥14**.

## F. What money is *not* the constraint

The binding constraints for the resubmission are not API spend:

1. **Human annotation** — RQ1.3 (60 pairs blind), RQ3 correctness labelling (40
   entities), and the 3-annotator scores needed for weighted κ / ICC. Zero API cost,
   dominant schedule risk.
2. **Multi-language extractors** — jdtls / tsserver wiring for RQ4.2. Zero API cost,
   several days of engineering.
3. **Baseline operation** — RepoAgent and DocAgent need environment work; their
   generation costs are comparable to ours, not additive in a problematic way.

## G. Immediate next step

ISO axis on the corpus we already have:

```powershell
$env:LLM_KEY="..."; $env:LLM_URL="https://api.deepseek.com/v1"
python scripts/run_judge.py --doc_dir outputs/bench_flask/docs --repo flask-main `
       --criteria iso_26514 --mode multi --entity_level_only
python scripts/analyze_scores.py --scores outputs/bench_flask/docs/scores_iso_26514 `
       --repo flask-main --criteria iso_26514
```

≈ ¥5.1 and 6 minutes, and it yields the ISO-vs-practice comparison on identical
documents — the direct answer to the review's complaint that the rubric dimensions are
not specific to code.


## H. Re-priced for the production endpoint (gpt-6-luna, USD)

The figures above are DeepSeek list prices in CNY. The console and the pipeline now run
against `gpt-6-luna` at `https://apic1.ohmycdn.com/v1`, priced in USD with two context
tiers and four service modes:

| | short context (<=272K) | long context (>272K) |
|---|---|---|
| input | $0.09 / M | $0.18 / M |
| cached input | $0.009 / M | $0.018 / M |
| cache creation | $0.1125 / M | $0.225 / M |
| output | $0.45 / M | $0.675 / M |
| flex / batch | half of standard | half of standard |
| priority | double of standard | double of standard |

Measured on the real endpoint (same prompts, richer relation sources):

| unit | tokens | cost (standard, short) |
|---|---|---|
| one generation | ~1,700 in / ~1,850 out | **$0.00099** |
| one ISO judging pass (14 dims) | ~2,500 in / ~900 out | ~$0.00063 |
| full pipeline per document | — | **~$0.0016** |

| scope | documents | cost |
|---|---|---|
| 900 (RQ2.1 main table) | 900 | ~$1.5 |
| whole validation suite | 1,800 | ~$2.9 |
| full corpus, both axes | 79,745 | ~$129 |

So the API budget is no longer a consideration at all: the entire planned experiment
matrix is a few dollars, and even dumping the whole corpus is cheaper than the review
round-trip. The binding constraints stay human annotation and the multi-language
extractors.

Notes:
* cached input is billed at one tenth of fresh input, so repeated runs over the same
  prompts get cheaper; the console records cached tokens when the provider reports them.
* the tier is chosen by prompt length, so the long-context rates only bite on prompts
  above 272K tokens — far above our largest (18.9K characters).
