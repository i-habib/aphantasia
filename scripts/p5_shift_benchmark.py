"""P5 exploratory benchmark: could a whole-group shift produce the absent-imagery pattern?

Added 18 October 2026 after a cold-read review, after all registered and earlier
exploratory results were known. Report it as exploratory whatever it shows.

The question: the autism group has more people with absent imagery (the lowest
possible score in a sense) and no difference among people with imagery in every
sense. Would that also happen if every autistic person simply scored a little
lower (a shift), or if the whole autism distribution were lower and more spread
out (a shift plus stretch)?

Method, fixed before running. In each study, take the comparison group's raw
sense scores and transform them, sense by sense, into a predicted autism group:
  shift:           score - (comparison mean - autism mean) for that sense
  shift + stretch: autism mean + (score - comparison mean) * autism SD / comparison SD
Round to whole points and clip to the scale (5-35 for New et al., 0-50 for
Arnold et al.). Each person keeps their own profile across senses. Then compute,
for the predicted group, the same statistics as for the real autism group:
share with absent imagery in at least one sense, share with the top score in at
least one sense, overall-score differences at the 10th, 25th, 50th, 75th and
90th percentiles, and the overall-score difference among people with imagery in
every sense. All statistics are unadjusted. The real autism group's values get
95% bootstrap intervals (2,000 resamples of the autism group).

Also writes group sex counts for New et al. (source codes 0, 1, O), aggregate only.

    python3 scripts/p5_shift_benchmark.py --preregistration-url https://osf.io/87udm
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aphantasia.datasets import load_arnold_code, load_new_study2_conditions  # noqa: E402
from aphantasia.p5 import PRIMARY_MODALITIES, verify_registration  # noqa: E402

QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)
DRAWS = 2000


def _composite(scores: pd.DataFrame, reference: pd.DataFrame) -> np.ndarray:
    """Overall score in comparison-group SD units, using the comparison group's own statistics."""
    mean, sd = reference.mean(), reference.std(ddof=1)
    ref_component = ((reference - mean) / sd).mean(axis=1)
    component = ((scores - mean) / sd).mean(axis=1)
    return ((component - ref_component.mean()) / ref_component.std(ddof=1)).to_numpy()


def _summary(group: pd.DataFrame, reference: pd.DataFrame, low: float, high: float) -> dict:
    absent = group.eq(low).any(axis=1).to_numpy()
    ref_absent = reference.eq(low).any(axis=1).to_numpy()
    z, ref_z = _composite(group, reference), _composite(reference, reference)
    out = {"any_absent_pct": float(100 * absent.mean()), "any_top_pct": float(100 * group.eq(high).any(axis=1).mean())}
    for q in QUANTILES:
        out[f"q{round(q * 100)}"] = float(np.quantile(z, q) - np.quantile(ref_z, q))
    out["all_present_difference"] = float(z[~absent].mean() - ref_z[~ref_absent].mean())
    return out


def _study(autism: pd.DataFrame, reference: pd.DataFrame, low: float, high: float, seed: int) -> dict:
    autism, reference = autism.astype(float), reference.astype(float)
    shift = reference - (reference.mean() - autism.mean())
    stretch = autism.mean() + (reference - reference.mean()) * autism.std(ddof=1) / reference.std(ddof=1)
    predicted = {name: frame.round().clip(low, high) for name, frame in (("shift", shift), ("shift_plus_stretch", stretch))}
    rng = np.random.default_rng(seed)
    draws = [_summary(autism.iloc[rng.integers(0, len(autism), len(autism))], reference, low, high) for _ in range(DRAWS)]
    observed = _summary(autism, reference, low, high)
    return {"comparison": _summary(reference, reference, low, high),
            "observed_autism": observed,
            "observed_bootstrap_ci95": {k: [float(np.quantile([d[k] for d in draws], 0.025)), float(np.quantile([d[k] for d in draws], 0.975))] for k in observed},
            **{f"predicted_{name}": _summary(frame, reference, low, high) for name, frame in predicted.items()},
            "n_autism": int(len(autism)), "n_comparison": int(len(reference))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preregistration-url", required=True)
    args = parser.parse_args()
    verify_registration(ROOT, args.preregistration_url)
    frame, _ = load_new_study2_conditions(ROOT / "2bdn6-osfstorage-archive.zip")
    new = {g: frame.loc[frame["group"].eq(g), PRIMARY_MODALITIES].apply(pd.to_numeric) for g in ("asd", "reference")}
    arnold, _, _, _ = load_arnold_code(ROOT / "Autism_Aphantasia_Analyses_code.zip")
    in_group = pd.to_numeric(arnold["diagnosis_group"])
    out = {"label": "exploratory; added 18 October 2026 after all other results were known; unadjusted",
           "new": _study(new["asd"], new["reference"], 5, 35, 20261018),
           "arnold": _study(arnold.loc[in_group.eq(1), PRIMARY_MODALITIES], arnold.loc[in_group.eq(0), PRIMARY_MODALITIES], 0, 50, 20261019),
           "new_sex_codes_by_group": {g: {str(k): int(v) for k, v in frame.loc[frame["group"].eq(g), "sex_gender"].astype(str).value_counts().items()}
                                      for g in ("asd", "adhd_only", "reference")}}
    path = ROOT / "runs/latest/P5/p5_shift_benchmark.json"
    path.write_text(json.dumps(out, indent=1) + "\n")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
