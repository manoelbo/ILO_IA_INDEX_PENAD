#!/usr/bin/env python3
"""Run the spatial-diagnostics replication component."""

from __future__ import annotations

import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CODE_ROOT = PACKAGE_ROOT / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from replication.component_pipeline import main_for


if __name__ == "__main__":
    raise SystemExit(main_for("spatial"))
