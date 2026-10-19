# Repository provenance and reproducibility

This file records **where the evaluated code came from, what is shipped, and what
cannot be reproduced**. Reviewers asked for exactly this (R1: commits and sample
properties; R3: how the repositories were selected).

## 1. Source and location

| | |
|---|---|
| original working copies | `E:\DZYCDscript\{Small,Middle,Large}-Size\<repo>` |
| shipped copies (this artifact) | `targets/<repo>` (never committed; see `targets/README.md`) |
| extraction method | full tree copy excluding `.git/`, `__pycache__/`, `node_modules/`, `.venv/`, `*.pyc` |

**The shipped snapshots are trimmed subsets of the upstream projects**, not full
clones: NumPy is 10 files, RAGFlow 6, Flask 18, PyTorch 42. This is why the
"#classes / #functions" counts are in the hundreds rather than in the tens of
thousands.

## 2. What is shipped

| repo | size class (folder) | .py files | size |
|---|---|---|---|
| numpy | Small | 10 | 1.0 MB |
| openui | Small | 11 | 0.9 MB |
| ragflow | Small | 6 | 0.5 MB |
| dify_api | Middle | 22 | 1.2 MB |
| flask-main | Middle | 18 | 4.0 MB |
| joblib | Middle | 22 | 5.0 MB |
| pyro | Middle | 21 | 3.3 MB |
| fairseq | Large | 23 | 2.4 MB |
| sonnet | Large | 61 | 3.8 MB |
| torch | Large | 42 | 8.9 MB |

> **Discrepancy 1 — size class.** The paper's Table 1 classifies **Joblib as
> Large** (and groups 3 / 3 / 4 over Small / Medium / Large), while the working
> tree keeps `joblib` under `Middle-Size/`. The table's own numbers
> (Joblib 445 entities) are consistent with Large, so the folder is stale —
> but the inconsistency must be fixed in one direction.

## 3. Entity counts: measured vs published

Counted with the shipped analyzer (`codedoc.deps.languages.python_pyan`), i.e.
the same rule the pipeline uses: top-level functions + class methods.

| repo | classes | methods | functions | documentable (methods+func) | total incl. classes | paper: classes / functions / total |
|---|---|---|---|---|---|---|
| numpy | 11 | 12 | 18 | 30 | 41 | 5 / 31 / 36 |
| openui | 7 | 10 | 11 | 21 | 28 | 3 / 21 / 24 |
| ragflow | 2 | 3 | 10 | 13 | 15 | 1 / 14 / **15** ✓ |
| dify_api | 3 | 5 | 43 | 48 | 51 | 3 / 47 / 50 |
| flask-main | 29 | 146 | 59 | 205 | 234 | 28 / **207** / 235 |
| joblib | 62 | 306 | 78 | 384 | 446 | 56 / 389 / **445** |
| pyro | 28 | 122 | 112 | **234** | **262** | 28 / 234 / **262** ✓ |
| sonnet | 181 | 709 | 96 | 805 | 986 | 177 / **801** / 978 |
| torch | 110 | 665 | 789 | 1454 | 1564 | 71 / 1279 / 1350 |
| fairseq | — | — | — | — | — | 45 / 378 / 423 |

**Good news:** the counting rule is reproducible. For **Pyro** the match is
exact (234 functions, 262 total) and for **RAGFlow** exact (15 total); Flask,
Joblib, Dify, Sonnet agree within a handful of entities.

**What this settles:** the paper's "documentation entities" = *classes + methods
+ functions* (the `total incl. classes` column). That confirms an inconsistency
already visible in the code: **classes are counted as entities but the pipeline
only generates documentation for methods and top-level functions** (a class gets
a one-line summary). Either classes become first-class entities or the count must
exclude them.

**Discrepancy 2 — NumPy, OpenUI, PyTorch do not reproduce.** The counts differ by
5–214 entities. The likely cause is that Table 1 was computed on a different
(earlier or differently filtered) snapshot; the artifact as shipped cannot
regenerate those numbers. This has to be either recomputed or disclosed.

## 4. Archived evidence: two defects

**(a) The `extracted_dependencies/` evidence for `joblib` and `torch` is
cross-labelled.** Verified by module-name signatures:

* `torch/extracted_dependencies/*.info` contains `memory`, `parallel`,
  `numpy_pickle`, `hashing`, `compressor`, `_memmapping_reducer` → these are
  **joblib** modules.
* `joblib/extracted_dependencies/*.info` contains `_VF`, `_custom_ops`,
  `_jit_internal`, `_linalg_utils`, `_lowrank`, `_distributor_init` → these are
  **PyTorch** modules.

**(b) The evidence covers more modules than the shipped snapshots.** 62 `.info`
files against 42 `.py` for torch, and 72 against 22 for joblib — so the scores
were produced from larger snapshots than those preserved here. Together with (a)
this means **the exact source snapshots used for the published per-repository
numbers are not preserved**.

## 5. Commit SHAs are NOT recoverable

Every `.git` directory in the working copies is a re-initialised repository with
**a single synthetic commit** (`Initial commit` / `init` / `name` / `test`) and no
upstream remote:

```
numpy        ca63f6d Initial commit
flask-main   2ce490f main
joblib       94f0d8d init
openui       2d7aac7 init
dify_api     5043ac8 name
pyro         1ac0867 name
ragflow      0d8b29e test
```

Large-Size repositories have no `.git` at all. **Therefore the upstream commit
SHAs reviewers requested cannot be recovered from local data**; they must be
re-cloned from upstream at a known commit, or the paper must state that the
evaluated snapshots were trimmed and their provenance is the table above.

## 6. `pyan3==1.1.1` cannot analyse all ten repositories

This is an artifact defect, not a corpus property. Two failure modes were found
while wiring `targets/` back into the pipeline:

| failure | affected | handling |
|---|---|---|
| `visit_AnnAssign` indexes an empty `sanitize_exprs(value)` list → `IndexError` | Flask (`ctx.py`, `sessions.py`, `testing.py`, `views.py`), PyTorch | patched in `codedoc/deps/pyan_compat.py`; pyan is now called **in-process** so the patch applies |
| `KeyError: <Node attribute:torch.backends.cuda>` and `KeyError: <Node import:fairseq.logging.meters>` — cross-file resolution on a *trimmed* snapshot | `torch/__init__.py` (excluded), **all of `fairseq`** (not analysable) | partial: failing files are detected and excluded, and the exclusion is printed |

Previously these failures were silent: `_run_pyan` returned `None`, and the
`None` produced a `TypeError` hundreds of lines away. On the published pipeline,
**Flask and PyTorch cannot regenerate their dependency graphs at all with the
pinned pyan version** — which is precisely the kind of gap the artifact
availability complaint was about.

Open items (S1 in `EXPERIMENT_SEQUENCE.md`): a per-file-and-merge fallback to
rescue `fairseq`, and adoption of an LSP-based backend that does not depend on
pyan's cross-file heuristics.

## 7. Selection criteria (to be stated in the paper)

The published text never explained how the ten repositories were chosen (R3
flagged this). The actual procedure, as reconstructible from the working tree:

1. candidate repositories generated/collected with assistance from an LLM;
2. reduced to a file subset keeping modules larger than ~20 KB of source;
3. ranked/filtered by hand using popularity (stars) and structural variety;
4. grouped into Small / Medium / Large by the resulting entity count.

Steps 2–4 are only partially recoverable from the tree and must be confirmed by
the authors before being written into the paper.
