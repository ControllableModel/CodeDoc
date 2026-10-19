# CodeDoc console

A local dashboard for the documentation pipeline: pick a criterion set, a repository,
and a full or sampled analysis; browse every file that participates in generation;
click an entity to see its source, the **exact prompt** that would be sent, the
extracted relations, the model parameters, and the generated document.

```
python webapp/server.py --port 8765
# open http://127.0.0.1:8765/
```

## Why it is built this way

* **stdlib only.** `http.server` plus static HTML/CSS/JS — no npm, no build step, no
  framework. Reproduction must not depend on a front-end toolchain.
* **Localhost by default.** The console can hold an API key, so it binds to
  `127.0.0.1` and the key is never sent back to the browser (only "configured" plus a
  masked hint).
* **Long work is a job.** Building the dependency index takes milliseconds on `ragflow`
  and about a minute on `torch`, so `GET /api/analyze` returns a job id and the page
  polls `GET /api/job`. Results are cached per (repo, path, mode, limit, seed).
* **Every number on screen is measured.** Generation returns the token counts the API
  reported and the resulting cost, accumulated in the status bar for the session.

## Panels

| area | contents |
|---|---|
| top bar | repository, custom path, full vs sampled analysis, sample size, seed |
| left | every source file that contributes entities, with per-file entity counts |
| middle | entity chips per file; source view and the *injected view* side by side |
| right | tabs: **prompt** (verbatim), **document** (generated), **relations** (per block), **model params** |
| drawer | API key, base URL, model, temperatures, prompt cap, source budget, template, criterion sets with per-kind applicability |

## API

| route | purpose |
|---|---|
| `GET /api/bootstrap` | config (key masked), repositories, criterion sets, templates |
| `GET /api/criteria?id=` | criteria with level and per-entity-kind applicability |
| `GET /api/analyze?repo&path&mode&limit&seed` | starts a job, returns `{job}` |
| `GET /api/job?id=` | job status and the entity/file listing |
| `GET /api/entity?…&qname=` | source, injected view, prompt, relations, params |
| `GET /api/document?repo&qname` | a previously generated document, if any |
| `POST /api/config` | persist runtime configuration |
| `POST /api/generate` | generate one document; returns text, tokens, cost, seconds |

## Configuration file

`webapp/config.local.json` (gitignored) holds the runtime settings. Environment
variables win over it, so a shell session does not have to paste the key into the form:

```powershell
$env:LLM_KEY="sk-..."; $env:LLM_URL="https://api.deepseek.com/v1"; $env:MODEL="deepseek-chat"
```

Generated documents are written to `outputs/console/<repo>/<entity>.md` alongside the
prompt that produced them (`<entity>.prompt.txt`), which is the audit trail for any
number shown in the UI.
