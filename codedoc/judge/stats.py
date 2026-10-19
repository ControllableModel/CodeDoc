"""Agreement and uncertainty statistics.

Why this exists: agreement among human raters is the precondition for treating
human scores as a reference, and the published artifact reported an unweighted
Fleiss' kappa on an *ordinal* 1-5 scale, which understates agreement.
:func:`weighted_kappa` and :func:`icc` give the ordinal-appropriate measures.

All functions are pure Python (no scipy dependency) so results reproduce without
a scientific stack.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Sequence


def _as_list(x: Sequence[float]) -> List[float]:
    return [float(v) for v in x]


def cohen_kappa(a: Sequence[int], b: Sequence[int]) -> float:
    """Unweighted Cohen's kappa for two raters over categorical labels."""
    if len(a) != len(b) or not a:
        raise ValueError("rater sequences must be non-empty and equal length")
    labels = sorted({*a, *b})
    idx = {lab: i for i, lab in enumerate(labels)}
    n = len(a)
    obs = [[0] * len(labels) for _ in labels]
    for x, y in zip(a, b):
        obs[idx[x]][idx[y]] += 1
    po = sum(obs[i][i] for i in range(len(labels))) / n
    row = [sum(obs[i]) / n for i in range(len(labels))]
    col = [sum(obs[i][j] for i in range(len(labels))) / n for j in range(len(labels))]
    pe = sum(row[i] * col[i] for i in range(len(labels)))
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def weighted_kappa(
    a: Sequence[int],
    b: Sequence[int],
    categories: Optional[Sequence[int]] = None,
) -> float:
    """Quadratic-weighted kappa for two raters on an ordinal scale.

    This is the statistic that should be reported for a 1-5 rubric: it treats a
    1-vs-2 disagreement as smaller than a 1-vs-5 disagreement.
    """
    if len(a) != len(b) or not a:
        raise ValueError("rater sequences must be non-empty and equal length")
    cats = list(categories) if categories else list(range(min(min(a), min(b)), max(max(a), max(b)) + 1))
    k = len(cats)
    pos = {c: i for i, c in enumerate(cats)}
    obs = [[0.0] * k for _ in range(k)]
    for x, y in zip(a, b):
        obs[pos[x]][pos[y]] += 1
    n = float(len(a))
    obs = [[v / n for v in row] for row in obs]
    row = [sum(obs[i]) for i in range(k)]
    col = [sum(obs[i][j] for i in range(k)) for j in range(k)]
    num = den = 0.0
    for i in range(k):
        for j in range(k):
            w = ((i - j) ** 2) / ((k - 1) ** 2) if k > 1 else 0.0
            num += w * obs[i][j]
            den += w * row[i] * col[j]
    return 1.0 if den == 0 else 1 - num / den


def fleiss_kappa(table: Sequence[Sequence[int]]) -> float:
    """Fleiss' kappa from a subjects x categories count table."""
    n_items = len(table)
    if n_items == 0:
        raise ValueError("empty table")
    n_raters = sum(table[0])
    if any(sum(row) != n_raters for row in table):
        raise ValueError("every item must be rated by the same number of raters")
    if n_raters < 2:
        raise ValueError("need at least two raters")
    p_i = []
    for row in table:
        p_i.append((sum(c * c for c in row) - n_raters) / (n_raters * (n_raters - 1)))
    p_bar = sum(p_i) / n_items
    totals = [sum(row[j] for row in table) for j in range(len(table[0]))]
    denom_total = n_items * n_raters
    p_e = sum((t / denom_total) ** 2 for t in totals)
    return 1.0 if p_e == 1 else (p_bar - p_e) / (1 - p_e)


def icc(matrix: Sequence[Sequence[float]], form: str = "ICC(2,1)") -> float:
    """Intraclass correlation for a subjects x raters matrix.

    ``ICC(2,1)`` is single-rater absolute agreement; ``ICC(2,k)`` is the
    reliability of the mean of k raters, which is what an averaged human score
    actually is.
    """
    n = len(matrix)
    if n < 2:
        raise ValueError("need at least two subjects")
    k = len(matrix[0])
    if any(len(row) != k for row in matrix):
        raise ValueError("ragged matrix")
    grand = sum(sum(row) for row in matrix) / (n * k)
    row_means = [sum(row) / k for row in matrix]
    col_means = [sum(matrix[i][j] for i in range(n)) / n for j in range(k)]
    ss_rows = k * sum((r - grand) ** 2 for r in row_means)
    ss_cols = n * sum((c - grand) ** 2 for c in col_means)
    ss_total = sum((x - grand) ** 2 for row in matrix for x in row)
    ss_err = ss_total - ss_rows - ss_cols
    ms_rows = ss_rows / (n - 1)
    ms_cols = ss_cols / (k - 1) if k > 1 else 0.0
    ms_err = ss_err / ((n - 1) * (k - 1)) if (n > 1 and k > 1) else 0.0
    if form.upper() == "ICC(2,K)":
        denom = ms_rows + (ms_cols - ms_err) / n if n else ms_rows
        return 0.0 if denom == 0 else (ms_rows - ms_err) / denom
    denom = ms_rows + (k - 1) * ms_err + (k * (ms_cols - ms_err)) / n
    return 0.0 if denom == 0 else (ms_rows - ms_err) / denom


def bootstrap_ci(
    values: Sequence[float],
    statistic=sum,
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 0,
) -> Dict[str, float]:
    """Percentile bootstrap confidence interval for a statistic over items."""
    vals = _as_list(values)
    if not vals:
        raise ValueError("no values")
    if statistic is sum:
        stat = lambda xs: sum(xs) / len(xs)  # noqa: E731
    else:
        stat = statistic
    rng = random.Random(seed)
    n = len(vals)
    boots = []
    for _ in range(n_boot):
        sample = [vals[rng.randrange(n)] for _ in range(n)]
        boots.append(stat(sample))
    boots.sort()
    lo = boots[int((alpha / 2) * n_boot)]
    hi = boots[int((1 - alpha / 2) * n_boot) - 1]
    return {"point": stat(vals), "lo": lo, "hi": hi, "n": n}


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    """Spearman rank correlation (ties get average ranks)."""
    if len(x) != len(y) or not x:
        raise ValueError("sequences must be non-empty and equal length")

    def ranks(v: Sequence[float]) -> List[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        out = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                out[order[k]] = avg
            i = j + 1
        return out

    rx, ry = ranks(x), ranks(y)
    n = len(rx)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return 0.0 if den == 0 else num / den


def describe(values: Sequence[float]) -> Dict[str, float]:
    """Mean, population standard deviation, min and max."""
    vals = _as_list(values)
    if not vals:
        raise ValueError("no values")
    mu = sum(vals) / len(vals)
    var = sum((v - mu) ** 2 for v in vals) / len(vals)
    return {"mean": mu, "sd": math.sqrt(var), "min": min(vals), "max": max(vals), "n": len(vals)}
