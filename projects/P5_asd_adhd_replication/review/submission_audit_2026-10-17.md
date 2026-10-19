# P5 submission audit - 17 October 2026

**Decision: working package prepared; not ready for submission.** The empirical contribution is a registered conceptual replication in another existing survey. The broad imagery association is supported; autism specificity and selective mean sensory deficits are not established. The registered crosswalk contains a substantive error that is now disclosed.

## Numerical and provenance checks completed

| Check | Evidence | Outcome |
|---|---|---|
| Frozen plan | SHA-256 ce102d64229b6a4efb2a7c646048f17c5ab338829f73bed4121bcc1deb147c14 | Preserved; production hash gate passes. |
| Registered estimates | Separate reproduction compared all 156 CSV rows, numeric and text fields | Exact reproduction, maximum absolute numeric difference 0. |
| Original run | Before/after SHA-256 fingerprints of all original p5_* files | Unchanged. |
| Primary continuous model | Independent comparison standardization, design construction and statsmodels OLS/HC3 with Student t inference | Coefficient, SE, CI and p value agree. |
| Firth fits | Five models compared with R brglm2 1.1.1 AS_mean | All reference fits converge; maximum absolute coefficient difference 3.75e-7, covariance and Wald inference agree within tolerance. |
| Secondary multiplicity | Independent statsmodels Holm adjustment | Matches registered correction; no secondary test passes .05. |
| Autism workbook linkage | Duplicate-aware multiset match of imagery scores, AQ total and age | All 327 code autism rows match; matched attention score 13. No participant IDs exported. |
| Measurement crosswalk | Workbook PSI-Q bodily-sensation item headings versus New motor prompts | Sixth components differ. Error documented without editing frozen plan. |
| Five-sense sensitivity | Specified in deviations log after registered results were known, before first sensitivity run | New -0.4349 SD, CI -0.6686 to -0.2012; Arnold -0.1992, CI -0.3775 to -0.0209. Explicitly exploratory. |
| Existing test suite | python3 -m pytest -q | 37 passed, 2 slow P8 tests skipped, 10 subtests passed. |
| PDF cold read | Fresh agent given only the initial PDF | Main contribution understood; reporting gaps identified and addressed as recorded in the companion report. |
| Expanded PDF review | PDF-only reader checked all 13 pages after reporting revisions | No numerical inconsistencies found; remaining layout/label/tolerance defects corrected in the final 14-page working copy. |
| Final PDF verification | Rendered all final pages, inspected tables/figures, checked text bounds and glyphs | No clipping, overlap, stray table headings or missing glyphs found. |

Machine-readable evidence is in `validation/numerical_validation.json`, `reference_firth.json`, `workbook_reconciliation.json`, `five_sense_check.json` and `participant_descriptives.json`. The converged R reference emitted no warnings. Its default-start attempt had failed on the sparse category; the final run used an intercept-only start and damped steps. Original optimizer precision warnings are retained, not erased.

## Reporting changes

Prepared an editable working manuscript, supplement, two figures, three result/descriptive tables plus the complete registered CSV, cover-letter draft, terminology list and author-confirmation list. Kept abstract/introduction/discussion as author-writing outlines in accordance with the author's instructions. Included all five secondary tests and the ADHD estimate/CI. Distinguished mean-score effects, floor frequencies, one-sided registered p values and two-sided exploratory inference.

Checked primary-source metadata and relevant findings for Arnold, New, King, Bouyer, Taylor and the PSI-Q instrument. This was a targeted audit with access limitations, not an exhaustive systematic review. New's published Methods establish Prolific reading-study recruitment, eligibility, attention-task meaning and the QMI + VocEmo instrument. Local data contain three retained ages above 30 despite the reported target eligibility; the registered age-restricted sensitivity is retained. King source reporting has inconsistent participant totals, so the manuscript does not repeat an unverified exact count.

Corrected stale non-frozen documentation: the Arnold workbook has 237 header columns and 414 nonheader rows including summaries, not 414 verified participant responses with 233 columns. The source-linked autism mapping is resolved; comparison recruitment is not.

## Remaining gates

1. Author writing and understanding: finish the prose outlines and check every substantive claim, model choice and inference. Numerical agreement is not a human statistical review. Sparse-data Wald interval coverage is not validated by matching another implementation.
2. Ethics documentation: author reports no approval/exemption determination. The source consent allows future research, but no exemption or journal acceptance of that situation has been established. An unsent inquiry draft is provided.
3. Source terms and comparison provenance: UQ reuse agreement still unread; Arnold comparison recruitment, administered PSI-Q details, attention checks and possible participant overlap need verification. Avoid claiming an independent or exact replication.
4. Author declarations: email, funding, competing interests, contributions, acknowledgements and accurate AI-use/oversight statement remain incomplete. Independent researcher is confirmed.
5. Submission mechanics: live C&C guide access reached CAPTCHA; exact limits, anonymization and required files remain unverified. Verify OSF embargo/reviewer access and final LLM-use policy before submitting.

No registration access settings were changed, source archives redistributed, correspondence sent or journal submission made.
