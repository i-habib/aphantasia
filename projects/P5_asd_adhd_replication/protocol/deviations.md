# P5 deviations log

Record every departure from the frozen `preregistration.md` here. Do not edit the plan itself after freezing.

| Date | Section | Change | Reason | Results seen before change? | Effect on conclusions |
|---|---|---|---|---|---|
| 2026-10-10 | §6.6 | The run computed d33 as 0.139 SD, not the "about 0.12 SD" given in the plan. The method is unchanged: d33 comes from the standard error of Arnold et al.'s adjusted H1 estimate, computed by the registered code. | The plan's figure was an approximation written before the code ran on Arnold et al.'s data with the final covariate coding. | Yes; noticed when reading the registered run. | None. H1 was significant, so the small-telescopes rule was not needed. |
| 2026-10-10 | §6.1 | For H2a, H2b, S3 and their robustness checks, the standard logistic model could not be fitted and the code used Firth's corrected logistic regression, as the plan allows. | Planned fallback, triggered automatically. The cause is the three people with sex "Other": none of them had no imagery in sight, smell or taste (checked after the run), so the sex term perfectly predicts the outcome. | No; the code chose the method before producing estimates. | None expected. Reported as planned. |
| 2026-10-11 | §3.1 | Correction of a label, not of the data. The SHA-256 given for `Analyses/Exp3.1020.txt` (`6abd7a36…62bdd`) is the fingerprint of the OSF archive that contains the file. The file's own SHA-256 is `f9468859aca11bd6da673edd5cf774a01c5699924e2104bc703687e541fbb1f2`. | Found while writing a later plan. | Yes. | None; the data used are the same. |
