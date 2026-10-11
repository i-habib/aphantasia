"""P5 follow-up analyses that were NOT in the registered plan.

Run only after the registered P5 analysis. Every result here is exploratory and
is reported as such. They address the obvious alternative explanations for the
registered H1 result:

E1  answering style: do autistic people use the ends of the scale more (more
    floor AND more ceiling scores), or are they shifted down (more floor, fewer
    ceiling scores)?
E2  careless answering: H1 among people who passed every attention check.
E3  whole-group shift or a subgroup: H1 among people with some imagery in all
    six senses, and group differences at the 10th to 90th percentiles.
E1 and E3 are repeated in Arnold et al.'s data.
E4  the three senses only New et al. measured (emotion, voice, inner body).
E5  H1 adjusted for current treatment and for education.
E6  the one non-imagery 1-7 rating in the survey ("I am an empathetic person").

    python3 scripts/p5_exploratory.py --preregistration-url https://osf.io/87udm

Writes aggregate results only, to runs/latest/P5/p5_exploratory.json. Uses statsmodels
(already a test dependency) for the quantile regressions.
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, norm, t
from statsmodels.regression.quantile_regression import QuantReg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aphantasia.datasets import NEW_MEMBERS, load_arnold_code, load_new_study2_conditions  # noqa: E402
from aphantasia.p5 import (ARNOLD_FLOOR_SCORE, EXPLORATORY_MODALITIES, _arnold_prepared, NEW_FLOOR_SCORE, PRIMARY_MODALITIES, _json_safe,  # noqa: E402
                           _linear_contrast, _shift_model, standardize_to_reference, verify_registration)

NEW_CEILING_SCORE = 35
ARNOLD_CEILING_SCORE = 50
BOOTSTRAP_DRAWS = 5000
CURVE_DRAWS = 2000
EQUIVALENCE_BOUND_SD = 0.2


def _extra_columns(path: Path) -> pd.DataFrame:
    """The survey fields the registered loader leaves out, in the loader's row order."""
    with zipfile.ZipFile(path) as archive, archive.open(NEW_MEMBERS[2]) as stream:
        source = pd.read_csv(stream, sep="\t", dtype="string", keep_default_na=False, encoding="cp1252")
    kept = source.loc[pd.to_numeric(source["nbact"], errors="coerce").ge(3)]
    out = pd.DataFrame({name: pd.to_numeric(kept[name], errors="coerce").to_numpy() for name in ("nbact", "diag", "edu", "empath")})
    return out


def _effect(frame: pd.DataFrame, outcome: str, *, extra_numeric: tuple[str, ...] = (), extra_categorical: tuple[str, ...] = ()) -> dict:
    data = frame.copy()
    if extra_categorical:
        for name in extra_categorical:
            for level in sorted(data[name].dropna().unique())[1:]:
                column = f"{name}_{level}"
                data[column] = data[name].eq(level).astype(float).where(data[name].notna())
                extra_numeric = (*extra_numeric, column)
    _, diag, beta, cov, names = _shift_model(data, ["in_group", *extra_numeric], outcome=outcome, model="E", cohort="new")
    estimate, se = _linear_contrast(beta, cov, names, {"in_group": 1.0})
    df = diag["df_resid"]
    half = t.ppf(0.975, df) * se
    return {"estimate": estimate, "se": se, "ci95": [estimate - half, estimate + half],
            "p_two_sided": float(2 * t.sf(abs(estimate / se), df)), "n": diag["n"]}


def _quantile_regression(pair: pd.DataFrame) -> dict:
    """Autism difference at several percentiles of overall imagery, adjusted for age and sex."""
    use = pair[["general_z", "in_group", "age", "sex_gender"]].dropna().copy()
    sexes = sorted(use["sex_gender"].astype(str).unique())
    columns = {"const": np.ones(len(use)), "in_group": use["in_group"].to_numpy(float), "age": use["age"].to_numpy(float)}
    for level in sexes[1:]:
        columns[f"sex_{level}"] = use["sex_gender"].astype(str).eq(level).to_numpy(float)
    x = pd.DataFrame(columns)
    x = x.loc[:, x.std().gt(0) | (x.columns == "const")]
    out = {}
    for q in (0.10, 0.25, 0.50, 0.75, 0.90):
        fit = QuantReg(use["general_z"].to_numpy(float), x).fit(q=q, max_iter=5000)
        estimate, se = float(fit.params["in_group"]), float(fit.bse["in_group"])
        out[f"q{round(q * 100)}"] = {"estimate": estimate, "se": se, "ci95": [estimate - 1.96 * se, estimate + 1.96 * se],
                                     "p_two_sided": float(2 * norm.sf(abs(estimate / se)))}
    out["n"] = int(len(use))
    return out


def _tail_analyses(pair: pd.DataFrame, *, floor: float, ceiling: float, seed: int) -> dict:
    """E1 (answering style) and E3 (whole-group shift or a subgroup) for one study."""
    autism, reference = pair["in_group"].eq(1), pair["in_group"].eq(0)
    style = {}
    for sense in PRIMARY_MODALITIES:
        row = {}
        for label, value in (("floor", floor), ("ceiling", ceiling)):
            a = int(pair.loc[autism, sense].eq(value).sum())
            r = int(pair.loc[reference, sense].eq(value).sum())
            odds, p = fisher_exact([[a, int(autism.sum()) - a], [r, int(reference.sum()) - r]])
            row[label] = {"autism_pct": 100 * a / autism.sum(), "comparison_pct": 100 * r / reference.sum(),
                          "odds_ratio": odds, "fisher_p": p}
        style[sense] = row
    pair = pair.copy()
    pair["n_ceiling"] = pair[PRIMARY_MODALITIES].eq(ceiling).sum(axis=1)
    pair["n_floor"] = pair[PRIMARY_MODALITIES].eq(floor).sum(axis=1)
    any_floor = pair["n_floor"].gt(0)
    a, r = int(any_floor[autism].sum()), int(any_floor[reference].sum())
    odds, p = fisher_exact([[a, int(autism.sum()) - a], [r, int(reference.sum()) - r]])
    style["any_sense_absent"] = {"autism_pct": 100 * a / autism.sum(), "comparison_pct": 100 * r / reference.sum(),
                                 "odds_ratio": odds, "fisher_p": p}
    for name in ("n_ceiling", "n_floor"):
        style[f"{name}_per_person"] = {"autism_mean": float(pair.loc[autism, name].mean()),
                                       "comparison_mean": float(pair.loc[reference, name].mean()),
                                       "adjusted_difference": _effect(pair, name)}
    rng = np.random.default_rng(seed)
    a_values = pair.loc[autism, "general_z"].dropna().to_numpy()
    r_values = pair.loc[reference, "general_z"].dropna().to_numpy()
    quantiles = {}
    for q in (0.10, 0.25, 0.5, 0.75, 0.90):
        observed = float(np.quantile(a_values, q) - np.quantile(r_values, q))
        draws = np.array([np.quantile(rng.choice(a_values, a_values.size), q) - np.quantile(rng.choice(r_values, r_values.size), q)
                          for _ in range(BOOTSTRAP_DRAWS)])
        quantiles[f"q{round(q * 100)}"] = {"difference": observed,
                                          "bootstrap_ci95": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))]}
    curve = []
    for q in np.arange(0.05, 0.951, 0.05):
        observed = float(np.quantile(a_values, q) - np.quantile(r_values, q))
        draws = np.array([np.quantile(rng.choice(a_values, a_values.size), q) - np.quantile(rng.choice(r_values, r_values.size), q)
                          for _ in range(CURVE_DRAWS)])
        curve.append({"percentile": round(100 * q), "difference": observed,
                      "ci95": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))]})
    return {"E1_answering_style": style,
            "E3_adjusted_quantile_regression": _quantile_regression(pair),
            "E3_percentile_curve_unadjusted": curve,
            "E3_H1_among_people_with_imagery_in_all_six_senses": _effect(pair.loc[~any_floor], "general_z"),
            "E3_percentile_differences_unadjusted": quantiles}


def _holm(p: dict[str, float]) -> dict[str, float]:
    running, out = 0.0, {}
    for rank, label in enumerate(sorted(p, key=p.get)):
        running = max(running, min(1.0, (len(p) - rank) * p[label]))
        out[label] = running
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preregistration-url", required=True)
    args = parser.parse_args()
    verify_registration(ROOT, args.preregistration_url)
    archive = ROOT / "2bdn6-osfstorage-archive.zip"
    frame, _ = load_new_study2_conditions(archive)
    frame = pd.concat([frame.reset_index(drop=True), _extra_columns(archive)], axis=1)
    data = standardize_to_reference(frame, frame["group"].eq("reference"), [*PRIMARY_MODALITIES, *EXPLORATORY_MODALITIES])
    pair = data.loc[data["group"].isin(["asd", "reference"])].copy()
    pair["in_group"] = pair["group"].eq("asd").astype(float)
    autism, reference = pair["in_group"].eq(1), pair["in_group"].eq(0)
    out: dict = {"label": "exploratory; not in the registered plan; run after the registered P5 analysis",
                 "registration": args.preregistration_url, "n_autism": int(autism.sum()), "n_comparison": int(reference.sum())}

    out.update(_tail_analyses(pair, floor=NEW_FLOOR_SCORE, ceiling=NEW_CEILING_SCORE, seed=20261010))
    adhd = data.loc[data["group"].eq("adhd_only")]
    adhd_absent = adhd[PRIMARY_MODALITIES].eq(NEW_FLOOR_SCORE).any(axis=1)
    autism_absent = pair.loc[autism, PRIMARY_MODALITIES].eq(NEW_FLOOR_SCORE).any(axis=1)
    reference_absent = pair.loc[reference, PRIMARY_MODALITIES].eq(NEW_FLOOR_SCORE).any(axis=1)
    out["E1_any_sense_absent_adhd_only"] = {"adhd_only_pct": float(100 * adhd_absent.mean())}
    for label, (x, y) in {"autism_vs_adhd_only": (autism_absent, adhd_absent),
                          "adhd_only_vs_comparison": (adhd_absent, reference_absent)}.items():
        odds, p = fisher_exact([[int(x.sum()), int((~x).sum())], [int(y.sum()), int((~y).sum())]])
        out["E1_any_sense_absent_adhd_only"][label] = {"odds_ratio": odds, "fisher_p": p}

    # E2 careless answering
    out["E2_all_attention_checks_passed"] = _effect(pair.loc[pair["nbact"].eq(5)], "general_z")

    # E1 and E3 repeated in Arnold et al.'s data (scores 0-50, floor 0)
    arnold, _, _, _ = load_arnold_code(ROOT / "Autism_Aphantasia_Analyses_code.zip")
    out["arnold"] = _tail_analyses(_arnold_prepared(arnold), floor=ARNOLD_FLOOR_SCORE, ceiling=ARNOLD_CEILING_SCORE, seed=20261011)
    key = "E3_H1_among_people_with_imagery_in_all_six_senses"
    pieces = [out[key], out["arnold"][key]]
    weights = [1 / piece["se"] ** 2 for piece in pieces]
    pooled = sum(w * piece["estimate"] for w, piece in zip(weights, pieces)) / sum(weights)
    pooled_se = sum(weights) ** -0.5
    out["E3_pooled_two_studies_people_with_imagery_in_all_senses"] = {
        "estimate": pooled, "se": pooled_se, "ci95": [pooled - 1.96 * pooled_se, pooled + 1.96 * pooled_se],
        "ci90": [pooled - 1.645 * pooled_se, pooled + 1.645 * pooled_se],
        "equivalence_bound_sd": EQUIVALENCE_BOUND_SD,
        "tost_p": float(max(norm.sf((pooled + EQUIVALENCE_BOUND_SD) / pooled_se), norm.cdf((pooled - EQUIVALENCE_BOUND_SD) / pooled_se))),
        "note": "fixed-effect inverse-variance pooling; selects people on their imagery scores, so read alongside the percentile results"}

    # E4 senses only New et al. measured, plus a nine-sense composite
    extra = {sense: _effect(pair, f"z_{sense}") for sense in EXPLORATORY_MODALITIES}
    holm = _holm({sense: extra[sense]["p_two_sided"] for sense in extra})
    for sense in extra:
        extra[sense]["holm_p"] = holm[sense]
    nine = pair[[f"z_{s}" for s in [*PRIMARY_MODALITIES, *EXPLORATORY_MODALITIES]]].mean(axis=1, skipna=False)
    base = nine[reference]
    pair["nine_z"] = (nine - base.mean()) / base.std(ddof=1)
    extra["nine_sense_composite"] = _effect(pair, "nine_z")
    out["E4_new_only_senses"] = extra

    # E5 covariates the plan left out
    out["E5_adjusted"] = {
        "current_treatment": _effect(pair, "general_z", extra_numeric=("diag",)),
        "education": _effect(pair.loc[pair["edu"].between(1, 5)], "general_z", extra_categorical=("edu",)),
        "both": _effect(pair.loc[pair["edu"].between(1, 5)], "general_z", extra_numeric=("diag",), extra_categorical=("edu",)),
    }
    out["E5_note"] = "education code 6 ('prefer not to answer') is left out of the education models"

    # E6 the non-imagery rating
    out["E6_empathy_item"] = {"autism_mean": float(pair.loc[autism, "empath"].mean()), "comparison_mean": float(pair.loc[reference, "empath"].mean()),
                              "adjusted_difference_raw_points": _effect(pair, "empath"),
                              "H1_adjusted_for_empathy": _effect(pair, "general_z", extra_numeric=("empath",))}

    target = ROOT / "runs" / "latest" / "P5" / "p5_exploratory.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(_json_safe(out), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(_json_safe(out), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
