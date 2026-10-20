# CodeDoc console

A local dashboard for the documentation pipeline: pick a criterion set, a repository,
and a full or sampled analysis; browse every file that participates in generation;
click an entity to see its source, the **exact prompt** that would be sent, the
extracted relations, the model parameters, and the generated document.

```
python webapp/server.py --port 8765
# open http://127.0.0.1:8765/
```

## Why it is built this way

* **stdlib only.** `http.server` plus static HTML/CSS/JS — no npm, no build step, no
  framework. Reproduction must not depend on a front-end toolchain.
* **Localhost by default.** The console can hold an API key, so it binds to
  `127.0.0.1` and the key is never sent back to the browser (only "configured" plus a
  masked hint).
* **Long work is a job.** Building the dependency index takes milliseconds on `ragflow`
  and about a minute on `torch`, so `GET /api/analyze` returns a job id and the page
  polls `GET /api/job`. Results are cached per (repo, path, mode, limit, seed).
* **Every number on screen is measured.** Generation returns the token counts the API
  reported and the resulting cost, accumulated in the status bar for the session.

## Panels

| area | contents |
|---|---|
| top bar | repository, custom path, full vs sampled analysis, sample size, seed |
| left | every source file that contributes entities, with per-file entity counts |
| middle | entity chips per file; source view and the *injected view* side by side |
| right | tabs: **prompt** (verbatim), **document** (generated), **relations** (per block), **model params** |
| middle, third tab | **dependency graph** — force-directed canvas, relation-kind filters, focus-on-entity with depth, click a node to open it |
| top bar | **生成全部** — batch-generate every entity in the current selection, with live progress, token/cost totals and failure count |
| drawer | API key, base URL, model, temperatures, prompt cap, source budget, template, criterion sets with per-kind applicability |

## API

| route | purpose |
|---|---|
| `GET /api/bootstrap` | config (key masked), repositories, criterion sets, templates |
| `GET /api/criteria?id=` | criteria with level and per-entity-kind applicability |
| `GET /api/analyze?repo&path&mode&limit&seed` | starts a job, returns `{job}` |
| `GET /api/job?id=` | job status and the entity/file listing |
| `GET /api/entity?…&qname=` | source, injected view, prompt, relations, params |
| `GET /api/document?repo&qname` | a previously generated document, if any |
| `POST /api/config` | persist runtime configuration |
| `POST /api/generate` | generate one document; returns text, tokens, cost, seconds |

## Configuration file

`webapp/config.local.json` (gitignored) holds the runtime settings. Environment
variables win over it, so a shell session does not have to paste the key into the form:

```powershell
$env:LLM_KEY="sk-..."; $env:LLM_URL="https://api.deepseek.com/v1"; $env:MODEL="deepseek-chat"
```

Generated documents are written to `outputs/console/<repo>/<entity>.md` alongside the
prompt that produced them (`<entity>.prompt.txt`), which is the audit trail for any
number shown in the UI.

## Batch generation

`POST /api/generate_all` runs the whole selection concurrently (default 5 workers).
Sequentially, 38 entities took 7 min 33 s; at 6 workers the same repository needs
1 min 09 s. Progress, tokens and cost are reported per completion and the job can be
cancelled.

Accounting note: usage is attributed **by per-call tag**, not by a positional snapshot
of the recorder. Under concurrency a snapshot also captures sibling threads' records,
which inflated the batch total by roughly the worker count (38 entities reported
6,765 input tokens each instead of ~1,200).

## Graph data

`GET /api/graph?repo&mode&limit&seed&focus&depth&kinds` returns nodes and edges.
Default edge kinds are the class-level relations (inheritance, subclassing,
instantiation, overriding, dispatch); `calls`, `called_by` and `attribute_access` are
opt-in, because a call graph over a whole repository is unreadable. With `focus` set,
the server returns the neighbourhood of that entity and adds the call and attribute
edges for it. Node labels are disambiguated by module suffix and then by full
qualified name, so two classes called `Blueprint` do not appear to be one node.

## What the prompt carries

Input tokens are the cheap side of the bill and output is the expensive one, so every
relation target now arrives with its **source**, not just its name:

| block | payload |
|---|---|
| `Uses` / `Used by` | every callee/caller listed; the first 10 also carry up to 40 lines of source |
| `Inherits` / `Subclassed by` | base class / subclass **class view** (declaration + `__init__` + method signatures), up to 40 lines |
| `Overrides` / `Overridden by` | the parent implementation body, up to 40 lines |
| `Instantiated at` / `Dispatch candidates` | the constructing or sibling implementation, up to 40 lines |
| `Attribute access` | the assignment that defines the attribute (`self.config = ...`), falling back to the name when the class never assigns it itself |

Measured effect (ragflow, same four entities before and after): 1,217 -> 1,359 input
tokens, 1,780 -> 2,228 output tokens, CNY 0.0167 -> 0.0205 per entity. The output grows
because a better-grounded prompt yields a longer document, which is the point.

The prompt cap is raised to 40,000 characters to leave room for the relation sources;
mean prompt length on flask-main is 5.9k characters and the largest is 18.9k.

## Models that reject `max_tokens`

Newer OpenAI-family models (`gpt-6-luna` and friends) reject `max_tokens` and require
`max_completion_tokens`. The installed SDK (openai 1.3.0) has no typed kwarg for it, so
the console sends it through `extra_body`. Both the writer and the judge honour the
same flag (`use_max_completion_tokens`).

Cost is computed from `price_in_per_m` / `price_out_per_m` in the config file. The
defaults are DeepSeek list prices and are **wrong for any other endpoint** — set them
before trusting the CNY figures on screen.

## Judging

The console scores a generated document under any rubric without leaving the page: the
`judge` tab shows the main dimensions, every dimension, and the judge's evidence, and a
`batch judge` button runs the same over the current selection. Scores are written next to
the documents under `scores_<axis>/` and can be re-read for free.

The judge is a **separate model** from the generator. `gpt-6-luna` rejects
`temperature` 0 ("Only the default (1) value is supported"), and a scoring instrument
must run at a fixed temperature to be reproducible, so judging defaults to
`deepseek-v4-flash` at temperature 0. Each score records the model, the temperature it
actually ran at, and a `temperature_forced` flag.

Entity-applicable dimensions are selected with `criterion_set.entity_level()` (the
criterion's `level` field), not with `applies_to(kind)`: a dimension that names no kinds
applies to every kind, so the kind test silently keeps all 26 ISO dimensions instead of
the 14 that govern a single entity.

## RepoAgent baseline

`scripts/run_repoagent.py` runs the published RepoAgent over the same entity set and
adapts its output so the same judge can score it. Four obstacles, each of which would
otherwise have produced a quietly unfair comparison:

* **Entity scope.** RepoAgent documents every object it parses, and the working trees held
  13,019 entities against our 578. The working copy is pruned to the sampled entities,
  with kept objects sliced from the original source. Nested entities (closures, classes
  built inside factories) are documented too: because RepoAgent walks the whole AST, the
  pruner keeps their outermost enclosing definition rather than dropping them.
* **Its own .gitignore.** When the target has no `.gitignore`, RepoAgent falls back to the
  one shipped with its repository, which ignores `lib/`, `build/`, `dist/` and more. That
  silently dropped every sampled entity under such a directory (numpy lost 9 files, 16
  entities). The working tree now carries a permissive `.gitignore`.
* **Git dependency.** Its ChangeDetector drives everything through GitPython, so a plain
  directory fails with InvalidGitRepositoryError; each working tree is git-initialised.
* **Temperature.** The CLI default is 0.2 and gpt-6-luna accepts only the default, so the
  run appears to hang while llama_index retries. Pinned to 1, matching CodeDoc.

Coverage after the fixes: 578/578 sampled entities, per repository, zero missing.
