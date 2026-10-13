"""P8 tests. Simulated data only; no real P8 data are analysed.

The quick R self-test checks the indicator, matching and verdict helpers.
Set P8_FULL_SELFTEST=1 to also run the taxometric procedures on simulated
two-group and continuous data (about 6 minutes).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aphantasia.cli import main  # noqa: E402
from aphantasia.models import AnalysisStop  # noqa: E402
from aphantasia.p8 import PLAN_PATH, run_p8  # noqa: E402

RSCRIPT = shutil.which("Rscript")
needs_r = pytest.mark.skipif(RSCRIPT is None, reason="Rscript not installed")


def _selftest(*extra: str) -> dict:
    completed = subprocess.run([RSCRIPT, str(ROOT / "scripts" / "p8_taxometrics.R"), "--selftest", *extra],
                               capture_output=True, text=True, check=True)
    return json.loads(completed.stdout.strip().splitlines()[-1])


@needs_r
def test_helpers_on_simulated_items() -> None:
    result = _selftest()
    assert result["scenes_ok"] and result["pairs_ok"] and result["band_edges_ok"] and result["verdict_rule_ok"]
    assert result["matched_rows_unique"] and result["matched_n"] > 0
    assert result["matched_band_gap"] < 0.01


@needs_r
@pytest.mark.skipif(os.environ.get("P8_FULL_SELFTEST") != "1", reason="slow; set P8_FULL_SELFTEST=1")
def test_taxometrics_separate_simulated_structures() -> None:
    result = _selftest("--full")
    assert result["taxonic_verdict"] == "two_groups"
    assert result["continuous_verdict"] == "continuum"


@needs_r
@pytest.mark.skipif(os.environ.get("P8_FULL_SELFTEST") != "1", reason="slow; set P8_FULL_SELFTEST=1")
def test_shards_then_full_run_match_one_full_run() -> None:
    result = _selftest("--shards")
    assert result["shards_match_full_run"]
    assert result["saved_by_shards"] > 0


def test_run_p8_refuses_without_registration(tmp_path: Path) -> None:
    with pytest.raises(AnalysisStop) as stop:
        run_p8(ROOT, tmp_path, registration=None)  # type: ignore[arg-type]
    assert stop.value.code == "awaiting_preregistration"


def test_cli_blocks_before_registration(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--root", str(ROOT), "--project", "P8"]) == 2
    assert "awaiting_preregistration" in capsys.readouterr().out


def test_plan_exists_and_names_rtaxometrics() -> None:
    text = (ROOT / PLAN_PATH).read_text(encoding="utf-8")
    assert "RTaxometrics" in text and "CCFI" in text
