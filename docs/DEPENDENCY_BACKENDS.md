# Dependency backends

Two backends now produce class **and** function relations for Python. They are
complementary, and the benchmark below makes the trade-off explicit instead of
declaring a winner.

| backend | module | third-party deps | resolution | structural coverage |
|---|---|---|---|---|
| `stdlib ast + import-graph` | `codedoc/deps/languages/python_ast.py` | none | names, imports, `self.m()` | **every** entity |
| `pyright LSP + ast` | `codedoc/deps/languages/python_pyright.py` | node + `pyright` (npm) | type inference | sampled entities |
| ~~`pyan3` (legacy, published)~~ | **removed** | — | call edges only | unusable: crashes on 5/10 repositories |

## Why the legacy backend was removed from the artifact

The pyan3 backend, its DOT parser and the compatibility patch were deleted; the
history keeps them at commit `61637cc` and earlier. The reasons it could not stay:

`pyan3` 1.1.1 cannot be the dependency layer:

* it models **call edges only**, so classes have no outbound relations — the root
  cause of the published paper's weak class documentation;
* it raises `IndexError` in `visit_AnnAssign`, `KeyError` on import resolution and
  `ValueError: Unknown scope` on lambdas; on the ten evaluated repositories it
  fails outright for NumPy, Dify, joblib, Fairseq and PyTorch;
* it is bound to the interpreter grammar, so a repository written for a newer
  Python cannot be parsed at all.

## Measured benchmark

`python scripts/benchmark_dependencies.py --budget 250` on the ten repositories
(`results/analysis/dependency_backends.md`, `.json`):

| repo | AST entities | AST calls | pyright entities | pyright calls | pyright call resolution | pyright sec |
|---|---|---|---|---|---|---|
| numpy | 2868 | 2018 | 428 | 988 | 55% | 706 |
| openui | 165 | 82 | 165 | 620 | 55% | 3 |
| ragflow | 38 | 40 | 38 | 191 | 55% | 1 |
| dify_api | 15813 | 11556 | 5636 | 947 | 59% | 110 |
| flask-main | 431 | 181 | 297 | 953 | 57% | 6 |
| joblib | 749 | 444 | 359 | 868 | 55% | 8 |
| pyro | 3396 | 1295 | 789 | 772 | 58% | 40 |
| fairseq | 5229 | 1875 | 1036 | 724 | 54% | 44 |
| sonnet | 1605 | 417 | 571 | 658 | 57% | 10 |
| torch | 49451 | 36595 | 5367 | 462 | 56% | 280 |

Both backends succeeded on **10/10** repositories; the legacy backend succeeds on
5/10.

### Reading the numbers honestly

1. **`call resolution` is a pyright-only column.** It is
   `internal calls / (internal + external)`. The AST backend's comparable figure
   is in `coverage['call_resolution_rate']` and is much lower (7–22 %), because
   `obj.method()` cannot be resolved without type inference. Do **not** compare
   the raw `AST calls` and `pyright calls` columns: they are computed over
   different entity sets (all entities vs a 250-entity sample), so the counts are
   not directly comparable yet. Making this apples-to-apples is the next
   measurement task.
2. **`instantiated_at` is 0 for pyright** in this run: it depends on
   `textDocument/references`, which is disabled by default (`use_references=False`)
   because it was the most expensive request. The AST backend supplies it for all
   entities.
3. **`overrides` / `dispatch` are lower for pyright** only because those
   relations are derived per *queried* method; with a 250-entity budget the other
   20 000 methods are not examined.
4. **Runtime**: pyright is 20–400× slower and needs a running language server;
   the AST backend finishes the whole corpus in ~85 s.

## Recommended configuration

* **Structure (all entities)** → AST backend. It is the only one that covers every
  class, method and function, and it is what the documentation generator needs to
  emit an artifact per entity.
* **Call resolution (sampled)** → pyright backend, budgeted. Use it for the
  relations where type inference matters and for the correctness study; report the
  budget and the sample explicitly.
* **Never** silently fall back: if a relation cannot be produced, say so (the
  extractor interface exposes `supported_relations` and `missing_relations()`, and
  `scripts/probe_relations.py` prints the gap).

## Reproducing

```bash
npm i -g pyright                       # language server (registry: npmmirror)
python scripts/probe_relations.py      # capability matrix + per-language gaps
python scripts/benchmark_dependencies.py --backend both --budget 250
```
