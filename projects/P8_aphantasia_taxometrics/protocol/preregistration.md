# Is aphantasia a separate group or the low end of a continuum? A taxometric analysis of visual and multisensory imagery

This is the full analysis plan. It will be registered on OSF (Secondary Data Preregistration template), and the registration will quote this file's SHA-256 fingerprint. The analysis code checks the fingerprint and will not run if this file has changed.

- **Author:** Ivan Habib (ORCID https://orcid.org/0009-0002-7812-0371)
- **Drafted:** 11 October 2026
- **Code:** https://github.com/i-habib/aphantasia, files `scripts/p8_taxometrics.R` and `src/aphantasia/p8.py`. Run with `python3 scripts/run_available.py --project P8 --preregistration-url <URL>`.

---

## 1. Background

People with aphantasia report little or no visual imagery. Researchers disagree about what kind of difference this is. One view treats aphantasia as a condition: a separate group of people who differ in kind from everyone else. The other treats it as the low end of a smooth continuum of imagery vividness, so any cut-off is a convention (Blomkvist & Marks, 2023). Studies use different cut-offs on the Vividness of Visual Imagery Questionnaire (VVIQ), most often a total of 32 or below, or 23 or below. Monzel et al. (2026) compared five such cut-offs in 35,467 people and recommended separating "core" aphantasia from weaker imagery ("hypophantasia"). Neither cut-off comparisons nor cluster analyses can settle whether the groups are real, because a cut-off or a clustering method will produce groups whatever the underlying structure is.

Taxometric analysis was built for this question (Meehl, 1995; Ruscio, Haslam & Ruscio, 2006). It asks whether the way several measures relate to each other matches what you would see if the data came from two separate groups (a *taxon* and everyone else) or from one continuum. It compares the real data with simulated data of both kinds that copy the real data's distributions and correlations. A meta-analysis of 183 taxometric studies found that most psychological differences are continuous, with a few possible exceptions, including autism (Haslam, McGrath, Viechtbauer & Kuppens, 2020). We found no taxometric study of aphantasia.

We ask:

1. Is low visual imagery, as measured by the VVIQ, a separate group or a continuum?
2. If it is a separate group, how large is that group?
3. Is low imagery across all the senses a separate group or a continuum?

The answer matters for how aphantasia should be studied. If it is a separate group, studies should identify its members and compare them with everyone else. If it is a continuum, studies should treat imagery as a score and stop relying on cut-offs.

## 2. Hypotheses

We test two competing descriptions and make no prediction about which will fit better:

- **Separate group:** the data fit simulated two-group data better than simulated continuous data.
- **Continuum:** the data fit simulated continuous data better.

The main question is (1), in the main sample (§3.1). Questions (2) and (3) are secondary.

## 3. Data

### 3.1 Main sample: Aphantasia Network (Monzel et al., 2026)

- VVIQ answers from 35,467 people collected online by the Aphantasia Network between July and November 2024 and shared by Monzel et al. (2026) at OSF project 8fn9v (view-only link given in their paper). File `Total_data_set.Rdata`, SHA-256 `2f601bff1328d7ae87832d67e689588c31fa4380177ec6f7c260b243dee5a5e6`.
- Each of the 16 VVIQ items is answered from 1 ("no image at all, I only know that I am thinking of the object") to 5 ("perfectly clear and as vivid as normal vision"). The total runs from 16 to 80.
- The questionnaire was hosted on an aphantasia website, so people with weak imagery are heavily over-represented. Monzel et al. say so themselves. §3.2 and §6.3 deal with this.

### 3.2 Population-matched subsample of the main sample

Over-representing one end of a continuum can make it look like two groups. To check this, we draw a subsample of the main sample whose VVIQ totals follow the distribution in an unselected sample: the pooled Dance et al. (2022) data (§3.3). We split VVIQ totals into 16 bands of 4 points (16–19, 20–23, …, 76–79, with 80 added to the top band). We then sample people at random, without replacement, from each band so that the proportions match the Dance et al. proportions. The subsample is the largest one possible under that rule. The random seed is fixed in the code (20261011).

### 3.3 Unselected sample: Dance et al. (2022)

- VVIQ answers from 1,004 people in two samples (university students and Amazon Mechanical Turk workers) who were not recruited for their imagery. OSF project mxyv9, file `AphantasiaPrevalenceData.sav`, SHA-256 `43512d3962d933ceadefd660c3be92dfe62be5528bb11fb35d8777c006ad9633`.
- Items are scored as in §3.1 (the file's readme defines aphantasia as a total of 16–32).
- Only about 4% of people in samples like this have a VVIQ total of 32 or below. Taxometric analysis has little power when the possible group is that small, so we expect this sample to be inconclusive and treat it as secondary.

### 3.4 Multisensory sample: New et al. (2026), both surveys

- Imagery scores for eight senses from two online surveys of adults recruited through Prolific (New et al., 2026; OSF project 2bdn6). Files `Analyses/Exp1.1003.txt` (SHA-256 `08e7f1411491e7fe976fba106987a242a6067cec187a5efae212d2a290cc20dd`) and `Analyses/Exp3.1020.txt` (SHA-256 `f9468859aca11bd6da673edd5cf774a01c5699924e2104bc703687e541fbb1f2`), inside the OSF archive with SHA-256 `6abd7a36b3e89c20936c295f5a8569aea545b49562f8ef388a057a5e75462bdd`.
- Study 1 has 1,003 people in its file. Study 2 has 1,003 after New et al.'s attention check.
- Each sense score is the sum of five 1–7 ratings (5 to 35). The eight senses in both surveys are sight (`image`), sound, touch, movement (`motor`), taste, smell, emotion and voice. Study 2's inner-body sense is left out because Study 1 did not measure it.
- We apply New et al.'s attention-check rule (`nbact` of 3 or more) to both surveys.

### 3.5 Who is included

In every sample we remove people with any missing item and, in the main sample, repeat entries with the same `subject_id` (we keep the first). We remove no other outliers. The code stops if any answer is outside the questionnaire's range.

## 4. Variables

### 4.1 Indicators

Taxometric analysis needs several separate measures of the same thing, called *indicators*.

- **VVIQ samples (§3.1–3.3).** The VVIQ has four scenes with four items each: a relative or friend (items 1–4), a rising sun (5–8), a shop (9–12) and a country scene (13–16). Each scene's sum (4 to 20) is one indicator, giving four indicators.
- **Multisensory sample (§3.4).** Each of the eight sense scores is one indicator. Scores are converted to z-scores within each survey before the two surveys are combined.

All indicators are reversed so that higher scores mean *weaker* imagery, because the software expects the possible group to score high.

### 4.2 Provisional group membership

The software needs a provisional split into "possible group" and "everyone else" to check the indicators and to build the simulated two-group data. We follow the package's recommended order:

1. Estimate the size of the possible group from a CCFI profile (§5.2), using the indicators only.
2. Assign the people with the highest summed indicator scores to the possible group, in that proportion (the base-rate method, `ClassifyCases`).

The profile only gives a meaningful group size if the data look like two groups. So if the profile's CCFI is below 0.55, we instead use the proportion with a VVIQ total of 32 or below (VVIQ samples), or with at least one sense at the lowest possible score (multisensory sample).

## 5. Analysis

All analyses use R with the RTaxometrics package, version 3.2.1 (Ruscio & Wang, 2023), with its default settings unless stated.

### 5.1 Checking the data

Before each analysis we run `CheckData` and report what it reports for each sample:
- how well each indicator separates the provisional groups (Cohen's d; 1.25 or more is the usual guide);
- correlations between indicators within each provisional group (0.30 or less is the usual guide);
- skew;
- sample size.

We run the analysis whatever these checks show, but if most indicators separate the groups by less than d = 1.25, we say the result is less trustworthy.

### 5.2 Main analysis

For each sample we run three taxometric procedures, MAMBAC, MAXEIG and L-Mode, with `RunTaxometrics`. Each procedure draws a curve from the real data. The package also draws the same curves for 100 simulated two-group data sets and 100 simulated continuous data sets, both built to copy the real indicators' distributions and correlations.

The result is the **comparison curve fit index (CCFI)**. It runs from 0 to 1: values near 1 mean the real curves look more like the two-group simulations, and values near 0 mean they look more like the continuous ones. We use the package's average across the three procedures (curves averaged before the CCFI is calculated; Ruscio, Carney, Dever, Pliskin & Wang, 2018).

We also run `RunCCFIProfile`, which repeats the comparison with simulated two-group data at 39 group sizes from 2.5% to 97.5%. If the data look like two groups, the group size with the highest CCFI is our estimate of how large the group is. This is slow (about 1.5 hours for 5,000 people), so in samples larger than 5,000 the profile uses a random subsample of 5,000 (seed 20261011). All other analyses use the whole sample.

Settings: the package defaults (100,000-case comparison populations, 100 comparison samples of each kind, 50 cuts for MAMBAC, 50 windows with 90% overlap for MAXEIG), with seed 20261011.

### 5.3 Robustness checks

In the main sample:

1. **Population-matched subsample** (§3.2).
2. **Eight indicators instead of four:** pairs of items (1–2, 3–4, …, 15–16).
3. **Provisional groups from the VVIQ cut-offs** of 32 and of 23 instead of the CCFI profile.
4. **Two random halves**, analysed separately, to see whether the result repeats.
5. **A wider "unclear" zone** (§6), from 0.40 to 0.60.

Checks 2 and 4 use the same provisional group size as the main analysis. Check 1 estimates its own (§4.2).

### 5.4 Secondary samples

The same analysis (§5.1–5.2) in the Dance et al. sample (§3.3) and the multisensory sample (§3.4).

## 6. How we will read the results

| Average CCFI | What it means |
|---|---|
| 0.55 or above | The data look more like two separate groups |
| 0.45 or below | The data look more like one continuum |
| Between 0.45 and 0.55 | Unclear |

Across samples:

| Main sample | Population-matched subsample | Reading |
|---|---|---|
| Two groups | Two groups | Aphantasia looks like a separate group, and this is not just because of how the main sample was collected. |
| Two groups | Continuum or unclear | The two-group result may come from the website sample over-representing weak imagery. We will not conclude that aphantasia is a separate group. |
| Continuum | any | Low visual imagery looks like the low end of a continuum, and VVIQ cut-offs are conventions rather than boundaries between kinds of people. |
| Unclear | any | The data cannot tell the two apart. |

We read the Dance et al. sample and the multisensory sample in the same way, but give an unclear result there little weight, because the possible group is expected to be small (§3.3).

## 7. What we already know about the data

- **Main sample:** we have read Monzel et al. (2026), which reports how many people fall below each cut-off and that the VVIQ items behave as a single scale. We have looked only at the file's column names and number of rows. We have not looked at any scores.
- **Dance et al. sample:** we have looked only at the column names, the number of rows and the readme.
- **Multisensory sample:** we have used New et al.'s data in earlier work, including how often people score at the lowest possible level in each sense, and how imagery differs between people who did or did not report autism or ADHD (a separate preregistered study, OSF https://osf.io/87udm). We have not run any taxometric or mixture analysis on it.
- The analysis code will not run until this plan is registered. Its tests use only simulated data.

## 8. Sample size

The samples are fixed. Taxometric analysis works best with at least 300 people and a possible group making up at least about 10% of the sample. The main sample is very large, and people with weak imagery are common in it. The population-matched subsample and the Dance et al. sample will have far fewer people with weak imagery, which is why we expect less clear results there.

## 9. Software

R 4.5 or later (we use 4.6.1) with RTaxometrics 3.2.1, jsonlite (to write results) and the `foreign` package, which comes with R and is used to read the SPSS file. A short Python step (`src/aphantasia/p8.py`) checks the registration before calling R. The code writes only summary results and the package's graphs, never individual rows. Random seeds are fixed in the code.

## 10. Changes to the plan

Any change is logged in `projects/P8_aphantasia_taxometrics/protocol/deviations.md` with the date, the reason, whether we had seen any results, and how it affects the conclusions. Changes are reported in the paper. This file is not edited after registration.

## 11. Planned outputs

- Flow of participants for each sample.
- Data checks (§5.1) for each sample.
- Average CCFI and the CCFI for each procedure, for each sample and robustness check.
- Figure: the package's graph sheet for the main sample, showing the real curves against the simulated two-group and continuous curves.
- If the data look like two groups: the estimated group size and how it compares with the VVIQ cut-offs.
- Limitations: the main sample came from an aphantasia website; the VVIQ is a self-report questionnaire; the four scene scores share a format and may correlate for reasons other than imagery; the secondary samples have small possible groups.

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
