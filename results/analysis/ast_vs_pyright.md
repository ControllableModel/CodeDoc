# AST vs Pyright: same-sample comparison

* sample: 100 entities per repository, seed 42
* metric: internal call resolution = internal calls / all call sites in the sample

| repo | sample | AST rate | AST build (s) | Pyright rate | Pyright query (s) | s/entity |
|---|---|---|---|---|---|---|
| ragflow | 34 | 20.4% | 0.01 | 19.4% | 1.17 | 0.036 |
| openui | 100 | 13.6% | 0.05 | 16.2% | 2.22 | 0.022 |
| flask-main | 100 | 14.1% | 0.11 | 23.0% | 2.02 | 0.02 |
| joblib | 100 | 15.7% | 0.2 | 19.2% | 2.81 | 0.028 |
