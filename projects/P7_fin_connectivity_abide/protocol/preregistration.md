# Do autistic brains show the connection pattern seen in aphantasia? Fusiform imagery node connectivity in ABIDE I

This is the full analysis plan. It is registered on OSF (Secondary Data Preregistration template), and the registration quotes this file's SHA-256 fingerprint. The analysis code checks the fingerprint and will not run if this file has changed.

- **Author:** Ivan Habib (ORCID https://orcid.org/0009-0002-7812-0371)
- **Drafted:** 29 September 2026; revised 1–10 October 2026
- **Registration:** on OSF under Ivan Habib's account; the registration's statistical-models answer quotes this file's SHA-256.
- **Code:** https://github.com/i-habib/aphantasia, file `src/aphantasia/p7.py`. Run with `python3 scripts/run_available.py --project P7 --preregistration-url <URL>`.

---

## 1. Background

A review of 27 brain-imaging studies (Spagna et al., 2021) found that visual imagery reliably activates a small area of the left fusiform gyrus, the *fusiform imagery node* (FIN), along with areas in the left parietal and frontal lobes. In people with lifelong aphantasia, the FIN still responds during imagery, but it is less connected to left frontal areas, especially dorsal premotor and prefrontal cortex (Liu et al., 2025; 10 people with aphantasia and 10 without). Brain injuries that cause aphantasia occur in areas connected to the FIN (Kutsche et al., 2026).

Autistic adults report weaker imagery on average (King et al., 2024; Arnold et al., 2026; Taylor et al., 2026), and autism has long been linked to differences in long-range brain connections (Just et al., 2004; Di Martino et al., 2014). Kutsche et al. suggested the two might be related, but we found no study that tested it.

We use resting-state brain scans from ABIDE I to ask:

1. Is the FIN less connected to left parietal and frontal imagery areas in autistic than in non-autistic people?
2. If so, is this specific to those imagery connections, or part of a general difference in how the FIN connects to the rest of the brain?

ABIDE has no imagery measure. A positive result would show that autistic brains share a feature of aphantasia on average. It would not show that this feature causes weaker imagery.

## 2. Hypotheses

- **H1 (main).** Autistic people have weaker average connectivity between the FIN and three left-hemisphere imagery areas: parietal, dorsal premotor, and precentral/middle frontal (§4.2).
- **H2 (specificity).** This difference is bigger than the difference in the FIN's average connectivity with the rest of the brain.
- **Other secondary analyses** (§6.2): each of the three connections separately; the left hemisphere compared with the matching right-hemisphere areas; and H1 in adults only.

We expect weaker connectivity, because that is what the aphantasia studies found. We still test in both directions, because autism studies have found both weaker and stronger connections depending on age and brain region. A stronger connection would count against our hypothesis.

## 3. Data

### 3.1 Sources

- **ABIDE I** (Autism Brain Imaging Data Exchange; Di Martino et al., 2014), in the version processed by the Preprocessed Connectomes Project (Craddock et al., 2013). Downloaded from its public Amazon S3 store and used under ABIDE's data-use terms.
- **Main analysis:** time series from the C-PAC pipeline with band-pass filtering and without global signal regression, averaged within each region of the CC400 atlas (`cpac/filt_noglobal/rois_cc400`), plus the participant file `Phenotypic_V1_0b_preprocessed1.csv`.
- **Robustness checks:** the same data with global signal regression (`cpac/filt_global/rois_cc400`), and the CC200 atlas version (`cpac/filt_noglobal/rois_cc200`).
- File fingerprints are in `data_raw/abide/manifest_*.json`.
- **Brain locations:** peak coordinates from Spagna et al.'s (2021) meta-analysis, github.com/alfredospagna/Mental-Imagery-Meta-Analysis (commit 67c7f70), table for imagery versus control conditions.

### 3.2 Who is included

The participant file lists 1,112 people; 1,035 have scan data (505 autistic, 530 not), from 20 sites. We remove people in this order and report how many at each step:

1. No scan file (`FILE_ID` is `no_filename`).
2. Average head movement during the scan (`func_mean_fd`) above 0.2 mm.
3. A rater marked the scan as failed (`qc_rater_1`, `qc_func_rater_2` or `qc_func_rater_3`).
4. No usable signal in one of the seven regions.
5. Missing age, sex or eye status.
6. Sites left with fewer than 5 autistic or 5 non-autistic people, since a site needs both groups to contribute a comparison.

We remove no other outliers. So far we have only counted people: 884 of the 1,035 with scans pass step 2 (not split by group), and 317 are 18 or older.

### 3.3 Variables

- **Group:** `DX_GROUP` (1 autistic, 2 non-autistic), recoded as autistic = 1, non-autistic = 0.
- **Covariates:** age (and age squared, to allow a curve), sex, head movement, whether eyes were open or closed (this affects connectivity in visual areas), and scanning site.
- We do not adjust for IQ in the main analysis, because it is missing at several sites and may itself be affected by autism. We adjust for it in a robustness check (§6.3).

## 4. Connectivity

### 4.1 Matching locations to atlas regions

We use the CC400 atlas (Craddock et al., 2012), which is the atlas the ABIDE time series were extracted with. Each location is matched to the region that contains it. If a location fell outside every region, we would use the nearest region within 6 mm; if there were none, the analysis would stop and we would record the change.

We did this matching before registering, using only the atlas. All seven locations fall inside different regions in both CC400 and CC200, and all seven CC400 regions appear in all 1,102 scan files (checked from the file headers). The matching is saved in `results/parcel_map.json`.

### 4.2 Brain areas

All peak locations from Spagna et al. (2021), in MNI coordinates:

| Role | Area | MNI (x, y, z) |
|---|---|---|
| FIN | Left fusiform gyrus | −42, −54, −18 |
| Left target 1 | Left parietal (inferior parietal lobule / intraparietal sulcus) | −40, −44, 46 |
| Left target 2 | Left dorsal premotor / middle frontal gyrus | −26, −2, 60 |
| Left target 3 | Left precentral / middle frontal gyrus, near the inferior frontal junction | −52, 10, 38 |
| Right fusiform | Mirror of the FIN | 42, −54, −18 |
| Right target 1 | Right parietal (inferior parietal lobule / precuneus) | 40, −42, 48 |
| Right target 2 | Right middle frontal / precentral gyrus | 30, −4, 54 |

Liu et al. (2025) found the dorsal premotor connection (left target 2) the most consistently weakened in aphantasia. We leave out Spagna et al.'s other peaks (supplementary motor area, anterior insula), because no aphantasia study has linked them to the FIN.

### 4.3 Outcomes

Connectivity between two regions is the correlation of their signals over the whole scan, converted to Fisher's z so that values can be averaged.

- **Main outcome:** the average connectivity between the FIN and the three left targets.
- **Specificity outcome:** the main outcome minus the FIN's average connectivity with all other CC400 regions. We leave out the three targets and any region whose centre is within 20 mm of the FIN, because neighbouring regions share signal.
- **Hemisphere outcome:** the main outcome minus the average connectivity between the right fusiform area and the two right targets.

## 5. What we already know about the data

- We know the aphantasia and autism research summarised above, including that ABIDE connectivity findings in autism are mixed and vary with age.
- Before registering, we looked only at:
  - the participant file's column names and how many people there are by group and site;
  - head movement, scan-quality ratings and ages across everyone, not split by group;
  - the two atlases, to match the brain locations;
  - the scan-file headers, to check every region is present;
  - Spagna et al.'s tables.
- We have not calculated any connectivity values or compared autistic and non-autistic people on any brain measure. The analysis code will not run until this plan is registered, and its tests use simulated data.

## 6. Analysis

### 6.1 Main analysis (H1)

A linear regression with the main outcome as the outcome and autism as the predictor, adjusting for age, age squared, sex, head movement, eye status and site. Standard errors are robust to unequal variance (HC3). We report the autism difference with a 95% confidence interval and a two-sided p-value at the 5% level. We also report it as a standardized difference: the difference divided by the outcome's within-group SD.

### 6.2 Secondary analyses

The same model with five other outcomes, Holm-corrected as a set of five tests:

- the specificity outcome (H2);
- each of the three FIN connections on its own (three tests);
- the hemisphere outcome.

We also report two analyses outside that set:

- H1 in adults only (18 or older), since the imagery research is in adults.
- H1 with an autism-by-age term, to see whether the difference changes with age.

### 6.3 Robustness checks

We repeat the main analysis in these ways and report all of them:

1. With global signal regression, a common but debated processing step.
2. With a stricter head-movement limit (0.1 mm), and with no movement limit.
3. With the CC200 atlas instead of CC400.
4. Adjusting for IQ, in people who have an IQ score.
5. Males only, since most ABIDE I participants are male.
6. Leaving out one site at a time, and reporting the range of results.
7. Handling site with clustered standard errors instead of site terms in the model.

### 6.4 Exploratory

- Within autistic people, whether the main outcome relates to autism symptom scores: ADOS and SRS totals, where at least 30 people have them.
- The same for the AQ, at the few sites that collected it.
- A map of how the FIN's connections to every region differ between the groups.

These are exploratory, and we draw no firm conclusions from them.

## 7. How we will read the results

| Result | What it means |
|---|---|
| H1 and H2 both show weaker connectivity, with confidence intervals that exclude zero | The FIN is less connected to the imagery areas in autism, beyond any general difference. This fits the idea that autistic brains share aphantasia's connection pattern. |
| H1 shows weaker connectivity, but H2's interval includes zero | The FIN is less connected, but no more than to the rest of the brain. This points to a general difference rather than one specific to imagery. |
| H1's interval includes zero, and an equivalence test (two one-sided tests) rules out differences as large as 0.15 SD | Any difference is too small to matter. |
| H1's interval includes zero, but the equivalence test does not rule out 0.15 SD | Inconclusive. |
| H1 shows stronger connectivity | This counts against the idea. |

We treat a standardized difference of 0.15 as the smallest that matters. This is our own judgement of a difference worth detecting, not a value taken from earlier studies.

## 8. Power

We expect around 400 people per group after exclusions; the exact numbers come from §3.2. With a two-sided 5% test, that gives about 80% power for a standardized difference of 0.20 and about 55% for 0.15. Adjusting for site and the other covariates will change this a little. The adults-only analysis (about 250 people) has much less power, so we treat it as descriptive.

## 9. Software

Python 3.12 or later, with NumPy, pandas and SciPy. Atlas files are read with the project's own NIfTI reader (`src/aphantasia/nifti.py`). The code writes only summary results, never individual rows.

## 10. Changes to the plan

Any change is logged in `projects/P7_fin_connectivity_abide/protocol/deviations.md` with the date, the reason, whether we had seen any results, and how it affects the conclusions. Changes are reported in the paper. This file is not edited after registration.

## 11. Planned outputs

- Flow of participants and group descriptions.
- Main and specificity results.
- Figure: the autism difference for each FIN connection.
- Robustness table.
- Exploratory map of FIN connection differences.
- Limitations: no imagery measure; resting scans rather than an imagery task; a mostly child and teenage sample; differences between sites; atlas regions rather than an exact seed point.
