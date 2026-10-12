# Reproduction guide

This guide describes how to rebuild the artifacts of the paper **from this repository**, and —
just as importantly — **what cannot currently be rebuilt** because the corresponding code or
inputs are not shipped. Read §5 before planning a full re-run.

---

## 1. Environment

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt                     # openai, pyan3, requests
```

Python 3.8+. The pipeline is CPU-only; the only network dependency is the LLM endpoint.

```bash
cp .env.example .env
export LLM_KEY=...     # required for any step that calls a model
export LLM_URL=...     # OpenAI-compatible base URL
export MODEL=...       # model identifier (see the paper's experimental setup)
```

`main.py` refuses to run with `--process True` when no key is available, so a missing
credential can never silently produce empty documentation.

## 2. Step 0 — obtain the evaluated repositories

See [`REPOSITORIES.md`](REPOSITORIES.md). Clone the ten repositories and keep a record of the
commit SHA of each one; the local snapshots used for the paper did **not** preserve them.

## 3. Step 1 — static analysis only (no LLM, no key needed)

```bash
python main.py --target_path /path/to/repo --process False
```

This exercises Phase (b) Stage 1 end to end: `pyan3` produces the call graph, the AST pass
resolves each entity to its source span, and per-file `.info` files are written containing the
dependency context (`Uses` / `Used by`). It is the cheapest way to check that the dependency
layer works before spending tokens.

To sanity-check the AST layer on the bundled example:

```bash
python main.py --target_path sample --process False
```

## 4. Step 2 — generation and ablation

```bash
# ISO criteria (default) / GitHub criteria
python main.py --target_path /path/to/repo --prompt_template prompts/ISO.txt
python main.py --target_path /path/to/repo --prompt_template prompts/Github.txt

# Component ablation (dependency context x prompt optimisation)
python run_ablation.py --target_path Small-Size/numpy \
    --modes full no_dep no_prompt baseline --output_base numpy_ablation
python evaluate_ablation.py --base_dir numpy_ablation
```

`evaluate_ablation.py` reports **surface metrics only** (length, token counts, number of
sections/code blocks, presence of dependency sections). It does not score documentation
quality. `numpy_ablation/` in this repository is the output of exactly these commands.

## 5. Step 3 — judging and scoring: **not reproducible as shipped**

The reported quality scores (`3Score/`, `5Score/`, `results/per-repository/`) were produced by
an LLM-as-a-judge harness that is **not part of this repository**. There is no script here that

* builds the judge prompts (their text is recovered in [`JUDGE_PROTOCOL.md`](JUDGE_PROTOCOL.md)),
* calls the judge and stores `judge` / `evidence` per dimension,
* aggregates dimension scores into the per-entity, per-repository and per-category numbers,
* performs the controlled-masking sensitivity experiment, or
* computes the human–judge agreement statistics.

What **is** shipped is the evidence: the judge transcripts and per-repository outputs under
`results/`, `3Score/` and `5Score/`. They can be inspected and re-aggregated by hand, and the
per-dimension definitions they contain have been extracted into
[`results/judge_criteria_recovered.json`](../results/judge_criteria_recovered.json).

## 6. Step 4 — token accounting

Per-entity token costs are obtained by dividing the cumulative token usage recorded in the
per-repository `Token Cost.txt` / `Size.txt` files (copied to `results/per-repository/`) by the
entity counts. The Long-Context baseline and the RepoAgent baseline were run with their own
tools; RepoAgent's outputs are recognisable by its `.project_doc_record/project_hierarchy.json`
schema and are intentionally **not** redistributed here.

## 7. Open action items for full reproducibility

| # | Item | Why it matters |
|---|---|---|
| 1 | Publish the judge + aggregation scripts (prompt construction, model call, per-dimension storage, aggregation, masking, agreement statistics). | Without them the reported scores cannot be re-derived; this was an explicit reviewer request. |
| 2 | Pin and report the upstream commit SHA of each of the ten repositories. | Requested by reviewers; the local snapshots lost provenance. |
| 3 | Publish the 1–5 scoring anchors for scores 2–4, or re-define and re-validate the scale. | Only "1 = not mentioned" and "5 = excellent" were ever specified (see `CRITERIA_ISO.md` §5–6). |
| 4 | Publish a genuine clause-to-dimension traceability table built from the standard text. | The table promised in the manuscript's appendix does not exist as an artifact. |
| 5 | Reconcile the entity counts in the manuscript's repository table with the counts actually documented in `results/per-repository/`. | Counts are currently transcribed from the manuscript, not recomputed. |
| 6 | Ship the human-evaluation protocol, the sampled entities and the raw annotations. | Needed for the agreement statistics; reviewers asked for inter-rater agreement. |
