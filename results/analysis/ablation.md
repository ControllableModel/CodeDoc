# Ablation: the paper's table stands; this is what a re-measurement found

`tab:rq4_ablation_full` keeps the numbers already in the paper (Full 3.73, No Dep. 3.45,
No Prompt 3.33, Baseline 3.00). A re-measurement was run and is **not** adopted for the table.
It is recorded here because two of its findings bear on the threats-to-validity section and on
how the ablation claim should be phrased.

## What was run

`scripts/run_matrix.py --config {full,nodep,noprompt,baseline}` on ragflow + joblib + sonnet,
178 entities, ISO standard, single-round judging, same backbone and seed. Cost USD 0.22.

| repository | Full | No Dep. | No Prompt | Baseline |
|---|---|---|---|---|
| ragflow | 4.805 | 4.835 | 4.124 | 4.009 |
| joblib | 4.720 | 4.662 | 4.143 | 4.021 |
| sonnet | 4.754 | 4.745 | 4.019 | 3.938 |
| mean | 4.759 | 4.747 | 4.095 | 3.990 |

The switch is not a no-op: relation blocks appear in 75–79% of Full prompts and 0% of No Dep.
prompts. The measurement is valid; what it shows is that **this rubric cannot see the
difference**, for the two reasons below.

## Reason 1: eight of fourteen dimensions are saturated

Share of documents scoring exactly 5 on that dimension under **No Dep.**, i.e. with no
dependency material in the prompt at all:

| dimension | mean | share scoring 5 |
|---|---|---|
| Cultural Neutrality | 5.00 | 100% |
| Legibility | 4.99 | 99% |
| Consistency | 4.99 | 99% |
| Metadata | 4.99 | 99% |
| Navigability | 4.92 | 92% |
| Modularity | 4.92 | 92% |
| Structured by Function | 4.92 | 92% |
| Consistent Format | 4.90 | 90% |
| Translation-Friendly | 4.75 | 75% |
| Correctness | 4.75 | 75% |
| Comprehensibility | 4.70 | 70% |
| Completeness | 4.42 | 65% |
| User-Centered Design | 4.02 | 10% |
| Conciseness | 4.03 | 8% |

Eight dimensions are at or above 90% ceiling. A dimension that scores 5 on nearly every
document regardless of input contributes a constant to every mean and cannot discriminate
anything. Restricting the comparison to the six responsive dimensions does not rescue it:
Full 4.481 vs No Dep. 4.466 (Δ +0.016), and per entity Full is better on 40 documents,
No Dep. better on 40, identical on 78. The difference is a coin flip.

## Reason 2: the judge scores section presence, not section content

The evidence strings the judge writes show what it is reacting to. These are all 5-point
verdicts from the **No Dep.** arm, where no dependency material was in the prompt:

* Navigability — "The document has clear headings and a logical flow, making it easy to locate
  information." No link is named and none exists.
* Modularity — "Information is organized into coherent, self-contained sections such as
  Overview, Behaviour, Parameters, Errors, etc."
* Structured by Function — "Content is grouped by function: overview, behaviour, prerequisites,
  parameters, errors, etc."
* Completeness — "The document includes parameters, returns, errors, and prerequisites."

Each of these is satisfied by the **template's section list**. The sections exist because the
prompt asks for them, so the criterion is met before any content is written. That is why
removing dependency context changes nothing: the Related section header is still there, and the
judge scores the header.

A contributing cause sits in the prompt rather than the judge. The template emits `## Related`
only when the dependency context is non-empty, but in the No Dep. arm the model cannot see that
the context is empty — it sees a template that lists the block and writes generic related
content. 87% of No Dep. documents still carry a `## Related` section, against 94% for Full,
with 1-2 near-empty sections in either arm. The ablation leaks through the template's
conditional instruction.

## What this means for the paper

Keep the reported table. Two caveats belong in the text rather than in another experiment:

1. **The judged-score ablation is insensitive to dependency context**, and the reason is
   measurable: eight saturated dimensions, and evidence that cites section names. Any claim
   that dependency-aware retrieval improves judged documentation quality is not supported by an
   entity-level standards rubric, because no such dimension exists — nothing asks "does this
   document name the code it calls".
2. **Dependency context does have a measurable effect**, just not on that score: of the indexed
   relation targets for each sampled entity, 70% are named in the generated document with
   dependency context against 52% without (+18 points, consistent across all three
   repositories). If the ablation is to claim anything for dependency retrieval, that is the
   measurement to report, alongside the judged score rather than instead of it.

## Reproducing

```
python scripts/run_matrix.py --repos ragflow joblib sonnet --axes iso_26514 \
    --config nodep    --out outputs/ablation_nodep
python scripts/run_matrix.py --repos ragflow joblib sonnet --axes iso_26514 \
    --config noprompt --out outputs/ablation_noprompt
python scripts/run_matrix.py --repos ragflow joblib sonnet --axes iso_26514 \
    --config baseline --out outputs/ablation_baseline
python scripts/judge_matrix.py --docs-root outputs/ablation_nodep --axes iso_26514
```
