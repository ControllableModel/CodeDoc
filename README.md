# CodeDoc — Standards-Guided and Dependency-Aware Code-Level Documentation Generation

This repository is the artifact and reference implementation of the paper
**"Standards-Guided and Dependency-Aware Code-Level Documentation Generation"**
(manuscript under review).

CodeDoc formulates code-level documentation generation as a **standards-guided software
engineering task** instead of an unconstrained text-generation problem: documentation is
generated *and* assessed against an explicit, reusable set of quality criteria derived from
authoritative documentation standards, and the generation prompt is grounded in the static
dependency structure of the repository.

---

## 1. How CodeDoc works

| Phase | Component | What it does |
|---|---|---|
| **(a) Offline criteria extraction** | `prompts/ISO.txt`, `prompts/Github.txt` | Turns two authoritative sources (ISO/IEC/IEEE software-documentation standards; the GitHub documentation style guide) into an explicit criterion set `Q`. Run once, before any repository is processed. |
| **(b) Stage 1 — static analysis** | `main.py` → `analyzer`, `DOT.py` | Builds a repository representation from a **static call graph** (`pyan3`) plus an **AST** pass that resolves each entity to its exact source span; recovers direct callers / callees for each entity. |
| **(b) Stage 2 — generation** | `DOT.py:build_prompt`, `LLM.py` | Assembles a **dependency-aware structured prompt** (entity source, file path, `Uses` / `Used by` context, criteria, required output structure) and calls the LLM. |
| **(b) Stage 2 — judge & refine** | `prompts/`, `LLM.py` | An LLM **document judge** scores the generated documentation dimension by dimension and returns textual feedback; the feedback is fed back into one refinement pass. |

## 2. Repository layout

```
CodeEval/
├── main.py                    # entry point: Phase (b) Stage 1 + Stage 2
├── DOT.py                     # call-graph (.dot) parsing, AST source location, prompt assembly
├── LLM.py                     # OpenAI-compatible client wrapper
├── run_ablation.py            # batch runner for the component ablation
├── evaluate_ablation.py       # aggregation / comparison of ablation runs
├── system.prompt              # system message used for generation
├── prompts/
│   ├── ISO.txt                # ISO-oriented criteria + required output structure
│   ├── Github.txt             # GitHub-style criteria + required output structure
│   ├── artifact.txt           # original (pre-standards) template, kept for reference
│   └── simple_prompt.txt      # template used by the "no prompt optimisation" ablation
├── module_OpenAI/             # thin request helper
├── docs/                      # criteria tables, judge protocol, reproduction guide
├── results/                   # published evaluation evidence (see §6)
├── 3Score/  5Score/           # raw judge outputs: 3-level and 1–5-level protocols
├── numpy_ablation/            # component-ablation outputs on NumPy
├── sample/                    # three-file example project used by the walkthrough
└── ablation_config.example.json
```

Downloads/inputs (the ten evaluated open-source repositories) are **not** distributed here;
`docs/REPRODUCTION.md` explains how to obtain them.

## 3. Installation

```bash
git clone https://github.com/DZYCD/CodeEval.git
cd CodeEval
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Requires **Python 3.8+**. Dependencies: `openai`, `pyan3`, `requests` (see `requirements.txt`).

## 4. Configuration

Credentials are read from the environment — **never** hard-code an API key in the source tree.

```bash
cp .env.example .env      # then edit
export LLM_KEY=...        # API key       (required unless --process False)
export LLM_URL=...        # OpenAI-compatible base URL
export MODEL=...          # model name
```

The paper's experiments used a single model family throughout (generation, refinement and
judging), as reported in the paper's experimental setup; the endpoint and model name are
intentionally configurable so that the pipeline can be re-run against any OpenAI-compatible
service.

## 5. Usage

```bash
# Full pipeline on a target repository
python main.py --target_path /path/to/repo

# Static analysis only (no LLM calls)
python main.py --target_path /path/to/repo --process False

# Choose the criteria set: ISO (default) or GitHub
python main.py --target_path /path/to/repo --prompt_template prompts/Github.txt

# Component ablation: full | no_dep | no_prompt | baseline
python run_ablation.py --target_path /path/to/repo --modes full no_dep no_prompt baseline
python evaluate_ablation.py --base_dir ablation_results
```

Outputs are written per source file as

* `<file>.md` — the generated documentation, and
* `<file>.info` — the dependency context handed to the model (source span + callers/callees).

A worked example is available in `sample/` (three files) — see also `docs/REPRODUCTION.md`.

## 6. Evaluation evidence in this repository

| Path | Content |
|---|---|
| `results/per-repository/` | Per-repository judge outputs (`*quality*.jsonl`, `*quality*.md`) and the token measurements (`Size.txt`, `Token Cost.txt`) for all ten repositories, grouped by scale (Small / Medium / Large). |
| `results/judge_criteria_recovered.json` | The per-dimension judge definitions **recovered verbatim from the archived judging logs** (see `docs/CRITERIA_ISO.md` for provenance and for the gaps). |
| `3Score/` | Judge protocol with a 3-level label scale (`bad` / `good` / `excellent`), 26 ISO requirement-level dimensions. |
| `5Score/` | Judge protocol with a 1–5 integer scale (`1 = not mentioned` … `5 = excellent`), including the raw judge transcripts. |
| `numpy_ablation/` | Component-ablation outputs on NumPy (`full`, `no_dep`, `no_prompt`, `baseline`) plus the generated report. |

## 7. Documentation index

* [`docs/CRITERIA_ISO.md`](docs/CRITERIA_ISO.md) — ISO criteria: the 26 requirement-level
  items, the 14-dimension rubric, the recovered judge definitions, and the scale anchors.
* [`docs/CRITERIA_GITHUB.md`](docs/CRITERIA_GITHUB.md) — GitHub-style criteria: the
  generation-time guidelines, the 12-dimension rubric, and what could not be recovered.
* [`docs/JUDGE_PROTOCOL.md`](docs/JUDGE_PROTOCOL.md) — the exact judge prompts
  (single-round and multi-round) and the prompt-engine template.
* [`docs/REPRODUCTION.md`](docs/REPRODUCTION.md) — how to rebuild every experiment.
* [`docs/REPOSITORIES.md`](docs/REPOSITORIES.md) — the ten evaluated repositories,
  their scale, the number of documented entities, and the provenance limitations.
* [`ABLATION_STUDY.md`](ABLATION_STUDY.md) — ablation study guide (Chinese; English
  version pending).

## 8. Relationship to RepoAgent and other prior work

We state the lineage explicitly, because earlier snapshots of this repository made it easy to
misread:

* **RepoAgent is a baseline, not the implementation.** CodeDoc's implementation is the
  pipeline in `main.py` / `DOT.py` / `LLM.py` described in §1.
* The `.project_doc_record/` and `markdown_docs/` directories are **RepoAgent's own working
  directories**, produced when RepoAgent was run over the same repositories for comparison.
  They follow RepoAgent's schema (`md_content`, `doc_version`, `fake_file_reflection`,
  `jump_files`, `deleted_items_from_older_meta`). They are *not* part of CodeDoc and are
  excluded from version control here; only a small `markdown_docs/sample/` excerpt is kept as
  an example of baseline output.
* CodeDoc's contributions relative to that prior line of work are: (i) an explicit,
  standards-derived criterion set shared by generation and evaluation; (ii) dependency-aware
  context construction with AST-resolved source spans; and (iii) a criterion-aligned
  judge-and-refine loop.

## 9. Licence and contact

MIT — see [`LICENSE`](LICENSE).
Issues and questions: please open an issue on this repository.
