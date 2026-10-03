"""P5 tests use synthetic data only.

No test compares imagery between New Study 2 condition groups: the real-data
check below asserts group counts and field hygiene, which are fixed by the
questionnaire and were recorded before registration.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aphantasia.cli import main  # noqa: E402
from aphantasia.datasets import DatasetError, classify_ndd_conditions, load_new_study2_conditions  # noqa: E402
from aphantasia.models import AnalysisStop  # noqa: E402
from aphantasia.p5 import (  # noqa: E402
    EXPLORATORY_MODALITIES,
    FREEZE_PATH,
    PLAN_PATH,
    PRIMARY_MODALITIES,
    PRIMARY_SEQUENCE,
    Registration,
    _floor_model,
    _repeated_model,
    plan_p5,
    run_p5,
    standardize_to_reference,
    verify_registration,
)


def _synthetic_new(seed: int = 5, shift: float = -0.5, chem_extra: float = -0.3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    sizes = {"reference": 700, "asd": 160, "adhd_only": 90, "other_ndd_only": 20}
    parts = []
    for group, n in sizes.items():
        latent = rng.normal(size=n) + (shift if group == "asd" else 0.0)
        part = {"group": [group] * n, "asd_with_adhd": (rng.random(n) < 0.3) & (group == "asd"),
                "age": rng.integers(18, 31, size=n).astype(float), "sex_gender": rng.choice(["0", "1"], size=n)}
        for modality in [*PRIMARY_MODALITIES, *EXPLORATORY_MODALITIES]:
            extra = chem_extra if (group == "asd" and modality in ("smell", "taste")) else 0.0
            score = np.clip(np.round(22 + 5 * (0.8 * latent + 0.6 * rng.normal(size=n) + extra)), 5, 35)
            # Floor (absent-imagery) mass so the absence models have events.
            absent_rate = 0.04 + (0.08 if extra else 0.0)
            score[rng.random(n) < absent_rate] = 5
            part[modality] = score
        parts.append(pd.DataFrame(part))
    return pd.concat(parts, ignore_index=True)


def _synthetic_arnold(seed: int = 9) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = 200
    frame = pd.DataFrame({"diagnosis_group": np.repeat([0, 1], n), "age": rng.normal(35, 10, 2 * n),
                          "sex_gender": rng.choice(["1", "2"], 2 * n)})
    latent = rng.normal(size=2 * n) - 0.2 * frame["diagnosis_group"].to_numpy()
    for modality in PRIMARY_MODALITIES:
        frame[modality] = np.clip(np.round(50 + 20 * (0.8 * latent + 0.6 * rng.normal(size=2 * n))), 0, 100)
    return frame


def test_condition_groups_are_exclusive_and_asd_takes_precedence():
    gate = pd.Series([0, 1, 1, 1, 1, 1])
    ticks = pd.Series([pd.NA, "ASD,", "ADHD,", "ASD,ADHD,", "Dyslexia,", pd.NA])
    result = classify_ndd_conditions(gate, ticks)
    assert result["group"].tolist() == ["reference", "asd", "adhd_only", "asd", "other_ndd_only", "unspecified_ndd"]
    assert result["asd_with_adhd"].tolist() == [False, False, False, True, False, False]


def test_condition_ticks_without_gate_yes_fail_closed():
    with pytest.raises(DatasetError):
        classify_ndd_conditions(pd.Series([0]), pd.Series(["ASD,"]))


def test_real_study2_group_counts_and_no_identifiers():
    frame, flow = load_new_study2_conditions(ROOT / "2bdn6-osfstorage-archive.zip")
    assert flow["published_analysis_n"] == 1003
    assert flow["group_counts"] == {"reference": 749, "asd": 150, "adhd_only": 84, "other_ndd_only": 20, "unspecified_ndd": 0}
    assert flow["asd_with_adhd"] == 46
    assert not {"id", "ProlificID", "comment", "neurodev2", "diag2"}.intersection(frame.columns)


def test_run_p5_refuses_without_verified_registration():
    with pytest.raises(AnalysisStop) as stop:
        run_p5(_synthetic_new(), Path(tempfile.mkdtemp()), registration="https://osf.io/fake")  # type: ignore[arg-type]
    assert stop.value.code == "awaiting_preregistration"


def test_registration_gate_requires_url_freeze_and_unchanged_plan():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / PLAN_PATH).parent.mkdir(parents=True)
        (root / PLAN_PATH).write_text("plan v1\n", encoding="utf-8")
        with pytest.raises(AnalysisStop) as no_url:
            verify_registration(root, None)
        assert no_url.value.code == "awaiting_preregistration"
        with pytest.raises(AnalysisStop) as not_frozen:
            verify_registration(root, "https://osf.io/abcde")
        assert not_frozen.value.code == "plan_not_frozen"
        import hashlib
        (root / FREEZE_PATH).write_text(hashlib.sha256(b"plan v1\n").hexdigest() + "  preregistration.md\n", encoding="utf-8")
        assert verify_registration(root, "https://osf.io/abcde").url == "https://osf.io/abcde"
        (root / PLAN_PATH).write_text("plan v2\n", encoding="utf-8")
        with pytest.raises(AnalysisStop) as changed:
            verify_registration(root, "https://osf.io/abcde")
        assert changed.value.code == "plan_changed_after_freeze"


def test_cli_p5_stops_before_loading_data_when_unregistered():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        assert main(["--project", "P5", "--root", str(root)]) == 2
        assert not (root / "runs").exists()


def test_run_p5_recovers_synthetic_effects_and_writes_aggregates_only():
    registration = Registration(url="https://osf.io/synthetic", plan_sha256="0" * 64)
    with tempfile.TemporaryDirectory() as directory:
        result = run_p5(_synthetic_new(), Path(directory), registration=registration, arnold=_synthetic_arnold())
        diagnostics = json.loads(Path(next(p for p in result["artifacts"] if p.endswith(".json"))).read_text(encoding="utf-8"))
        estimates = pd.read_csv(next(p for p in result["artifacts"] if p.endswith(".csv")))
    primary = diagnostics["details"]["primary"]
    assert list(primary) == PRIMARY_SEQUENCE
    h1 = primary["H1_general_imagery_shift"]
    # Latent shift −0.5 plus the smell/taste penalty, in re-scaled composite SD units.
    assert -1.0 < h1["estimate"] < -0.4
    assert h1["confirmatory_support"] is True
    chem = diagnostics["details"]["secondary"]["S1_modality_profile_asd"]["chemosensory_minus_visual"]
    assert chem["estimate"] < 0
    assert diagnostics["details"]["H1_interpretation"] in {"replicated", "informative_non_replication", "inconclusive"}
    assert "difference_p_two_sided" in diagnostics["details"]["cross_study"]["general_imagery_shift"]
    assert diagnostics["contains_participant_rows"] is False
    assert len(estimates) == diagnostics["estimate_rows"]
    assert set(estimates["project"]) == {"P5"}


def test_gatekeeping_stops_confirmatory_testing_after_first_failure():
    registration = Registration(url="https://osf.io/synthetic", plan_sha256="0" * 64)
    with tempfile.TemporaryDirectory() as directory:
        result = run_p5(_synthetic_new(shift=0.0, chem_extra=0.0), Path(directory), registration=registration)
        diagnostics = json.loads(Path(next(p for p in result["artifacts"] if p.endswith(".json"))).read_text(encoding="utf-8"))
    primary = diagnostics["details"]["primary"]
    if not primary["H1_general_imagery_shift"]["confirmatory_support"]:
        assert primary["H2a_smell_absence"]["tested_confirmatorily"] is False
        assert primary["H2b_taste_absence"]["confirmatory_support"] is False


def test_sparse_absence_falls_back_to_exact_odds_ratio():
    frame = _synthetic_new(seed=3)
    pair = frame.loc[frame["group"].isin(["reference", "asd"])].copy()
    pair["in_group"] = pair["group"].eq("asd").astype(float)
    pair["smell"] = 20.0
    pair.iloc[:3, pair.columns.get_loc("smell")] = 5.0  # three reference events only
    pair.loc[pair.index[pair["in_group"].eq(1)][:4], "smell"] = 5.0
    rows, diagnostics = _floor_model(pair, "in_group", "smell", 5, model="fixture", cohort="toy")
    assert rows[0]["effect_kind"] == "odds_ratio_conditional_exact_unadjusted"
    assert diagnostics["events"] == 7
    assert 0 < diagnostics["one_sided_p_greater"] <= 1
    assert diagnostics["absent_counts"]["in_group=1"]["absent"] == "<5"


def test_zero_absent_cases_in_one_group_still_writes_strict_json():
    frame = _synthetic_new(seed=4)
    asd = frame["group"].eq("asd")
    frame.loc[asd & frame["taste"].eq(5), "taste"] = 6  # no ASD taste-absence cases -> exact OR of 0
    frame.loc[~asd & frame["taste"].eq(5), "taste"] = 6
    frame.loc[frame.index[~asd][:6], "taste"] = 5
    registration = Registration(url="https://osf.io/synthetic", plan_sha256="0" * 64)
    with tempfile.TemporaryDirectory() as directory:
        result = run_p5(frame, Path(directory), registration=registration)
        diagnostics = json.loads(Path(next(p for p in result["artifacts"] if p.endswith(".json"))).read_text(encoding="utf-8"))
    taste = diagnostics["details"]["primary"]["H2b_taste_absence"]
    assert taste["method"].startswith("conditional exact")
    assert taste["odds_ratio"] == 0.0


def test_chemosensory_contrast_matches_statsmodels_cluster_ols():
    frame = _synthetic_new(seed=21)
    pair = frame.loc[frame["group"].isin(["reference", "asd"])].copy()
    pair["in_group"] = pair["group"].eq("asd").astype(float)
    pair = standardize_to_reference(pair, pair["group"].eq("reference"), PRIMARY_MODALITIES).reset_index(drop=True)
    _rows, diagnostics = _repeated_model(pair, "in_group", model="fixture", cohort="toy")
    long = pd.concat([pd.DataFrame({"pid": pair.index, "g": pair["in_group"], "age": pair["age"],
                                    "sex1": pair["sex_gender"].eq("1").astype(float), "m": m, "y": pair[f"z_{m}"]})
                      for m in PRIMARY_MODALITIES], ignore_index=True)
    design = {"const": 1.0, "g": long["g"], "age": long["age"]}
    for m in PRIMARY_MODALITIES[1:]:
        design[f"mod_{m}"] = long["m"].eq(m).astype(float)
        design[f"gx_{m}"] = long["g"] * design[f"mod_{m}"]
    design["sex1"] = long["sex1"]
    x = pd.DataFrame(design)
    fit = sm.OLS(long["y"], x).fit(cov_type="cluster", cov_kwds={"groups": long["pid"], "use_correction": True})
    weights = np.zeros(x.shape[1])
    weights[list(x.columns).index("gx_smell")] = 0.5
    weights[list(x.columns).index("gx_taste")] = 0.5
    assert diagnostics["chemosensory_minus_visual"]["estimate"] == pytest.approx(float(weights @ fit.params), abs=1e-8)
    se = float(np.sqrt(weights @ fit.cov_params().to_numpy() @ weights))
    assert diagnostics["chemosensory_minus_visual"]["se"] == pytest.approx(se, rel=1e-6)


def test_power_plan_uses_counts_only():
    with tempfile.TemporaryDirectory() as directory:
        counts = {"reference": 749, "asd": 150, "adhd_only": 84, "other_ndd_only": 20, "unspecified_ndd": 0, "asd_without_adhd": 104}
        result = plan_p5(_synthetic_arnold(), counts, Path(directory))
        plan = json.loads(Path(result["artifacts"][0]).read_text(encoding="utf-8"))
    assert plan["uses_new_group_by_imagery_comparisons"] is False
    assert 0 < plan["continuous"]["H1_general_imagery_shift"]["asd_vs_reference"]["power_one_sided_05_at_arnold_effect"] < 1
