# Fresh PDF-only cold read - 18 October 2026

A fresh subagent read only `output/pdf/p5_submission_review.pdf` (18-page full draft, after the abstract, introduction and discussion were written) as a C&C reviewer. Pre-review manuscript: `manuscript_pre_coldread_2026-10-18.md`.

## Reader's verdict

Main contribution was easy to state. The registered replication is solid and clearly reported. Not ready as is: the framing sold the exploratory "minority with absent imagery" result more strongly than the design allows, and administrative items (ethics, AI disclosure, placeholders) are open.

## Main findings and what was done

| Finding | Action |
|---|---|
| Abstract, intro and conclusion centred on the exploratory result | Abstract and conclusion now lead with the registered replication and its null secondary tests; exploratory result framed as needing a registered test. |
| "Did not differ" among people with imagery in every sense rests on selection on the outcome | Methods now say this analysis cannot by itself show the groups are alike; claim removed from the abstract. |
| Subset versus a more spread-out distribution not tested | New exploratory shift benchmark (Table 4; `scripts/p5_shift_benchmark.py`; deviations log). New et al.: neither model reproduces the pattern. Arnold et al.: shift + stretch accounts for most of it. Text, abstract and discussion now say so. |
| Arnold et al.'s data presented as an independent check | Intro and discussion now say these data shaped the predictions and were analysed before registration, so they are a consistency check only. |
| Overreach about other studies' mean differences | Removed; replaced with a concrete suggestion (compare absent-imagery shares with a whole-group benchmark) and acknowledgement that King and Arnold already report cut-off rates. |
| S7 results that cut against the story not discussed (AQ without imagination items; Dance, Ward & Simner correlations) | Both discussed in the Discussion; S7 now explains why each exploratory analysis was run. |
| Undefined or unmotivated items: Prolific, Holm, Wald intervals, one-sided tests, 6 of 9 scales, absent-imagery threshold, ages to 32, sex composition, Study 2 vs file name, deviations log not provided | Each defined or motivated in place; female % added to Table 1; sex coding basis stated; Table S8 summarises deviations. |
| Two Dance 2021 papers ambiguous | Cited as Dance, Jaquiery et al. (2021) and Dance, Ward and Simner (2021). |
| Table 2 mixed p-value types; S2 CI excludes zero but "No" | Separate one-sided and Holm-adjusted columns; note explains unadjusted intervals. |
| Table 3 note wrong for first row; no Fisher p | Fixed. |
| Figure 2 caption did not say unadjusted; one comparison legend for two datasets; S1 legend overlap | Fixed. |
| Repetition (Bouyer point, -0.42 to -0.39, ADHD caveat), hedge stack, formulaic leads, "the author" vs "we" | Repeats removed, ADHD paragraph shortened, leads rewritten, "we" throughout. |
| Supplement contained shell commands and internal names | Commands moved to the repository; source-measure text rewritten. |

## Not changed

- Working-copy footer and bracketed declarations remain until the author supplies ethics, funding, competing interests, email and AI-use statement.
- Firth Wald intervals kept as registered; limitation stated.
- A second cold read should be run after the declarations are complete.
