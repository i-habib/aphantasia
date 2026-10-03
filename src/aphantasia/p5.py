"""P5: preregistered test of Arnold et al. (2026) in New et al. Study 2.

The plan is ``projects/P5_asd_adhd_replication/protocol/preregistration.md``.
``run_p5`` refuses to touch the confirmatory contrasts until that plan has been
frozen (its SHA-256 recorded next to it) and a public registration URL is
supplied. ``plan_p5`` is the only P5 entry point that may run before
registration: it uses Arnold's already-published arrays and New's group
counts, never a New group-by-imagery comparison.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2, fisher_exact, norm, t
from scipy.stats.contingency import odds_ratio

from .models import ESTIMATE_COLUMNS, AnalysisStop, _fit_logit, _hedges_g, _matrix, _ols_cluster_state, _ols_hc3, _rows, _write


PRIMARY_MODALITIES = ["visual", "auditory", "smell", "taste", "touch", "movement"]
EXPLORATORY_MODALITIES = ["emotion", "voice", "interoception"]
CHEMOSENSORY = ["smell", "taste"]
NEW_FLOOR_SCORE = 5  # New source script: modality score == 5 is absent imagery.
ARNOLD_FLOOR_SCORE = 0  # Strict-absence endpoint of the Arnold arrays; descriptive only.
ALPHA_ONE_SIDED = 0.05
SMALL_TELESCOPE_POWER = 1 / 3
PRIMARY_SEQUENCE = ["H1_general_imagery_shift", "H2a_smell_absence", "H2b_taste_absence"]
PLAN_PATH = Path("projects/P5_asd_adhd_replication/protocol/preregistration.md")
FREEZE_PATH = PLAN_PATH.with_name("preregistration.sha256")
SUPPRESS_BELOW = 5
MIN_ABSENT_EVENTS_FOR_LOGIT = 10


@dataclass(frozen=True)
class Registration:
    url: str
    plan_sha256: str


def plan_digest(root: Path, plan_path: Path = PLAN_PATH) -> str:
    return hashlib.sha256((root / plan_path).read_bytes()).hexdigest()


def verify_registration(root: Path, url: str | None, plan_path: Path = PLAN_PATH) -> Registration:
    """Fail closed unless the frozen plan is unchanged and a registration URL exists.

    ``plan_path`` selects the project's plan (P5 by default); its freeze file
    is ``preregistration.sha256`` in the same folder.
    """
    freeze_path = plan_path.with_name("preregistration.sha256")
    if not url or not url.startswith("https://"):
        raise AnalysisStop("blocked", "awaiting_preregistration",
                           "This analysis runs only after its plan is registered; pass --preregistration-url with the public https:// registration link.")
    frozen = root / freeze_path
    if not frozen.exists():
        raise AnalysisStop("blocked", "plan_not_frozen",
                           f"No {freeze_path.name}; run scripts/freeze_preregistration.py on the exact text you registered.")
    recorded = frozen.read_text(encoding="utf-8").split()[0]
    current = plan_digest(root, plan_path)
    if current != recorded:
        raise AnalysisStop("blocked", "plan_changed_after_freeze",
                           "preregistration.md no longer matches its frozen SHA-256; record any change as a deviation instead of editing the plan.",
                           {"frozen": recorded, "current": current})
    return Registration(url=url, plan_sha256=current)


def _suppressed(count: int) -> int | str:
    return int(count) if count >= SUPPRESS_BELOW else f"<{SUPPRESS_BELOW}"


def standardize_to_reference(frame: pd.DataFrame, reference: pd.Series, modalities: list[str]) -> pd.DataFrame:
    """Express each modality in reference-group SD units and build the general composite.

    The general composite is the mean of the six shared-modality z scores,
    re-standardized so the reference group has mean 0 and SD 1; a group
    coefficient on it is therefore in reference-SD units in both studies.
    """
    out = frame.copy()
    for modality in modalities:
        values = pd.to_numeric(out[modality], errors="coerce")
        base = values[reference]
        mean, sd = float(base.mean()), float(base.std(ddof=1))
        if not math.isfinite(sd) or sd <= 0:
            raise AnalysisStop("blocked", "invalid_reference_variance", f"{modality} has invalid reference-group variance.")
        out[f"z_{modality}"] = (values - mean) / sd
    component = out[[f"z_{name}" for name in PRIMARY_MODALITIES]].mean(axis=1, skipna=False)
    base = component[reference]
    out["general_z"] = (component - float(base.mean())) / float(base.std(ddof=1))
    out["general_raw"] = out[PRIMARY_MODALITIES].apply(pd.to_numeric, errors="coerce").mean(axis=1, skipna=False)
    return out


def _linear_contrast(beta: np.ndarray, covariance: np.ndarray, names: list[str], weights: dict[str, float]) -> tuple[float, float]:
    vector = np.zeros(len(names))
    for term, weight in weights.items():
        vector[names.index(term)] = weight
    return float(vector @ beta), math.sqrt(max(0.0, float(vector @ covariance @ vector)))


def _contrast_row(estimate: float, se: float, *, model: str, cohort: str, outcome: str, term: str,
                  n: int, effect_kind: str, df: int | None = None) -> dict[str, Any]:
    critical = norm.ppf(0.975) if df is None else t.ppf(0.975, df)
    statistic = estimate / se if se > 0 else math.nan
    p = float(2 * (norm.sf(abs(statistic)) if df is None else t.sf(abs(statistic), df))) if math.isfinite(statistic) else math.nan
    return {"project": "P5", "model": model, "cohort": cohort, "outcome": outcome, "term": term,
            "coef": estimate, "se": se, "ci_low": estimate - critical * se, "ci_high": estimate + critical * se,
            "p": p, "effect_kind": effect_kind, "n": int(n)}


def _one_sided(estimate: float, se: float, *, predicted: str, df: int | None = None) -> float:
    statistic = estimate / se
    tail = norm if df is None else t(df)
    return float(tail.cdf(statistic) if predicted == "negative" else tail.sf(statistic))


def _shift_model(frame: pd.DataFrame, indicators: list[str], *, outcome: str, model: str, cohort: str,
                 adjusted: bool = True) -> tuple[list[dict[str, Any]], dict[str, Any], np.ndarray, np.ndarray, list[str]]:
    """HC3 OLS of an imagery outcome on group indicators (+ age and recorded sex/gender)."""
    numeric = [*indicators, *(["age"] if adjusted else [])]
    categorical = ["sex_gender"] if adjusted else []
    use = frame[[outcome, *numeric, *categorical]].replace({"": np.nan}).dropna()
    x, names = _matrix(use, numeric, categorical)
    y = pd.to_numeric(use[outcome], errors="coerce").to_numpy(dtype=float)
    beta, covariance, diagnostics = _ols_hc3(y, x)
    rows = _rows(beta, covariance, names, project="P5", model=model, cohort=cohort, outcome=outcome,
                 effect_kind="mean_difference_HC3", n=len(use), p_df=len(use) - x.shape[1])
    diagnostics["df_resid"] = int(len(use) - x.shape[1])
    return rows, diagnostics, beta, covariance, names


def _floor_model(frame: pd.DataFrame, indicator: str, modality: str, floor: float, *, model: str,
                 cohort: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Adjusted absence odds ratio; exact unadjusted fallback when events are sparse (plan §6.1)."""
    use = frame.copy()
    use[f"absent_{modality}"] = (pd.to_numeric(use[modality], errors="coerce") == floor).astype(float)
    use.loc[use[modality].isna(), f"absent_{modality}"] = np.nan
    events = int(use[f"absent_{modality}"].sum())
    if events >= MIN_ABSENT_EVENTS_FOR_LOGIT:
        rows, diagnostics = _fit_logit(use, project="P5", model=model, cohort=cohort, outcome=f"absent_{modality}",
                                       numeric=[indicator, "age"], categorical=["sex_gender"], outcome_name=f"absent_{modality}")
    else:
        rows, diagnostics = _exact_odds_ratio(use, indicator, f"absent_{modality}", model=model, cohort=cohort)
    by_group = use.groupby(indicator)[f"absent_{modality}"].agg(["sum", "count"])
    diagnostics["absent_counts"] = {f"{indicator}={int(level)}": {"absent": _suppressed(int(values["sum"])), "n": int(values["count"])}
                                    for level, values in by_group.iterrows()}
    return rows, diagnostics


def _exact_odds_ratio(use: pd.DataFrame, indicator: str, outcome: str, *, model: str,
                      cohort: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Conditional-MLE odds ratio with exact interval; unadjusted by design."""
    complete = use[[indicator, outcome]].dropna()
    group = complete[indicator].eq(1)
    absent = complete[outcome].eq(1)
    table = np.array([[int((group & absent).sum()), int((group & ~absent).sum())],
                      [int((~group & absent).sum()), int((~group & ~absent).sum())]])
    result = odds_ratio(table, kind="conditional")
    interval = result.confidence_interval(0.95)
    estimate = float(result.statistic)
    log_estimate = math.log(estimate) if 0 < estimate < math.inf else math.nan
    one_sided = float(fisher_exact(table, alternative="greater")[1])
    row = {"project": "P5", "model": model, "cohort": cohort, "outcome": outcome, "term": indicator,
           "coef": estimate, "se": math.nan, "ci_low": float(interval.low), "ci_high": float(interval.high),
           "p": float(fisher_exact(table)[1]), "effect_kind": "odds_ratio_conditional_exact_unadjusted", "n": int(len(complete))}
    return [row], {"method": "conditional exact odds ratio (sparse-event fallback)", "events": int(absent.sum()),
                   "one_sided_p_greater": one_sided, "log_odds_ratio": log_estimate, "n": int(len(complete))}


def _repeated_model(frame: pd.DataFrame, indicator: str, *, model: str, cohort: str,
                    nuisance: bool = False) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Participant-clustered long model on reference-standardized modality scores.

    Visual is the reference modality, so ``group_x_<m>`` is the group gap in m
    minus the group gap in visual imagery. The secondary S1 contrast averages
    the smell and taste interaction terms.
    """
    base = frame.reset_index(drop=True)
    long = base[[indicator, "age", "sex_gender"]].copy()
    long["participant_index"] = np.arange(len(base))
    stacked = []
    for modality in PRIMARY_MODALITIES:
        part = long.copy()
        part["modality"] = modality
        part["score"] = base[f"z_{modality}"]
        stacked.append(part)
    repeated = pd.concat(stacked, ignore_index=True)
    nonreference = PRIMARY_MODALITIES[1:]
    numeric = [indicator, "age"]
    sex_levels = sorted(base["sex_gender"].astype("string").dropna().unique())
    for modality in nonreference:
        mask = repeated["modality"].eq(modality).astype(float)
        repeated[f"modality_{modality}"] = mask
        repeated[f"group_x_{modality}"] = pd.to_numeric(repeated[indicator]) * mask
        numeric += [f"modality_{modality}", f"group_x_{modality}"]
        if nuisance:
            repeated[f"age_x_{modality}"] = pd.to_numeric(repeated["age"], errors="coerce") * mask
            numeric.append(f"age_x_{modality}")
            for index, level in enumerate(sex_levels[1:], start=1):
                term = f"sex_level_{index}_x_{modality}"
                repeated[term] = repeated["sex_gender"].astype("string").eq(level).astype(float) * mask
                numeric.append(term)
    use, _x, names, beta, covariance, diagnostics = _ols_cluster_state(
        repeated, cluster="participant_index", numeric=numeric, categorical=["sex_gender"], y_name="score")
    df = len(use) - len(names)
    rows = _rows(beta, covariance, names, project="P5", model=model, cohort=cohort, outcome="modality_z",
                 effect_kind="mean_difference_clustered", n=len(use), p_df=df)
    terms = [f"group_x_{modality}" for modality in nonreference]
    index = [names.index(term) for term in terms]
    wald = float(beta[index] @ np.linalg.pinv(covariance[np.ix_(index, index)]) @ beta[index])
    estimate, se = _linear_contrast(beta, covariance, names, {f"group_x_{m}": 1 / len(CHEMOSENSORY) for m in CHEMOSENSORY})
    rows.append(_contrast_row(estimate, se, model=model, cohort=cohort, outcome="modality_z",
                              term="chemosensory_minus_visual", n=len(use), effect_kind="contrast_clustered", df=df))
    diagnostics.update({"omnibus_group_by_modality_wald_chi2": wald, "omnibus_df": len(terms),
                        "omnibus_p": float(chi2.sf(wald, len(terms))),
                        "chemosensory_minus_visual": {"estimate": estimate, "se": se,
                                                      "one_sided_p_negative": _one_sided(estimate, se, predicted="negative", df=df)},
                        "nuisance_age_and_sex_by_modality": nuisance})
    return rows, diagnostics


def _pair(frame: pd.DataFrame, group: str, *, reference: str = "reference") -> pd.DataFrame:
    use = frame.loc[frame["group"].isin([group, reference])].copy()
    use["in_group"] = use["group"].eq(group).astype(float)
    return use


def _arnold_prepared(arnold: pd.DataFrame) -> pd.DataFrame:
    frame = arnold.copy()
    frame["in_group"] = pd.to_numeric(frame["diagnosis_group"]).astype(float)
    return standardize_to_reference(frame, frame["in_group"].eq(0), PRIMARY_MODALITIES)


def _power(effect: float, se: float, alpha_one_sided: float = ALPHA_ONE_SIDED) -> float:
    return float(norm.sf(norm.isf(alpha_one_sided) - abs(effect) / se))


def plan_p5(arnold: pd.DataFrame, group_counts: dict[str, int], output_dir: Path) -> dict[str, Any]:
    """Pre-registration power plan from Arnold's published arrays and New's group sizes only."""
    prepared = _arnold_prepared(arnold)
    control = prepared["in_group"].eq(0)
    z = prepared[[f"z_{m}" for m in PRIMARY_MODALITIES]].to_numpy(dtype=float)
    covariance = np.cov(z[control.to_numpy()].T)
    weights = {
        "H1_general_imagery_shift": None,
        "S1_chemosensory_minus_visual": np.array([-1, 0, 0.5, 0.5, 0, 0]),
    }
    arnold_effects = {}
    for label, vector in weights.items():
        if vector is None:
            person = prepared["general_z"].to_numpy(dtype=float)
            variance = float(np.var(person[control.to_numpy()], ddof=1))
        else:
            person = z @ vector
            variance = float(vector @ covariance @ vector)
        effect = float(person[~control.to_numpy()].mean() - person[control.to_numpy()].mean())
        arnold_effects[label] = {"effect": effect, "person_variance": variance,
                                 "arnold_se": math.sqrt(variance * (1 / int((~control).sum()) + 1 / int(control.sum())))}
    sizes = {"asd_vs_reference": (group_counts["asd"], group_counts["reference"]),
             "asd_without_adhd_vs_reference": (group_counts["asd_without_adhd"], group_counts["reference"]),
             "adhd_only_vs_reference": (group_counts["adhd_only"], group_counts["reference"])}
    continuous = {}
    for label, values in arnold_effects.items():
        continuous[label] = {"arnold_unadjusted_effect_reference_sd": values["effect"], "arnold_se": values["arnold_se"]}
        for comparison, (n1, n0) in sizes.items():
            se = math.sqrt(values["person_variance"] * (1 / n1 + 1 / n0))
            continuous[label][comparison] = {
                "expected_se": se,
                "power_one_sided_05_at_arnold_effect": _power(values["effect"], se),
                "power_one_sided_05_at_half_arnold_effect": _power(values["effect"] / 2, se),
            }
    d33_se = arnold_effects["H1_general_imagery_shift"]["arnold_se"]
    absence = {}
    for modality in ("visual", *CHEMOSENSORY):
        rates = {}
        for level, name in ((0, "control"), (1, "autistic")):
            values = pd.to_numeric(arnold.loc[arnold["diagnosis_group"] == level, modality])
            rates[name] = float((values == ARNOLD_FLOOR_SCORE).mean())
        n1, n0 = sizes["asd_vs_reference"]
        scenarios = {}
        for odds_ratio in (1.5, 2.0, 3.0):
            p0 = rates["control"]
            p1 = odds_ratio * p0 / (1 - p0 + odds_ratio * p0)
            se = math.sqrt(1 / (n1 * p1) + 1 / (n1 * (1 - p1)) + 1 / (n0 * p0) + 1 / (n0 * (1 - p0)))
            scenarios[f"OR_{odds_ratio}"] = {"expected_asd_events": n1 * p1, "expected_reference_events": n0 * p0,
                                             "power_one_sided_05": _power(math.log(odds_ratio), se)}
        absence[modality] = {"arnold_absent_rate": rates, "new_power_if_reference_rate_equals_arnold_control": scenarios}
    plan = {"project": "P5", "status": "planning_only", "contains_participant_rows": False,
            "uses_new_group_by_imagery_comparisons": False,
            "new_group_counts": group_counts, "continuous": continuous, "absence": absence,
            "small_telescope_d33_reference_sd": d33_se * (norm.ppf(0.975) - norm.ppf(1 - SMALL_TELESCOPE_POWER)),
            "note": "Arnold effects are unadjusted, control-SD standardized, and subject to winner's-curse inflation; power at half the Arnold effect is the conservative planning scenario."}
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "p5_power_plan.json"
    path.write_text(json.dumps(plan, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return {"project": "P5", "status": "planning_only", "artifacts": [str(path)]}


def _small_telescope(new_estimate: float, new_se: float, arnold_se: float) -> dict[str, float | bool]:
    """Simonsohn (2015): is the replication effect smaller than d33 of the original design?"""
    d33 = arnold_se * (norm.ppf(0.975) - norm.ppf(1 - SMALL_TELESCOPE_POWER))
    # Effects are predicted negative, so "smaller than d33" means closer to zero than -d33.
    p = float(norm.sf((new_estimate + d33) / new_se))
    return {"d33_reference_sd": d33, "one_sided_p_new_effect_smaller_than_d33": p, "smaller_than_d33": p < ALPHA_ONE_SIDED}


def run_p5(frame: pd.DataFrame, output_dir: Path, *, registration: Registration,
           arnold: pd.DataFrame | None = None) -> dict[str, Any]:
    """Run every preregistered P5 analysis once and label each by its plan role."""
    if not isinstance(registration, Registration):
        raise AnalysisStop("blocked", "awaiting_preregistration", "run_p5 requires a verified Registration.")
    required = {"group", "asd_with_adhd", "age", "sex_gender", *PRIMARY_MODALITIES, *EXPLORATORY_MODALITIES}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise AnalysisStop("blocked", "missing_p5_fields", f"Missing P5 fields: {', '.join(missing)}")
    cohort = "new_2026_study_2"
    data = standardize_to_reference(frame, frame["group"].eq("reference"), [*PRIMARY_MODALITIES, *EXPLORATORY_MODALITIES])
    rows: list[dict[str, Any]] = []
    details: dict[str, Any] = {}

    # ---- Primary family, fixed-sequence gatekeeping (plan §6.1) ----
    asd = _pair(data, "asd")
    h1_rows, h1_diag, beta, cov, names = _shift_model(asd, ["in_group"], outcome="general_z", model="H1_general_imagery_shift", cohort=cohort)
    rows.extend(h1_rows)
    h1_estimate, h1_se = _linear_contrast(beta, cov, names, {"in_group": 1.0})
    primary = {"H1_general_imagery_shift": {"estimate": h1_estimate, "se": h1_se, "predicted": "negative",
                                            "one_sided_p": _one_sided(h1_estimate, h1_se, predicted="negative", df=h1_diag["df_resid"]),
                                            **h1_diag}}
    for label, modality in (("H2a_smell_absence", "smell"), ("H2b_taste_absence", "taste")):
        floor_rows, floor_diag = _floor_model(asd, "in_group", modality, NEW_FLOOR_SCORE, model=label, cohort=cohort)
        rows.extend(floor_rows)
        group_row = next(row for row in floor_rows if row["term"] == "in_group")
        if "one_sided_p_greater" in floor_diag:
            one_sided = floor_diag["one_sided_p_greater"]
        else:
            one_sided = float(norm.sf(math.log(group_row["coef"]) / group_row["se"]))
        primary[label] = {"odds_ratio": group_row["coef"], "ci95": [group_row["ci_low"], group_row["ci_high"]],
                          "predicted": "odds ratio > 1", "one_sided_p": one_sided, **floor_diag}
    still_open = True
    for label in PRIMARY_SEQUENCE:
        rejected = still_open and primary[label]["one_sided_p"] < ALPHA_ONE_SIDED
        primary[label]["tested_confirmatorily"] = still_open
        primary[label]["confirmatory_support"] = bool(rejected)
        still_open = bool(rejected)
    details["primary"] = primary

    # ---- Secondary family (plan §6.2); Holm across the listed p values ----
    secondary: dict[str, Any] = {}
    s1_rows, s1_diag = _repeated_model(asd, "in_group", model="S1_modality_profile_asd", cohort=cohort)
    rows.extend(s1_rows)
    secondary["S1_modality_profile_asd"] = s1_diag
    three = data.loc[data["group"].isin(["reference", "asd", "adhd_only"])].copy()
    three["asd_indicator"] = three["group"].eq("asd").astype(float)
    three["adhd_only_indicator"] = three["group"].eq("adhd_only").astype(float)
    s2_rows, s2_diag, beta, cov, names = _shift_model(three, ["asd_indicator", "adhd_only_indicator"], outcome="general_z",
                                                      model="S2_specificity_three_group", cohort=cohort)
    rows.extend(s2_rows)
    difference, difference_se = _linear_contrast(beta, cov, names, {"asd_indicator": 1.0, "adhd_only_indicator": -1.0})
    rows.append(_contrast_row(difference, difference_se, model="S2_specificity_three_group", cohort=cohort, outcome="general_z",
                              term="asd_minus_adhd_only", n=s2_diag["n"], effect_kind="contrast_HC3", df=s2_diag["df_resid"]))
    adhd_estimate, adhd_se = _linear_contrast(beta, cov, names, {"adhd_only_indicator": 1.0})
    secondary["S2_specificity_three_group"] = {**s2_diag, "adhd_only_vs_reference": {"estimate": adhd_estimate, "se": adhd_se},
                                               "asd_minus_adhd_only": {"estimate": difference, "se": difference_se}}
    visual_rows, visual_diag = _floor_model(asd, "in_group", "visual", NEW_FLOOR_SCORE, model="S3_visual_absence_asd", cohort=cohort)
    rows.extend(visual_rows)
    secondary["S3_visual_absence_asd"] = visual_diag
    adhd = _pair(data, "adhd_only")
    s4_rows, s4_diag = _repeated_model(adhd, "in_group", model="S4_modality_profile_adhd_only", cohort=cohort)
    rows.extend(s4_rows)
    secondary["S4_modality_profile_adhd_only"] = s4_diag
    secondary_p = {
        "S1_chemosensory_minus_visual": 2 * min(s1_diag["chemosensory_minus_visual"]["one_sided_p_negative"],
                                                1 - s1_diag["chemosensory_minus_visual"]["one_sided_p_negative"]),
        "S1_omnibus": s1_diag["omnibus_p"],
        "S2_asd_minus_adhd_only": next(r["p"] for r in rows if r["model"] == "S2_specificity_three_group" and r["term"] == "asd_minus_adhd_only"),
        "S3_visual_absence": next(r["p"] for r in visual_rows if r["term"] == "in_group"),
        "S4_adhd_chemosensory_minus_visual": 2 * min(s4_diag["chemosensory_minus_visual"]["one_sided_p_negative"],
                                                     1 - s4_diag["chemosensory_minus_visual"]["one_sided_p_negative"]),
    }
    order = sorted(secondary_p, key=secondary_p.get)
    running = 0.0
    holm = {}
    for rank, label in enumerate(order):
        running = max(running, min(1.0, (len(order) - rank) * secondary_p[label]))
        holm[label] = running
    secondary["two_sided_p"] = secondary_p
    secondary["holm_adjusted_p"] = holm
    details["secondary"] = secondary

    # ---- Sensitivity analyses (plan §6.3); never substitute for the primary ----
    sensitivity: dict[str, Any] = {}
    asd_no_adhd = _pair(data.loc[~(data["group"].eq("asd") & data["asd_with_adhd"])], "asd")
    age_band = asd.loc[pd.to_numeric(asd["age"], errors="coerce").between(18, 30)]
    shift_specs = [
        ("SENS_asd_without_adhd", asd_no_adhd, "general_z", True),
        ("SENS_raw_score_composite", asd, "general_raw", True),
        ("SENS_age_18_30", age_band, "general_z", True),
        ("SENS_unadjusted", asd, "general_z", False),
    ]
    for label, subset, outcome, adjusted in shift_specs:
        sens_rows, sens_diag, beta, cov, names = _shift_model(subset, ["in_group"], outcome=outcome, model=label,
                                                              cohort=cohort, adjusted=adjusted)
        rows.extend(sens_rows)
        estimate, se = _linear_contrast(beta, cov, names, {"in_group": 1.0})
        sensitivity[label] = {"estimate": estimate, "se": se, **sens_diag}
    for modality in CHEMOSENSORY:
        label = f"SENS_asd_without_adhd_{modality}_absence"
        sens_rows, sens_diag = _floor_model(asd_no_adhd, "in_group", modality, NEW_FLOOR_SCORE, model=label, cohort=cohort)
        rows.extend(sens_rows)
        sensitivity[label] = sens_diag
    nuisance_rows, nuisance_diag = _repeated_model(asd, "in_group", model="SENS_modality_profile_nuisance", cohort=cohort, nuisance=True)
    rows.extend(nuisance_rows)
    sensitivity["SENS_modality_profile_nuisance"] = nuisance_diag
    details["sensitivity"] = sensitivity

    # ---- Descriptive / exploratory (plan §6.4) ----
    descriptive = []
    for group in ("asd", "adhd_only"):
        pair = _pair(data, group)
        for modality in [*PRIMARY_MODALITIES, *EXPLORATORY_MODALITIES]:
            values = pair[[modality, "in_group"]].dropna()
            g, se, low, high, p = _hedges_g(values.loc[values["in_group"].eq(1), modality].to_numpy(dtype=float),
                                            values.loc[values["in_group"].eq(0), modality].to_numpy(dtype=float))
            role = "descriptive" if modality in PRIMARY_MODALITIES else "exploratory"
            rows.append({"project": "P5", "model": f"{role}_hedges_g_{group}", "cohort": cohort, "outcome": f"{modality}_score",
                         "term": f"{group}_vs_reference", "coef": g, "se": se, "ci_low": low, "ci_high": high, "p": p,
                         "effect_kind": "hedges_g_unadjusted", "n": int(len(values))})
            absent = values[modality].eq(NEW_FLOOR_SCORE)
            descriptive.append({"group": group, "modality": modality, "role": role, "g": g,
                                "absent_group": _suppressed(int(absent[values["in_group"].eq(1)].sum())),
                                "absent_reference": _suppressed(int(absent[values["in_group"].eq(0)].sum()))})
    details["descriptive"] = descriptive

    # ---- Cross-study comparison with Arnold (plan §6.5); no pooled estimate ----
    if arnold is not None:
        prepared = _arnold_prepared(arnold)
        a_rows, a_diag, beta, cov, names = _shift_model(prepared, ["in_group"], outcome="general_z",
                                                        model="XS_arnold_general_imagery_shift", cohort="arnold_2026_all_self_reported_formal_dx")
        rows.extend(a_rows)
        a_estimate, a_se = _linear_contrast(beta, cov, names, {"in_group": 1.0})
        a_profile_rows, a_profile = _repeated_model(prepared, "in_group", model="XS_arnold_modality_profile",
                                                    cohort="arnold_2026_all_self_reported_formal_dx")
        rows.extend(a_profile_rows)
        chem_new, chem_arnold = s1_diag["chemosensory_minus_visual"], a_profile["chemosensory_minus_visual"]
        details["cross_study"] = {
            "general_imagery_shift": {"new": {"estimate": h1_estimate, "se": h1_se}, "arnold": {"estimate": a_estimate, "se": a_se},
                                      "difference_new_minus_arnold": h1_estimate - a_estimate,
                                      "difference_p_two_sided": float(2 * norm.sf(abs(h1_estimate - a_estimate) / math.hypot(h1_se, a_se)))},
            "chemosensory_minus_visual": {"new": chem_new, "arnold": chem_arnold,
                                          "difference_p_two_sided": float(2 * norm.sf(abs(chem_new["estimate"] - chem_arnold["estimate"])
                                                                                      / math.hypot(chem_new["se"], chem_arnold["se"])))},
            "small_telescope_H1": _small_telescope(h1_estimate, h1_se, a_se),
            "pooling": "none; two cohorts with different instruments and recruitment are shown side by side",
        }
        telescope = details["cross_study"]["small_telescope_H1"]
        h1 = primary["H1_general_imagery_shift"]
        details["H1_interpretation"] = ("replicated" if h1["confirmatory_support"]
                                        else "informative_non_replication" if telescope["smaller_than_d33"]
                                        else "inconclusive")

    estimates = pd.DataFrame(rows, columns=ESTIMATE_COLUMNS)
    diagnostics = {"project": "P5", "status": "complete", "contains_participant_rows": False,
                   "registration": {"url": registration.url, "plan_sha256": registration.plan_sha256},
                   "sample_sizes": {name: int(count) for name, count in frame["group"].value_counts().items()},
                   "floor_score": NEW_FLOOR_SCORE, "alpha_one_sided": ALPHA_ONE_SIDED,
                   "primary_sequence": PRIMARY_SEQUENCE, "details": details, "estimate_rows": int(len(estimates))}
    return _write("P5", estimates, _json_safe(diagnostics), output_dir)


def _json_safe(value: Any) -> Any:
    """Replace non-finite floats (e.g. an exact OR of inf with zero events) by None for strict JSON."""
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, np.integer):
        return int(value)
    return value
