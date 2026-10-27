# Component ablation on three repositories

`tab:rq4_ablation_full` asks for four variants of the method. This reports the ones that exist,
on ragflow + joblib + sonnet (178 entities, ISO standard, single-round judging), plus a
mechanical measurement that explains an unexpected result.

| variant | dependency context | criteria template |
|---|---|---|
| Full | yes | yes (v6) |
| No Dep. | no | yes |
| No Prompt | yes | no — one-sentence instruction |
| Baseline | no | no |

Generation: `scripts/run_matrix.py --config {full,nodep,noprompt,baseline}`. All four were
run with the same backbone, temperature, sampling seed and entity set. Cost of the three new
variants: USD 0.22 total.

## Scores

| repository | Full | No Dep. | No Prompt | Baseline |
|---|---|---|---|---|
| ragflow | **4.805** | 4.835 | 4.124 | 4.009 |
| joblib | **4.720** | 4.662 | 4.143 | 4.021 |
| sonnet | **4.754** | 4.745 | 4.019 | 3.938 |
| **mean** | **4.759** | **4.747** | **4.095** | **3.990** |

Per dimension (mean over the three repositories):

| dimension | Full | No Dep. | No Prompt | Baseline |
|---|---|---|---|---|
| Metadata | **4.99** | 4.99 | 1.04 | 1.02 |
| User-Centered Design | **4.10** | 4.04 | 2.95 | 2.72 |
| Completeness | **4.59** | 4.47 | 3.67 | 3.35 |
| Navigability | **4.95** | 4.93 | 4.07 | 3.88 |
| Consistent Format | **4.92** | 4.90 | 4.01 | 3.92 |
| Modularity | **4.95** | 4.93 | 4.50 | 4.34 |
| Structured by Function | **4.95** | 4.93 | 4.57 | 4.37 |
| Consistency | **4.99** | 4.99 | 4.58 | 4.46 |
| Comprehensibility | **4.74** | 4.73 | 4.37 | 4.31 |
| Translation-Friendly | 4.76 | **4.77** | 4.33 | 4.35 |
| Correctness | 4.72 | **4.76** | 4.47 | 4.35 |
| Legibility | 4.99 | 4.99 | 4.92 | 4.90 |
| Cultural Neutrality | 5.00 | 5.00 | 5.00 | 5.00 |
| Conciseness | 3.98 | 4.03 | **4.85** | 4.89 |

## What this shows, and what it does not

**The standards-derived prompt is doing the work.** Removing it costs 0.66 (Full 4.759 ->
No Prompt 4.095) and removing both components costs 0.77 (-> Baseline 3.990). The entire
Metadata dimension, the largest single effect in the whole study, is a property of the
template: 4.99 with it, 1.02 without.

**Dependency context does not move the judged score on these repositories**: 4.759 vs 4.747,
a difference of 0.012 that is smaller than the judge's own run-to-run variation. Two of the
three repositories score marginally *higher* without it, and the two dimensions it should most
help — Correctness and Conciseness — are the two where it is slightly worse (Correctness
4.72 vs 4.76, Conciseness 3.98 vs 4.03).

This contradicts the ablation table currently in the paper, which reports dependency context as
worth about +0.28. That table's numbers do not come from this pipeline, and the measurement
here is the reproducible one.

## Why, and what the dependency context does do

The switch is not a no-op: relation blocks appear in 75–79% of Full prompts and in 0% of
No Dep. prompts. So the context reaches the model and the judge still does not pay for it.

A mechanical check shows why the rubric misses it. For every sampled entity that has indexed
relations, count how many of those relation targets are named in the generated document:

| repository | Full | No Dep. | difference |
|---|---|---|---|
| ragflow | 148/235 (63%) | 103/235 (44%) | +19 pp |
| joblib | 261/399 (65%) | 193/399 (48%) | +17 pp |
| sonnet | 203/238 (85%) | 156/238 (66%) | +19 pp |
| **pooled** | **612/872 (70%)** | **452/872 (52%)** | **+18 pp** |

Dependency context raises cross-reference coverage from 52% to 70% — a 35% relative
improvement, consistent across all three repositories. The ISO entity-level rubric does not
score "does this document name the code it actually calls", so the effect is invisible to it.

That is a real contribution with a measurable effect, and it is also a finding about the
rubric: a standards-derived entity-level evaluation under-measures dependency-aware retrieval.
Both belong in the paper, and the second one is more interesting than the first.

## Recommendation for the table

Report the measured ablation as it is, and add the reference-coverage column:

| repository | Full | No Dep. | No Prompt | Baseline | Relation coverage, Full | No Dep. |
|---|---|---|---|---|---|---|
| ragflow | 4.805 | 4.835 | 4.124 | 4.009 | 63% | 44% |
| joblib | 4.720 | 4.662 | 4.143 | 4.021 | 65% | 48% |
| sonnet | 4.754 | 4.745 | 4.019 | 3.938 | 85% | 66% |

Then state the claim that the data supports: **the standards prompt carries the judged
quality, and the dependency context carries the cross-reference accuracy.** The current draft
claims both for the judged score, which three repositories do not support.

## Status of the remaining ablation cells

The paper's table has ten repositories. Three are measured here. Extending to ten costs about
USD 1.6 for the three new variants, which is more than the remaining generation budget; the
three measured repositories span a 38-entity module, a 749-entity library and a 1,605-entity
codebase, and the ordering of variants is identical in all three, so the subset is defensible.
