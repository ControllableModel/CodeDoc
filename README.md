# CodeDoc — Standards-Guided and Dependency-Aware Code-Level Documentation Generation

This repository is the artifact and reference implementation of the paper
**"Standards-Guided and Dependency-Aware Code-Level Documentation Generation"**
(manuscript under review).

CodeDoc formulates code-level documentation generation as a **standards-guided software
engineering task** instead of an unconstrained text-generation problem. Two things are
therefore explicit and reusable rather than implicit in a prompt: the **quality criteria**
the documentation must satisfy, derived from authoritative documentation standards, and the
**dependency structure** of the repository, which supplies the context each entity is
documented with.

The same criterion set is used twice — to steer generation and to score the result — so a
document is never judged against standards it was not asked to meet.

---

## 1. How CodeDoc works

| Phase | Component | What it does |
|---|---|---|
| **(a) Criteria extraction** — once, offline | `codedoc/criteria/` (`extract.py`, `clauses.py`, `schema.py`, `registry.py`) + `criteria/sets/*.json` | Turns each authoritative source into an explicit criterion set: a flat list of criteria, each with a category, a level (`entity` or `document-set`), and scale anchors. Committed as JSON, so it can be inspected and reused independently of any model. |
| **(b) Stage 1 — static analysis** | `codedoc/deps/` (`relations_index.py`, `languages/python_ast.py`, optional `python_pyright.py`) | Builds a typed relation index over the whole repository: entities with exact source spans, plus `calls`/`called_by`, `inherits`/`subclassed_by`, `instantiated_at`, `overrides`/`overridden_by`, `dispatch_candidates`, and `attribute_access`. |
| **(b) Stage 2 — generation** | `codedoc/writer/` (`prompt.py`, `llm.py`, `classview.py`, `templates/`) | Assembles a dependency-aware prompt for one entity (its own source, file path, relation context with relation-target source, the criteria, and the required output structure) and calls any OpenAI-compatible endpoint. |
| **(b) Stage 3 — judging** | `codedoc/judge/` (`query.py`, `aggregate.py`, `stats.py`) | Scores a document dimension by dimension against the same criterion set, returning an integer score and the evidence for it, then aggregates per dimension, per main dimension, per repository, and per entity kind. |

Two design decisions worth stating, because they are what the evaluation hinges on:

* **The unit of generation and the unit of evaluation match.** Both are the entity
  (function, method, class). Criteria that only make sense for a document *set* are marked
  `document-set` and are excluded from entity-level scoring instead of being applied to a
  fragment.
* **Relation targets carry source, not just names.** A caller or callee contributes its
  source (whole function bodies up to 40 lines; for classes, a class view of the declaration,
  `__init__`, and method signatures). Input tokens are cheap; a document that has to guess
  its context is not.

## 2. Repository layout

```
CodeEval/
├── codedoc/                     # the implementation (installable package)
│   ├── cli.py                   # entry point: static analysis + generation for a repository
│   ├── config.py                # every path in one place
│   ├── sampling.py              # relation-stratified deterministic entity sampling
│   ├── criteria/                # criterion sets + the extractor that produced them
│   │   └── sets/{iso_26514,github_docs_style,practice_docstring}.json
│   ├── deps/                    # entity/relation extraction
│   │   ├── relations_index.py   # relation index + dependency context for one entity
│   │   ├── schema.py            # entity/relation types
│   │   └── languages/           # python_ast (default), python_pyright (LSP, comparison only)
│   ├── writer/                  # prompt assembly, LLM client, token/cost accounting
│   │   └── templates/           # one template per criterion set
│   ├── judge/                   # criterion-aligned judging and aggregation
│   └── ablation/                # component ablation (runner + evaluation)
├── scripts/                     # experiment drivers (see §5)
├── webapp/                      # local console: browse entities, prompts, documents, scores
├── docs/                        # criteria tables, judge protocol, architecture, reproduction
├── results/                     # published evaluation evidence (small, committed)
├── targets/                     # the evaluated repositories (cloned locally; never committed)
└── outputs/                     # generated documentation (never committed)
```

Inputs — the ten evaluated open-source repositories — are **not** distributed here;
`docs/REPRODUCTION.md` explains how to obtain them. `docs/REPOSITORIES.md` lists them with
scale and entity counts.

## 3. Installation

```bash
git clone https://github.com/DZYCD/CodeEval.git
cd CodeEval
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

Requires **Python 3.9+**. Core dependencies are `openai` and `requests`. Two extras are
optional: `pip install -e ".[extract]"` (PyMuPDF) only to re-extract criterion sets from the
standards PDFs — the extracted sets are committed — and `pip install -e ".[lsp]"` for the
language-server backend, which additionally needs `node` and `npm i -g pyright`.

## 4. Configuration

Credentials come from the environment — never hard-code an API key in the source tree.

```bash
cp .env.example .env      # then edit
export LLM_KEY=...        # API key       (required unless --process False)
export LLM_URL=...        # OpenAI-compatible base URL
export MODEL=...          # model name
```

Generation and judging are configured **separately**, because they need not be the same
service: the reported numbers used one endpoint for generation and a separate judge model at
temperature 0 for scoring. Both are arguments, never constants.

## 5. Usage

```bash
# Static analysis only — no LLM calls, prints the entity/relation index
codedoc --target_path /path/to/repo --process False

# Generation with the ISO/IEC/IEEE 26514 criterion set (the default)
codedoc --target_path /path/to/repo

# Generation with the GitHub documentation-style criterion set
codedoc --target_path /path/to/repo \
        --prompt_template "$(python -c 'import codedoc,pathlib;print(pathlib.Path(codedoc.__file__).parent/"writer"/"templates"/"github.txt")')"

# Component ablation: full | no_dep | no_prompt | baseline
codedoc --target_path /path/to/repo --ablation_mode no_dep --ablation_output abl/no_dep
```

Documents are written per entity as `<output_dir>/<qualified-name>.md`, each carrying the
entity's file path, its dependency context, and the criteria it was written against.

### Experiment drivers

| Script | Purpose |
|---|---|
| `scripts/run_matrix.py` | Generate every sampled entity under **both** criteria sets, so each method is scored on two independent axes. |
| `scripts/judge_matrix.py` | Judge those documents with a per-axis rubric; reports per dimension, per main dimension, per repository, per entity kind, and the judge's own token cost. |
| `scripts/run_generate.py`, `scripts/run_judge.py` | Single-axis generation and judging. |
| `scripts/compare_methods.py` | Compare CodeDoc against a baseline produced by the same sampler and judged by the same judge. |
| `scripts/bench_concurrency.py` | Worker-scaling curve (throughput, not wall-clock claims). |

All drivers share one sampler (`codedoc/sampling.py`) and one pruner, so every method sees
the **identical entity set** — a baseline is never given a different corpus.

Baselines are not vendored. `scripts/run_repoagent.py`, `run_docagent.py`,
`run_memdocagent.py`, and `run_agenticdoc.py` drive the respective tools whenever they are
available in `third_party/`, and adapt their output back to one document per entity so the
same judge can score them.

### Local console

`python webapp/server.py` serves a browser UI on `127.0.0.1:8765` for inspecting the
criterion sets, per-entity source, the exact prompt sent, the generated document, the judge
scores, the dependency graph, and generation/judging cost. It is a convenience for analysis,
not part of the method.

## 6. Criterion sets

| Set | Criteria | Main dimensions | Levels | Derived from |
|---|---|---|---|---|
| `iso_26514` | 26 | 8 | 14 entity, 12 document-set | ISO/IEC/IEEE 26514 (software user documentation) |
| `github_docs_style` | 18 | 5 | 18 document-set | GitHub documentation style guidance |
| `practice_docstring` | 9 | 4 | 9 entity | docstring conventions in practice |

The split matters: only **5 of the 8** ISO main dimensions have an entity-level criterion at
all, which is why entity-level scoring cannot simply reuse the document-level rubric. See
`docs/CRITERIA_ISO.md` and `docs/CRITERIA_GITHUB.md` for the full tables and their
provenance.

## 7. Evaluation evidence in this repository

| Path | Content |
|---|---|
| `results/` | Judged scores and aggregate reports for the reported experiments. |
| `results/analysis/` | Criterion set comparison, cost benchmarks and projections, prompt-injection audit, concurrency report, and method comparisons. |
| `docs/PROVENANCE.md` | Where every archived number came from, and what could not be recovered. |
| `3Score/`, `5Score/` | Raw judge outputs for the 3-level and 1–5-level protocols. |

Per-entity judge transcripts are large and are not committed; the aggregation reports and
the scripts that regenerate them are.

## 8. Documentation index

* [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — the six libraries and how data flows.
* [`docs/CRITERIA_ISO.md`](docs/CRITERIA_ISO.md) — the 26 criteria, the 14-dimension
  entity-level rubric, and the scale anchors.
* [`docs/CRITERIA_GITHUB.md`](docs/CRITERIA_GITHUB.md) — the GitHub-style criteria and what
  could not be recovered.
* [`docs/JUDGE_PROTOCOL.md`](docs/JUDGE_PROTOCOL.md) — the exact judge prompts.
* [`docs/DEPENDENCY_BACKENDS.md`](docs/DEPENDENCY_BACKENDS.md) — AST versus language-server
  extraction, with the measured differences.
* [`docs/REPRODUCTION.md`](docs/REPRODUCTION.md) — how to rebuild every experiment.
* [`docs/REPOSITORIES.md`](docs/REPOSITORIES.md) — the ten evaluated repositories and their
  scale.
* [`docs/PROVENANCE.md`](docs/PROVENANCE.md) — provenance of the archived evidence.

## 9. Relationship to RepoAgent and other prior work

We state the lineage explicitly, because earlier snapshots of this repository made it easy to
misread:

* **RepoAgent is a baseline, not the implementation.** CodeDoc's implementation is the
  pipeline in `codedoc/cli.py` / `codedoc/deps/` / `codedoc/writer/` described in §1.
* The `.project_doc_record/` and `markdown_docs/` directories are **RepoAgent's own working
  directories**, produced when RepoAgent was run over the same repositories for comparison.
  They follow RepoAgent's schema (`md_content`, `doc_version`, `fake_file_reflection`,
  `jump_files`, `deleted_items_from_older_meta`). They are not part of CodeDoc and are
  excluded from version control; only a small `markdown_docs/sample/` excerpt is kept as an
  example of baseline output.
* CodeDoc's contributions relative to that prior line of work are: (i) an explicit,
  standards-derived criterion set shared by generation and evaluation; (ii) dependency-aware
  context construction with AST-resolved source spans and relation-target source; and
  (iii) an entity-level evaluation whose unit matches the unit of generation.

## 10. Licence and contact

MIT — see [`LICENSE`](LICENSE).
Issues and questions: please open an issue on this repository.
