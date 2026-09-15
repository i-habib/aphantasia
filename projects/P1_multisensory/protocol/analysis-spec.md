# P1 analysis specification — working draft

This is an exploratory specification. The treatment question crosswalk is now confirmed from both archived questionnaires; the novelty review and final estimand freeze remain open. Do not label a model confirmatory until the analysis plan is frozen with the prior data inspection disclosed.

## Question and data

Does visual imagery add a conditional association with current neurological/psychiatric treatment status after accounting for the common nonvisual imagery profile, age, and recorded sex/gender? Run Studies 1 and 2 separately. The Study 2 diagnosed-or-strongly-suspected NDD outcome is a separate secondary analysis, not an autism outcome.

Source: New et al. (2026), OSF 2bdn6. Apply `nbact >= 3`; the contract requires N=949 and N=1,003. Keep the source rows in memory. Never save IDs, open text, comments, or participant-level transformed data. The treatment outcome is the confirmed item “Are you currently receiving treatment for a neurologic or psychiatric condition?” with No/Yes responses; `diag2` is an open follow-up shown only after Yes and is excluded.

## Working estimand and model

For each study, fit a logistic model for source field `diag` using within-study z-scores for direct visual imagery and the common nonvisual modalities (sound, touch, motor, taste, smell, emotion, voice), age, and recorded sex/gender categories. The working effects are adjusted odds ratios and 95% intervals per within-study SD, not prevalence ratios and not causal effects. Secondary models use an all-modality mean composite and a visual-minus-nonvisual deviation conditional on that composite. The visual residual form is algebraically equivalent to the direct two-predictor model for the visual coefficient; it is not treated as a competing visual sensitivity.

Sensitivity checks: restriction to age 18–30 with missing ages excluded; Study 2 `isneurodev` outcome; and an explicit pooled study-by-imagery interaction. Use Firth bias-reduced logistic regression when ordinary logistic regression is singular/separated. Do not change predictor coding to chase agreement.

## Required pre-manuscript checks

1. Verify modality scoring and direction against the questionnaire/source script.
2. Tabulate the paper's already-published treatment and NDD analyses against this proposal; state the unique contribution precisely.
3. Freeze outcome, predictor coding, covariates, interval method, and the Study 2 role. Report current estimates as exploratory and disclose that the proposed question was selected after data and publication inspection.
4. Generate full participant flow and missingness from aggregate diagnostics; explain age exceptions without silently removing them from the primary reproduced sample.

## Stop or revise rules

- If `diag` is not the claimed treatment item, stop the clinical interpretation and remap only with source documentation.
- If questionnaire scoring does not support the seven common fields, revise the composite before final analysis and document the change.
- If the paper already reports the same conditional treatment association, revise the question or stop rather than relabeling a reanalysis as novel.
- If Study 1 is more precise and Study 2 is weaker or less precise, report attenuation and the failure to obtain a clear replication; do not label this a demonstrated study difference or claim that replication failed definitively. Use the pooled Study-by-imagery interaction to quantify evidence for heterogeneity.
