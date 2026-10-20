# RQ2 comparison: CodeDoc against RepoAgent

Both methods are scored by the same judge under the same rubric; each rubric's
own dimension set is used, so ISO and GitHub numbers must not be compared with
each other.

## GitHub docs style (full set)

| method | documents | dimensions | overall mean |
|---|---|---|---|
| CodeDoc (this work) | 578 | 18 | 3.44 |
| RepoAgent | 578 | 18 | 2.263 |

* CodeDoc (this work) leads RepoAgent by +1.18 overall (+52.0%).

| main dimension | CodeDoc (this work) | RepoAgent | gap |
|---|---|---|---|
| Content Types & Completeness | 4.15 | 1.38 | +2.77 |
| Styling & Formatting | 3.62 | 2.60 | +1.02 |
| Structure & Organization | 3.17 | 2.92 | +0.25 |
| Article Content Families | 3.09 | 1.82 | +1.27 |
| Content Quality | 2.92 | 3.48 | -0.56 |

| repository | CodeDoc (this work) | RepoAgent | gap |
|---|---|---|---|
| dify_api | 3.49 | 2.31 | +1.18 |
| fairseq | 3.60 | 2.20 | +1.40 |
| flask-main | 3.58 | 2.30 | +1.29 |
| joblib | 3.42 | 2.25 | +1.16 |
| numpy | 3.41 | 2.24 | +1.17 |
| openui | 3.42 | 2.32 | +1.10 |
| pyro | 3.39 | 2.28 | +1.11 |
| ragflow | 3.33 | 2.27 | +1.06 |
| sonnet | 3.34 | 2.26 | +1.08 |
| torch | 3.38 | 2.20 | +1.18 |

| kind | CodeDoc (this work) | RepoAgent | gap |
|---|---|---|---|
| class | 3.37 | 2.24 | +1.13 |
| function | 3.57 | 2.33 | +1.24 |
| method | 3.44 | 2.25 | +1.19 |

## ISO/IEC 26514 (entity-level dimensions)

| method | documents | dimensions | overall mean |
|---|---|---|---|
| CodeDoc (this work) | 578 | 14 | 4.737 |
| RepoAgent | 578 | 14 | 4.267 |

* CodeDoc (this work) leads RepoAgent by +0.47 overall (+11.0%).

| main dimension | CodeDoc (this work) | RepoAgent | gap |
|---|---|---|---|
| Information Structure | 4.96 | 3.79 | +1.17 |
| Format & Presentation | 4.95 | 4.35 | +0.60 |
| Internationalization & Localization | 4.76 | 4.61 | +0.16 |
| Content Quality | 4.59 | 4.68 | -0.09 |
| Usability & User Experience | 4.11 | 3.28 | +0.83 |

| repository | CodeDoc (this work) | RepoAgent | gap |
|---|---|---|---|
| dify_api | 4.74 | 4.39 | +0.35 |
| fairseq | 4.75 | 4.11 | +0.64 |
| flask-main | 4.79 | 4.32 | +0.47 |
| joblib | 4.73 | 4.31 | +0.42 |
| numpy | 4.77 | 4.22 | +0.55 |
| openui | 4.74 | 4.34 | +0.40 |
| pyro | 4.66 | 4.24 | +0.41 |
| ragflow | 4.81 | 4.32 | +0.49 |
| sonnet | 4.74 | 4.33 | +0.40 |
| torch | 4.69 | 4.11 | +0.58 |

| kind | CodeDoc (this work) | RepoAgent | gap |
|---|---|---|---|
| class | 4.61 | 4.26 | +0.35 |
| function | 4.80 | 4.33 | +0.47 |
| method | 4.83 | 4.25 | +0.58 |

