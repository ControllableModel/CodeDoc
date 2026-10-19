# outputs/ — documentation store

Generated documentation artifacts live here. Nothing in this directory is
committed: the contents are reproducible from `targets/` plus the criteria set
and the recorded model configuration.

Expected layout after a run:

```
outputs/
└── <repository>/
    ├── <module>.md            # generated documentation (per source file)
    ├── <module>.info          # dependency context actually injected
    └── scores_<criteria>/     # judge verdicts, one file per artifact
        └── <module>quality.jsonl
```

The `.info` files are the audit trail for the *dependency-aware* claim: they show
exactly which callers, callees and (once S1 lands) hierarchy relations reached
the prompt. Without them the paper's central mechanism cannot be checked.
