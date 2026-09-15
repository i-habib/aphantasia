#!/usr/bin/env python3
"""Run representation CV on New et al. P1 outcomes only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from representation_cv import OutcomeSpec, P1_MODALITIES, load_new_from_fetch, repeated_nested_cv, render_markdown


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("representation_cv_results"))
    ap.add_argument("--outer-repeats", type=int, default=20)
    args = ap.parse_args()

    new_frame, new_flow = load_new_from_fetch(args.data_root)
    specs = []
    for study in (1, 2):
        sf = new_frame.loc[new_frame["study_id"].eq(study)].copy()
        specs.append(OutcomeSpec("P1", f"new_study_{study}", "current_treatment", sf, P1_MODALITIES, "image", "treatment"))
    sf2 = new_frame.loc[new_frame["study_id"].eq(2)].copy()
    specs.append(OutcomeSpec("P1", "new_study_2", "broad_diagnosed_or_suspected_NDD", sf2, P1_MODALITIES, "image", "ndd"))

    results = []
    for spec in specs:
        print(f"Running {spec.project} {spec.cohort} {spec.outcome}", flush=True)
        results.append(repeated_nested_cv(spec, outer_repeats=args.outer_repeats))

    args.output.mkdir(parents=True, exist_ok=True)
    payload = {
        "analysis": "visual binary vs visual continuous vs general vs multidimensional imagery prediction",
        "status": "exploratory_post_hoc",
        "source_flow": {"new": new_flow},
        "results": results,
    }
    (args.output / "representation_cv.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "representation_cv.md").write_text(render_markdown(results), encoding="utf-8")
    print((args.output / "representation_cv.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
