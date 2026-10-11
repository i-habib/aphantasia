"""P8: is aphantasia a separate group or the low end of a continuum?

The taxometric analysis itself is in ``scripts/p8_taxometrics.R`` (RTaxometrics).
This module only checks the registration and then calls R, so the R step
never runs on real data before the plan is registered and frozen.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .models import AnalysisStop
from .p5 import Registration

PLAN_PATH = Path("projects/P8_aphantasia_taxometrics/protocol/preregistration.md")
R_SCRIPT = Path("scripts/p8_taxometrics.R")


def run_p8(root: Path, output_dir: Path, *, registration: Registration) -> dict[str, Any]:
    if not isinstance(registration, Registration):
        raise AnalysisStop("blocked", "awaiting_preregistration", "run_p8 requires a verified Registration.")
    rscript = shutil.which("Rscript")
    if rscript is None:
        raise AnalysisStop("blocked", "r_missing", "Rscript is not installed; P8 needs R with RTaxometrics 3.2.1.")
    completed = subprocess.run([rscript, str(root / R_SCRIPT), "--root", str(root), "--out", str(output_dir),
                                "--registration", registration.url], capture_output=True, text=True)
    last = completed.stdout.strip().splitlines()[-1] if completed.stdout.strip() else ""
    if completed.returncode != 0:
        raise AnalysisStop("blocked", "r_failed", (completed.stderr or last)[-2000:])
    summary = json.loads(last)["P8"]
    return {**summary, "project": "P8", "artifacts": [str(output_dir / "p8_results.json"), str(output_dir / "graphs_main.png")]}
