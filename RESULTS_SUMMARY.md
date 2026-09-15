# First-pass results — 14 September 2026

These are exploratory secondary analyses, run after reviewing the published articles and public files. They are not a preregistered confirmatory test. Estimates below are model outputs from the scripts in `src/aphantasia`; all source-level files and intermediate participant rows remain local and are not included here.

## P1 — New et al. multisensory imagery

The source `nbact >= 3` rule reproduces the paper's reported samples: Study 1 N=949 (53 treatment-field positives) and Study 2 N=1,003 (67 positives; 1,002 complete cases for the primary model because one age is missing). The questionnaires confirm that `diag` asks whether the respondent is currently receiving treatment for a neurologic or psychiatric condition, with No/Yes response choices; `diag2` is a Yes-only open follow-up and is excluded. The 18–30 age sensitivity has N=947 and N=999 respectively.

In the current direct adjusted logistic model, Study 1 shows lower odds with visual imagery (OR 0.67, 95% CI 0.48–0.94) and with the nonvisual composite (OR 0.89, 95% CI 0.57–1.39). A separate all-modality mean gives OR 0.60 (95% CI 0.44–0.84); a visual-minus-nonvisual deviation conditional on that general score gives OR 0.72 (95% CI 0.51–1.00). The visual coefficient is essentially unchanged by expressing visual imagery as a residual because the direct and residualized models span the same predictor space; the nonvisual coefficient changes because it represents a different conditional quantity.

Study 2's visual association points in the same lower-odds direction but is weaker and imprecise: direct visual OR 0.82 (95% CI 0.59–1.15), nonvisual OR 1.06 (95% CI 0.70–1.62), general-imagery OR 0.88 (95% CI 0.66–1.18), and visual-deviation OR 0.84 (95% CI 0.60–1.17). In the joint model, the Study 1 reference visual OR is 0.68 (95% CI 0.49–0.94); the Study 2 visual interaction is OR 1.20 (95% CI 0.78–1.85, p=0.41), and the nonvisual interaction is OR 1.23 (95% CI 0.68–2.22, p=0.49). Thus the data suggest attenuation / failure to obtain a clear within-study replication, not evidence of a demonstrated study difference. For the separate, broad diagnosed-or-strongly-suspected NDD field, Study 2 nonvisual OR is 0.87 (95% CI 0.68–1.11), while visual OR is 0.86 (95% CI 0.70–1.05). The NDD field is not autism-specific or diagnosis-confirmed.

**Interpretation gate:** The questionnaire crosswalk is now resolved. The remaining gate is novelty: New et al. already report categorical aphantasia / hyperphantasia comparisons with treatment and NDD status, so the manuscript must state exactly what the continuous conditional and general-imagery models add. The treatment outcome is not a diagnosis or symptom score. The best current reading is a modest association that leans in the same direction across samples but is precise only in Study 1; do not describe the interaction as evidence that the studies differ.

## P3 — Arnold autism and imagery

The code-embedded arrays yield 327 participants reporting a formal autism diagnosis and 327 comparison participants. For the full diagnosis group, unadjusted Hedges g (diagnosed minus comparison; negative means lower imagery scores in the diagnosed group) is:

| Modality | Hedges g | 95% CI |
|---|---:|---:|
| Visual | -0.16 | [-0.31, -0.00] |
| Auditory | -0.14 | [-0.29, 0.02] |
| Smell | -0.30 | [-0.45, -0.14] |
| Taste | -0.23 | [-0.39, -0.08] |
| Touch | -0.15 | [-0.30, 0.01] |
| Movement | -0.09 | [-0.24, 0.06] |

These estimates describe one published dataset, not a new independent discovery. A participant-clustered repeated-modality model (3,924 modality observations from 654 people) gives an omnibus autism-by-modality interaction χ²(5)=19.28, p=0.0017; the largest individual deviation is for smell (interaction estimate −2.15, 95% CI −3.73 to −0.57). This tests whether the group gap varies by modality while accounting for within-person dependence, but it does not establish a causal sensory mechanism. The authors' AQ≥26 case-selection rule yields 242 diagnosed participants versus the same 327 controls; it is reported as a sensitivity and not treated as a second cohort. Before writing a cross-study result, verify the source of the earlier comparison cohort, reconcile the public workbook with the analysis-code arrays, and obtain harmonizable independent autism-study data. The public Dance `h24vm` archive is a different sensory-sensitivity dataset; the user reports separately requesting the autism-study data.

## P4 — Mawtus mental-healthcare survey

The staged quantitative CSV has 2,815 rows and 80 fields. Overall treatment effectiveness has 2,110 nonblank responses across three levels. Auditory imagery score is present for all 2,815 rows, but the auditory-therapy field has 302 nonblank responses with one observed response level; the file does not identify explicit use versus non-use paired with modality-specific effectiveness. The audit therefore stops before inferential modeling. Do not turn this overall retrospective outcome into a per-modality or causal treatment-matching claim.

## Reproduce

Run `python3 scripts/run_available.py --project all` from the workspace root. Machine-readable estimates, model diagnostics, source-flow counts, and the P4 feasibility output are under `runs/latest/` (ignored by Git). Run `python3 -m pytest` to verify the data contracts and privacy-safe outputs.
