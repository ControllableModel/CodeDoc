"""Generate documentation for a target repository.

Thin entry point around :mod:`codedoc.cli` so the canonical command is short and
stable::

    python scripts/run_generate.py --target_path targets/flask --llm_key $env:LLM_KEY
    python scripts/run_generate.py --target_path targets/flask --process False   # static analysis only
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codedoc.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
