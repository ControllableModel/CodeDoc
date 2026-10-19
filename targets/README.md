# targets/ — target code repositories

Third-party repositories under analysis live here. They are **never committed**:
each has its own licence, and cloning them would add hundreds of megabytes and
nested `.git` directories.

```bash
git clone --depth 1 https://github.com/pallets/flask.git targets/flask
```

Record, for every repository used in an experiment:

| field | why it is needed |
|---|---|
| upstream URL | provenance; reviewers asked for it |
| commit SHA | reproducibility — "the repository at HEAD" is not reproducible |
| retrieval date | repositories move |
| declared size class | so the Small/Medium/Large grouping is auditable |
| #classes / #methods / #functions | recomputable with `scripts/probe_relations.py` |

The size classes in the paper were derived from these counts; the earlier
submission did not record commit SHAs, which reviewers flagged. See
`docs/REPOSITORIES.md` for the current record.
