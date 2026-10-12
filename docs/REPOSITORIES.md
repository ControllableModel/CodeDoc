# The ten evaluated repositories

These are the open-source Python repositories used in the manuscript's evaluation. They are
**inputs**, not part of this artifact: they are cloned locally under `Small-Size/`,
`Middle-Size/` and `Large-Size/`, they carry their own licences, and they are excluded from
version control here.

| Scale | Local directory | Repository | URL | #Class | #Function | Entities |
|---|---|---|---|---|---|---|
| Small | `Small-Size/numpy` | NumPy | https://github.com/numpy/numpy | 5 | 31 | 36 |
| Small | `Small-Size/openui` | OpenUI | https://github.com/wandb/openui | 3 | 21 | 24 |
| Small | `Small-Size/ragflow` | RAGFlow | https://github.com/infiniflow/ragflow | 1 | 14 | 15 |
| Medium | `Middle-Size/dify_api` | Dify | https://github.com/langgenius/dify | 3 | 47 | 50 |
| Medium | `Middle-Size/flask-main` | Flask | https://github.com/pallets/flask | 28 | 207 | 235 |
| Medium | `Middle-Size/pyro` | Pyro | https://github.com/pyro-ppl/pyro | 28 | 234 | 262 |
| Large | `Large-Size/fairseq` | Fairseq | https://github.com/facebookresearch/fairseq | 45 | 378 | 423 |
| Large | `Large-Size/joblib` | Joblib | https://github.com/joblib/joblib | 56 | 389 | 445 |
| Large | `Large-Size/sonnet` | Sonnet | https://github.com/google-deepmind/sonnet | 177 | 801 | 978 |
| Large | `Large-Size/torch` | PyTorch | https://github.com/pytorch/pytorch | 71 | 1279 | 1350 |

The numbers above are transcribed from the manuscript's repository table so that the criteria
and the sample are readable from the artifact alone. The raw evidence of what was actually
documented lives in `results/per-repository/` (per-repository judge outputs and token
measurements); a script to reconcile the two counts is listed as an open action item in
[`REPRODUCTION.md`](REPRODUCTION.md) §4.

## 1. How the snapshots were prepared

Each upstream repository was cloned, then restricted to the Python modules in scope (unrelated
directories removed), which is why the entity counts are far below the size of the full
projects. `main.py` then documents every function and every method of every class found by
the AST pass, per file.

## 2. Provenance limitation (must be fixed before resubmission)

**The local snapshots do not record the upstream commits.** The `.git` directories inside
`Small-Size/`, `Middle-Size/` and `Large-Size/` were re-initialised (they contain a single
local "init"/"Initial commit" history and no `origin` remote), and `Large-Size/` has no `.git`
at all. Consequently the exact upstream revision used for each repository **cannot be
recovered from this artifact**.

Remedy for the manuscript: pin and report, for each of the ten repositories, the upstream
commit SHA (and the date it was fetched). If the exact revisions cannot be recovered, either
re-clone at a tagged release and re-run, or state the fetch date as the proxy and add it to
the threats-to-validity discussion.

## 3. Fetching the repositories

```bash
mkdir -p repositories && cd repositories
git clone --depth 1 https://github.com/numpy/numpy.git            numpy
git clone --depth 1 https://github.com/wandb/openui.git           openui
git clone --depth 1 https://github.com/infiniflow/ragflow.git     ragflow
git clone --depth 1 https://github.com/langgenius/dify.git        dify
git clone --depth 1 https://github.com/pallets/flask.git          flask
git clone --depth 1 https://github.com/pyro-ppl/pyro.git          pyro
git clone --depth 1 https://github.com/facebookresearch/fairseq.git fairseq
git clone --depth 1 https://github.com/google-deepmind/sonnet.git sonnet
git clone --depth 1 https://github.com/joblib/joblib.git          joblib
git clone --depth 1 https://github.com/pytorch/pytorch.git        torch
cd .. && for d in repositories/*; do git -C "$d" rev-parse HEAD; done   # record the SHAs
```

See [`REPRODUCTION.md`](REPRODUCTION.md) for how to reduce each clone to the in-scope modules
and run the pipeline over them.
