# Prompt injection audit and relation-stratified sampling

The review asked what actually reaches the model, and the artifact had no way to
answer. `scripts/audit_prompt_injection.py` now measures it per relation family, per
entity kind, and at the rendered-prompt level.

## 1. Two defects found

| # | defect | evidence | fix |
|---|---|---|---|
| 1 | `attribute_access` was declared in the schema but **no extractor emitted it** — nine relation families promised, eight delivered | audit reported `found=0` for every repository | implemented in `python_ast` (`self.x` / `cls.x` inside methods), `EntityKind.ATTRIBUTE` added; the relation now appears as an `## Attribute access` block |
| 2 | the injected list was **hard-capped at 6** per relation family, so the model saw a truncated dependency set | `max_deps=6` in `get_dep` | every relation is listed; only the *source snippet* is budgeted (20 lines for the first 6). Names cost ~30 characters, bodies ~1 KB, so truncating the list saved almost nothing and hid structure |

Consequence of (1): 733 attribute relations in flask-main, 14,126 in fairseq,
7,502 in pyro, all previously invisible.

## 2. Injection recall (flask-main, 431 entities)

| relation | rendered as | found | injected | recall | entities | covered |
|---|---|---|---|---|---|---|
| calls | Uses | 181 | 181 | 100% | 123 | 123 |
| called_by | Used by | 159 | 159 | 100% | 106 | 106 |
| inherits | Inherits | 18 | 18 | 100% | 18 | 18 |
| subclassed_by | Subclassed by | 18 | 18 | 100% | 10 | 10 |
| instantiated_at | Instantiated at | 22 | 22 | 100% | 12 | 12 |
| overrides | Overrides | 39 | 39 | 100% | 37 | 37 |
| overridden_by | Overridden by | 52 | 52 | 100% | 22 | 22 |
| dispatch_candidates | Dispatch candidates | 155 | 155 | 100% | 33 | 33 |
| attribute_access | Attribute access | 733 | 733 | 100% | 244 | 244 |

Verified on ragflow, numpy, sonnet as well: **9/9 families at 100% recall**, and the
prompt-level check (rendering the prompt and searching for every relation name) reports
`entities_with_missing_relations=0`.

Class view completeness: for 47 classes, **0** dropped method signatures and **0**
missing an existing `__init__`.

## 3. Prompt size after the change

| repository | entities | mean chars | max | >10k | attribute relations | entities with any |
|---|---|---|---|---|---|---|
| ragflow | 38 | 6,047 | 8,936 | 0 | 155 | 74% |
| openui | 165 | 5,224 | 9,774 | 0 | 166 | 36% |
| flask-main | 431 | 5,414 | 10,371 | 1 | 733 | 57% |
| joblib | 749 | 5,502 | 11,816 | 1 | 1,803 | 64% |
| sonnet | 1,605 | 4,906 | 9,800 | 0 | 2,826 | 71% |
| numpy | 2,868 | 5,789 | 11,540 | 10 | 2,127 | 26% |
| pyro | 3,396 | 5,230 | 10,606 | 2 | 7,502 | 66% |
| fairseq | 5,229 | 5,253 | 9,981 | 0 | 14,126 | 64% |

Mean prompts stay at 4.9–6.0k characters. Only 14 of ~14,500 entities exceeded the old
10,000-character guard, and those would have been silently truncated, so the default
`--max_tokens` is raised to 16,000.

## 4. Relation-stratified sampling

A kind-balanced sample is not enough: a repository can have hundreds of methods and
almost no class that overrides anything, so a 60-entity sample can contain zero
override or dispatch relations. `pick_entities` now reserves a quota per relation
family first (subclassed_by 4, instantiated_at 4, overrides 6, dispatch 4, inherits 4,
attribute access 3, called_by 3) and fills the remainder kind-balanced. Deterministic
for a given seed.

Sample of 60 entities per repository — entities carrying each family, old vs new:

| repo | scheme | inherits | subclassed | instantiated | overrides | overridden | dispatch | attribute | calls | called_by |
|---|---|---|---|---|---|---|---|---|---|---|
| numpy | old | 4 | 2 | 9 | **0** | 2 | **1** | 30 | 16 | 14 |
| numpy | **new** | 8 | 6 | 9 | **9** | 6 | **8** | 31 | 14 | 10 |
| fairseq | old | 2 | 2 | 3 | **0** | 2 | **0** | 28 | 13 | 13 |
| fairseq | **new** | 5 | 5 | 8 | **9** | 5 | **11** | 43 | 13 | 10 |
| sonnet | old | 5 | **0** | 4 | 4 | **0** | 3 | 31 | 9 | 9 |
| sonnet | **new** | 5 | 4 | 5 | 7 | 5 | 10 | 38 | 8 | 8 |
| pyro | old | 5 | 3 | 9 | 6 | 2 | 8 | 33 | 10 | 7 |
| pyro | **new** | 12 | 8 | 8 | 9 | 7 | 11 | 43 | 13 | 10 |
| flask-main | old | 7 | 4 | 7 | 5 | 3 | 4 | 29 | 14 | 13 |
| flask-main | **new** | 9 | 7 | 6 | 11 | 6 | 8 | 37 | 9 | 9 |

The stratified sample is what makes a 60-entity sample able to support claims about
class documentation and polymorphism at all.

## 5. Consequence for existing outputs

`outputs/bench_flask` was generated **before** attribute relations existed in the
prompt, so that corpus no longer reflects the current pipeline. Two options:

* keep it for the ISO-vs-practice rubric comparison (judging is prompt-independent for
  the documents themselves) and label it as pre-change;
* regenerate the sampled corpus once the sampling protocol is fixed, which is the
  cleaner choice for anything reported as a result.

## 6. Reproduce

```bash
python scripts/audit_prompt_injection.py --repo flask-main --prompt-check 20
python scripts/audit_prompt_injection.py --repo fairseq --model-kind class
```

Exit status is non-zero when any relation family falls below full recall, so the check
can gate the experiment pipeline.
