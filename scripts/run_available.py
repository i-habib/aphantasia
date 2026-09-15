#!/usr/bin/env python3
"""Thin launcher that works from a checkout without a virtual environment."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aphantasia.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
