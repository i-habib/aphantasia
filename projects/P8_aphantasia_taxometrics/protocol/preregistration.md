# Is aphantasia a separate group or the low end of a continuum? A taxometric analysis of visual and multisensory imagery

This is the full analysis plan. It will be registered on OSF (Secondary Data Preregistration template), and the registration will quote this file's SHA-256 fingerprint. The analysis code checks the fingerprint and will not run if this file has changed.

- **Author:** Ivan Habib (ORCID https://orcid.org/0009-0002-7812-0371)
- **Drafted:** 11 October 2026
- **Code:** https://github.com/i-habib/aphantasia, files `scripts/p8_taxometrics.R` and `src/aphantasia/p8.py`. Run with `python3 scripts/run_available.py --project P8 --preregistration-url <URL>`.

---

## 1. Background

People with aphantasia report little or no visual imagery. Researchers disagree about what kind of difference this is. One view treats aphantasia as a condition: a separate group of people who differ in kind from everyone else. The other treats it as the low end of a smooth continuum of imagery vividness, so any cut-off is a convention (Blomkvist & Marks, 2023). Studies use different cut-offs on the Vividness of Visual Imagery Questionnaire (VVIQ), most often a total of 32 or below, or 23 or below. Monzel et al. (2026) compared five ways of defining aphantasia from VVIQ answers in 35,467 people, and recommended telling "core" aphantasia apart from weak imagery ("hypophantasia"). Neither cut-offs nor cluster analyses can show whether such groups are real, because both produce groups whatever the underlying structure is.

Taxometric analysis was built for this question (Meehl, 1995; Ruscio, Haslam & Ruscio, 2006). In this plan, a **taxon** means a separate group of people who differ in kind from everyone else. The analysis asks whether the way several measures of the same thing relate to each other looks more like data from a taxon plus everyone else, or like data from one continuum. It does this by comparing the real data with simulated data of both kinds. A meta-analysis of 183 taxometric studies found that most psychological differences are continuous, with a few possible exceptions, one of which is autism (Haslam, McGrath, Viechtbauer & Kuppens, 2020). We found no taxometric study of aphantasia.

We ask:

1. Is low visual imagery, as measured by the VVIQ, a taxon or a continuum?
2. If it is a taxon, how large is it?
3. Is low imagery across several senses a taxon or a continuum?

The answer matters for how aphantasia should be studied. If it is a taxon, studies should identify its members and compare them with everyone else. If it is a continuum, studies should treat imagery as a score and rely less on cut-offs.

## 2. Hypotheses

We test two competing descriptions and make no prediction about which will fit better:

- **Taxon:** the data fit the simulated taxon data better than the simulated continuous data.
- **Continuum:** the data fit the simulated continuous data better.

The main question is (1), in the main sample (§3.1). Questions (2) and (3) are secondary.

## 3. Data

### 3.1 Main sample: Aphantasia Network (Monzel et al., 2026)

- VVIQ answers from 35,467 people, collected online by the Aphantasia Network between July and November 2024 and shared by Monzel et al. (2026) at OSF project 8fn9v (view-only link given in their paper). Original file `Total_data_set.Rdata`, stored locally as `data_raw/monzel2026_total_data_set.Rdata`, SHA-256 `2f601bff1328d7ae87832d67e689588c31fa4380177ec6f7c260b243dee5a5e6`.
- Each of the 16 VVIQ items is answered from 1 ("no image at all, I only know that I am thinking of the object") to 5 ("perfectly clear and as vivid as normal vision"). The total runs from 16 to 80.
- The questionnaire was hosted on an aphantasia website, so people with weak imagery are heavily over-represented. Monzel et al. say so themselves. §3.2 and §5.4 deal with this.

### 3.2 Population-matched subsample of the main sample

Over-representing one end of a continuum can make it look like two groups. To check this, we draw a subsample of the main sample whose VVIQ totals follow the distribution in an unselected sample, the pooled Dance et al. (2022) data (§3.3). We split VVIQ totals into 16 bands of 4 points (16–19, 20–23, …, 76–79, with 80 added to the top band). We then sample people at random, without replacement, from each band, so that the band proportions match the Dance et al. proportions. The subsample is the largest one possible under that rule (seed 20261011). Bands with nobody in the Dance et al. data get nobody in the subsample.

This check can only weaken a taxon result, not support one. After matching, only about 4% of the subsample will have a total of 32 or below, which is below the size taxometric analysis handles well (§8), and the people at the very bottom of the scale may drop out entirely. §5.4 tests whether the check could detect a taxon at all.

### 3.3 Unselected sample: Dance et al. (2022)

- VVIQ answers from 1,004 people in two samples (university students and Amazon Mechanical Turk workers) who were not recruited for their imagery. OSF project mxyv9, file `AphantasiaPrevalenceData.sav`, stored locally as `data_raw/dance2021_prevalence.sav`, SHA-256 `43512d3962d933ceadefd660c3be92dfe62be5528bb11fb35d8777c006ad9633`. Items are scored as in §3.1.
- Only about 4% of people in samples like this have a VVIQ total of 32 or below, so we expect this sample to be inconclusive and treat it as secondary.

### 3.4 Multisensory sample: New et al. (2026), both surveys

- Imagery scores for eight senses from two online surveys of adults recruited through Prolific (New et al., 2026; OSF project 2bdn6). Files `Analyses/Exp1.1003.txt` (SHA-256 `08e7f1411491e7fe976fba106987a242a6067cec187a5efae212d2a290cc20dd`) and `Analyses/Exp3.1020.txt` (SHA-256 `f9468859aca11bd6da673edd5cf774a01c5699924e2104bc703687e541fbb1f2`), inside the OSF archive stored locally as `2bdn6-osfstorage-archive.zip` (SHA-256 `6abd7a36b3e89c20936c295f5a8569aea545b49562f8ef388a057a5e75462bdd`).
- Each sense score is the sum of five 1–7 ratings (5 to 35). The eight senses in both surveys are sight (`image`), sound, touch, movement (`motor`), taste, smell, emotion and voice. Study 2's inner-body sense is left out because Study 1 did not measure it.
- Both surveys included attention checks. We keep people who passed at least 3, as New et al. did (the `nbact` column). Study 2 then has 1,003 people, as New et al. report. We report the number for Study 1.

### 3.5 Who is included

In every sample we remove people with any missing item and, in the main sample, repeat entries with the same `subject_id` (we keep the first). We remove no other outliers. The code stops if any answer is outside the questionnaire's range, if a needed column is missing, or if a data file does not match the SHA-256 given above.

## 4. Variables

### 4.1 Indicators

Taxometric analysis needs several separate measures of the same thing, called *indicators*.

- **VVIQ samples (§3.1–3.3).** The VVIQ has four scenes with four items each: a relative or friend (items 1–4), a rising sun (5–8), a shop (9–12) and a country scene (13–16). Each scene's sum (4 to 20) is one indicator, giving four indicators.
- **Multisensory sample (§3.4).** Each of the eight sense scores is one indicator. Scores are converted to z-scores within each survey before the two surveys are combined.

All indicators are reversed so that higher scores mean weaker imagery, because the software expects taxon members to score high.

### 4.2 Provisional taxon

The software needs a provisional split into "provisional taxon" and "everyone else", both to check the indicators and to build the simulated taxon data. The split puts the people with the highest summed indicator scores into the provisional taxon, in a chosen proportion (the package's `ClassifyCases` function). If the cut falls inside a block of people with identical scores, the whole block goes to one side, so the share actually used can differ from the one asked for. We report both.

The proportion we ask for is:

- **VVIQ samples:** the share with a VVIQ total of 32 or below, the most common cut-off.
- **Multisensory sample:** the share with at least four of the eight senses at the lowest possible score.

We fix the proportion this way, rather than choosing the one that fits best, because choosing the best-fitting proportion would push the result towards "taxon". The CCFI profile (§5.2) is reported alongside as a second, independent estimate. If a provisional taxon would hold fewer than 30 people, that analysis is not run, and we report it as not possible.

## 5. Analysis

All analyses use R with the RTaxometrics package, version 3.2.1 (Ruscio & Wang, 2023), with its default settings unless stated.

### 5.1 Checking the data

For each analysis we report:

- how well each indicator separates the provisional taxon from everyone else (Cohen's d; 1.25 or more is the usual guide);
- the full table of correlations between indicators within each group (0.30 or less is the usual guide), noting any that cannot be calculated because everyone in a group has the same score;
- skew, sample size, and the package's own data check (`CheckData`).

We run every analysis whatever these checks show. We call a result **lower-trust** if most indicators separate the groups by less than d = 1.25, or if the average correlation within either group is above 0.30. The four scene scores are parts of one questionnaire, so we expect high within-group correlations. This is a known weakness of the design.

### 5.2 Main analysis

We run three standard taxometric procedures with `RunTaxometrics`:

- **MAMBAC** sorts people on one indicator and, at many cut points along it, compares the average of another indicator above and below the cut. With a taxon, the difference peaks near the cut that best separates the groups. With a continuum, it tends to be highest at the ends.
- **MAXEIG** sorts people on one indicator and, in overlapping slices along it, measures how strongly the other indicators go together. With a taxon this peaks where the two groups are mixed. With a continuum it stays flatter.
- **L-Mode** looks at the distribution of people's scores on what the indicators share. A taxon tends to give two peaks, a continuum one.

Each procedure draws curves from the real data. The package draws the same curves for 100 simulated taxon data sets and 100 simulated continuous data sets, both built to copy the real indicators' distributions and correlations. The result is the **comparison curve fit index (CCFI)**. It runs from 0 to 1. Values near 1 mean the real curves look more like the simulated taxon curves, and values near 0 mean they look more like the continuous ones. We use the package's average across the three procedures (Ruscio, Carney, Dever, Pliskin & Wang, 2018) and report each procedure's value.

We also run a **CCFI profile** (`RunCCFIProfile`). It repeats the comparison with simulated taxon data at 39 taxon sizes from 2.5% to 97.5%. It reports a summary CCFI (a weighted average across the 39 sizes, giving most weight to sizes near the best-fitting one) and an estimated taxon size (where a smoothed version of the profile peaks). The profile is slow, about 1.5 hours for 5,000 people, so in samples larger than 5,000 it uses a random subsample of 5,000 (seed 20261011).

Settings: the package defaults (100,000-case comparison populations, 100 comparison samples of each kind, 50 cut points for MAMBAC, 50 slices with 90% overlap for MAXEIG), seed 20261011.

### 5.3 Robustness checks

In the main sample:

1. **Population-matched subsample** (§3.2), with its own provisional taxon share and its own CCFI profile.
2. **Eight indicators instead of four:** pairs of items (1–2, 3–4, …, 15–16).
3. **A different provisional taxon share:** the share at or below 23, and, if the profile reads as a taxon, the profile's estimated size.
4. **Two random halves** (split with seed 20261011), each with its own share at or below 32.
5. **A wider "unclear" zone** (§6), from 0.40 to 0.60, applied to the main analysis only.

### 5.4 Simulation checks

Two checks use simulated data built from features of the real data, run through exactly the same steps as the main analysis:

- **Floor check.** Many website respondents give the lowest answer to every item, so they sit at the floor on all four scene scores at once. The package's simulated continuous data copy each indicator's floor separately, but not this shared floor, while its simulated taxon data do. A continuum with a floor could therefore look like a taxon. To test this, we simulate a continuum with the same floor: one normally distributed underlying factor, each item cut into five answers so that the answer proportions match the real item, and the strength of the factor set so the simulated items correlate as strongly on average as the real ones. It has the same number of people as the main sample.
- **Detectability check for the matched subsample.** We simulate a known taxon with the matched subsample's size, provisional taxon share, average indicator separation and average within-group correlations (`CreateData`). If the analysis cannot detect that taxon, the matched subsample cannot tell us anything either way.

### 5.5 Secondary samples

The same analysis (§5.1–5.2, with the CCFI profile) in the Dance et al. sample (§3.3) and the multisensory sample (§3.4).

## 6. How we will read the results

**One analysis.** For each analysis, the average CCFI reads as:

| Average CCFI | Reading |
|---|---|
| 0.55 or above | Taxon |
| 0.45 or below | Continuum |
| Between 0.45 and 0.55 | Unclear |

**The main analysis** reads as taxon only if both the main CCFI and the profile's summary CCFI read as taxon. It reads as continuum only if both read as continuum. Otherwise it is unclear.

**Conclusion for question 1.** We start from the main analysis and apply these rules in order:

| If | Then the conclusion is |
|---|---|
| The main analysis reads as taxon, and the simulated floored continuum also reads as taxon | We cannot tell a taxon apart from a floor effect. |
| The main analysis reads as taxon, but the two halves do not both read as taxon | Unclear. |
| The main analysis reads as taxon, the matched subsample reads as continuum, and the detectability check detects its simulated taxon | A taxon may exist, but the result could come from how the website sample was collected. |
| The main analysis reads as taxon, and none of the above applies | Low visual imagery looks like a taxon. |
| The main analysis reads as continuum | The VVIQ data give no support for a boundary between people with and without aphantasia. |
| The main analysis is unclear | The data cannot tell the two apart. |

We also report, without changing the conclusion:

- whether the three procedures point in opposite directions (one at 0.55 or above and another at 0.45 or below);
- whether the result is lower-trust (§5.1);
- how robustness checks 2, 3 and 5 compare with the main result.

**Question 2.** If the conclusion is that low visual imagery looks like a taxon, its estimated size is the CCFI profile's estimate in the main sample. We compare it with the shares at or below 32 and 23.

**Question 3 and the Dance et al. sample** are read with the one-analysis table. In both, the provisional taxon is expected to be small (§3.3, §8), so an unclear result there tells us little.

## 7. What we already know about the data

- **Main sample:** we have read Monzel et al. (2026), which reports how many people fall below each cut-off and that the VVIQ items behave as a single scale. We have looked at the file's column names and number of rows, and at nothing else.
- **Dance et al. sample:** we have looked at the column names, the number of rows and the readme.
- **Multisensory sample:** we have used New et al.'s data in earlier work. That includes how often people score at the lowest possible level in each sense, and how imagery differs between people who did or did not report autism or ADHD (a separate preregistered study, OSF https://osf.io/87udm). We have not run any taxometric or mixture analysis on it.
- The analysis code will not run until this plan is registered. Its tests use only simulated data.

## 8. Sample size

The samples are fixed. Taxometric analysis works best with at least 300 people and a taxon making up at least about 10% of the sample. The main sample is very large, and people with weak imagery are common in it. The population-matched subsample, the Dance et al. sample and the multisensory sample will have far fewer such people, so we expect less clear results there.

## 9. Software

R 4.5 or later (we use 4.6.1) with RTaxometrics 3.2.1, jsonlite (to write results) and the `foreign` package (comes with R; reads the SPSS file). A short Python step (`src/aphantasia/p8.py`) checks the registration before calling R. The code writes only summary results and the package's graphs, never individual rows. A full run takes several hours.

## 10. Changes to the plan

Any change is logged in `projects/P8_aphantasia_taxometrics/protocol/deviations.md` with the date, the reason, whether we had seen any results, and how it affects the conclusions. Changes are reported in the paper. This file is not edited after registration.

## 11. Planned outputs

- Flow of participants for each sample.
- How many people are at the floor: a VVIQ total of 16, and each scene score at its lowest, in each VVIQ sample.
- Data checks (§5.1) for each analysis.
- The average CCFI, each procedure's CCFI and the CCFI profile, for each analysis.
- Figure: the package's graph sheet for the main analysis, showing the real curves against the simulated taxon and continuous curves.
- The conclusion for question 1 (§6), and, if it is a taxon, its estimated size.
- Limitations: the main sample came from an aphantasia website; the VVIQ is a self-report questionnaire; the four scene scores are parts of one questionnaire and share its format, which raises their correlations; the matched, Dance et al. and multisensory samples have small provisional taxa.

## References

- Blomkvist, A., & Marks, D. F. (2023). Defining and "diagnosing" aphantasia: Condition or individual difference? *Cortex*, 169, 220–234. https://doi.org/10.1016/j.cortex.2023.09.004
- Dance, C. J., Ipser, A., & Simner, J. (2022). The prevalence of aphantasia (imagery weakness) in the general population. *Consciousness and Cognition*, 97, 103243. https://doi.org/10.1016/j.concog.2021.103243. Data: OSF mxyv9.
- Haslam, N., McGrath, M. J., Viechtbauer, W., & Kuppens, P. (2020). Dimensions over categories: A meta-analysis of taxometric research. *Psychological Medicine*. https://doi.org/10.1017/S003329172000183X
- Meehl, P. E. (1995). Bootstraps taxometrics: Solving the classification problem in psychopathology. *American Psychologist*, 50, 266–275.
- Monzel, M., Pickering, J. W., Condon, D. M., Beran, M. J., & Ebeyer, T. (2026). Reimagining the vividness of visual imagery questionnaire as a single item screener for aphantasia. *Consciousness and Cognition*, 142, 104061. https://doi.org/10.1016/j.concog.2026.104061
- New, B., Barra, J., Chauvin, A., Huson, M., Lœvenbruck, H., et al. (2026). Multimodal mental imagery profiles and the prevalence of aphantasia and hyperphantasia in the general population. *Cortex*, 201, 119–136. https://doi.org/10.1016/j.cortex.2026.04.019. Data: OSF 2bdn6.
- Ruscio, J., Carney, L. M., Dever, L., Pliskin, M., & Wang, S. B. (2018). Using the comparison curve fit index (CCFI) in taxometric analyses: Averaging curves, standard errors, and CCFI profiles. *Psychological Assessment*, 30(6), 744–754.
- Ruscio, J., Haslam, N., & Ruscio, A. M. (2006). *Introduction to the taxometric method: A practical guide*. Lawrence Erlbaum.
- Ruscio, J., & Wang, S. B. (2023). RTaxometrics: Taxometric analysis (R package version 3.2.1). https://CRAN.R-project.org/package=RTaxometrics
