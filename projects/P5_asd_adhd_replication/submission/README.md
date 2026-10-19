# P5 submission preparation

Prepared 17 October 2026; restructured 18 October 2026 (registered replication plus an exploratory "where is the gap" section, main Tables 1-3, Figures 1-2, supplement Tables S1-S7 and Figure S1). Abstract, introduction and discussion drafted 18 October 2026. **Retargeted to MDPI Brain Sciences on 18 October 2026: see [brainsci/SUBMISSION_CHECKLIST.md](brainsci/SUBMISSION_CHECKLIST.md).** **Not ready to submit.** Previous drafts are in `../review/*_2026-10-17.md`.

The affiliation is Independent researcher. The author reports no ethics approval or exemption determination. This package does not invent either. The current journal guide could not be verified because access reached a CAPTCHA.

## Read first

- [Working manuscript](manuscript_working.md): editable Methods/Results, author-writing outlines for the abstract, introduction and discussion, limitations and incomplete declarations. Review PDF: `output/pdf/p5_submission_review.pdf` at the repository root; it includes the supplement and both figures.
- [Author confirmations](author_confirmations.md): contact, ethics documentation, source reuse, reviewer access to registration, declarations and human review. Includes an **unsent** inquiry draft.
- [Audit report](../review/submission_audit_2026-10-17.md): evidence, changes and remaining gates.
- [PDF cold read](../review/pdf_cold_read_2026-10-17.md): independent reading of the initial PDF and how the reporting gaps were addressed.
- [Cover letter draft](cover_letter_draft.md): incomplete author declarations; do not send unchanged.
- [Literature and novelty](literature_and_novelty.md) and [terminology](terminology.md): checked claims and reporting rules.

## Results and figures

- Main tables (generated, included in the manuscript): `table_main1_participants.md`, `table_main2_registered.md`, `table_main3_tails.md`.
- [Figure 1](figure1_overall_imagery.png): registered six-sense and exploratory five-sense overall differences, both datasets.
- [Figure 2](figure2_where_the_gap_sits.png): exploratory. Difference at each percentile, and absent-imagery rates by sense, both datasets.
- [Supplement](supplement.md): Tables S1-S7 (S7 lists every exploratory analysis run) and Figure S1 (per-sense descriptive effects).
- CSVs: `table0_participants_outcomes.csv`, `table1_primary.csv`, `table2_secondary.csv`, `supplement_registered_estimates.csv`.

Registered: all three primary tests supported; no secondary test survives Holm correction. Exploratory: the difference sits in the low tail (absent imagery in at least one sense 20.0% vs 6.5%; no difference among people with imagery in every sense), in both datasets, with one exception in Arnold's AQ 26+ subset.

## Reproduce

Run from the repository root with the source archives already staged locally. These scripts write aggregates only; do not redistribute the input archives, identifiers or free text.

```sh
python3 -m pytest -q
Rscript -e 'install.packages("brglm2", lib="/private/tmp/p5-r-library", repos="https://cloud.r-project.org")'
python3 scripts/p5_submission_audit.py --r-library /private/tmp/p5-r-library
python3 scripts/p5_provenance_audit.py
python3 scripts/p5_five_sense_check.py
python3 scripts/p5_descriptive_tables.py
MPLCONFIGDIR=/private/tmp/p5-matplotlib python3 scripts/build_p5_submission.py
PYTHONPATH=/private/tmp/p5-pylib python3 scripts/render_p5_review.py   # needs reportlab: python3 -m pip install --target /private/tmp/p5-pylib reportlab
```

Create the task-specific R library directory before installation. The PDF renderer requires reportlab, available in the bundled workspace Python; the base interpreter may not have it. The audit used brglm2 1.1.1 with R 4.6.1. `requirements-lock.txt` records the analysis environment; audit JSON additionally records versions. The R library under `/private/tmp` is temporary and may need reinstalling later.

The audit reproduces P5 in `review/validation/reproduced/`, independently reconstructs the primary OLS regression, checks Holm correction and compares five Firth fits with R. It checks that the original `runs/latest/P5` files and frozen plan remain unchanged. Do not run the old freeze command again.

## Final author work

Write and approve the abstract/introduction/discussion from the outlines. Supply an email, funding/conflict/contribution statements and actual AI-use/oversight disclosure. Resolve the journal's ethics-documentation requirements, source reuse terms and Arnold comparison-cohort methods/independence. Verify the live journal requirements and provide reviewer access to the registration. Read and explain the analysis choices in the author-confirmations file; a human methods review remains advisable, especially for sparse-data Wald inference.

For the low-cost publication route, choose subscription publication rather than optional open access, after checking the journal's current terms. Check its current LLM-use disclosure policy before submitting. Once author text and source checks are complete, regenerate and cold-read the final submission PDF; the current review applies to a working copy.
