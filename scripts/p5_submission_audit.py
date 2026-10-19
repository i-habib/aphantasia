"""Reproduce saved P5 outputs and check them against independent engines.

Never overwrites runs/latest. Raw rows stay in memory, including the R pipe.
R dependency: brglm2 (AS_mean equals Firth mean bias reduction for logit).
Example: python3 scripts/p5_submission_audit.py --r-library /private/tmp/p5-r-library
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
from scipy.stats import norm
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aphantasia.datasets import load_new_study2_conditions, load_arnold_code  # noqa: E402
from aphantasia.models import _logit_firth  # noqa: E402
from aphantasia.p5 import PRIMARY_MODALITIES, run_p5, verify_registration  # noqa: E402


def design(frame, indicators):
    """Independently construct the same declared regression design."""
    columns = {"intercept": np.ones(len(frame))}
    columns.update({k: pd.to_numeric(frame[k]).to_numpy(float) for k in [*indicators, "age"]})
    levels = sorted(frame.sex_gender.astype(str).unique())
    columns.update({f"sex_gender_level_{i}": frame.sex_gender.astype(str).eq(v).to_numpy(float)
                    for i, v in enumerate(levels[1:], 1)})
    return np.column_stack(list(columns.values())), list(columns)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r-library", default="/private/tmp/p5-r-library")
    args = parser.parse_args()
    out = ROOT / "projects/P5_asd_adhd_replication/review/validation"
    out.mkdir(parents=True, exist_ok=True)
    latest = ROOT / "runs/latest/P5"
    originals = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in latest.glob("p5_*") if p.is_file()}
    registration = verify_registration(ROOT, "https://osf.io/87udm")
    frame, flow = load_new_study2_conditions(ROOT / "2bdn6-osfstorage-archive.zip")
    arnold, _, _, _ = load_arnold_code(ROOT / "Autism_Aphantasia_Analyses_code.zip")
    reproduced = out / "reproduced"
    run_p5(frame, reproduced, registration=registration, arnold=arnold)
    old = pd.read_csv(latest / "p5_estimates.csv")
    new = pd.read_csv(reproduced / "p5_estimates.csv")
    assert list(old.columns) == list(new.columns) and old.shape == new.shape
    num = old.select_dtypes(include="number").columns
    nonnum = [c for c in old if c not in num]
    assert old[nonnum].equals(new[nonnum])
    delta = float(np.nanmax(np.abs(old[num].to_numpy() - new[num].to_numpy())))
    np.testing.assert_allclose(old[num], new[num], rtol=1e-7, atol=1e-8, equal_nan=True)

    # Independent standardization, not the production helper.
    data = frame.copy()
    reference = data.group.eq("reference")
    z = (data[PRIMARY_MODALITIES] - data.loc[reference, PRIMARY_MODALITIES].mean()) / data.loc[reference, PRIMARY_MODALITIES].std(ddof=1)
    composite = z.mean(axis=1, skipna=False)
    data["general_z"] = (composite - composite[reference].mean()) / composite[reference].std(ddof=1)
    pair = data.loc[data.group.isin(["asd", "reference"])].copy()
    pair["in_group"] = pair.group.eq("asd").astype(float)
    pair = pair.dropna(subset=["age", "sex_gender", "general_z"])
    x, names = design(pair, ["in_group"])
    ols = sm.OLS(pair.general_z.to_numpy(float), x).fit(cov_type="HC3", use_t=True)
    h1 = old.loc[(old.model == "H1_general_imagery_shift") & (old.term == "in_group")].iloc[0]
    np.testing.assert_allclose([h1.coef, h1.se, h1.ci_low, h1.ci_high, h1.p],
                               [ols.params[1], ols.bse[1], *ols.conf_int()[1], ols.pvalues[1]], rtol=1e-8, atol=1e-10)

    specs = [("H2a_smell_absence", pair, "smell"), ("H2b_taste_absence", pair, "taste"),
             ("S3_visual_absence_asd", pair, "visual")]
    no_adhd = pair.loc[~(pair.group.eq("asd") & pair.asd_with_adhd)]
    specs += [(f"SENS_asd_without_adhd_{m}_absence", no_adhd, m) for m in ["smell", "taste"]]
    cases, fits = [], {}
    for label, subset, modality in specs:
        matrix, columns = design(subset, ["in_group"])
        y = subset[modality].eq(5).to_numpy(float)
        beta, covariance, diagnostics = _logit_firth(y, matrix)
        fits[label] = (beta, covariance, columns, diagnostics)
        cases.append({"label": label, "x": matrix.tolist(), "y": y.tolist(), "names": columns})
    process = subprocess.run(["Rscript", str(ROOT / "scripts/p5_reference_firth.R"), args.r_library],
                             input=json.dumps({"cases": cases}), text=True, capture_output=True, check=True)
    reference_results = json.loads(process.stdout)
    (out / "reference_firth.json").write_text(json.dumps(reference_results, indent=2) + "\n")
    (out / "reference_firth_stderr.txt").write_text(process.stderr)
    checks = []
    for case in reference_results["cases"]:
        beta, covariance, columns, diagnostics = fits[case["label"]]
        ref_beta, ref_cov = np.asarray(case["beta"]), np.asarray(case["covariance"])
        assert case["converged"], case["label"]
        np.testing.assert_allclose(beta, ref_beta, rtol=1e-5, atol=2e-6)
        np.testing.assert_allclose(covariance, ref_cov, rtol=1e-5, atol=2e-6)
        i = columns.index("in_group")
        se = float(np.sqrt(ref_cov[i, i]))
        ref_values = [float(np.exp(ref_beta[i])), se,
                      *np.exp(ref_beta[i] + np.array([-1, 1]) * norm.ppf(.975) * se),
                      float(2 * norm.sf(abs(ref_beta[i] / se)))]
        row = old.loc[(old.model == case["label"]) & (old.term == "in_group")].iloc[0]
        np.testing.assert_allclose([row.coef, row.se, row.ci_low, row.ci_high, row.p], ref_values, rtol=2e-5, atol=2e-6)
        checks.append({"model": case["label"], "reference_converged": True,
                       "max_abs_beta_difference": float(np.max(np.abs(beta - ref_beta))),
                       "max_abs_covariance_difference": float(np.max(np.abs(covariance - ref_cov))),
                       "reference_group_OR": ref_values[0], "reference_group_se_log_odds": se,
                       "reference_group_ci95_Wald": ref_values[2:4], "reference_group_p_two_sided_Wald": ref_values[4],
                       "production_gradient_max_abs": diagnostics["gradient_max_abs"]})
    diagnostics = json.loads((latest / "p5_diagnostics.json").read_text())
    secondary = diagnostics["details"]["secondary"]
    labels = list(secondary["two_sided_p"])
    adjusted = multipletests([secondary["two_sided_p"][k] for k in labels], method="holm")[1]
    np.testing.assert_allclose(adjusted, [secondary["holm_adjusted_p"][k] for k in labels], atol=1e-14)
    for name, digest in originals.items():
        assert hashlib.sha256((latest / name).read_bytes()).hexdigest() == digest
    result = {"status": "passed", "registration": registration.url, "plan_sha256": registration.plan_sha256,
              "production_outputs_unchanged": True, "reproduction_rows": len(new), "reproduction_max_absolute_difference": delta,
              "H1_matches_statsmodels_HC3": True, "Holm_matches_statsmodels": True,
              "Firth_reference": {k: v for k, v in reference_results.items() if k != "cases"},
              "Firth_checks": checks, "R_stderr": process.stderr.strip(),
              "inference_note": "Reference matches the registered implementation's Wald inference; profile-likelihood intervals were not substituted.",
              "source_flow": flow, "original_output_sha256": originals,
              "versions": {"python": sys.version.split()[0], "numpy": np.__version__, "pandas": pd.__version__}}
    (out / "numerical_validation.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "reproduced_rows": len(new), "Firth_models_checked": len(checks),
                      "max_Firth_coefficient_difference": max(c["max_abs_beta_difference"] for c in checks),
                      "report": str(out / "numerical_validation.json")}))


if __name__ == "__main__":
    main()
