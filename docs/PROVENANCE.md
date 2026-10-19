# Repository provenance and reproducibility

This file records **where the evaluated code came from, what is shipped, and what
cannot be reproduced**. Reviewers asked for exactly this (R1: commits and sample
properties; R3: how the repositories were selected).

## 1. Current corpus: upstream, pinned by commit

The ten repositories under `targets/` are extracted from upstream GitHub at a
**recorded commit**, keeping only the library's core package (front-end, docs,
tests, CI and examples are dropped). Downloads go through
`codeload.github.com` pinned to the resolved SHA, which is stricter than
`git clone --depth 1`: the recorded SHA and the extracted tree cannot drift.

| repo | upstream | commit | branch | committed | core package | files | size |
|---|---|---|---|---|---|---|---|
| dify_api | [langgenius/dify](https://github.com/langgenius/dify) | `67887de9e427` | main | 2026-10-19 | `api` | 2417 | 19.19 MB |
| fairseq | [facebookresearch/fairseq](https://github.com/facebookresearch/fairseq) | `3d262bb25690` | main | 2025-09-30 | `fairseq` | 476 | 3.58 MB |
| flask-main | [pallets/flask](https://github.com/pallets/flask) | `d086db856be1` | main | 2026-10-07 | `src/flask` | 26 | 0.33 MB |
| joblib | [joblib/joblib](https://github.com/joblib/joblib) | `878c9e05995b` | main | 2026-10-16 | `joblib` | 45 | 0.55 MB |
| numpy | [numpy/numpy](https://github.com/numpy/numpy) | `3e225b263fd6` | main | 2026-10-18 | `numpy` | 893 | 19.19 MB |
| openui | [wandb/openui](https://github.com/wandb/openui) | `42d7ab4ab665` | main | 2026-06-30 | `backend/openui` | 38 | 2.29 MB |
| pyro | [pyro-ppl/pyro](https://github.com/pyro-ppl/pyro) | `a31bc1784707` | dev | 2026-10-03 | `pyro` | 309 | 2.33 MB |
| ragflow | [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | `efbb80074309` | pinned@api/ragflow_server.py | 2026-09-28 | `api` | 21 | 0.13 MB |
| sonnet | [google-deepmind/sonnet](https://github.com/google-deepmind/sonnet) | `8e7158b2beb8` | v2 | 2026-09-29 | `sonnet` | 267 | 31.73 MB |
| torch | [pytorch/pytorch](https://github.com/pytorch/pytorch) | `25a447541892` | main | 2026-10-19 | `torch` | 4559 | 65.43 MB |

Manifest with sizes, timestamps and per-repository extraction details:
`targets/PROVENANCE.json`. Re-fetch with:

```bash
python scripts/fetch_core_repos.py --list
python scripts/fetch_core_repos.py --all --force
```

### Repository identification note

`openui` is **`wandb/openui`** (identified from `api.wandb.ai`, the litellm config
generator and the default port 7878), and its core is the Python backend
`backend/openui`.

`ragflow` needs a **pinned commit**: upstream restructured the project and the
Python `api/` package is gone from HEAD (its core moved to Go-style
`cmd/`/`internal/`). The fetcher pins the last commit that still contains
`api/ragflow_server.py` (2026-09-28), which is recorded in the manifest.

## 2. Legacy trimmed snapshots (what the published results used)

The original evaluation ran on **hand-trimmed** snapshots (NumPy 10 files, RAGFlow
6, etc.) whose provenance was never recorded. Those are preserved outside the
repository at `_CodeEval_offcuts/targets_trimmed_v1/` and are *not* the current
corpus. Their entity counts were the only way to cross-check the published table:

| repo | legacy trimmed entities | paper (classes / functions / total) |
|---|---|---|
| numpy | 42 | 5 / 31 / 36 |
| openui | 20 | 3 / 21 / 24 |
| ragflow | 14 | 1 / 14 / 15 |
| dify_api | 47 | 3 / 47 / 50 |
| flask-main | 207 | 28 / 207 / 235 |
| pyro | 234 | 28 / 234 / 262 |
| fairseq | 378 | 45 / 378 / 423 |
| sonnet | 801 | 177 / 801 / 978 |

For Flask, Pyro, Fairseq and Sonnet the archived entity count equals the paper's
*function* column exactly, which settles the counting rule: **total entities =
classes + methods + functions**. Two consequences:

1. Classes were **counted** as documentation entities although the generator only
   documents methods and top-level functions (a class received a one-line
   summary). Either classes become first-class or the count must exclude them.
2. The archived `extracted_dependencies/` evidence for `joblib` and `torch` is
   **cross-labelled** (each folder's evidence describes the other library, verified
   by module-name signatures) and covers more modules than the shipped snapshots
   (62 vs 42, 72 vs 22). The exact snapshots behind the published per-repository
   numbers were therefore not preserved.

## 3. Commit SHAs — now recoverable, previously not

Every `.git` directory in the old local copies was a re-initialised repository
with **one synthetic commit** (`Initial commit` / `init` / `name` / `test`) and no
remote, and the Large-Size copies had no `.git` at all. The upstream SHAs reviewers
asked for were unrecoverable from local data. Section 1 resolves that: the corpus
is now fetched from upstream and every commit is recorded.

## 4. Dependency analysis: legacy backend vs replacements

`pyan3==1.1.1` (the backend behind the published numbers) cannot analyse these
repositories:

| failure | affected |
|---|---|
| `IndexError` in `visit_AnnAssign` (empty `sanitize_exprs` result) | Flask `ctx.py`/`sessions.py`/`testing.py`/`views.py`, PyTorch |
| `KeyError` on cross-file import resolution | NumPy, joblib, Fairseq |
| `ValueError: Unknown scope …lambda` | PyTorch, Fairseq |
| grammar bound to the interpreter | any repository needing a newer Python |

Two replacements are shipped and benchmarked — see
[`DEPENDENCY_BACKENDS.md`](DEPENDENCY_BACKENDS.md): a dependency-free AST extractor
that covers every entity, and a Pyright-backed extractor that resolves calls with
type inference (54–59 % internal resolution versus 7–22 % for the AST backend).
Both succeed on all ten repositories.

## 5. Selection criteria (to be stated in the paper)

The published text never explained how the ten repositories were chosen (R3
flagged this). What is reconstructible from the working tree:

1. candidate repositories were collected with LLM assistance;
2. each was reduced to a file subset (modules larger than roughly 20 KB of source);
3. the subset was filtered by hand using popularity and structural variety;
4. repositories were grouped into Small / Medium / Large by resulting entity count.

Step 4 is inconsistent with the working tree: **Joblib sits under
`Middle-Size/` while the paper's Table 1 classifies it as Large** (and its entity
count supports Large). The grouping has to be fixed in one direction.
