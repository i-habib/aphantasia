# P3 — autism and mental imagery

**State:** Arnold public-data reanalysis complete; cross-study synthesis remains blocked on cohort provenance and comparable independent data.

## Sources and current run

- [Arnold et al. (2026)](https://discovery.ucl.ac.uk/id/eprint/10230162/); [UQ dataset DOI 10.48610/57f325b](https://doi.org/10.48610/57f325b); [UQ repository item](https://espace.library.uq.edu.au/view/UQ:57f325b).
- The workspace has the workbook and public MATLAB code archive; fingerprints and staged schema are in [`DATA_SOURCES.md`](../../DATA_SOURCES.md).
- Run: `python3 scripts/run_available.py --project P3`
- The run reports all 327 self-reported formal diagnoses versus 327 controls, and separately reports the authors' AQ≥26 selection (242 diagnosed participants vs the same controls). Do not treat the overlapping analysis sets as independent samples.

The user reports having emailed the author for the separate Dance autism-study data. The sent date and response are not in the workspace; check that correspondence and do not send a duplicate request. The public Dance `h24vm` OSF archive is an imagery × sensory-sensitivity auxiliary dataset, not the autism experiment.

## Current scope and interpretation

The current code reanalyses score arrays embedded in the authors' published analysis script and writes aggregate estimates only. AQ/CATI trait models are restricted to the diagnosed group because those questionnaires are absent from the controls. The public workbook's exact correspondence to these analysis arrays has not been verified. Controls came from an earlier sample; identify its source and check participant overlap before comparing or synthesizing results.

Do not describe this single-cohort reanalysis as a new autism–aphantasia association paper. The publishable version needs a clearly new question, reliable measurement harmonization, independent eligible cohorts, overlap handling, and a registered study-level synthesis plan. Keep diagnosis contrasts separate from AQ/CATI trait associations.

## Finish checklist

1. Reconcile workbook row/column labels and exclusions with the code's 327+327 analysis arrays.
2. Ask the authors for prior-control cohort provenance and overlap counts if public documentation is insufficient.
3. Log the user's existing Dance autism-data request and await its response.
4. Complete the systematic-search eligibility and construct-compatibility table; the header template is in `templates/study-compatibility-matrix.csv`.
5. Add author-requested datasets only after confirming instruments, diagnosis definitions, and recruitment frame.
6. Freeze independent study estimates and any pooling strata before fitting summary effects.

First-pass estimates are in [`RESULTS_SUMMARY.md`](../../RESULTS_SUMMARY.md).
