# Autistic adults more often report absent sensory imagery: a preregistered replication with an ADHD comparison

Ivan Habib | Independent researcher | ORCID 0009-0002-7812-0371 | [email to add]

Working copy, 18 October 2026. Declarations are incomplete.

## Abstract

Arnold et al. (2026) found that autistic adults report weaker mental imagery than non-autistic adults, and more often report no smell or taste imagery. Following a preregistered plan, we tested these findings in a separate online survey of young UK adults (New et al., 2026). We compared 150 respondents who reported diagnosed or strongly suspected autism with 749 who reported no neurodevelopmental condition and 84 who reported ADHD without autism. All three registered predictions were supported. The autism group's overall imagery was 0.42 standard deviations lower, and absent smell and taste imagery were more common (odds ratios 2.7 and 3.8). The difference was no larger for smell and taste than for other senses, and the autism-versus-ADHD difference did not survive correction. Exploratory analyses located the difference. In New et al.'s survey it was carried by a subset: 20% of the autism group reported no imagery in at least one sense, against 6.5% of the comparison group, and neither a uniform shift nor a wider spread reproduced this. In Arnold et al.'s data, wider spread explained most of the pattern. Studies of autism and imagery should report how many people have absent imagery, not only group means.

## Introduction

Try to imagine the smell of fresh coffee, or the face of a close friend. Most people report some sensory experience when they do this, although its vividness varies a great deal. A minority report no experience at all. When this applies to visual imagery it is called aphantasia (Zeman et al., 2015), and many people with aphantasia also report weak or no imagery in other senses (Dance, Ward & Simner, 2021). In this paper, imagery means what people report on questionnaires about this kind of experience. We do not measure the ability to use imagery in a task.

Several recent studies link autism with weaker reported imagery. Arnold et al. (2026) surveyed 327 adults who reported a formal autism diagnosis. On the Plymouth Sensory Imagery Questionnaire, they reported weaker imagery than a comparison group across the senses, and more of them reported no smell or taste imagery. King et al. (2024) found lower visual imagery vividness in a group that combined diagnosed and self-identifying autistic adults, and a higher proportion of that group scored at the aphantasia cut-off. Going the other way, Dance, Jaquiery et al. (2021) found that people with aphantasia reported more autistic traits than people without it. Two studies complicate this picture. Bouyer et al. (2025) pointed out that the Autism Spectrum Quotient, the most widely used autistic-trait questionnaire, contains items about imagination, so correlating it with imagery partly measures imagery twice. Once those items were set aside, the association they found was weak. Taylor et al. (2026) found that lower imagery went with more autistic traits, but that imagery was barely related to sensory sensitivity.

Most of this evidence compares group means, and three different patterns produce a lower mean. The whole autistic group can sit slightly lower than the comparison group. It can be lower on average and also more spread out. Or most autistic people can report imagery like anyone else, while a minority report none at all in one or more senses. Only the third links autism to the absence of imagery in some people, and so to aphantasia. It also means a mean difference understates how different the affected minority is and overstates how different everyone else is. Arnold et al.'s finding that absent smell and taste imagery was more common points to the third pattern, but group means cannot tell the three apart.

New et al. (2026) surveyed mental imagery in 1,003 young UK adults. Their survey also asked whether respondents had been diagnosed with, or strongly suspected, a neurodevelopmental condition, and which ones. New et al. analysed these respondents as a single pooled group. Separating them allows three things. First, it provides a test of Arnold et al.'s three main findings in a different sample and with a different questionnaire, which we registered before running any autism or ADHD comparison. Second, attention-deficit/hyperactivity disorder (ADHD) was reported almost as often as autism, which allows a comparison with another neurodevelopmental condition. If the imagery difference were a general feature of reporting any such condition, the ADHD group should show it too. Third, the data can show where in the distribution an autism difference lies. We added this third analysis after seeing the registered results, so we report it as exploratory. We also repeated it in Arnold et al.'s public data. Those data had motivated the registered predictions and had been analysed before registration, so this repeat is a consistency check rather than an independent test.

## Methods

### Data and registration

We reanalysed Study 2 of New et al. (2026), an online survey of mental imagery in young UK adults. The data are public on the Open Science Framework (OSF; project 2bdn6). New et al. recruited through Prolific, an online platform for recruiting research participants, and advertised a reading study without mentioning imagery. Eligibility was UK residence or nationality, English as a first language, and age 18-30.

The analysis plan was registered on OSF on 10 October 2026, before any autism or ADHD comparison was run (https://osf.io/87udm). Before registering, we had read both source papers, reanalysed Arnold et al.'s public data, and seen New et al.'s pooled neurodevelopmental-condition result. The registration lists this prior knowledge. The registered analysis was run once, on the day of registration. We call its results "registered". Analyses we added after reading those results are labelled "exploratory" throughout. Most were run on 10 and 11 October; the five-sense check was added on 17 October and the shift benchmark on 18 October, after an internal review. Departures from the plan are listed in Table S8. The most important is an error in matching the two questionnaires, described under "Comparison with Arnold et al.".

### Participants

New et al. excluded respondents who failed an attention check. The check asked people to pick their five favourite activities twice, and kept those who repeated at least three. This left 1,003 of 1,020 respondents.

One survey question asked whether the respondent had been diagnosed with, or strongly suspected, a neurodevelopmental condition. Those who said yes ticked the conditions that applied. We formed three groups from these answers:

- **Autism group** (n = 150): ticked autism. Forty-six of them also ticked ADHD.
- **ADHD-only group** (n = 84): ticked ADHD but not autism.
- **Comparison group** (n = 749): reported no neurodevelopmental condition.

We excluded 20 respondents who ticked only other conditions. The groups reflect what people reported, not a clinical assessment. One comparison respondent had no recorded age, so the adjusted models use 898 people for autism versus comparison and 982 for the three-group model. Table 1 describes the groups.

[INCLUDE table_main1_participants.md]

### Imagery measure

New et al. used an extended version of the Questionnaire upon Mental Imagery (QMI; Sheehan, 1967). Respondents imagined familiar things, such as a face, a sound or a taste, and rated how vivid the experience was from 1 to 7. A rating of 1 means thinking about the item without any sensory experience. A rating of 7 means an experience as vivid as the real thing. Each scale has five items, so its score runs from 5 to 35.

New et al. measured nine kinds of imagery. We used the six that the registered plan matched to the six senses in Arnold et al.'s questionnaire: sight, sound, smell, taste, touch and movement. Results for the other three (emotion, voice and inner body) are in Table S7.

A score of 5 in a sense means the person chose "no experience" for all five items. We call this **absent imagery** in that sense. It is the strictest possible definition, it is the one New et al.'s analysis code uses, and it corresponds to reporting no image at all, as in aphantasia. It is a questionnaire answer, not a test of ability.

The **overall imagery score** is the average of the six sense scores, each first expressed relative to the comparison group. We converted each sense score to standard-deviation units using the comparison group's mean and standard deviation, averaged the six, and then rescaled that average in the same way. A difference of -0.4 therefore means the autism group scored 0.4 comparison-group standard deviations lower. The conversion gives each sense equal weight.

### Registered analyses

**Primary tests.** We tested three predictions from Arnold et al., in a fixed order:

1. the autism group has a lower overall imagery score;
2. absent smell imagery is more common in the autism group;
3. absent taste imagery is more common in the autism group.

Arnold et al.'s results set the direction of each prediction, so each was a one-sided test at the 5% level. A later prediction could only count as supported if all earlier ones were. This fixed order keeps the chance of any false positive across the three tests at 5% without a further correction. We report two-sided 95% confidence intervals.

For the overall score we used linear regression with heteroskedasticity-robust (HC3) standard errors, which do not assume equal variance in the two groups. For absent smell and taste we used logistic regression. All models adjusted for age and sex.

Two respondents in the analysed groups reported their sex as "other", and neither had absent smell or taste imagery. Ordinary logistic regression cannot be fitted in that case, because one predictor perfectly predicts the outcome. As the plan allowed, we used Firth's penalised logistic regression (Firth, 1993), which gives finite estimates when this happens. As registered, its confidence intervals are Wald intervals: the estimate plus or minus 1.96 standard errors on the log-odds scale.

**Secondary tests.** Five secondary tests asked whether the autism difference was specific. They were corrected together with Holm's (1979) method, which compares the smallest p value with the strictest threshold, the next smallest with a slightly looser one, and so on:

- S1(a): is the autism difference larger for smell and taste than for sight?
- S1(b): does the autism difference vary at all across the six senses?
- S2: is the overall difference larger for autism than for ADHD-only?
- S3: is absent visual imagery more common in the autism group?
- S4: does the ADHD-only group show a larger difference for smell and taste than for sight?

S1 and S4 used a model with one row per person per sense, with standard errors that allow for each person contributing six scores. Each sense was standardised against the comparison group, so contrasts between senses are in comparison-group standard deviations.

**Sensitivity analyses.** We repeated the main overall-score test four ways: without autistic respondents who also reported ADHD; on the raw 5-35 scale; restricted to ages 18-30 (three respondents were older); and without age and sex adjustment.

### Comparison with Arnold et al.

Arnold et al. (2026) published scores for 327 adults who reported a formal autism diagnosis and 327 comparison adults. They used the Plymouth Sensory Imagery Questionnaire (PSI-Q; Andrade et al., 2014), with each sense scored from 0 (no image) to 50. We ran the same models on all 327 autistic adults. Arnold et al.'s own analysis kept the 242 who scored 26 or more on the Autism Spectrum Quotient (AQ). New et al.'s survey has no AQ, so the full group is the closer match to our checklist-defined group.

The registered plan treated Arnold et al.'s sixth sense as movement. It is in fact bodily sensation (for example, warmth or a sore throat). We found this while preparing the manuscript, after the registered results were known. The registered results stand as run. To check that the mismatch did not drive them, we added one analysis that drops the sixth sense from both datasets and uses only sight, sound, smell, taste and touch. We recorded this check in the deviations log before running it, but after seeing the registered results, so it is exploratory.

### Exploratory analyses: where is the difference?

These analyses ask whether the lower average reflects the whole autism group scoring lower, a different way of using the rating scale, or a subset of people with absent imagery. Each was run in both datasets. In Arnold et al.'s data a score of 0 is absent imagery and 50 is the top score.

- **Ends of the scale.** For each sense, we counted how many people gave the lowest possible score (absent imagery) and how many gave the highest. If autistic respondents simply used the ends of the scale more, both should be more common. We compared percentages with Fisher's exact test, and counted for each person in how many senses they gave the lowest and the highest score.
- **Percentiles.** We compared the groups at the 10th, 25th, 50th, 75th and 90th percentiles of the overall score, using quantile regression (Koenker & Bassett, 1978) adjusted for age and sex. A uniform downward shift predicts similar differences at every percentile. A subset with absent imagery predicts a large difference at low percentiles only.
- **People with imagery in every sense.** We repeated the overall-score comparison among people with no absent sense. Because this selects people by their scores, and removes more autistic than comparison respondents, we interpret it together with the shift benchmark below.
- **Shift benchmark.** A larger difference at low percentiles can also arise if the autism group is lower and more spread out, without any distinct subset. To test this, we built two predicted autism groups from the comparison group's own scores. In the "shift" model, each comparison respondent's score in each sense was lowered by the autism-comparison mean difference in that sense. In the "shift + stretch" model, each sense was also rescaled to the autism group's standard deviation. Scores were rounded to whole points and kept within the scale, and each person kept their own profile across senses. We then compared the predicted groups with the real autism group on the measures above, using unadjusted values and 95% bootstrap intervals for the real group (2,000 resamples). If either model matched the real group, there would be no need to posit a distinct subset.

We ran several other exploratory analyses: restricting to the most attentive respondents, the three kinds of imagery not in the overall score, adjustment for current treatment, education and a self-rating of empathy, Arnold et al.'s AQ-selected subset, and a reanalysis of public data from Dance, Ward and Simner (2021). Table S7 gives every result and the reason for each analysis.

### Reproducibility

Code and aggregate outputs are at https://github.com/i-habib/aphantasia/tree/main/projects/P5_asd_adhd_replication. We do not redistribute the source data; all datasets are available from their original archives. We reproduced all registered estimates in a separate run and checked the Firth fits against an independent implementation in R (brglm2).

## Results

### Registered primary tests

All three primary predictions were supported (Table 2, Figure 1). The autism group's overall imagery score was 0.42 standard deviations lower than the comparison group's (95% CI -0.66 to -0.19; one-sided p = .0002).

Absent smell imagery was reported by 15 of 150 autistic respondents (10.0%) and 29 of 749 comparison respondents (3.9%), adjusted odds ratio 2.69 (95% CI 1.42 to 5.10; one-sided p = .001). Absent taste imagery was reported by 17 autistic respondents (11.3%) and 23 comparison respondents (3.1%), adjusted odds ratio 3.81 (95% CI 2.00 to 7.26; one-sided p < .001).

[INCLUDE table_main2_registered.md]

[FIGURE figure1_overall_imagery.png | Figure 1. Difference in overall imagery between the autism and comparison groups, adjusted for age and sex, with 95% confidence intervals. Negative values mean weaker reported imagery in the autism group. Blue: the registered six-sense score. Orange: the exploratory five-sense check, which drops the sixth sense because it differs between the two questionnaires. Each dataset is standardised against its own comparison group. The four rows come from two datasets, not four independent samples.]

### Registered secondary tests

None of the five secondary tests was significant after Holm correction (Table 2).

The difference was not larger for smell and taste than for sight (S1a: +0.03 standard deviations, 95% CI -0.15 to +0.20). It did not vary detectably across the six senses (S1b: chi-square 4.34 on 5 degrees of freedom, p = .50). So although absent smell and taste imagery was more common, the average difference in those senses was no larger than in the others.

The autism group's overall score was 0.36 standard deviations below the ADHD-only group's (95% CI -0.69 to -0.02; unadjusted p = .037; Holm-adjusted p = .15), so the registered test of autism specificity was not supported. The ADHD-only group differed little from the comparison group (-0.07, 95% CI -0.32 to +0.19).

Absent visual imagery was more common in the autism group (odds ratio 2.84, 95% CI 1.27 to 6.33), but this did not survive correction (Holm-adjusted p = .054). The ADHD-only group showed no smell-and-taste pattern (S4: +0.02, 95% CI -0.15 to +0.20).

### Sensitivity analyses

The overall difference was similar without autistic respondents who also reported ADHD (-0.39, 95% CI -0.65 to -0.13), on the raw scale (-2.2 points on the 5-35 scale, 95% CI -3.5 to -1.0), at ages 18-30 only (-0.42), and without adjustment (-0.43). Table S4 gives all sensitivity estimates.

### Comparison with Arnold et al. and the five-sense check

In Arnold et al.'s full sample the registered six-sense difference was smaller, -0.18 standard deviations (95% CI -0.36 to -0.002). Dropping the mismatched sixth sense changed little in either dataset (Figure 1). The five-sense difference was -0.43 (95% CI -0.67 to -0.20) in New et al.'s data and -0.20 (95% CI -0.38 to -0.02) in Arnold et al.'s.

### Exploratory: where is the difference?

In both datasets the difference was concentrated at the low end of the distribution (Table 3, Figure 2). Whether that reflects a distinct subset depends on the dataset (Table 4).

**New et al.'s survey.** Twenty percent of autistic respondents reported absent imagery in at least one of the six senses, against 6.5% of the comparison group (Fisher p < .001). Absent imagery was more common in every sense, while top scores were about equally common (Table S6). On average, autistic respondents had absent imagery in 0.34 more senses (95% CI 0.14 to 0.54) and the same number of top-scoring senses (-0.03, 95% CI -0.21 to +0.15), so they did not simply use both ends of the scale more. At the 10th percentile of overall imagery the difference was -1.27 standard deviations (95% CI -1.66 to -0.88), and at the 25th it was -0.56 (95% CI -0.81 to -0.30). At the median and above it was between -0.09 and -0.19, and none of these intervals excluded zero. Among the 819 respondents with imagery in every sense, the difference was -0.03 (95% CI -0.21 to +0.14).

Neither whole-group model reproduced this pattern (Table 4). Lowering every comparison respondent's scores by the mean difference predicted 8.3% with absent imagery in at least one sense; also stretching the distribution predicted 12.0%. The observed 20.0% lay above both (bootstrap interval 13.3% to 26.7%). Both models predicted a smaller difference at the 10th percentile than observed, and a clear difference among people with imagery in every sense (-0.38 and -0.28) where the observed difference was close to zero.

**Arnold et al.'s data.** Absent imagery in at least one sense was reported by 9.8% of autistic adults and 4.6% of comparison adults (Fisher p = .015). The adjusted difference was -0.67 standard deviations at the 10th percentile (95% CI -1.07 to -0.28) and -0.04 at the median (95% CI -0.23 to +0.15). Among people with imagery in every sense it was -0.07 (95% CI -0.22 to +0.08). Here the shift + stretch model fitted well: it predicted 8.9% with absent imagery (observed 9.8%) and a difference of -0.10 among people with imagery in every sense (observed, unadjusted, -0.12). Only the 10th-percentile difference fell outside its prediction (observed -0.75, 95% CI -1.08 to -0.41; predicted -0.39). In Arnold et al.'s data, a lower and more spread-out distribution accounts for most of the pattern.

Among the 242 autistic adults in Arnold et al.'s AQ-selected subset, a difference remained among people with imagery in every sense (-0.19, 95% CI -0.37 to -0.02).

**ADHD.** In New et al.'s data, 8.3% of the ADHD-only group reported absent imagery in at least one sense, close to the comparison group (Fisher p = .49) and lower than the autism group (odds ratio 2.75, Fisher p = .024).

[INCLUDE table_main3_tails.md]

[INCLUDE table_main4_benchmark.md]

[FIGURE figure2_where_the_gap_sits.png | Figure 2. Where the difference sits (exploratory). A: unadjusted autism-minus-comparison difference in overall imagery at each 5th percentile, with 95% bootstrap intervals, in New et al.'s data (blue) and Arnold et al.'s data (orange). At low percentiles the autism group scores much lower; above the median the two groups are close. The intervals at the lowest percentiles are wide. B: how often imagery is absent. Percentage of each group with the lowest possible score in each sense. Bars: autism groups. Circles: comparison groups, in the matching colour. Only the five senses measured in both questionnaires are shown.]

## Discussion

In a separate sample and with a different questionnaire, the registered analysis replicated the three main findings of Arnold et al. (2026). Young adults who reported diagnosed or strongly suspected autism reported weaker imagery overall, and more of them reported no smell or taste imagery. The overall difference was larger than in Arnold et al.'s sample (-0.42 against -0.18 standard deviations). The samples differ in age, in how autism was identified and in the questionnaire, and we did not compare them formally.

Absent smell and taste imagery was more common in the autism group, but the average difference in those senses was no larger than in sight (S1). In New et al.'s data, absent imagery was more common in the autism group in every sense (Table S6). Smell and taste have the highest rates of absent imagery in both groups, so the gaps in percentage points are largest there. The result is therefore not a deficit specific to smell and taste. Absent imagery is more common across the senses in autism, including sight (odds ratio 2.8, Holm-adjusted p = .054).

In these data the difference did not extend to ADHD. The ADHD-only group was close to the comparison group on overall imagery (-0.07 standard deviations) and on absent imagery (8.3% against 6.5%). The direct autism-versus-ADHD test did not survive correction, so establishing that the difference is specific to autism needs a larger ADHD sample.

In New et al.'s survey, the difference lies in a subset. One in five autistic respondents reported no imagery in at least one sense. Neither a uniformly lower nor a more spread-out distribution reproduced this, and autistic respondents with imagery in every sense scored like the comparison group. Arnold et al.'s data also showed more absent imagery in the autism group, but there a lower and more spread-out distribution accounted for most of the pattern. The samples differ in two relevant ways: New et al.'s respondents were younger, and their autism group included people who strongly suspected autism without a diagnosis.

When a subset drives the difference, a group mean is a poor summary. In New et al.'s data, a difference of 0.4 standard deviations is too small for the one in five autistic respondents with absent imagery and too large for everyone else. Earlier studies already report the share of people at the aphantasia cut-off or with absent imagery (King et al., 2024; Arnold et al., 2026). Comparing those shares with what a whole-group shift predicts, as in Table 4, shows whether the difference lies in a subset. The subset pattern fits the finding that people with aphantasia report more autistic traits (Dance, Jaquiery et al., 2021). Among Arnold et al.'s autistic adults, those with absent imagery scored higher on the AQ items that do not concern imagination (d = 0.35, p = .046), so the link is not just overlap between imagery and imagination items. Our reanalysis of Dance, Ward and Simner's (2021) data is less clear-cut: AQ scores went with weaker imagery among people without aphantasia (rho = -0.27) but not among people with aphantasia (rho = -0.01; Table S7). In Arnold et al.'s AQ-selected subset, a small difference remained among people with imagery in every sense. Because some AQ items ask about imagination, selecting on the AQ also selects for weaker imagery (Bouyer et al., 2025).

### Limitations

Group membership rests on self-report, and New et al.'s question combined diagnosis with strong suspicion, so the autism group probably includes some people without a diagnosis. Both datasets come from online questionnaires at a single time point, and New et al.'s sample is young and UK-based. The two questionnaires differ, and the registered plan wrongly treated Arnold et al.'s sixth sense, bodily sensation, as movement. Dropping that sense changed the results little, but this check was added afterwards. The files available to us do not document how Arnold et al. recruited their comparison group, or whether anyone took part in both surveys, so we do not formally compare the two datasets. All distribution analyses, including the benchmark, were added after the registered results were known, and the benchmark models are simple: they keep the comparison group's shape and change only its mean and spread. Some logistic models relied on Wald intervals, which can be inaccurate when one category is very small. Finally, an imagery score cannot be used to identify autism in an individual.

### Conclusion

A preregistered test in a new sample replicated Arnold et al.'s finding that autistic adults report weaker imagery overall and more often report no smell or taste imagery. The difference was no larger for smell and taste than for other senses, and did not extend to ADHD. In the newer sample, it lies in a subset of autistic adults who report no imagery in one or more senses. The next step is a registered test of this pattern in a third sample, ideally with confirmed diagnoses and a trait measure free of imagination items.

## Declarations

- **Ethics:** [to resolve before submission. This study reanalysed existing public data and involved no contact with participants, but no ethics determination has been obtained for it.]
- **Funding:** [none / to confirm].
- **Competing interests:** [none / to confirm].
- **Author contributions:** Ivan Habib: conceptualisation, methodology, formal analysis, writing (original draft, review and editing).
- **Data and code availability:** New et al. (2026) data: OSF project 2bdn6. Arnold et al. (2026) data: University of Queensland data collection, doi:10.48610/57f325b. Dance, Ward and Simner (2021) data: OSF project h24vm. Registration: https://osf.io/87udm. Code, aggregate outputs and the full deviations log: https://github.com/i-habib/aphantasia/tree/main/projects/P5_asd_adhd_replication. No participant-level data are redistributed.
- **Use of AI tools:** [author to write. Name every tool actually used, including Claude (Anthropic) and OpenAI Codex; say what each did (for example analysis code, numerical checks, drafting and editing text); and state that the author reviewed and takes responsibility for all content.]

## References

Andrade, J., May, J., Deeprose, C., Baugh, S.-J., & Ganis, G. (2014). Assessing vividness of mental imagery: The Plymouth Sensory Imagery Questionnaire. British Journal of Psychology, 105, 547-563. https://doi.org/10.1111/bjop.12050

Arnold, D. H., Bouyer, L., Saurels, B. W., Schwarzkopf, D. S., & Pellicano, E. (2026). Autism and aphantasia. Consciousness and Cognition, 143, 104085. https://doi.org/10.1016/j.concog.2026.104085

Bouyer, L. N., Pellicano, E., Saurels, B. W., Schwarzkopf, D. S., & Arnold, D. H. (2025). The vividness of visualisations and autistic trait expression are not strongly associated. Consciousness and Cognition, 129, 103821. https://doi.org/10.1016/j.concog.2025.103821

Dance, C. J., Jaquiery, M., Eagleman, D. M., Porteous, D., Zeman, A., & Simner, J. (2021). What is the relationship between aphantasia, synaesthesia and autism? Consciousness and Cognition, 89, 103087. https://doi.org/10.1016/j.concog.2021.103087

Dance, C. J., Ward, J., & Simner, J. (2021). What is the link between mental imagery and sensory sensitivity? Insights from aphantasia. Perception, 50, 757-782. https://doi.org/10.1177/03010066211042186

Firth, D. (1993). Bias reduction of maximum likelihood estimates. Biometrika, 80, 27-38. https://doi.org/10.2307/2336755

Holm, S. (1979). A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics, 6, 65-70.

King, R., Buxton, H., & Tyndall, I. (2024). Aphantasia and autism: An investigation of mental imagery vividness. Consciousness and Cognition, 125, 103749. https://doi.org/10.1016/j.concog.2024.103749

Koenker, R., & Bassett, G. (1978). Regression quantiles. Econometrica, 46, 33-50. https://doi.org/10.2307/1913643

New, B., Barra, J., Chauvin, A., Huson, N., & Lœvenbruck, H. (2026). Multimodal mental imagery profiles and the prevalence of aphantasia and hyperphantasia in the general population. Cortex, 201, 119-136. https://doi.org/10.1016/j.cortex.2026.04.019

Sheehan, P. W. (1967). A shortened form of Betts' Questionnaire upon Mental Imagery. Journal of Clinical Psychology, 23, 386-389.

Taylor, R., Sumner, P., Singh, K. D., & Jones, C. R. G. (2026). Exploring the association between mental imagery, sensory sensitivity, and autistic traits in autistic and non-autistic adults. Scientific Reports, 16, 11018. https://doi.org/10.1038/s41598-026-38574-9

Zeman, A., Dewar, M., & Della Sala, S. (2015). Lives without imagery: Congenital aphantasia. Cortex, 73, 378-380. https://doi.org/10.1016/j.cortex.2015.05.019
