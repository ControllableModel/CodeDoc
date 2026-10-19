"""Token and latency accounting for every model call the pipeline makes.

Reviewers ask two questions that the artifact could not answer: how much does a
run cost, and where does the cost go. This module answers both by recording every
call at the point where the SDK response is available — no estimation from
character counts.

Two call sites feed it: ``writer.llm.LinguisticCore.process`` (generation) and
``judge.query.LLM_Remote_query`` (judging). Each record keeps the phase, the model,
the prompt/completion token counts reported by the API, the wall time, and whether
the call succeeded.

Usage::

    from codedoc.writer.usage import RECORDER
    ...run the pipeline...
    print(RECORDER.summary())
    RECORDER.save("outputs/cost_report.json")
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional


class UsageRecorder:
    """Thread-safe accumulator of per-call usage records."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.records: List[Dict[str, object]] = []
        self._started = time.time()

    # -- recording ----------------------------------------------------------
    def record(
        self,
        phase: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        seconds: float = 0.0,
        ok: bool = True,
        error: str = "",
        label: str = "",
    ) -> None:
        with self._lock:
            self.records.append(
                {
                    "phase": phase,
                    "model": model,
                    "label": label,
                    "prompt_tokens": int(prompt_tokens or 0),
                    "completion_tokens": int(completion_tokens or 0),
                    "total_tokens": int(prompt_tokens or 0) + int(completion_tokens or 0),
                    "seconds": round(float(seconds), 3),
                    "ok": bool(ok),
                    "error": error[:200],
                }
            )

    def record_response(self, phase: str, model: str, response, seconds: float, label: str = "") -> None:
        """Record straight from an OpenAI SDK response object."""
        usage = getattr(response, "usage", None)
        self.record(
            phase=phase,
            model=model,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            seconds=seconds,
            label=label,
        )

    # -- reporting ----------------------------------------------------------
    def summary(self) -> Dict[str, object]:
        with self._lock:
            records = list(self.records)
        if not records:
            return {"calls": 0}

        def aggregate(subset: List[Dict[str, object]]) -> Dict[str, object]:
            prompt = sum(r["prompt_tokens"] for r in subset)  # type: ignore[misc]
            completion = sum(r["completion_tokens"] for r in subset)  # type: ignore[misc]
            seconds = sum(r["seconds"] for r in subset)  # type: ignore[misc]
            failed = sum(0 if r["ok"] else 1 for r in subset)
            n = len(subset)
            return {
                "calls": n,
                "failed": failed,
                "prompt_tokens": prompt,
                "completion_tokens": completion,
                "total_tokens": prompt + completion,
                "seconds": round(seconds, 2),
                "prompt_tokens_per_call": round(prompt / n, 1),
                "completion_tokens_per_call": round(completion / n, 1),
                "seconds_per_call": round(seconds / n, 3),
            }

        by_phase: Dict[str, Dict[str, object]] = {}
        for phase in sorted({str(r["phase"]) for r in records}):
            by_phase[phase] = aggregate([r for r in records if r["phase"] == phase])

        return {
            "wall_seconds": round(time.time() - self._started, 2),
            "total": aggregate(records),
            "by_phase": by_phase,
            "by_model": {
                model: aggregate([r for r in records if r["model"] == model])
                for model in sorted({str(r["model"]) for r in records})
            },
        }

    def save(self, path: str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {"summary": self.summary(), "records": self.records}
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def reset(self) -> None:
        with self._lock:
            self.records.clear()
        self._started = time.time()


#: Process-wide recorder. One pipeline run, one report.
RECORDER = UsageRecorder()


def log_call(phase: str, model: str, callable_, label: str = "", **kwargs):
    """Time a model call and record its usage; re-raises on failure."""
    started = time.time()
    try:
        response = callable_(**kwargs)
    except Exception as exc:
        RECORDER.record(
            phase=phase, model=model, seconds=time.time() - started,
            ok=False, error=f"{type(exc).__name__}: {exc}", label=label,
        )
        raise
    RECORDER.record_response(phase, model, response, time.time() - started, label=label)
    return response
