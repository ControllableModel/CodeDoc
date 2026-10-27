# Experiment audit against the paper

What each table in `sections/experiment_revised.tex` and `tables/` needs, what the repository
already holds, and what is still missing. Written before the re-run so nothing is generated
that no table consumes, and no table is left without data.

Judge for every row below: `deepseek-chat`, temperature 0, unless a row says otherwise.
Corpus: 10 repositories, 60 sampled entities each (ragflow contributes all 38 it has), one
sampling seed (42) shared by every method through `codedoc/sampling.py`.

## 1. `tab:rq2_extended` — main comparison

Cells needed: `{Long-Context, RepoAgent, CodeDoc}` x `{ISO, GitHub}` x `{Single-round S,
Multi-round M}`, averaged over 10 repositories.

| cell | status | note |
|---|---|---|
| CodeDoc, S, both axes | **re-running now** (`outputs/matrix_v6`) | template v6; earlier v1 numbers stay in `outputs/matrix/` |
| RepoAgent, S, both axes | have | 10 repositories already judged |
| Long-Context, S, both axes | **missing** | baseline never implemented |
| CodeDoc, M, both axes | **missing** | `judge_matrix.py` only scores all dimensions in one interaction |
| RepoAgent / Long-Context, M | **missing** | same gap |
| MemDocAgent (extra row, optional) | partial | 4 repositories (ragflow, joblib, sonnet, flask-main) |

`S` and `M` are *judge interaction styles*, not generation settings: single-round scores every
dimension in one conversation, multi-round scores each dimension in an independent interaction.
`codedoc/judge/query.py` already implements both (`load_JudgeContent_Once` and
`load_judgeContent`); only the matrix driver uses one of them.

Long-Context is defined in the paper as the full source file containing the target entity,
fed to the same backbone under a matched token budget, with no documentation structure. The
pieces exist (`PromptArgs.prompt_template = None` is the no-criteria branch, and the file body
is already in the AST index), so this is a driver, not new machinery.

## 2. `tab:rq4_ablation_full` — component ablation

Cells needed: 10 repositories x `{Full, No Dependency, No Prompt, Baseline}`, ISO, single-round.

| variant | definition in the paper | how to produce it |
|---|---|---|
| Full | dependency retrieval + standards prompt | `relevant=True`, template v6 |
| No Dependency | target entity only, no dependency context | `relevant=False`, template v6 |
| No Prompt | dependency retained, structured prompt replaced by a simplified prompt without standards-derived criteria | `relevant=True`, `prompt_template=None` |
| Baseline | both removed | `relevant=False`, `prompt_template=None` |

All four are already expressible: `build_prompt` has an explicit no-template ablation branch and
`_PromptArgs.relevant` gates the dependency blocks. What is missing is a switch on
`run_matrix.py` to select the variant; the scoring side needs nothing new.

## 3. `tab:token_iso_eval` and `tables/token.tex` — cost tables

Per-repository input/output/total tokens.

| need | status |
|---|---|
| CodeDoc per-repository tokens | **regenerate from v6** — `usage.py` records `prompt_tokens` / `completion_tokens` per call, so these become measured rather than estimated |
| RepoAgent per-repository tokens | **have for ragflow only** (35 calls, 61,183 in / 26,607 out) — RepoAgent logs tokens at DEBUG, so the other nine repositories need a re-run with `-ll DEBUG` |
| Long-Context tokens | missing with the baseline itself |

`tables/token.tex` also compares against a baseline named "CodeRepo", which is not a method in
the current experiment set. Either it is an earlier name for RepoAgent or the table is stale;
it should be rewritten against the methods actually run.

## 4. `tab:rq5_combined` — human alignment and cross-family judges

Cells needed: `{RepoAgent, CodeDoc}` x `{Human, GPT-5-mini, Claude-3.5-Sonnet}` score and rank.

| need | status |
|---|---|
| Human annotation | **missing, and not automatable** — this is the owner's annotation work (RQ1.3 / D3) |
| GPT-5-mini judge | missing — our judges have been DeepSeek and gpt-6-luna |
| Claude-3.5-Sonnet judge | missing |

The judge substrate is model-agnostic (`judge_matrix.py --judge-model/--judge-url`), so once a
key for each family is available these are scripted runs over documents we already have. The
human column is the binding constraint on this table, not compute.

## 5. `tab:rq6_dep_audit` — static dependency recovery

Cells needed: `{Flask, NumPy, PyTorch}` x `{Precision, Recall, F1, Dynamic %}`.

**This table is inconsistent with the current code.** It audits `Pyan3`, which was removed
from the package in favour of the stdlib `python_ast` backend; the numbers cannot be
regenerated from this repository. Two options:

1. Re-point the table at the shipped extractor and re-measure precision/recall/F1 against a
   hand-checked relation sample. Offline and free, but needs an annotation pass.
2. Keep the Pyan3 audit as a historical comparison and add the shipped extractor as a row,
   which requires reinstalling Pyan3 in an isolated environment purely as a measurement
   instrument.

`Dynamic %` (the share of relations only visible at run time) requires runtime tracing, which
no script here performs. Either it is measured with a tracing harness or the column is dropped.

## 6. What runs, in what order

| # | run | documents | cost | wall |
|---|---|---|---|---|
| 1 | CodeDoc v6, 10 repos, both axes, S | 1,156 | ~$1.3 | ~1 h |
| 2 | judge 1 | 1,156 | ~¥12 | ~30 min |
| 3 | Long-Context baseline, 10 repos, both axes | 1,156 | ~$0.6 | ~25 min |
| 4 | judge 3 | 1,156 | ~¥10 | ~25 min |
| 5 | ablation, 3 variants x 10 repos, ISO only | 1,734 | ~$1.5 | ~1.5 h |
| 6 | judge 5 | 1,734 | ~¥14 | ~40 min |
| 7 | RepoAgent re-run with DEBUG on 9 repos (token table) | 540 | ~$0.3 | ~30 min |
| 8 | multi-round judging on 3 repos x 3 methods (M column) | ~500 judgments x 14 calls | ~¥20 | ~1.5 h |

Rows 1-2 establish every number in the main table that does not depend on a baseline we have
not built. Rows 3-4 close the Long-Context gap. Row 5 gives the Ablation table. Row 7 makes
the token table measured rather than estimated. Row 8 gives the M column.

Order matters only for cost control: the generation key has roughly $2.5 left, and rows 1, 3
and 5 together exceed that, so the ablation (row 5) is the one to defer or to run on a subset
of repositories if the key is not topped up.

## 7. Blocked on the owner, not on compute

* human annotation for `tab:rq5_combined`;
* API keys for GPT-5-mini and Claude-3.5-Sonnet if the cross-family column is to be filled;
* a decision on `tab:rq6_dep_audit`: re-point at the shipped extractor, or reinstate Pyan3 as a
  measurement instrument;
* whether the backbone stays `gpt-6-luna` (what every measurement here used) or the paper's
  stated `GPT-5-mini`.
