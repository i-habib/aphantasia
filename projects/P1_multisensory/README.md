# P1 — New et al. multisensory imagery and reported treatment

**State:** exploratory model run complete; questionnaire crosswalk complete; novelty and final estimand checks remain. This is a secondary analysis of the public New et al. dataset, not an untouched replication.

## Source and input

- Article: [New et al. (2026), *Cortex*](https://doi.org/10.1016/j.cortex.2026.04.019)
- OSF: [project 2bdn6](https://osf.io/2bdn6/), [download repository ZIP](https://files.osf.io/v1/resources/2bdn6/providers/osfstorage/?zip=)
- Local immutable working archive: workspace root `2bdn6-osfstorage-archive.zip`; exact hash and contents are in [`DATA_SOURCES.md`](../../DATA_SOURCES.md).
- Run: `python3 scripts/run_available.py --project P1`

## Data contract and model

The source tables contain 953 and 1,020 rows. Applying the source `nbact >= 3` rule yields N=949 and N=1,003. The loader keeps the source rows in memory, scores the common imagery fields, and removes participant keys, comments, and open-response text before returning an analysis frame.

The current exploratory models fit each study separately: confirmed treatment field `diag` predicted by direct visual and seven-modality nonvisual z-score terms, age, and recorded sex/gender. Additional models use an all-modality mean composite and a visual-minus-nonvisual deviation, plus a pooled study-by-imagery interaction model. Outputs are odds ratios with 95% intervals. An age 18–30 sensitivity is generated. Study 2's diagnosed-or-strongly-suspected NDD field is secondary and must never be described as autism-specific.

The exact treatment/NDD wording, response coding, and `diag2` branch are documented in the [questionnaire crosswalk](protocol/questionnaire-crosswalk.md).

## Finish checklist

1. Check the source script/questionnaire that defines each modality score and document why the seven common nonvisual modalities are included while Study 2 `intstate` is excluded.
2. Compare the direct conditional, general-imagery, and study-interaction models with every treatment and NDD analysis in the article. Write the incremental contribution in one paragraph before selecting a journal.
3. Freeze one estimand and interval method, then rerun the code. Keep Study 2 as an independent confirmation regardless of Study 1 results.
4. Draft the sample-flow, measurement, missingness, sensitivity, and limitations sections from the generated diagnostics.

The current aggregate estimates and interpretation limits are in [`RESULTS_SUMMARY.md`](../../RESULTS_SUMMARY.md). Do not call the reported treatment status a psychiatric diagnosis or severity measure.
