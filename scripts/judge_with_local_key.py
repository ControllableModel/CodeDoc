"""Run judge_matrix.py with the judge credentials from webapp/config.local.json.

The console keeps the key in a gitignored local file rather than in the environment. This
wrapper moves it into the environment for the duration of one run, so no key ever appears
in a shell command, a log, or a transcript. All arguments are passed straight through::

    python scripts/judge_with_local_key.py --mode per-dim --repos flask-main --axes iso_26514
"""
from __future__ import annotations

import json
import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "webapp" / "config.local.json"


def main() -> int:
    if not CONFIG.exists():
        print("  webapp/config.local.json is missing; cannot read the judge key")
        return 2
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    key = cfg.get("judge_api_key") or cfg.get("api_key")
    if not key:
        print("  no judge_api_key in webapp/config.local.json")
        return 2
    os.environ["JUDGE_KEY"] = key
    if cfg.get("judge_base_url"):
        os.environ["JUDGE_URL"] = cfg["judge_base_url"]
    if cfg.get("judge_model"):
        os.environ["JUDGE_MODEL"] = cfg["judge_model"]

    print(f"  judge key loaded ({len(key)} chars), "
          f"endpoint {'configured' if cfg.get('judge_base_url') else 'default'}, "
          f"model {cfg.get('judge_model', 'deepseek-chat')}")

    sys.argv = [str(ROOT / "scripts" / "judge_matrix.py")] + sys.argv[1:]
    runpy.run_path(str(ROOT / "scripts" / "judge_matrix.py"), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
