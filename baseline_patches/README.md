# Baseline harness patches

Patches that make four public repository-documentation baselines runnable against an
OpenAI-compatible gateway, so they can be compared with this work on the same corpus, the
same backbone, and the same judge.

These are the exact changes used for the numbers in the paper. None of them changes what a
baseline *generates*: they only route its requests to a compatible endpoint and repair
code that does not run as shipped. Every change is a unified diff against a pinned upstream
commit, and the reason for each hunk is stated in a comment at the patched site.

| baseline | upstream | pinned commit | license | files patched |
|---|---|---|---|---|
| RepoAgent | [OpenBMB/RepoAgent](https://github.com/OpenBMB/RepoAgent) | (see artifact) | Apache-2.0 | none — used as released |
| DocAgent | [facebookresearch/DocAgent](https://github.com/facebookresearch/DocAgent) | `f27f685` (2025-04-23) | MIT | 3 |
| MemDocAgent | [bsy99615/MemDocAgent](https://github.com/bsy99615/MemDocAgent) | `1064f29` (2026-09-29) | MIT | 6 |
| CodeWiki | [FSoft-AI4Code/CodeWiki](https://github.com/FSoft-AI4Code/CodeWiki) | `5b95c84` (2026-10-15) | MIT | 1 |
| Agentic Doc | [ishkapoor2000/agentic-ai](https://github.com/ishkapoor2000/agentic-ai) | `b754200` (2025-11-27) | MIT | 3 |

## Why this directory exists

Two of the four baselines do not run on a clean checkout, and the other two cannot be
pointed at any endpoint other than the vendor default. Both facts are worth reporting,
because a comparison that silently works around them would misrepresent the state of the
art. The repairs are published here so the comparison is reproducible rather than asserted.

A recurring pattern is worth noting: DocAgent and MemDocAgent share an ancestor, so the
same two defects — no way to set a base URL, and a hardcoded `max_tokens` — appear in both,
and MemDocAgent additionally inherited an `agent/__init__.py` that imports a module its own
release deleted.

## Applying

```bash
# Linux / macOS
./apply.sh /path/to/checkouts

# Windows
./apply.ps1 -Root C:\path\to\checkouts
```

The scripts clone each upstream at the pinned commit into `<root>/<tool>` and apply that
tool's patch. They do not download models, write configuration, or touch credentials.

## What each patch fixes

### DocAgent (`facebookresearch/DocAgent`)

Its output unit is a **docstring**, not a document. It writes generated docstrings back into
the source files through `astor`, so there is no document artifact to score; the harness
reads the docstrings out of the rewritten sources. It is therefore reported as a
docstring-unit baseline and not mixed into the document-level table.

1. **No endpoint override.** `OpenAILLM` constructed `openai.OpenAI(api_key=...)` with no
   way to pass a base URL, so the system could not run on the study's gateway.
2. **`max_tokens` rejected.** `gpt-6-luna` (and newer OpenAI-family models) reject
   `max_tokens` and require `max_completion_tokens`; the first full run produced a
   placeholder string for every component before this was found. The SDK in use has no
   typed kwarg for it, so it travels through `extra_body`.
3. **Eager provider imports.** `agent/llm/__init__.py` imported the Anthropic, Gemini, and
   HuggingFace backends unconditionally, so the OpenAI path required all three SDKs to be
   importable. Only one provider is used per run, so the unused imports are now optional.

Not repaired, because it is part of what is being measured: the Searcher agent retrieves
external context through Perplexity, and no Perplexity key was available, so the
four-agent system runs with three agents doing work. That retrieval path already degrades to
empty on its own (its call site is wrapped in `try/except`), so no patch was needed.

### MemDocAgent (`bsy99615/MemDocAgent`)

This is the only baseline whose unit matches ours exactly: `documentation.json` is keyed by
qualified name, one entry per component. Six repairs:

1. **No endpoint override** — same defect and same fix as DocAgent.
2. **`max_completion_tokens` model test too narrow.** The upstream code switched on
   `"gpt-5" / "o1" / "o3"` appearing in the model name, which does not cover `gpt-6-luna`.
3. **`agent/base.py` is missing from the release.** `worker_agent.WorkerAgent` inherits
   `BaseAgent` and uses the `_memory` list it owns 73 times, but the module is absent, so
   importing the package fails. MemDocAgent is a fork of DocAgent, so the ancestor's
   implementation is restored verbatim (126 lines, providing only `name`, `_memory`, `llm`,
   `llm_params`).
4. **`agent/__init__.py` imports a deleted module.** It still does
   `from .reader import CodeComponentType`, a leftover from the DocAgent name, which fails on
   import. The module now exposes the classes that actually exist, lazily.
5. **`torch` imported at module scope.** `llm/factory.py` imported `torch` and referenced
   `torch.bfloat16` in a dtype map, so the OpenAI path demanded a multi-gigabyte GPU
   dependency. `torch` is now optional and the map falls back to strings, which only affects
   the local/HuggingFace backends.
6. **Parameter name drift.** The restored `base.py` called `llm.generate(..., max_tokens=...)`
   while the fork renamed the argument to `max_output_tokens`, so every call raised
   `TypeError`. Note the failure mode: the ReAct loop catches the exception, writes an
   *empty* document, and the run still exits reporting `38/38 documented`. A reproduction
   must check the documents, not the summary counts.
7. **Topological order could exhaust memory.** `dependency_first_dfs` pushed a node once per
   incoming edge, so on a graph with many shared dependencies (every Flask blueprint method
   reaching the same helpers, 278 components, 4 dependency cycles) the stack re-expanded the
   same subgraph until the process died with `MemoryError` after 54 s. A `scheduled` set now
   keeps each node on the stack at most once.

Not repaired, because it is part of the system under test: when a component's ReAct loop
ends without a draft, MemDocAgent records an **empty** documentation string. The harness
counts those components as undocumented rather than scoring an empty document.

### CodeWiki (`FSoft-AI4Code/CodeWiki`)

Its unit is a **module page** plus an overview, not an entity, and it deliberately does not
repeat per-component detail ("refer to that core module's documentation rather than
duplicating it here"). It is therefore reported qualitatively, together with the observation
that the unit of existing tools does not match an entity-level rubric.

1. **`reasoning_effort` breaks tool calls.** CodeWiki drives every agent through function
   tools, and a reasoning-capable model rejects that combination on
   `/v1/chat/completions` ("Function tools with reasoning_effort are not supported … set
   reasoning_effort to 'none'"). Model settings now pin `reasoning_effort="none"`.

No other change was needed: it already omits `temperature` and already chooses between
`max_tokens` and `max_completion_tokens`.

### Agentic Doc (`ishkapoor2000/agentic-ai`)

Its unit is a **file-level** document with per-symbol subsections, the same granularity as
RepoAgent, so it decomposes to the entity level. It has no peer-reviewed publication and is
reported as a practitioner tool, not as a research baseline.

1. **No endpoint override** — same defect and same fix.
2. **The release ships a syntax error.** `agentic_doc/config_manager.py` ends with a stray
   Markdown code fence (```` ``` ````), so the module cannot be imported and the tool's own
   `agentic-doc init` reports "Could not validate API configuration" on a fresh install.
3. **A cache failure discarded paid work.** The SQLModel `llmcache` insert raised on the
   datetime default, and because the call was not guarded, the exception propagated out of
   `LLMClient.generate` and aborted the component whose text had just been generated — the
   API call was paid for and the document was lost. Caching now fails soft.

Not repaired, because it is part of what is being measured: the prompt truncates file
content to 10,000 characters. On `channels/whatsapp/channel.py` the tool states this itself
— "The provided source ends partway through `_apply_snapshot`" — and then documents a file it
cannot see the end of. That is the clearest evidence for injecting complete dependency
source rather than a truncated prefix.

## Harness scripts

`scripts/` holds the drivers used to produce the numbers, taken verbatim from the artifact:

| script | baseline |
|---|---|
| `run_repoagent.py` | RepoAgent (prune → run → adapt sections) |
| `run_docagent.py` | DocAgent (prune → run → read docstrings back out of the sources) |
| `run_memdocagent.py` | MemDocAgent (prune → run → cut `documentation.json` per entity) |
| `run_agenticdoc.py` | Agentic Doc (prune → run → cut sections per entity) |

All four share the same sampler and pruner, so every baseline sees the same entity set, and
all four write one Markdown file per entity under `outputs/baselines/<tool>/<repo>/` in a
form the same judge can score.
