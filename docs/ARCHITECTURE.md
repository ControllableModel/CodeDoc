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
python      stdlib ast + import-graph resolution  calls, called_by, inherits, subclassed_by, instantiated_at, overrides, overridden_by, dispatch_candidates
python      pyright LSP + stdlib ast          same, with type-aware call resolution
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
| Python AST extractor (classes + functions, zero dependencies) | done, benchmarked on 10 repositories |
| Python Pyright extractor (type-aware calls) | done, benchmarked on 10 repositories |
| pyan3 / DOT pipeline 供 | **removed** — DOT survives only as an export format (`deps/export_dot.py`) |
| LSP extractors (class hierarchy, instantiation, overrides) | **skeleton** — `NotImplementedError` with the required requests documented |
| writer prompt blocks for classes/polymorphism | done (data-level); wired into generation during S4 |
| judge driver + aggregation + statistics | done |
| session orchestration (`codedoc/cli.py`) | still contains the generation loop; extracting it into `writer/generate.py` is the next refactor step |
| class entities in generation | **not yet** — the generator documents methods and top-level functions; a class only receives a one-line summary. Wiring class entities is step S4 |

Deliberate choice: an unimplemented capability **raises** instead of silently
degrading to function-only analysis. A silent fallback is how the earlier class
documentation ended up context-free while the paper claimed dependency awareness.

## Prompt budget and the class view

The assembled prompt has a hard cap (`--max_tokens`, characters) because every
extra character is paid for at inference time. Three rules keep it under control
without deleting evidence:

| section | policy |
|---|---|
| criteria (template) | **fixed** — the standard text is never trimmed |
| required output structure | **fixed** — the 12 mandated sections stay in every prompt |
| entity source | budgeted from what the template leaves over; head + tail kept with an explicit elision marker |
| dependency snippets | 20 lines per dependency, at most 6 dependencies |

### Class entities

A class body is a poor prompt (Flask's class is 1,517 lines). The class view
(`writer/classview.py`) is:

* the class declaration — where the bases, i.e. the inheritance, are visible;
* `__init__` **in full** — the constructor is what a class document explains;
* every other method as a **signature only** (parameters + return annotation,
  body dropped).

Method bodies are not lost: each method is its own entity, documented one level
below its class.

### Artifact hierarchy

The generated Markdown mirrors the modelled structure:

```
## Class: `Flask`
<class document>

### Method: `__init__`
<method document>

### Method: `wsgi_app`
<method document>

## Functions
### Function: `send_from_directory`
<function document>
```

Inspect any prompt without a model call:

```bash
python scripts/show_prompt.py --repo targets/flask-main --entity Flask --show-info
```
