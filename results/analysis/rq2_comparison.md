# RQ2 comparison: CodeDoc against RepoAgent

Both methods are scored by the same judge under the same rubric; each rubric's
own dimension set is used, so ISO and GitHub numbers must not be compared with
each other.

## GitHub docs style (full set)

| method | documents | dimensions | overall mean |
|---|---|---|---|
| CodeDoc (this work) | 578 | 18 | 3.084 |
| RepoAgent | 38 | 18 | 2.721 |

* CodeDoc (this work) leads RepoAgent by +0.36 overall (+13.3%).

| main dimension | CodeDoc (this work) | RepoAgent | gap |
|---|---|---|---|
| Content Types & Completeness | 3.71 | 1.38 | +2.33 |
| Article Content Families | 3.18 | 2.04 | +1.13 |
| Styling & Formatting | 3.15 | 2.86 | +0.29 |
| Structure & Organization | 2.57 | 3.16 | -0.60 |
| Content Quality | 2.23 | 4.64 | -2.40 |

| repository | CodeDoc (this work) | RepoAgent | gap |
|---|---|---|---|
| dify_api | 3.10 | — |  |
| fairseq | 3.22 | — |  |
| flask-main | 3.13 | — |  |
| joblib | 3.14 | — |  |
| numpy | 3.04 | — |  |
| openui | 2.90 | — |  |
| pyro | 3.04 | — |  |
| ragflow | 3.18 | 2.72 | +0.46 |
| sonnet | 3.02 | — |  |
| torch | 3.11 | — |  |

| kind | CodeDoc (this work) | RepoAgent | gap |
|---|---|---|---|
| class | 2.98 | 2.44 | +0.54 |
| function | 3.07 | 2.65 | +0.42 |
| method | 3.19 | 2.79 | +0.40 |

## ISO/IEC 26514 (entity-level dimensions)

| method | documents | dimensions | overall mean |
|---|---|---|---|
| CodeDoc (this work) | 578 | 14 | 4.661 |
| RepoAgent | 38 | 14 | 4.363 |

* CodeDoc (this work) leads RepoAgent by +0.30 overall (+6.8%).

| main dimension | CodeDoc (this work) | RepoAgent | gap |
|---|---|---|---|
| Format & Presentation | 4.92 | 4.54 | +0.38 |
| Information Structure | 4.75 | 3.95 | +0.81 |
| Internationalization & Localization | 4.72 | 4.50 | +0.22 |
| Usability & User Experience | 4.63 | 3.55 | +1.08 |
| Content Quality | 4.46 | 4.73 | -0.27 |

| repository | CodeDoc (this work) | RepoAgent | gap |
|---|---|---|---|
| dify_api | 4.67 | — |  |
| fairseq | 4.68 | — |  |
| flask-main | 4.67 | — |  |
| joblib | 4.63 | — |  |
| numpy | 4.65 | — |  |
| openui | 4.65 | — |  |
| pyro | 4.61 | — |  |
| ragflow | 4.74 | 4.36 | +0.37 |
| sonnet | 4.68 | — |  |
| torch | 4.65 | — |  |

| kind | CodeDoc (this work) | RepoAgent | gap |
|---|---|---|---|
| class | 4.57 | 4.27 | +0.30 |
| function | 4.73 | 4.46 | +0.28 |
| method | 4.71 | 4.35 | +0.36 |

