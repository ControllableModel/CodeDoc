"""Aggregation of per-dimension scores into reported numbers.

Everything the paper reports is an aggregate, and every aggregate is a choice.
This module makes the choices explicit and swappable:

``flat_mean``          all dimensions equally weighted (what was published)
``category_balanced``  average inside each category, then across categories —
                       removes the accidental weight that categories with more
                       dimensions silently receive in a flat mean
``weighted``           caller-supplied weights, for the sensitivity analysis
``flatten``            parse the archived ``*quality.jsonl`` records

No weighting scheme is baked in as "the right one": the published flat mean
stays the default so published numbers remain reproducible.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence

ScoreMap = Mapping[str, float]


def flat_mean(scores: ScoreMap, dimensions: Optional[Sequence[str]] = None) -> float:
    """Mean over the selected dimensions (default: all present)."""
    keys = [d for d in (dimensions or scores.keys()) if d in scores]
    if not keys:
        raise ValueError("no overlapping dimensions")
    return sum(scores[k] for k in keys) / len(keys)


def category_balanced(
    scores: ScoreMap, groups: Mapping[str, Sequence[str]]
) -> float:
    """Mean of per-category means.

    Categories containing no scored dimension are skipped.  Use this to check
    whether a conclusion survives a more defensible weighting of the rubric.
    """
    per_category: List[float] = []
    for dims in groups.values():
        present = [d for d in dims if d in scores]
        if present:
            per_category.append(sum(scores[d] for d in present) / len(present))
    if not per_category:
        raise ValueError("no category had a scored dimension")
    return sum(per_category) / len(per_category)


def weighted(
    scores: ScoreMap, weights: Mapping[str, float], dimensions: Optional[Sequence[str]] = None
) -> float:
    """Weighted mean; missing weights default to 1.0."""
    keys = [d for d in (dimensions or scores.keys()) if d in scores]
    if not keys:
        raise ValueError("no overlapping dimensions")
    num = sum(scores[k] * float(weights.get(k, 1.0)) for k in keys)
    den = sum(float(weights.get(k, 1.0)) for k in keys)
    return num / den


def boost_weights(dimensions: Iterable[str], boosted: Iterable[str], factor: float = 2.0) -> Dict[str, float]:
    """Weight map that emphasises a subset (e.g. correctness-type dimensions)."""
    target = set(boosted)
    return {d: (factor if d in target else 1.0) for d in dimensions}


def _merge_record(target: Dict[str, float], data: object) -> None:
    if not isinstance(data, dict):
        return
    for name, value in data.items():
        if isinstance(value, dict) and isinstance(value.get("judge"), (int, float)):
            target[name] = float(value["judge"])


def _iter_json_objects(text: str):
    """Yield every JSON object in a file that may hold one or several."""
    decoder = json.JSONDecoder()
    idx, n = 0, len(text)
    while idx < n:
        while idx < n and text[idx] in " \t\r\n":
            idx += 1
        if idx >= n:
            return
        obj, idx = decoder.raw_decode(text, idx)
        yield obj


def load_quality_record(path: str | Path) -> Dict[str, float]:
    """Read one archived ``*quality.jsonl`` file into ``{dimension: score}``.

    Archived files are inconsistent: some hold a single pretty-printed JSON
    object, others concatenate several objects. Both shapes are accepted and
    merged, because the audit must not silently drop evidence.
    """
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    out: Dict[str, float] = {}
    for obj in _iter_json_objects(text):
        _merge_record(out, obj)
    if not out:
        raise ValueError(f"no judge scores found in {path}")
    return out


def load_quality_dir(directory: str | Path, pattern: str = "*quality.jsonl") -> Dict[str, Dict[str, float]]:
    """Load every archived quality record in a directory tree."""
    root = Path(directory)
    return {
        p.relative_to(root).as_posix(): load_quality_record(p)
        for p in sorted(root.rglob(pattern))
    }


def sensitivity(
    records: Mapping[str, ScoreMap],
    schemes: Mapping[str, Callable[[ScoreMap], float]],
) -> Dict[str, Dict[str, float]]:
    """Apply several aggregation schemes to the same records.

    Returns ``{scheme: {record: score}}`` plus the spread, which is what the
    paper should report instead of a single mean.
    """
    out: Dict[str, Dict[str, float]] = {}
    for name, fn in schemes.items():
        per_record: Dict[str, float] = {}
        for rec, scores in records.items():
            try:
                per_record[rec] = fn(scores)
            except ValueError:
                continue
        out[name] = per_record
    return out


def spread(scheme_scores: Mapping[str, Mapping[str, float]]) -> Dict[str, float]:
    """Per-scheme mean and the overall range across schemes."""
    means = {
        name: sum(v.values()) / len(v)
        for name, v in scheme_scores.items()
        if v
    }
    if not means:
        return {}
    return {
        "means": means,  # type: ignore[dict-item]
        "min": min(means.values()),
        "max": max(means.values()),
        "range": max(means.values()) - min(means.values()),
    }
