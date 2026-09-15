"""Small, explicit statistical engines for the public-data analyses.

Only NumPy, pandas, and SciPy are required. Outputs are aggregate estimates
and diagnostics; input participant rows are never written to disk.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import chi2, norm, t


ESTIMATE_COLUMNS = ["project", "model", "cohort", "outcome", "term", "coef", "se", "ci_low", "ci_high", "p", "effect_kind", "n"]
Z975 = float(norm.ppf(0.975))
P1_DIRECT_CONTRASTS = {
    "common_imagery_shift": {"visual_z": 1.0, "nonvisual_z": 1.0},
    "visual_minus_nonvisual": {"visual_z": 1.0, "nonvisual_z": -1.0},
}


@dataclass
class AnalysisStop(Exception):
    status: str
    code: str
    message: str
    details: dict[str, Any] | None = None


def _matrix(frame: pd.DataFrame, numeric: list[str], categorical: list[str]) -> tuple[np.ndarray, list[str]]:
    columns = [np.ones(len(frame), dtype=float)]
    names = ["intercept"]
    for field in numeric:
        values = pd.to_numeric(frame[field], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(values).all() or np.std(values) == 0:
            raise AnalysisStop("blocked", "invalid_predictor", f"{field} is missing, non-finite, or constant.")
        columns.append(values)
        names.append(field)
    for field in categorical:
        values = frame[field].astype("string").fillna("").to_numpy()
        levels = sorted(set(values))
        if "" in levels:
            raise AnalysisStop("deferred", "missing_categorical_data", f"{field} has missing values.")
        if len(levels) < 2:
            raise AnalysisStop("blocked", "constant_categorical_predictor", f"{field} has fewer than two levels.")
        for index, level in enumerate(levels[1:], start=1):
            columns.append((values == level).astype(float))
            # Do not put source-coded demographic labels in results.
            names.append(f"{field}_level_{index}")
    design = np.column_stack(columns)
    if np.linalg.matrix_rank(design) != design.shape[1]:
        raise AnalysisStop("blocked", "rank_deficient_design", "Declared predictors do not form a full-rank design.")
    return design, names


def _ols_hc3(y: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    n, p = x.shape
    if n <= p + 2:
        raise AnalysisStop("blocked", "small_model_sample", "Too few complete observations for the declared OLS model.")
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    residual = y - x @ beta
    xtx_inv = np.linalg.inv(x.T @ x)
    leverage = np.einsum("ij,jk,ik->i", x, xtx_inv, x)
    adjusted = residual / np.maximum(1.0 - leverage, 1e-8)
    meat = x.T @ ((adjusted**2)[:, None] * x)
    covariance = xtx_inv @ meat @ xtx_inv
    if not np.isfinite(beta).all() or not np.isfinite(covariance).all():
        raise AnalysisStop("blocked", "nonfinite_estimates", "The OLS model produced non-finite estimates.")
    return beta, covariance, {"n": int(n), "design_rank": int(p), "covariance": "HC3"}


def _logit_hc3(y: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    n, p = x.shape
    if n <= p + 2 or np.unique(y).size != 2:
        raise AnalysisStop("blocked", "invalid_logit_sample", "Logistic regression needs both outcomes and more rows than model parameters.")

    def objective(beta: np.ndarray) -> tuple[float, np.ndarray]:
        eta = x @ beta
        probability = expit(eta)
        value = float(np.logaddexp(0.0, eta).sum() - y @ eta)
        gradient = x.T @ (probability - y)
        return value, gradient

    initial = np.zeros(p, dtype=float)
    initial[0] = math.log(float(y.mean()) / (1.0 - float(y.mean())))
    fit = minimize(objective, initial, jac=True, method="BFGS", options={"gtol": 1e-8, "maxiter": 2000})
    beta = np.asarray(fit.x, dtype=float)
    probability = expit(x @ beta)
    weight = np.maximum(probability * (1.0 - probability), 1e-12)
    information = x.T @ (weight[:, None] * x)
    information_rank = int(np.linalg.matrix_rank(information))
    if information_rank != p or not np.isfinite(beta).all():
        raise AnalysisStop("blocked", "singular_logit", "The logistic model is singular or non-finite.",
                           {"design_columns": int(p), "information_rank": information_rank,
                            "beta_max_abs": float(np.max(np.abs(beta))), "probability_min": float(probability.min()),
                            "probability_max": float(probability.max()), "weight_min": float(weight.min())})
    bread = np.linalg.inv(information)
    # statsmodels' GLM path currently falls back to its White score
    # sandwich when ``cov_type='HC3'`` is requested. Match that independent
    # implementation exactly so the engine has a numerical reference. The
    # Firth fallback below remains model-based because sparse separation makes
    # a conventional robust covariance unstable.
    score = x * (y - probability)[:, None]
    covariance = bread @ (score.T @ score) @ bread
    gradient_norm = float(np.max(np.abs(objective(beta)[1])))
    if (np.max(np.abs(beta)) > 18) or not np.isfinite(covariance).all():
        raise AnalysisStop("blocked", "separation_or_unstable_logit", "The logistic model appears separated or numerically unstable.", {"gradient_max_abs": gradient_norm})
    if not fit.success and gradient_norm > 1e-4:
        raise AnalysisStop("blocked", "logit_not_converged", "The logistic model did not converge.", {"optimizer": str(fit.message), "gradient_max_abs": gradient_norm})
    return beta, covariance, {"n": int(n), "events": int(y.sum()), "non_events": int(n - y.sum()), "covariance": "statsmodels-compatible White score sandwich", "optimizer": str(fit.message), "gradient_max_abs": gradient_norm}


def _logit_firth(y: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Bias-reduced logistic fit for sparse factor levels causing separation."""
    n, p = x.shape
    if n <= p + 2 or np.unique(y).size != 2:
        raise AnalysisStop("blocked", "invalid_firth_sample", "Bias-reduced logistic regression needs both outcomes and adequate rows.")

    def objective(beta: np.ndarray) -> tuple[float, np.ndarray]:
        eta = x @ beta
        probability = expit(eta)
        weight = np.maximum(probability * (1.0 - probability), 1e-12)
        information = x.T @ (weight[:, None] * x)
        sign, logdet = np.linalg.slogdet(information)
        if sign <= 0 or not np.isfinite(logdet):
            return float("inf"), np.full(p, np.nan)
        bread = np.linalg.inv(information)
        leverage = weight * np.einsum("ij,jk,ik->i", x, bread, x)
        nll = float(np.logaddexp(0.0, eta).sum() - y @ eta)
        gradient = x.T @ (probability - y) - 0.5 * x.T @ (leverage * (1.0 - 2.0 * probability))
        return nll - 0.5 * float(logdet), gradient

    initial = np.zeros(p, dtype=float)
    initial[0] = math.log(float(y.mean()) / (1.0 - float(y.mean())))
    fit = minimize(objective, initial, jac=True, method="BFGS", options={"gtol": 1e-8, "maxiter": 3000})
    beta = np.asarray(fit.x, dtype=float)
    probability = expit(x @ beta)
    weight = np.maximum(probability * (1.0 - probability), 1e-12)
    information = x.T @ (weight[:, None] * x)
    if np.linalg.matrix_rank(information) != p or not np.isfinite(beta).all() or np.max(np.abs(beta)) > 25:
        raise AnalysisStop("blocked", "firth_not_estimable", "Bias-reduced logistic regression remains numerically unstable.")
    covariance = np.linalg.inv(information)
    gradient_norm = float(np.max(np.abs(objective(beta)[1])))
    if not fit.success and gradient_norm > 1e-4:
        raise AnalysisStop("blocked", "firth_not_converged", "Bias-reduced logistic regression did not converge.", {"gradient_max_abs": gradient_norm})
    return beta, covariance, {"n": int(n), "events": int(y.sum()), "non_events": int(n-y.sum()),
                             "covariance": "model-based expected information", "method": "Firth bias-reduced logistic",
                             "optimizer": str(fit.message), "gradient_max_abs": gradient_norm}


def _rows(beta: np.ndarray, covariance: np.ndarray, names: list[str], *, project: str, model: str,
          cohort: str, outcome: str, effect_kind: str, n: int, odds_ratio: bool = False,
          p_df: int | None = None) -> list[dict[str, Any]]:
    rows = []
    for index, name in enumerate(names):
        estimate = float(beta[index])
        se = math.sqrt(max(0.0, float(covariance[index, index])))
        statistic = estimate / se if se > 0 else math.nan
        p_value = float(2 * (norm.sf(abs(statistic)) if p_df is None else t.sf(abs(statistic), p_df))) if math.isfinite(statistic) else math.nan
        critical = Z975 if p_df is None else float(t.ppf(0.975, p_df))
        low, high = estimate - critical * se, estimate + critical * se
        if odds_ratio:
            coef, ci_low, ci_high = math.exp(estimate), math.exp(low), math.exp(high)
        else:
            coef, ci_low, ci_high = estimate, low, high
        rows.append({"project": project, "model": model, "cohort": cohort, "outcome": outcome,
                     "term": name, "coef": coef, "se": se, "ci_low": ci_low, "ci_high": ci_high,
                     "p": p_value, "effect_kind": effect_kind, "n": int(n)})
    return rows


def _contrast_rows(beta: np.ndarray, covariance: np.ndarray, names: list[str], contrasts: dict[str, dict[str, float]], *,
                   project: str, model: str, cohort: str, outcome: str, effect_kind: str, n: int) -> list[dict[str, Any]]:
    """Return exponentiated linear contrasts from one fitted logistic model."""
    index = {name: position for position, name in enumerate(names)}
    rows: list[dict[str, Any]] = []
    for label, weights in contrasts.items():
        vector = np.zeros(len(names), dtype=float)
        for term, weight in weights.items():
            if term not in index:
                raise AnalysisStop("blocked", "unknown_contrast_term", f"Contrast {label} references absent term {term}.")
            vector[index[term]] = float(weight)
        estimate = float(vector @ beta)
        variance = float(vector @ covariance @ vector)
        se = math.sqrt(max(0.0, variance))
        statistic = estimate / se if se > 0 else math.nan
        p_value = float(2 * norm.sf(abs(statistic))) if math.isfinite(statistic) else math.nan
        low = estimate - Z975 * se
        high = estimate + Z975 * se
        rows.append({"project": project, "model": model, "cohort": cohort, "outcome": outcome,
                     "term": label, "coef": math.exp(estimate), "se": se,
                     "ci_low": math.exp(low), "ci_high": math.exp(high), "p": p_value,
                     "effect_kind": f"odds_ratio_contrast_{effect_kind.removeprefix('odds_ratio_')}", "n": int(n)})
    return rows


def _fit_logit(frame: pd.DataFrame, *, project: str, model: str, cohort: str, outcome: str,
               numeric: list[str], categorical: list[str], outcome_name: str,
               contrasts: dict[str, dict[str, float]] | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    required = [outcome_name, *numeric, *categorical]
    use = frame[required].copy()
    missing = {name: int(use[name].isna().sum() + use[name].astype("string").eq("").sum()) for name in required}
    use = use.replace({"": np.nan}).dropna(subset=required)
    y = pd.to_numeric(use[outcome_name], errors="coerce").to_numpy(dtype=float)
    if not set(np.unique(y)).issubset({0.0, 1.0}):
        raise AnalysisStop("blocked", "invalid_binary_outcome", f"{outcome_name} must be coded 0/1.")
    x, names = _matrix(use, numeric, categorical)
    try:
        beta, covariance, diagnostics = _logit_hc3(y, x)
        effect_kind = "odds_ratio_robust_score"
    except AnalysisStop as stop:
        if stop.code not in {"singular_logit", "separation_or_unstable_logit", "logit_not_converged"}:
            raise
        beta, covariance, diagnostics = _logit_firth(y, x)
        diagnostics["fallback_reason"] = stop.code
        effect_kind = "odds_ratio_Firth_model_based"
    rows = _rows(beta, covariance, names, project=project, model=model, cohort=cohort,
                 outcome=outcome, effect_kind=effect_kind, n=len(use), odds_ratio=True)
    if contrasts:
        rows.extend(_contrast_rows(beta, covariance, names, contrasts, project=project, model=model,
                                   cohort=cohort, outcome=outcome, effect_kind=effect_kind, n=len(use)))
    return rows, {
        **diagnostics, "complete_case_n": int(len(use)), "missing_before_complete_case": missing,
        "outcome_yes": int(y.sum()), "outcome_no": int(len(y) - y.sum()),
        **({"contrasts": contrasts} if contrasts else {}),
    }


def _fit_ols(frame: pd.DataFrame, *, project: str, model: str, cohort: str, outcome: str,
             y_name: str, numeric: list[str], categorical: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    required = [y_name, *numeric, *categorical]
    use = frame[required].copy().replace({"": np.nan}).dropna(subset=required)
    y = pd.to_numeric(use[y_name], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(y).all():
        raise AnalysisStop("deferred", "missing_outcome", f"{y_name} has missing or nonnumeric values.")
    x, names = _matrix(use, numeric, categorical)
    beta, covariance, diagnostics = _ols_hc3(y, x)
    return _rows(beta, covariance, names, project=project, model=model, cohort=cohort,
                 outcome=outcome, effect_kind="mean_difference_HC3", n=len(use), p_df=len(use)-x.shape[1]), diagnostics


def _ols_cluster_state(frame: pd.DataFrame, *, cluster: str, numeric: list[str],
                       categorical: list[str], y_name: str) -> tuple[pd.DataFrame, np.ndarray, list[str], np.ndarray, np.ndarray, dict[str, Any]]:
    """Fit state for a participant-clustered OLS model, retaining covariance in memory."""
    required = [y_name, cluster, *numeric, *categorical]
    use = frame[required].copy().replace({"": np.nan}).dropna(subset=required)
    y = pd.to_numeric(use[y_name], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(y).all():
        raise AnalysisStop("deferred", "missing_outcome", f"{y_name} has missing or nonnumeric values.")
    x, names = _matrix(use, numeric, categorical)
    n, p = x.shape
    if n <= p:
        raise AnalysisStop("blocked", "small_repeated_model", "Repeated-measures model has too few observations for its design.")
    xtx_inv = np.linalg.inv(x.T @ x)
    beta = xtx_inv @ (x.T @ y)
    residual = y - x @ beta
    clusters = use[cluster].to_numpy()
    unique = pd.unique(clusters)
    meat = np.zeros((p, p), dtype=float)
    for value in unique:
        mask = clusters == value
        score = x[mask].T @ residual[mask]
        meat += np.outer(score, score)
    covariance = xtx_inv @ meat @ xtx_inv
    correction = (len(unique) / max(len(unique) - 1, 1)) * ((n - 1) / max(n - p, 1))
    covariance *= correction
    if not np.isfinite(covariance).all():
        raise AnalysisStop("blocked", "invalid_cluster_covariance", "Clustered covariance is non-finite.")
    diagnostics = {"n": int(n), "clusters": int(len(unique)), "covariance": "participant-clustered sandwich (CR1)", "rank": int(np.linalg.matrix_rank(x))}
    return use, x, names, beta, covariance, diagnostics


def _fit_ols_cluster(frame: pd.DataFrame, *, cluster: str, project: str, model: str,
                     cohort: str, outcome: str, y_name: str, numeric: list[str],
                     categorical: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """OLS with a participant-clustered sandwich covariance for repeated measures."""
    use, _x, names, beta, covariance, diagnostics = _ols_cluster_state(
        frame, cluster=cluster, numeric=numeric, categorical=categorical, y_name=y_name)
    return _rows(beta, covariance, names, project=project, model=model, cohort=cohort,
                 outcome=outcome, effect_kind="mean_difference_clustered", n=len(use), p_df=len(use)-len(names)), diagnostics


def run_p1(frame: pd.DataFrame, output_dir: Path) -> dict[str, Any]:
    required = {"study_id", "treatment", "nonvisual_z", "visual_z", "general_z", "visual_aphantasia", "visual_hyperphantasia", "age", "sex_gender"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise AnalysisStop("blocked", "missing_p1_fields", f"Missing P1 fields: {', '.join(missing)}")
    rows: list[dict[str, Any]] = []
    details: dict[str, Any] = {
        "primary_outcome": "source diag field: currently receiving treatment for a neurologic or psychiatric condition (No/Yes)",
        "questionnaire_verification": {
            "source_archive": "2bdn6-osfstorage-archive.zip",
            "study_1_pdf_page": 4,
            "study_2_pdf_page": 5,
            "question": "Are you currently receiving treatment for a neurologic or psychiatric condition?",
            "response_options": ["No, I am not currently receiving treatment", "Yes, I am currently receiving treatment"],
            "yes_code_in_export": 1,
            "no_code_in_export": 0,
            "diag2": "open follow-up shown only after Yes; excluded",
            "status": "confirmed from archived questionnaires",
        },
        "models": [],
        "coordinate_system_note": "The direct visual + nonvisual model is primary. The general-imagery-only model is a distinct estimand. Linear common-shift and visual-minus-nonvisual contrasts are computed from the same direct model; no separate general-plus-deviation regression is treated as robustness evidence.",
    }
    for study in (1, 2):
        cohort = frame.loc[pd.to_numeric(frame["study_id"], errors="coerce") == study].copy()
        if cohort.empty:
            raise AnalysisStop("blocked", "missing_study", f"Study {study} has no rows.")
        estimated, diagnostics = _fit_logit(cohort, project="P1", model=f"study_{study}_treatment_primary",
                                            cohort=f"study_{study}", outcome="current_treatment",
                                            numeric=["visual_z", "nonvisual_z", "age"],
                                            categorical=["sex_gender"], outcome_name="treatment",
                                            contrasts=P1_DIRECT_CONTRASTS)
        rows.extend(estimated)
        details["models"].append({"name": f"study_{study}_treatment_primary", "estimand": "visual and nonvisual conditional associations", **diagnostics})

        general, general_diag = _fit_logit(cohort, project="P1", model=f"study_{study}_general_imagery_secondary",
                                           cohort=f"study_{study}", outcome="current_treatment",
                                           numeric=["general_z", "age"], categorical=["sex_gender"], outcome_name="treatment")
        rows.extend(general)
        details["models"].append({"name": f"study_{study}_general_imagery_secondary", "estimand": "all-modality mean composite", **general_diag})

        # Exploratory shape check: the New source script defines visual
        # aphantasia as image == 5 and hyperphantasia as image >= 35. The
        # middle of the observed visual distribution is the reference group.
        threshold, threshold_diag = _fit_logit(
            cohort, project="P1", model=f"study_{study}_visual_threshold_secondary",
            cohort=f"study_{study}", outcome="current_treatment",
            numeric=["visual_aphantasia", "visual_hyperphantasia", "nonvisual_z", "age"],
            categorical=["sex_gender"], outcome_name="treatment")
        rows.extend(threshold)
        details["models"].append({
            "name": f"study_{study}_visual_threshold_secondary",
            "estimand": "source-defined visual extremes versus middle, conditional on nonvisual imagery",
            "source_cutpoints": {"visual_aphantasia": "image == 5", "visual_hyperphantasia": "image >= 35"},
            **threshold_diag,
        })

        # Source-paper eligibility was 18–30; the primary retains the exact
        # published QC sample and this sensitivity enforces the recorded age
        # band, excluding missing ages as well as out-of-band ages.
        eligible_age = pd.to_numeric(cohort["age"], errors="coerce").between(18, 30)
        age_subset = cohort.loc[eligible_age].copy()
        age_rows, age_diag = _fit_logit(age_subset, project="P1", model=f"study_{study}_age_18_30_sensitivity",
                                        cohort=f"study_{study}_age_18_30", outcome="current_treatment",
                                        numeric=["visual_z", "nonvisual_z", "age"],
                                        categorical=["sex_gender"], outcome_name="treatment",
                                        contrasts=P1_DIRECT_CONTRASTS)
        rows.extend(age_rows)
        details["models"].append({"name": f"study_{study}_age_18_30_sensitivity", **age_diag})

        if "ndd" in cohort and cohort["ndd"].notna().any() and study == 2:
            ndd, ndd_diag = _fit_logit(cohort, project="P1", model="study_2_ndd_secondary",
                                       cohort="study_2", outcome="diagnosed_or_suspected_NDD",
                                       numeric=["visual_z", "nonvisual_z", "age"],
                                       categorical=["sex_gender"], outcome_name="ndd",
                                       contrasts=P1_DIRECT_CONTRASTS)
            rows.extend(ndd)
            details["models"].append({"name": "study_2_ndd_secondary", **ndd_diag,
                                       "interpretation": "broad self-reported diagnosed-or-strongly-suspected NDD; not autism-specific"})

    # Joint model is valid because the questionnaire uses the same treatment
    # item and response choices in both studies. Study 1 is the reference; the
    # interaction terms test whether conditional visual/nonvisual coefficients
    # differ in Study 2. Separate study models above remain the primary display.
    pooled = frame.copy()
    pooled["study_2_indicator"] = (pd.to_numeric(pooled["study_id"], errors="coerce") == 2).astype(float)
    pooled["visual_x_study_2"] = pooled["visual_z"] * pooled["study_2_indicator"]
    pooled["nonvisual_x_study_2"] = pooled["nonvisual_z"] * pooled["study_2_indicator"]
    pooled_rows, pooled_diag = _fit_logit(pooled, project="P1", model="pooled_treatment_study_interactions",
                                          cohort="studies_1_and_2", outcome="current_treatment",
                                          numeric=["visual_z", "nonvisual_z", "study_2_indicator", "visual_x_study_2", "nonvisual_x_study_2", "age"],
                                          categorical=["sex_gender"], outcome_name="treatment",
                                          contrasts={
                                              "common_imagery_shift_study_1": {"visual_z": 1.0, "nonvisual_z": 1.0},
                                              "visual_minus_nonvisual_study_1": {"visual_z": 1.0, "nonvisual_z": -1.0},
                                              "common_imagery_shift_study_2": {"visual_z": 1.0, "nonvisual_z": 1.0, "visual_x_study_2": 1.0, "nonvisual_x_study_2": 1.0},
                                              "visual_minus_nonvisual_study_2": {"visual_z": 1.0, "nonvisual_z": -1.0, "visual_x_study_2": 1.0, "nonvisual_x_study_2": -1.0},
                                          })
    rows.extend(pooled_rows)
    details["models"].append({"name": "pooled_treatment_study_interactions", "estimand": "Study 1 reference effects plus Study 2 study-by-imagery interactions", **pooled_diag})
    estimates = pd.DataFrame(rows, columns=ESTIMATE_COLUMNS)
    diagnostics = {"project": "P1", "status": "complete", "contains_participant_rows": False,
                   "sample_sizes": {f"study_{study}": int((pd.to_numeric(frame["study_id"], errors="coerce") == study).sum()) for study in (1, 2)},
                   "details": details, "estimate_rows": int(len(estimates))}
    return _write("P1", estimates, diagnostics, output_dir)


def _hedges_g(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float, float, float]:
    n1, n0 = len(a), len(b)
    if min(n1, n0) < 2:
        raise AnalysisStop("blocked", "small_group", "Hedges g requires at least two observations per group.")
    df = n1 + n0 - 2
    pooled = math.sqrt(((n1 - 1) * float(np.var(a, ddof=1)) + (n0 - 1) * float(np.var(b, ddof=1))) / df)
    if pooled <= 0:
        raise AnalysisStop("blocked", "zero_pooled_variance", "A modality has zero pooled variance.")
    d = (float(np.mean(a)) - float(np.mean(b))) / pooled
    correction = 1.0 - 3.0 / (4.0 * df - 1.0)
    g = correction * d
    se = math.sqrt((n1 + n0) / (n1 * n0) + g * g / (2.0 * df))
    return g, se, g - Z975 * se, g + Z975 * se, float(2 * norm.sf(abs(g / se)))


def _build_repeated_modality_frame(group_frame: pd.DataFrame, modalities: list[str], *, standardized: bool,
                                   nuisance_interactions: bool) -> tuple[pd.DataFrame, str, list[str], list[str]]:
    """Build a long repeated-outcome frame and prespecified interaction columns."""
    base = group_frame.reset_index(drop=True)
    long_rows: list[dict[str, Any]] = []
    for participant_index, (_, person) in enumerate(base.iterrows()):
        for modality in modalities:
            long_rows.append({
                "participant_index": participant_index,
                "diagnosis_group": person["diagnosis_group"],
                "age": person["age"],
                "sex_gender": person["sex_gender"],
                "modality": modality,
                "score": person[modality],
            })
    repeated = pd.DataFrame(long_rows)
    outcome_column = "score"
    if standardized:
        repeated["score_standardized"] = np.nan
        for modality in modalities:
            values = pd.to_numeric(base[modality], errors="coerce")
            mean = float(values.mean())
            sd = float(values.std(ddof=0))
            if not np.isfinite(sd) or sd <= 0:
                raise AnalysisStop("blocked", "invalid_modality_standardization", f"{modality} has invalid variance.")
            mask = repeated["modality"].eq(modality)
            repeated.loc[mask, "score_standardized"] = (pd.to_numeric(repeated.loc[mask, "score"], errors="coerce") - mean) / sd
        outcome_column = "score_standardized"

    reference = modalities[0]
    nonreference = [modality for modality in modalities if modality != reference]
    for modality in nonreference:
        indicator = repeated["modality"].eq(modality).astype(float)
        repeated[f"modality_{modality}"] = indicator
        repeated[f"autism_x_{modality}"] = pd.to_numeric(repeated["diagnosis_group"], errors="coerce") * indicator
        if nuisance_interactions:
            repeated[f"age_x_{modality}"] = pd.to_numeric(repeated["age"], errors="coerce") * indicator

    sex_levels = sorted(base["sex_gender"].astype("string").dropna().unique())
    sex_interaction_terms: list[str] = []
    if nuisance_interactions:
        for modality in nonreference:
            indicator = repeated["modality"].eq(modality).astype(float)
            for level_index, level in enumerate(sex_levels[1:], start=1):
                term = f"sex_level_{level_index}_x_{modality}"
                repeated[term] = repeated["sex_gender"].astype("string").eq(level).astype(float) * indicator
                sex_interaction_terms.append(term)
    return repeated, outcome_column, nonreference, sex_interaction_terms


def _fit_repeated_modality_model(group_frame: pd.DataFrame, *, modalities: list[str], model: str,
                                 standardized: bool = False, nuisance_interactions: bool = False) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    repeated, outcome_column, nonreference, sex_interaction_terms = _build_repeated_modality_frame(
        group_frame, modalities, standardized=standardized, nuisance_interactions=nuisance_interactions)
    modality_terms = [f"modality_{modality}" for modality in nonreference]
    autism_terms = [f"autism_x_{modality}" for modality in nonreference]
    age_terms = [f"age_x_{modality}" for modality in nonreference] if nuisance_interactions else []
    numeric = ["diagnosis_group", "age", *modality_terms, *autism_terms, *age_terms, *sex_interaction_terms]
    use, _x, names, beta, covariance, diagnostics = _ols_cluster_state(
        repeated, cluster="participant_index", numeric=numeric, categorical=["sex_gender"], y_name=outcome_column)
    rows = _rows(beta, covariance, names, project="P3", model=model,
                 cohort="arnold_2026_all_self_reported_formal_dx", outcome=outcome_column,
                 effect_kind="mean_difference_clustered", n=len(use), p_df=len(use)-len(names))
    interaction_indices = [names.index(term) for term in autism_terms]
    interaction_beta = beta[interaction_indices]
    interaction_covariance = covariance[np.ix_(interaction_indices, interaction_indices)]
    joint_stat = float(interaction_beta @ np.linalg.pinv(interaction_covariance) @ interaction_beta)
    diagnostics.update({
        "reference_modality": modalities[0],
        "modalities": modalities,
        "interaction_terms": autism_terms,
        "joint_autism_by_modality_wald_chi2": joint_stat,
        "joint_autism_by_modality_df": len(autism_terms),
        "joint_autism_by_modality_p": float(chi2.sf(joint_stat, len(autism_terms))),
        "standardized_outcome": standardized,
        "nuisance_age_by_modality_and_sex_by_modality": nuisance_interactions,
        "interpretation": "omnibus test of whether autism-group differences vary by modality; participant-clustered covariance",
    })
    return rows, diagnostics


def run_p3(group_frame: pd.DataFrame, trait_frame: pd.DataFrame, output_dir: Path,
           author_code_frame: pd.DataFrame | None = None) -> dict[str, Any]:
    required = {"diagnosis_group", "age", "sex_gender", "visual", "auditory", "smell", "taste", "touch", "movement"}
    missing = sorted(required - set(group_frame.columns))
    if missing:
        raise AnalysisStop("blocked", "missing_p3_fields", f"Missing P3 case-control fields: {', '.join(missing)}")
    rows: list[dict[str, Any]] = []
    modality_details: list[dict[str, Any]] = []
    analysis_sets = [("all_self_reported_formal_dx", group_frame)]
    if author_code_frame is not None:
        analysis_sets.append(("author_code_AQ_ge_26_sensitivity", author_code_frame))
    for set_name, set_frame in analysis_sets:
        for modality in ("visual", "auditory", "smell", "taste", "touch", "movement"):
            use = set_frame[["diagnosis_group", "age", "sex_gender", modality]].dropna().copy()
            control = use.loc[use["diagnosis_group"] == 0, modality].to_numpy(dtype=float)
            diagnosed = use.loc[use["diagnosis_group"] == 1, modality].to_numpy(dtype=float)
            g, se, low, high, p = _hedges_g(diagnosed, control)
            model = f"{set_name}_hedges_g"
            cohort_name = f"arnold_2026_{set_name}"
            rows.append({"project": "P3", "model": model, "cohort": cohort_name,
                         "outcome": f"{modality}_score", "term": "formal_autism_group", "coef": g, "se": se,
                         "ci_low": low, "ci_high": high, "p": p, "effect_kind": "hedges_g_unadjusted", "n": len(use)})
            adjusted, adj_diag = _fit_ols(use, project="P3", model=f"{set_name}_adjusted_{modality}", cohort=cohort_name,
                                          outcome=f"{modality}_score", y_name=modality,
                                          numeric=["diagnosis_group", "age"], categorical=["sex_gender"])
            group_row = next(item for item in adjusted if item["term"] == "diagnosis_group")
            modality_details.append({"analysis_set": set_name, "modality": modality,
                                     "control_n": int(len(control)), "autism_n": int(len(diagnosed)),
                                     "g": g, "g_ci95": [low, high], "adjusted_mean_difference": group_row["coef"],
                                     "adjusted_ci95": [group_row["ci_low"], group_row["ci_high"]], "adjusted_model_n": adj_diag["n"],
                                     "strict_zero_control": int(np.sum(control == 0)), "strict_zero_autism": int(np.sum(diagnosed == 0)),
                                     "low_imagery_le_10_control": int(np.sum(control <= 10)), "low_imagery_le_10_autism": int(np.sum(diagnosed <= 10))})
            rows.extend(adjusted)

    # The six modality scores are repeated outcomes from the same people, so
    # their effects cannot be treated as six independent tests. The primary
    # long-format model and three prespecified stress variants use the same
    # participant-clustered covariance and joint autism-by-modality Wald test.
    all_modalities = ["visual", "auditory", "smell", "taste", "touch", "movement"]
    repeated_specs = [
        ("repeated_modality_clustered", all_modalities, False, False),
        ("repeated_modality_clustered_standardized", all_modalities, True, False),
        ("repeated_modality_clustered_nuisance", all_modalities, False, True),
        ("repeated_modality_clustered_without_smell", ["visual", "auditory", "taste", "touch", "movement"], False, False),
    ]
    repeated_diagnostics: dict[str, dict[str, Any]] = {}
    for model_name, modalities, standardized, nuisance in repeated_specs:
        repeated_rows, repeated_diag = _fit_repeated_modality_model(
            group_frame, modalities=modalities, model=model_name,
            standardized=standardized, nuisance_interactions=nuisance)
        rows.extend(repeated_rows)
        repeated_diagnostics[model_name] = repeated_diag

    trait_required = {"age", "sex_gender", "AQ_total", "AQ_nonimagination", *required - {"diagnosis_group", "age", "sex_gender"}}
    trait_missing = sorted(trait_required - set(trait_frame.columns))
    trait_families: dict[str, list[dict[str, Any]]] = {}
    if not trait_missing:
        for trait in ("AQ_total", "AQ_nonimagination"):
            family_rows = []
            for modality in ("visual", "auditory", "smell", "taste", "touch", "movement"):
                estimated, model_diag = _fit_ols(trait_frame, project="P3", model=f"arnold_{trait}_{modality}",
                                                  cohort="autistic_only_arnold_2026", outcome=f"{modality}_score",
                                                  y_name=modality, numeric=[trait, "age"], categorical=["sex_gender"])
                rows.extend(estimated)
                slope = next(item for item in estimated if item["term"] == trait)
                family_rows.append({"trait": trait, "modality": modality, "p": slope["p"], "estimate": slope["coef"],
                                    "ci95": [slope["ci_low"], slope["ci_high"]], "n": model_diag["n"]})
            # Holm correction is applied within each six-modality trait family.
            order = np.argsort([item["p"] for item in family_rows])
            adjusted_p = np.ones(len(family_rows), dtype=float)
            running = 0.0
            for rank, index in enumerate(order):
                value = min(1.0, (len(order) - rank) * family_rows[index]["p"])
                running = max(running, value)
                adjusted_p[index] = running
            for index, item in enumerate(family_rows):
                item["p_holm"] = float(adjusted_p[index])
            trait_families[trait] = family_rows
    estimates = pd.DataFrame(rows, columns=ESTIMATE_COLUMNS)
    diagnostics = {"project": "P3", "status": "complete", "contains_participant_rows": False,
                   "sample_sizes": {
                       "all_self_reported_formal_dx": {
                           "controls": int((group_frame["diagnosis_group"] == 0).sum()),
                           "formally_diagnosed": int((group_frame["diagnosis_group"] == 1).sum()),
                       },
                       **({"author_code_AQ_ge_26_sensitivity": {
                           "controls": int((author_code_frame["diagnosis_group"] == 0).sum()),
                           "formally_diagnosed": int((author_code_frame["diagnosis_group"] == 1).sum()),
                       }} if author_code_frame is not None else {}),
                   },
                   "formal_diagnosis_cohort": "Arnold 2026, code-embedded self-reported formally diagnosed participants and prior comparison sample",
                   "modalities": modality_details, "trait_family_results": trait_families,
                   "repeated_modality_model": repeated_diagnostics["repeated_modality_clustered"],
                   "repeated_modality_stress_tests": repeated_diagnostics,
                   "trait_frame_missing_columns": trait_missing,
                   "author_code_sensitivity": "The author's MATLAB code filters the 327 diagnosed respondents to AQ >= 26 (N=242); estimates are reported separately from all 327 diagnosed respondents.",
                   "pooling": "No pooled autism meta-analysis: one formal-diagnosis cohort was processed; New et al. NDD is broad and remains separate.",
                   "interpretive_limit": "AQ and CATI are present only in the diagnosed sample; this is not a within-study trait-vs-control comparison.",
                   "estimate_rows": int(len(estimates))}
    return _write("P3", estimates, diagnostics, output_dir)


def _write(project: str, estimates: pd.DataFrame, diagnostics: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    estimates_path = output_dir / f"{project.lower()}_estimates.csv"
    diagnostics_path = output_dir / f"{project.lower()}_diagnostics.json"
    estimates.to_csv(estimates_path, index=False)
    diagnostics_path.write_text(json.dumps(diagnostics, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return {"project": project, "status": diagnostics.get("status", "complete"),
            "sample_sizes": diagnostics.get("sample_sizes", {}), "artifacts": [str(estimates_path), str(diagnostics_path)]}


def run_model(project: str, frame: pd.DataFrame, output_dir: Path, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Stable single-frame entry point retained for the project CLI."""
    normalized = project.upper()
    if normalized == "P1":
        return run_p1(frame, output_dir)
    if normalized == "P2":
        raise AnalysisStop("blocked", "awaiting_nzavs_access", "P2 requires NZAVS permission and the approved linked extract.")
    if normalized == "P3":
        if not {"diagnosis_group"}.issubset(frame.columns):
            raise AnalysisStop("blocked", "missing_p3_case_control", "P3 requires a harmonized formal-diagnosis case-control frame.")
        return run_p3(frame, pd.DataFrame(), output_dir)
    if normalized == "P4":
        raise AnalysisStop("deferred", "feasibility_only", "P4 is an audit-only candidate; no inferential model is authorized by its data-linkage design.")
    raise ValueError("project must be P1, P2, P3, or P4")
