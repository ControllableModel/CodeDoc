# Judge protocol and prompt templates

This file records the **exact prompts** used by the two LLM-facing components of CodeDoc. All
prompts below are transcribed from artifacts in this repository; the provenance of each is
given.

---

## 1. Prompt engine (generation)

The generation prompt is assembled by [`DOT.py:build_prompt`](../DOT.py) from a template file
plus the dependency context. The template *structure* is fixed — only the criteria block and
the required output structure change between the ISO and GitHub instantiations:

```text
You are an AI documentation assistant.
Generate clear, accurate documentation for the
given code following documentation standards:{Standard}

## Target Code Information
**Function Name:** {Function_Name}
**File Path:** {Path}
**Source Code:**
```python
{Source_Code}
```
**Relation Code**
```
{Uses}  {Used_by}
```
## Required Output Structure
Generate documentation in the following format:
{Required_Documentation Format}
```

Provenance: the paper's prompt figure, and
[`prompts/ISO.txt`](../prompts/ISO.txt) / [`prompts/Github.txt`](../prompts/Github.txt).
Placeholders `{real_name}`, `{path}`, `{source_code}`, `{uses}`, `{used_by}`, `{language}` are
filled by `build_prompt`; `{uses}` / `{used_by}` are empty strings in the
`no_dep` / `baseline` ablation modes.

**Dependency context.** `Uses` and `Used by` are rendered as Markdown sections in which each
related entity contributes its own name and its **exact source span**, resolved by the AST pass
in [`DOT.py`](../DOT.py) (`CodeFinder._extract` uses `lineno`/`end_lineno` of the matching
`FunctionDef`/`ClassDef` node). When `--relevant False` (or in the `no_dep` / `baseline`
ablation modes) both sections are omitted.

## 2. Document judge

### Where these prompts are built

Both judge prompts are produced in code, not typed by hand per run:
[`module_OpenAI/__init__.py`](../module_OpenAI/__init__.py)

```python
class LLM_Remote_query:
    def __init__(self, api_key='<>', api_url='', model='gpt-5-mini'): ...
    def load_judgeContent(self, name, behavior, example=''):        # single-round, per dimension
    def load_JudgeContent_Once(self, judge, example=''):            # multi-round, all dimensions
    def solo_query(self, question, write=False): ...                # caller, temperature=1, max_tokens=1024
    def multi_query(self, question): ...                            # caller, temperature=0.5, max_tokens=1024
```

The `(name, behavior)` pair for `load_judgeContent` is the `(dimension, definition)` pair
listed in [`CRITERIA_ISO.md`](CRITERIA_ISO.md) §4; the table that supplies those pairs is the
one artifact that is still missing (see [`REPRODUCTION.md`](REPRODUCTION.md) §5).

### Single-round prompt (per dimension)

```text
A good document should have the quality of {Dimension}, which means to {Description}.
Please view the following document and judge the quality of {Dimension}, you can choose
from 1 score(Not Mention) to 5 score (Excellent), and give your evidence.
your output must be a JSON, which have two attribute, 'judge' include your choice,
'evidence' include your evidence.
You should output like {Judge: ..., Evidence: ...}
```

### Multi-round prompt (all dimensions in one call)

```text
A good document should have the quality of {Standard}. Here are a good document details:
{Description}.
Please view the following document and judge the quality of {Standard}, you can choose
from 1 score(Not Mention) to 5 score (excellent), and give your evidence.
your output must be a JSON, which have two attribute, 'judge' include your choice,
'evidence' include your evidence.
You should output like {JudgeName : {Judge: ..., Evidence: ...}, JudgeName : {Judge: ...,
Evidence: ...}}
```

Provenance: the paper's prompt figure and the archived transcripts in `5Score/`, where the
system message of each judge call is preserved verbatim, e.g.

```text
"A good document should have the quality of Metadata, which means to Each topic should
include metadata (e.g., audience, product version, information type) to facilitate content
management and retrieval."
```

The `{Description}` slot of every ISO dimension that appears in the archive is recovered in
[`CRITERIA_ISO.md`](CRITERIA_ISO.md) §4.

## 3. Archive layout

| Directory | Protocol | Scale | Content |
|---|---|---|---|
| `3Score/` | per-dimension judge | `bad` / `good` / `excellent` | 26 ISO requirement-level dimensions, one JSON record per dimension with `judge` and `evidence`; `*_Eval` = CodeDoc, `*_Repo` = RepoAgent. |
| `5Score/` | per-dimension + multi-round judge | 1–5 integer | Raw judge transcripts (system message + document + JSON reply). `DOTquality_mul_Eval.jsonl` is a truncated stream: it contains 18 dimension prompts and 19 scored replies. |
| `results/per-repository/` | — | — | The same judging outputs, grouped per evaluated repository, plus `Size.txt` / `Token Cost.txt` token measurements. |

## 4. What the archived protocols do **not** pin down

1. **Intermediate anchors of the 1–5 scale** (scores 2, 3, 4) — only the endpoints are stated
   in the prompt (see [`CRITERIA_ISO.md`](CRITERIA_ISO.md) §5).
2. **Judge model identifiers**: the archived `5Score` transcripts do not record the model name
   or the decoding parameters in the same file as the scores. The manuscript states the model
   family used, but the artifact alone does not.
3. **The GitHub-rubric judge prompts** are absent from the archive (see
   [`CRITERIA_GITHUB.md`](CRITERIA_GITHUB.md) §3).
