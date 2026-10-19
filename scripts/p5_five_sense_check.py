"""Post-registration measurement check, specified 17 Oct 2026 after seeing P5.

Exclude Arnold bodily sensation / New motor imagery from both composites.
This supplements, and never replaces, the registered six-component analysis.
Participant rows are never written. All inferential p values here are exploratory.
"""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aphantasia.datasets import load_arnold_code, load_new_study2_conditions  # noqa: E402


def fit(frame, group_field, group_value, reference_value):
    modalities = ["visual", "auditory", "smell", "taste", "touch"]
    frame = frame.loc[frame[group_field].isin([group_value, reference_value])].copy()
    reference = frame[group_field].eq(reference_value)
    z = (frame[modalities] - frame.loc[reference, modalities].mean()) / frame.loc[reference, modalities].std(ddof=1)
    average = z.mean(axis=1, skipna=False)
    frame["composite"] = (average - average[reference].mean()) / average[reference].std(ddof=1)
    frame = frame.dropna(subset=["composite", "age", "sex_gender"])
    design = pd.DataFrame({"intercept": 1.0, "in_group": frame[group_field].eq(group_value).astype(float),
                           "age": pd.to_numeric(frame.age)}, index=frame.index)
    levels = sorted(frame.sex_gender.astype(str).unique())
    for i, level in enumerate(levels[1:], 1):
        design[f"sex_level_{i}"] = frame.sex_gender.astype(str).eq(level).astype(float)
    result = sm.OLS(frame.composite.to_numpy(float), design.to_numpy(float)).fit(cov_type="HC3", use_t=True)
    return {"n": int(result.nobs), "adjusted_difference_reference_SD": float(result.params[1]),
            "se_HC3": float(result.bse[1]), "ci95": result.conf_int()[1].tolist(),
            "p_two_sided_exploratory": float(result.pvalues[1]), "modalities": modalities}


def main():
    new, _ = load_new_study2_conditions(ROOT / "2bdn6-osfstorage-archive.zip")
    arnold, _, _, _ = load_arnold_code(ROOT / "Autism_Aphantasia_Analyses_code.zip")
    result = {"role": "post-registration measurement sensitivity; results already seen before specification",
              "reason": "Arnold PSI-Q bodily sensation and New QMI motor imagery are not the same construct.",
              "New": fit(new, "group", "asd", "reference"),
              "Arnold": fit(arnold, "diagnosis_group", 1, 0), "participant_rows_written": False}
    out = ROOT / "projects/P5_asd_adhd_replication/review/validation/five_sense_check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
