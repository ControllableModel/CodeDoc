# Architecture

The repository is organised as **six libraries** so that each concern of the
paper's pipeline has exactly one home. The split exists because reviewers could
not tell which part of the artifact implemented which claim.

| # | Library | Path | Responsibility |
|---|---|---|---|
| 1 | **Criteria** | `codedoc/criteria/` | Standards-derived criterion sets, anchors, provenance, extraction (Phase a) |
| 2 | **Dependencies** | `codedoc/deps/` | Language-agnostic entity/relation extraction, one adapter per language |
| 3 | **Writer** | `codedoc/writer/` | Prompt assembly and LLM access for generation/refinement |
| 4 | **Judge** | `codedoc/judge/` | Criterion-aligned judging, aggregation, agreement and uncertainty statistics |
| 5 | **Targets** | `targets/` | Third-party repositories under analysis (never committed) |
| 6 | **Outputs** | `outputs/` | Generated documentation and judge verdicts (never committed) |

```
                       ┌──────────────────────────┐
   standards docs ───► │ 1 criteria/              │ ── criterion set (JSON) ──┐
   (ISO 26514,        │   sets/*.json            │                           │
    docstring convs.) │   extract.py (Phase a)   │                           │
                       └──────────────────────────┘                           │
                                                                              ▼
   targets/<repo> ───► ┌──────────────────────────┐        ┌──────────────────────────┐
                       │ 2 deps/                  │ ─────► │ 3 writer/                │
                       │   languages/<lang>.py    │ context│   prompt.py (blocks)     │
                       │   schema.py (relations)  │        │   llm.py                 │
                       └──────────────────────────┘        └──────────┬───────────────┘
                                                                      ▼
                                                            outputs/<repo>/*.md
                                                                      │
                       ┌──────────────────────────┐                   │
                       │ 4 judge/                 │ ◄─────────────────┘
                       │   query.py  (prompts)    │  scores_<criteria>/<file>quality.jsonl
                       │   aggregate.py (means)   │
                       │   stats.py (kappa, ICC)  │
                       └──────────────────────────┘
```

## Why the dependency layer is language-agnostic

The paper's claim is about standards-guided generation, not about Python. So a
language contributes only an **extractor**; the relation schema
(`codedoc/deps/schema.py`), the prompt assembly (`codedoc/writer/prompt.py`) and
the judging (`codedoc/judge/`) are shared. That is what makes the multi-language
study a genuine generalisation test instead of a rewrite.

Extractors declare the relations they can actually produce:

```
$ python scripts/probe_relations.py
language    backend          supported relations
python      pyan3 + ast      calls, called_by
java        LSP (java)       calls, called_by, inherits, ... (skeleton)
typescript  LSP (typescript) calls, called_by, inherits, ... (skeleton)
```

`missing_relations()` reports the gap per backend, so no claim in the paper can
outrun the tooling.

## Relation schema

The published method injected direct callers/callees — a function-level notion.
A class has no callees, which is why class documentation had no usable context.

| kind | meaning | typical use |
|---|---|---|
| `calls` / `called_by` | call edges | function & method docs |
| `inherits` / `subclassed_by` | class hierarchy, interfaces | class docs: "inherits X, extended by Y" |
| `instantiated_at` | where instances are created | class docs: "used from `app.make()`" |
| `overrides` / `overridden_by` | method override pairs | polymorphism contract |
| `dispatch_candidates` | same-named implementations | "which implementation may run" |
| `attribute_access` | attribute reads/writes | state contract (optional) |

## Migration status

| area | state |
|---|---|
| criteria library + three shipped sets | done |
| dependency schema, graph helpers, language registry | done |
| Python call-graph extractor (pyan3) | done (parity with the published pipeline) |
| LSP extractors (class hierarchy, instantiation, overrides) | **skeleton** — `NotImplementedError` with the required requests documented |
| writer prompt blocks for classes/polymorphism | done (data-level); wired into generation during S4 |
| judge driver + aggregation + statistics | done |
| session orchestration (`codedoc/cli.py`) | still contains the generation loop; extracting it into `writer/generate.py` and `deps/analyzer.py` is the next refactor step |

Deliberate choice: an unimplemented capability **raises** instead of silently
degrading to function-only analysis. A silent fallback is how the earlier class
documentation ended up context-free while the paper claimed dependency awareness.
