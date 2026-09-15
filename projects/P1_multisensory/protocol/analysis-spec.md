# P1 analysis specification — working draft

This is an exploratory specification. The treatment question crosswalk is now confirmed from both archived questionnaires; the novelty review and final estimand freeze remain open. Do not label a model confirmatory until the analysis plan is frozen with the prior data inspection disclosed.

## Question and data

Does visual imagery add a conditional association with current neurological/psychiatric treatment status after accounting for the common nonvisual imagery profile, age, and recorded sex/gender? Run Studies 1 and 2 separately. The Study 2 diagnosed-or-strongly-suspected NDD outcome is a separate secondary analysis, not an autism outcome.

Source: New et al. (2026), OSF 2bdn6. Apply `nbact >= 3`; the contract requires N=949 and N=1,003. Keep the source rows in memory. Never save IDs, open text, comments, or participant-level transformed data. The treatment outcome is the confirmed item “Are you currently receiving treatment for a neurologic or psychiatric condition?” with No/Yes responses; `diag2` is an open follow-up shown only after Yes and is excluded.

## Working estimand and model

For each study, fit a logistic model for source field `diag` using within-study z-scores for direct visual imagery and the common nonvisual modalities (sound, touch, motor, taste, smell, emotion, voice), age, and recorded sex/gender categories. Average the modality z-scores into the nonvisual and all-modality composites, then re-standardize each completed composite within study. The working effects are adjusted odds ratios and 95% intervals per predictor SD, not prevalence ratios and not causal effects. A separate general-imagery mean model is genuinely distinct. Common-imagery-shift and visual-minus-nonvisual coefficient contrasts are computed from the direct visual + nonvisual model; no general-plus-deviation regression is treated as independent robustness evidence.

Sensitivity checks: restriction to age 18–30 with missing ages excluded; Study 2 `isneurodev` outcome; and an explicit pooled study-by-imagery interaction. The ordinary logistic path uses the statsmodels-compatible White score sandwich; use Firth bias-reduced logistic regression when ordinary logistic regression is singular/separated. Do not change predictor coding to chase agreement.

### Exploratory threshold-versus-dose-response comparison

The source analysis script defines visual aphantasia as `image == 5` and visual hyperphantasia as `image >= 35`. The runner therefore fits a secondary categorical model with those two indicators and the middle visual range as the reference, conditional on the re-standardized nonvisual composite, age, and sex/gender. This asks whether the published extreme-phenotype framing adds information beyond a smooth continuous dose-response. It is exploratory because the public script and outcomes were inspected before this comparison was specified. Do not call the categorical model a causal threshold or select cut points from the observed treatment association.

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
