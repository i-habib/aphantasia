# Autism and weaker multisensory imagery: testing Arnold et al. (2026) in an independent sample, with ADHD for comparison

This is the full analysis plan. It is registered on OSF (Secondary Data Preregistration template), and the registration quotes this file's SHA-256 fingerprint. The analysis code checks the fingerprint and will not run if this file has changed.

- **Author:** Ivan Habib (ORCID https://orcid.org/0009-0002-7812-0371)
- **Drafted:** 27 September 2026; revised 1–10 October 2026
- **Registration:** on OSF under Ivan Habib's account; the registration's statistical-models answer quotes this file's SHA-256.
- **Code:** https://github.com/i-habib/aphantasia, file `src/aphantasia/p5.py`. Run with `python3 scripts/run_available.py --project P5 --preregistration-url <URL>`.

---

## 1. Background

Arnold et al. (2026, *Consciousness and Cognition* 143, 104085) surveyed 327 adults with a formal autism diagnosis and compared them with 327 people from an earlier survey. The autistic group reported less vivid imagery across the senses on average. They were not more likely to say they had no visual imagery, but they were more likely to say they could not imagine smells or tastes. Other studies disagree about whether autism goes with aphantasia (for example, Taylor et al., 2026, *Scientific Reports*). Arnold et al.'s findings have not been checked in a second sample.

New et al. (2026, *Cortex* 201, 119–136) ran two online surveys of imagery in eight senses. Their second survey ("Study 2", public on OSF as project 2bdn6) also asked people whether they had been diagnosed with, or strongly suspected they had, a neurodevelopmental condition, and if so which one. New et al. analysed only the combined any-condition group, not autism or ADHD separately.

We use New et al.'s second survey to ask two questions:

1. Do people who reported autism show Arnold et al.'s pattern: weaker imagery overall, and more often no smell or taste imagery?
2. If so, is this specific to autism, or do people who reported ADHD (without autism) show it too?

## 2. Hypotheses

**Groups.** The *autism group* is everyone who ticked autism, including those who also ticked ADHD. The *ADHD group* ticked ADHD but not autism. The *comparison group* said they had no neurodevelopmental condition.

**Main hypotheses** (directions taken from Arnold et al.):

- **H1.** The autism group has a lower overall imagery score than the comparison group, after adjusting for age and sex. The overall score is the average across the six senses both studies measured: sight, sound, smell, taste, touch and movement (§4.2).
- **H2a.** More people in the autism group have no smell imagery at all (the lowest possible score).
- **H2b.** The same for taste.

**Secondary hypotheses:**

- **S1.** The autism group's gap is bigger for smell and taste than for sight. We also test whether the gap differs across the six senses at all.
- **S2.** Whether the autism and ADHD groups differ in overall imagery. This tells us whether any effect is specific to autism. We make no prediction about direction.
- **S3.** Whether the autism group is more likely to have no visual imagery. Arnold et al. found no clear difference. We make no prediction and report the estimate.
- **S4.** Whether the ADHD group shows the S1 pattern (smell and taste gap versus sight gap). No prediction.

## 3. Data

### 3.1 Sources

- **Main data:** New et al. (2026), second survey, file `Analyses/Exp3.1020.txt` in OSF project 2bdn6. SHA-256 of our copy: `6abd7a36b3e89c20936c295f5a8569aea545b49562f8ef388a057a5e75462bdd`. Participants were adults recruited online, apparently through Prolific (the file includes Prolific IDs).
- **Comparison data:** Arnold et al.'s public analysis code, which contains their survey responses (UQ eSpace, DOI 10.48610/57f325b). SHA-256 of our copy: `48b3eaf7a9e3fbc97fb8db5d9e2d6306c3f8df2d9197d1ca55c61dfecf4394e3`. Used only to set the two studies side by side.

### 3.2 Who is included

- The file has 1,020 people. Keeping those with an attention-check score (`nbact`) of 3 or more, as New et al. did, leaves 1,003, the number they report. The code stops if this number does not come out at 1,003.
- Group sizes: comparison 749; autism 150 (46 of whom also ticked ADHD, 104 who did not); ADHD 84; other conditions only (such as dyslexia or dyspraxia) 20; answered Yes but ticked nothing 0.
- We leave out the 20 people with other conditions only. They belong in neither the comparison group nor the groups we are studying.
- We remove no outliers. The questionnaire limits scores to 5–35, so a value outside that range would mean a data error, and the code stops rather than dropping it.

### 3.3 Missing data

One person has no recorded age. They are left out of the analyses that adjust for age and kept in the simple descriptive ones. We do not fill in missing values, since this affects fewer than 0.1% of people. No imagery scores are missing; if any were, that person would have no overall score.

## 4. Variables

### 4.1 Groups

The neurodevelopmental question (questionnaire p. 3) read: *"Have you ever been diagnosed with, or strongly suspected to have, a neurodevelopmental disorder such as Autism Spectrum Disorder (ASD), Attention-Deficit/Hyperactivity Disorder (ADHD), or a learning disability?"* (No/Yes). People who answered Yes then ticked any that applied (p. 4): ASD, ADHD, dyslexia, dyscalculia, dysgraphia, language disorder, dyspraxia, other.

| Group | Who |
|---|---|
| Autism (`asd`) | Ticked ASD, with or without other conditions |
| ADHD (`adhd_only`) | Ticked ADHD, did not tick ASD |
| Other conditions only (`other_ndd_only`) | Left out |
| Comparison (`reference`) | Answered No |

Because the question combined diagnosis with strong suspicion, our autism group is people who reported *diagnosed or suspected* autism. Arnold et al. required a formal diagnosis. We will discuss this difference rather than try to adjust for it.

### 4.2 Imagery

Each sense has five questions rated 1–7, added up to a score from 5 to 35 (higher means more vivid). Matched to Arnold et al.'s six senses:

| Arnold et al. | New et al. field | Use |
|---|---|---|
| sight | `image` | overall score |
| sound | `sound` | overall score |
| smell | `smell` | overall score; H2a |
| taste | `taste` | overall score; H2b |
| touch | `touch` | overall score |
| movement | `motor` | overall score |
| (not measured) | `emotion`, `voice`, `intstate` | described only |

- **Rescaling.** Each sense's score is rescaled so the comparison group has an average of 0 and a standard deviation (SD) of 1. The overall score is the average of the six rescaled scores, rescaled again in the same way. A group difference of −0.2 therefore means that group scores 0.2 SD below the comparison group. Arnold et al.'s data are rescaled the same way against their comparison group.
- **No imagery** in a sense means the lowest score, 5: the bottom answer on all five questions. This is New et al.'s own definition. Arnold et al.'s equivalent is a score of 0.

### 4.3 Covariates

Age (in years) and sex. The questionnaire offered Female, Male and Other, stored as 0, 1 and O. The file does not say which number is which, which does not matter when adjusting for sex. The three people who chose Other stay in as their own category. We do not adjust for education or occupation, because autism can affect both, and Arnold et al. did not adjust for them.

## 5. What we already know about the data

- We have read both papers and reanalysed Arnold et al.'s data, using all 327 autistic participants and the 242 who scored 26 or more on the Autism Spectrum Quotient. We used those results to estimate power (§8).
- We have used New et al.'s second survey before, for a different question: whether imagery relates to currently being treated for a neurological or psychiatric condition. One model in that work used the combined any-condition group as its outcome. The estimates leaned towards people with more vivid imagery being less likely to report a condition, but both confidence intervals included no difference (visual imagery odds ratio 0.86, 95% CI 0.70–1.05; other senses 0.89, 0.73–1.08). That group mixes autism, ADHD and learning conditions, but it hints at the direction of H1, so we report it here.
- For this study we have looked only at the questionnaire wording, the condition codes, the size of each group, and the age range and sex codes across everyone. We have not compared imagery between the autism, ADHD and comparison groups. The analysis code will not run until this plan is registered, and its tests use simulated data.

## 6. Analysis

Every analysis is run once and reported with a 95% confidence interval, whatever the result.

### 6.1 Main analyses

**H1, overall imagery.** A linear regression with overall imagery as the outcome, autism group versus comparison group as the predictor, and age and sex as covariates. Standard errors are robust to unequal variance (HC3). We predict the autism group scores lower, so the test is one-sided.

**H2a and H2b, no smell or no taste imagery.** A logistic regression of "no smell imagery" (then "no taste imagery") on group, age and sex, with robust standard errors. We predict higher odds in the autism group, so the test is one-sided. If one group has very few such cases, the standard model can fail, and the code then uses Firth's corrected logistic regression. If fewer than 10 people across the two groups have no imagery in that sense, we use Fisher's exact test instead, without covariates, and report the exact odds ratio.

**Order of testing.** We test H1 first, then H2a, then H2b, each at the one-sided 5% level. A hypothesis only counts as supported if all the ones before it were. This keeps the overall chance of a false positive across the three at 5%. H1 comes first because it is Arnold et al.'s broadest finding and the one we have the most power to detect (§8). We report all three results either way.

### 6.2 Secondary analyses

These are two-sided, with a Holm correction across five tests: S1(a), S1(b), S2, S3 and S4.

- **S1.** Using all six rescaled sense scores for each person, we estimate how the autism group's gap varies by sense, with sight as the baseline. The model includes group, sense, the group-by-sense interaction, age and sex, with standard errors that account for each person contributing six scores. We test (a) whether the average of the smell and taste gaps is bigger than the sight gap, and (b) whether the gap differs across the six senses at all (a 5-degree-of-freedom Wald test).
- **S2.** One regression comparing both the autism and ADHD groups with the comparison group, adjusting for age and sex. We test whether the autism and ADHD groups differ from each other, and report the ADHD group's difference from the comparison group alongside.
- **S3.** As H2, for sight.
- **S4.** As S1(a), for the ADHD group.

### 6.3 Robustness checks

We repeat the analyses in a few different ways and report all of them alongside the main results:

1. H1, H2a and H2b using only the 104 autistic people who did not also report ADHD.
2. H1 using the plain average of the six raw scores, without rescaling.
3. H1 without the 3 people older than 30 (everyone else is 18–30).
4. H1 without adjusting for age and sex.
5. S1 allowing the effects of age and sex to differ by sense.

### 6.4 Description only

- Group differences in each sense, without testing (Hedges' *g* for the autism and ADHD groups versus the comparison group). This includes emotion, voice and inner-body imagery, which only New et al. measured.
- The number of people with no imagery in each sense and group, with counts below 5 shown as "fewer than 5".

### 6.5 Comparison with Arnold et al.

We run the H1 and S1 analyses on Arnold et al.'s data in the same way (all 327 autistic and 327 comparison adults) and show the two studies side by side, with a z-test of whether the two estimates differ. We do not combine them into one estimate, because the studies used different questionnaires, recruitment and definitions of autism. Arnold et al.'s own comparisons of how many people lack imagery used their 242-person subset. We use all 327, because New et al.'s survey has no Autism Spectrum Quotient to match on.

### 6.6 How we will read the results

To judge a null H1 result we use Simonsohn's (2015) "small telescopes" approach, which asks whether the original study could have detected an effect as small as ours. We call d33 the effect Arnold et al.'s study had a 33% chance of detecting, based on the standard error of their adjusted H1 estimate (about 0.12 SD).

| Result | What it means |
|---|---|
| H1 significant (one-sided p below .05) | Replicated: lower overall imagery in autism, as Arnold et al. found |
| H1 not significant, and a one-sided test rules out a drop in imagery as large as d33 | Failed to replicate: any real effect is too small for Arnold et al.'s study to have picked up reliably |
| Neither | Inconclusive: we report the range of effects our data cannot rule out |

- **H2** counts as a replication only if it passes the order of testing in §6.1. Otherwise we report its odds ratio next to Arnold et al.'s (about 3.2 for smell and 2.6 for taste).
- **Specific to autism** only if the autism and ADHD groups differ significantly (S2). A near-zero result for the ADHD group does not show this on its own.
- These are associations in a self-selected online sample, and we make no causal claims.

## 7. Software

- Python 3.12 or later, with NumPy, pandas and SciPy (versions in `requirements-lock.txt`). statsmodels is used only in the tests, to check our calculations.
- The code writes only summary results, never individual rows: `runs/latest/P5/p5_estimates.csv`, `p5_diagnostics.json` and `p5_source_flow.json`. The diagnostics file records the registration link and this file's fingerprint.

## 8. Sample size and power

The group sizes are set by the data. We estimated power from Arnold et al.'s results for all 327 autistic adults (their effect sizes, and how strongly the senses correlate within a person) and from New et al.'s group sizes, using a one-sided 5% test:

| Test | Arnold et al.'s effect | Power at that effect | Power at half that effect |
|---|---|---|---|
| H1, autism versus comparison | 0.22 SD lower | 79% | 34% |
| H1, autism without ADHD | 0.22 SD lower | 67% | 27% |
| S1, smell and taste versus sight | 0.13 SD bigger gap | 63% | 25% |
For H2, Arnold et al. found that 7.3% (smell) and 6.1% (taste) of autistic adults had no imagery in that sense, against 2.4% of their comparison group: odds ratios of about 3.2 and 2.6. Assuming a comparison-group rate of 2.4%, power is 87% if the true odds ratio is 3 and 46% if it is 2.

First studies tend to overestimate effects, so the half-size column is a realistic lower scenario. This is why §6.6 sets out how a null result will be read.

## 9. Changes to the plan

Any change is logged in `projects/P5_asd_adhd_replication/protocol/deviations.md` with the date, the reason, whether we had seen any results, and how it affects the conclusions. Changes are reported in the paper. This file is not edited after registration.

## 10. Planned outputs

- Flow of participants and group descriptions.
- Main results table (H1, H2a, H2b, and whether each passed the order of testing).
- Figure: the group difference in each sense for the autism and ADHD groups, with Arnold et al.'s results alongside.
- Secondary and robustness tables.
- Limitations: self-report that mixes diagnosis and suspicion; an online sample; different questionnaires in the two studies; the comparison with Arnold et al. uses all 327 rather than their 242-person subset; our earlier use of the combined condition group (§5).
