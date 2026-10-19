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

The ten evaluated repositories are already extracted here:

    numpy  openui  ragflow  dify_api  flask-main  joblib  pyro  fairseq  sonnet  torch

**Read `docs/PROVENANCE.md` first**: it records what each snapshot contains, which
published entity counts reproduce and which do not, two defects in the archived
evidence, why upstream commit SHAs are not recoverable, and the two
`pyan3==1.1.1` failure modes that make one repository (fairseq) unanalysable.
Provenance, not just presence, is what reviewers asked for.
