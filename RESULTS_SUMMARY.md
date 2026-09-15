# First-pass results — 14 September 2026

These are exploratory secondary analyses, run after reviewing the published articles and public files. They are not a preregistered confirmatory test. Estimates below are model outputs from the scripts in `src/aphantasia`; all source-level files and intermediate participant rows remain local and are not included here.

## P1 — New et al. multisensory imagery

The source `nbact >= 3` rule reproduces the paper's reported samples: Study 1 N=949 (53 treatment-field positives) and Study 2 N=1,003 (67 positives; 1,002 complete cases for the primary model because one age is missing). The questionnaires confirm that `diag` asks whether the respondent is currently receiving treatment for a neurologic or psychiatric condition, with No/Yes response choices; `diag2` is a Yes-only open follow-up and is excluded. The 18–30 age sensitivity has N=947 and N=999 respectively.

In the current direct adjusted logistic model, Study 1 shows lower odds with visual imagery (OR 0.67, 95% CI 0.48–0.93) and a weaker, imprecise association with the re-standardized nonvisual composite (OR 0.92, 95% CI 0.65–1.29). A separate re-standardized all-modality mean gives OR 0.68 (95% CI 0.53–0.86). The direct model also emits a common-imagery-shift contrast (OR 0.62, 95% CI 0.48–0.80) and a visual-minus-nonvisual coefficient contrast (OR 0.73, 95% CI 0.40–1.36); these are linear contrasts of the same fitted model, not separate robustness regressions.

The exploratory source-threshold model uses image score 5 for visual aphantasia and ≥35 for visual hyperphantasia, with the middle range as reference and the nonvisual composite, age, and sex/gender adjusted. Study 1 threshold estimates are imprecise (aphantasia OR 1.49, 95% CI 0.35–6.36; hyperphantasia OR 0.67, 95% CI 0.04–12.26); Study 2 estimates are similarly wide (OR 0.55, 95% CI 0.09–3.25 and OR 0.55, 95% CI 0.10–2.94). The threshold model is included to distinguish an extreme-phenotype threshold story from a smooth continuous dose-response; cut points were fixed from the source analysis script rather than selected from the treatment outcome.

Study 2's visual association points in the same lower-odds direction but is weaker and imprecise: direct visual OR 0.82 (95% CI 0.59–1.15), re-standardized nonvisual OR 1.05 (95% CI 0.75–1.47), and general-imagery OR 0.90 (95% CI 0.72–1.14). Its direct-model contrasts are common shift OR 0.87 (95% CI 0.67–1.11) and visual-minus-nonvisual OR 0.78 (95% CI 0.42–1.46). In the joint model, the Study 1 reference visual OR is 0.68 (95% CI 0.49–0.94); the Study 2 visual interaction is OR 1.20 (95% CI 0.78–1.84, p=0.41), and the nonvisual interaction is OR 1.18 (95% CI 0.74–1.87, p=0.48). Thus the data suggest attenuation / failure to obtain a clear within-study replication, not evidence of a demonstrated study difference. For the separate, broad diagnosed-or-strongly-suspected NDD field, Study 2 nonvisual OR is 0.89 (95% CI 0.73–1.08), while visual OR is 0.86 (95% CI 0.70–1.05). The NDD field is not autism-specific or diagnosis-confirmed.

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

These estimates describe one published dataset, not a new independent discovery. A participant-clustered repeated-modality model (3,924 modality observations from 654 people) gives an omnibus autism-by-modality interaction χ²(5)=19.28, p=0.0017; the largest individual deviation is for smell (interaction estimate −2.15, 95% CI −3.73 to −0.57). Prespecified stress variants remain positive but attenuate: modality-standardized outcomes χ²(5)=15.12, p=0.0099; age×modality and sex×modality nuisance interactions χ²(5)=13.35, p=0.0203; and dropping smell χ²(4)=10.66, p=0.0307. These tests assess modality heterogeneity while accounting for within-person dependence; they do not establish a causal sensory mechanism. The authors' AQ≥26 case-selection rule yields 242 diagnosed participants versus the same 327 controls; it is reported as a sensitivity and not treated as a second cohort. Before writing a cross-study result, verify the source of the earlier comparison cohort, reconcile the public workbook with the analysis-code arrays, and obtain harmonizable independent autism-study data. The public Dance `h24vm` archive is a different sensory-sensitivity dataset; the user reports separately requesting the autism-study data.

## P4 — Mawtus mental-healthcare survey

The staged quantitative CSV has 2,815 rows and 80 fields. Overall treatment effectiveness has 2,110 nonblank responses across three levels. Auditory imagery score is present for all 2,815 rows, but the auditory-therapy field has 302 nonblank responses with one observed response level; the file does not identify explicit use versus non-use paired with modality-specific effectiveness. The audit therefore stops before inferential modeling. Do not turn this overall retrospective outcome into a per-modality or causal treatment-matching claim.

## Reproduce

Run `python3 scripts/run_available.py --project all` from the workspace root. Machine-readable estimates, model diagnostics, source-flow counts, and the P4 feasibility output are under `runs/latest/` (ignored by Git). Run `python3 -m pytest` to verify the data contracts and privacy-safe outputs.
