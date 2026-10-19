"""Write aggregate P5 participant/outcome summaries; never write source rows."""
import csv
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aphantasia.datasets import load_new_study2_conditions  # noqa: E402
from aphantasia.p5 import PRIMARY_MODALITIES  # noqa: E402


def main():
    frame, _ = load_new_study2_conditions(ROOT / "2bdn6-osfstorage-archive.zip")
    reference = frame.group.eq("reference")
    scores = frame[PRIMARY_MODALITIES]
    z = (scores - scores.loc[reference].mean()) / scores.loc[reference].std(ddof=1)
    composite = z.mean(axis=1, skipna=False)
    frame["composite"] = (composite - composite[reference].mean()) / composite[reference].std(ddof=1)
    labels = {"reference": "Comparison", "asd": "Autism", "adhd_only": "ADHD-only"}
    measures = {"age": "Age (years)", "composite": "Registered composite (comparison SD)",
                **{m: m.title() + " score (5-35)" for m in PRIMARY_MODALITIES}}
    rows = []
    for group, label in labels.items():
        subset = frame.loc[frame.group.eq(group)]
        rows.append({"measure": "Retained participants", "group": label, "n": len(subset),
                     "mean": "", "sd": "", "min": "", "max": ""})
        for column, measure in measures.items():
            values = pd.to_numeric(subset[column], errors="raise").dropna()
            rows.append({"measure": measure, "group": label, "n": len(values),
                         "mean": float(values.mean()), "sd": float(values.std(ddof=1)),
                         "min": float(values.min()), "max": float(values.max())})
    out = ROOT / "projects/P5_asd_adhd_replication/submission"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "table0_participants_outcomes.csv").open("w") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    # Aggregate source-code counts. The mapping of 0/1 to sex labels is unverified.
    # Avoid group-specific small cells and don't publish source IDs or individual ages.
    counts = frame.sex_gender.value_counts()
    summary = {"source_sex_codes_all_retained": {str(k): int(v) for k, v in counts.items()},
               "sex_code_0_1_mapping": "Unverified; no inferred Female/Male labels.",
               "age_above_30_all_retained": int(frame.age.gt(30).sum()),
               "age_missing_by_group": {k: int(frame.loc[frame.group.eq(k), "age"].isna().sum()) for k in labels},
               "participant_rows_written": False}
    validation = ROOT / "projects/P5_asd_adhd_replication/review/validation"
    (validation / "participant_descriptives.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
