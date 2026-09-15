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

from aphantasia.datasets import (  # noqa: E402
    audit_mawtus_feasibility,
    load_arnold_code,
    load_new_studies,
)
from aphantasia.models import (  # noqa: E402
    _build_repeated_modality_frame,
    _fit_logit,
    _fit_ols_cluster,
    _fit_repeated_modality_model,
    _hedges_g,
    run_p1,
    run_p3,
)


def test_new_qc_reproduces_published_sample_counts_and_drops_identifiers():
    frame, flow = load_new_studies(ROOT / "2bdn6-osfstorage-archive.zip")
    assert flow["study_1"]["source_rows"] == 953
    assert flow["study_1"]["attention_excluded_nbact_lt_3"] == 4
    assert flow["study_1"]["published_analysis_n"] == 949
    assert flow["study_2"]["source_rows"] == 1020
    assert flow["study_2"]["attention_excluded_nbact_lt_3"] == 17
    assert flow["study_2"]["published_analysis_n"] == 1003
    assert len(flow["study_1"]["nonvisual_composite"]) == 7
    assert flow["study_1"]["outcome_mapping"]["question"] == "Are you currently receiving treatment for a neurologic or psychiatric condition?"
    assert flow["study_2"]["outcome_mapping"]["follow_up_branch"] == "shown only after Yes"
    for study in (1, 2):
        subset = frame.loc[frame["study_id"].eq(study)]
        assert float(subset["nonvisual_z"].mean()) == pytest.approx(0.0, abs=1e-12)
        assert float(subset["nonvisual_z"].std(ddof=0)) == pytest.approx(1.0, abs=1e-12)
        assert float(subset["general_z"].mean()) == pytest.approx(0.0, abs=1e-12)
        assert float(subset["general_z"].std(ddof=0)) == pytest.approx(1.0, abs=1e-12)
        assert subset["visual_aphantasia"].sum() > 0
        assert subset["visual_hyperphantasia"].sum() > 0
    assert "ProlificID" not in frame.columns
    assert "comment" not in frame.columns
    assert "id" not in frame.columns


def test_arnold_full_and_author_code_selection_are_distinct():
    formal, code_filtered, traits, flow = load_arnold_code(ROOT / "Autism_Aphantasia_Analyses_code.zip")
    assert formal["diagnosis_group"].value_counts().to_dict() == {0: 327, 1: 327}
    assert len(code_filtered) == 327 + flow["diagnosed_selected_by_code_AQ_threshold"]
    assert flow["diagnosed_selected_by_code_AQ_threshold"] == 242
    assert len(traits) == 327
    assert not {"participant_id", "name", "comment"}.intersection(formal.columns)


def test_p1_and_p3_only_write_aggregate_artifacts():
    p1_frame, _ = load_new_studies(ROOT / "2bdn6-osfstorage-archive.zip")
    p3_formal, p3_code_filtered, p3_traits, _ = load_arnold_code(ROOT / "Autism_Aphantasia_Analyses_code.zip")
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory)
        p1_result = run_p1(p1_frame, target / "P1")
        p3_result = run_p3(p3_formal, p3_traits, target / "P3", p3_code_filtered)
        assert p1_result["status"] == "complete"
        assert p3_result["status"] == "complete"
        assert p3_result["sample_sizes"]["all_self_reported_formal_dx"] == {
            "controls": 327,
            "formally_diagnosed": 327,
        }
        diagnostics_path = next(Path(path) for path in p3_result["artifacts"] if path.endswith("p3_diagnostics.json"))
        repeated = json.loads(diagnostics_path.read_text(encoding="utf-8"))["repeated_modality_model"]
        assert repeated["clusters"] == 654
        assert repeated["joint_autism_by_modality_df"] == 5
        stress = json.loads(diagnostics_path.read_text(encoding="utf-8"))["repeated_modality_stress_tests"]
        assert stress["repeated_modality_clustered_standardized"]["standardized_outcome"] is True
        assert stress["repeated_modality_clustered_nuisance"]["nuisance_age_by_modality_and_sex_by_modality"] is True
        assert stress["repeated_modality_clustered_without_smell"]["joint_autism_by_modality_df"] == 4
        p1_estimates_path = next(Path(path) for path in p1_result["artifacts"] if path.endswith("p1_estimates.csv"))
        p1_estimates = pd.read_csv(p1_estimates_path)
        primary_terms = set(p1_estimates.loc[p1_estimates["model"] == "study_1_treatment_primary", "term"])
        assert {"visual_z", "nonvisual_z", "common_imagery_shift", "visual_minus_nonvisual"}.issubset(primary_terms)
        threshold_terms = set(p1_estimates.loc[p1_estimates["model"] == "study_1_visual_threshold_secondary", "term"])
        assert {"visual_aphantasia", "visual_hyperphantasia"}.issubset(threshold_terms)
        for result in (p1_result, p3_result):
            for artifact in result["artifacts"]:
                text = Path(artifact).read_text(encoding="utf-8")
                assert "ProlificID" not in text
                assert "participant_rows" in text or "project" in text


def test_mawtus_gate_detects_global_not_modality_specific_effectiveness():
    result = audit_mawtus_feasibility(ROOT / "v7krh-osfstorage-archive.zip")
    assert result["rows"] == 2815
    assert result["decision"] == "feasibility_only_no_inferential_model"
    assert "no per-modality effectiveness" in result["outcome_granularity"]
    assert result["modalities"]["auditory"]["therapy_has_explicit_yes_and_no"] is False


def test_logit_hc3_matches_statsmodels_fixture():
    rng = np.random.default_rng(20260914)
    n = 90
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    probability = 1 / (1 + np.exp(-(0.25 + 0.7 * x1 - 0.4 * x2)))
    outcome = rng.binomial(1, probability)
    frame = pd.DataFrame({"y": outcome, "x1": x1, "x2": x2})
    rows, diagnostics = _fit_logit(frame, project="fixture", model="logit", cohort="toy",
                                    outcome="toy", numeric=["x1", "x2"], categorical=[], outcome_name="y")
    ours = {row["term"]: row for row in rows}
    reference = sm.GLM(outcome, sm.add_constant(frame[["x1", "x2"]]), family=sm.families.Binomial()).fit(cov_type="HC3")
    assert diagnostics["covariance"] == "statsmodels-compatible White score sandwich"
    for term, index in (("x1", 1), ("x2", 2)):
        assert ours[term]["coef"] == pytest.approx(float(np.exp(reference.params.iloc[index])), abs=1e-6)
        assert ours[term]["se"] == pytest.approx(float(reference.bse.iloc[index]), abs=1e-4)


def test_clustered_ols_matches_statsmodels_fixture():
    rng = np.random.default_rng(17)
    clusters = np.repeat(np.arange(18), 4)
    x1 = rng.normal(size=len(clusters))
    y = 1.2 + 0.8 * x1 + rng.normal(scale=0.5 + clusters / 50, size=len(clusters))
    frame = pd.DataFrame({"cluster": clusters, "x1": x1, "y": y})
    rows, diagnostics = _fit_ols_cluster(frame, cluster="cluster", project="fixture", model="ols",
                                          cohort="toy", outcome="toy", y_name="y", numeric=["x1"], categorical=[])
    ours = {row["term"]: row for row in rows}
    reference = sm.OLS(y, sm.add_constant(frame[["x1"]])).fit(
        cov_type="cluster", cov_kwds={"groups": clusters, "use_correction": True})
    assert diagnostics["clusters"] == 18
    for term, index in (("intercept", 0), ("x1", 1)):
        assert ours[term]["coef"] == pytest.approx(float(reference.params.iloc[index]), abs=1e-6)
        assert ours[term]["se"] == pytest.approx(float(reference.bse.iloc[index]), abs=1e-4)


def test_hedges_g_matches_known_fixture():
    result = _hedges_g(np.array([2., 3., 4., 5., 6.]), np.array([1., 2., 3., 4., 5.]))
    assert result[0] == pytest.approx(0.5712501579659007, abs=1e-12)
    assert result[1] == pytest.approx(0.6483790723303801, abs=1e-12)
    assert result[2] == pytest.approx(-0.6995494721311349, abs=1e-12)
    assert result[3] == pytest.approx(1.8420497880629365, abs=1e-12)


def test_repeated_modality_wald_matches_statsmodels_fixture():
    rng = np.random.default_rng(1234)
    n = 48
    group = pd.DataFrame({
        "diagnosis_group": np.tile([0, 1], n // 2),
        "age": rng.normal(30, 4, size=n),
        "sex_gender": np.tile(["0", "1", "1", "0", "1", "0"], n // 6),
        "visual": rng.normal(20, 3, size=n),
        "auditory": rng.normal(18, 3, size=n),
        "smell": rng.normal(16, 3, size=n),
    })
    modalities = ["visual", "auditory", "smell"]
    ours_rows, ours_diag = _fit_repeated_modality_model(group, modalities=modalities, model="fixture")
    repeated, outcome_column, nonreference, sex_interactions = _build_repeated_modality_frame(
        group, modalities, standardized=False, nuisance_interactions=False)
    numeric = ["diagnosis_group", "age", *[f"modality_{m}" for m in nonreference],
               *[f"autism_x_{m}" for m in nonreference]]
    columns = [np.ones(len(repeated))]
    for field in numeric:
        columns.append(pd.to_numeric(repeated[field], errors="coerce").to_numpy(dtype=float))
    for level in sorted(repeated["sex_gender"].astype("string").unique())[1:]:
        columns.append(repeated["sex_gender"].astype("string").eq(level).astype(float).to_numpy())
    reference = sm.OLS(repeated[outcome_column].to_numpy(dtype=float), np.column_stack(columns)).fit(
        cov_type="cluster", cov_kwds={"groups": repeated["participant_index"], "use_correction": True})
    interaction_indices = list(range(1 + len(numeric) - len(nonreference), 1 + len(numeric)))
    beta = reference.params[interaction_indices]
    covariance = np.asarray(reference.cov_params())[np.ix_(interaction_indices, interaction_indices)]
    reference_wald = float(beta @ np.linalg.pinv(covariance) @ beta)
    assert ours_diag["joint_autism_by_modality_wald_chi2"] == pytest.approx(reference_wald, abs=1e-6)
    assert len(ours_rows) > 0
