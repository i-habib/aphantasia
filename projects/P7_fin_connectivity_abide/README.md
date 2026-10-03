# P7 — fusiform imagery node (FIN)–frontoparietal connectivity in ABIDE I

**State:** plan drafted; data downloaded; code and tests written. The group comparison is locked until the plan is registered and frozen. No connectivity value has been computed from real data.

- Plan: [`protocol/preregistration.md`](protocol/preregistration.md) · deviations: [`protocol/deviations.md`](protocol/deviations.md)
- Rationale and literature: [`../P6_imagery_brainmaps/literature-review.md`](../P6_imagery_brainmaps/literature-review.md) §B
- Code: `src/aphantasia/p7.py`; tests: `tests/test_p7_connectivity.py` (synthetic data, plus header and phenotype-count checks)

## Data (`data_raw/`, git-ignored; ~820 MB)

| Item | Source | Fingerprint |
|---|---|---|
| ABIDE I Preprocessed, C-PAC, `filt_noglobal`, `rois_cc400` (1,102 files, 851 MB) | `s3://fcp-indi/data/Projects/ABIDE_Initiative/Outputs/` | listing SHA-256 `a05c49e9…3a6d` (`data_raw/abide/manifest_filt_noglobal_rois_cc400.json`) |
| Phenotype `Phenotypic_V1_0b_preprocessed1.csv` | same bucket | `009f01a8…0865` |
| CC400 / CC200 atlases | GitHub `preprocessed-connectomes-project/abide`, `resources/abide_rois` | in manifest |
| Spagna et al. (2021) ALE map and cluster tables | GitHub `alfredospagna/Mental-Imagery-Meta-Analysis` @ `67c7f70` | — |

Download script: `scripts/p7_download_abide.py` (resumable). Also downloaded: the global-signal-regression set (`--strategy filt_global`; 1,102 files; listing SHA-256 `30784cca…67b6`) and the CC200 set (`--derivative rois_cc200`; 1,102 files; listing SHA-256 `18f5adb1…07d0`). All seven CC200 node regions are present in every file.

## Pre-registration checks already run (no group comparison)

- `--project P7-map`: all seven Spagna coordinates fall inside distinct parcels in CC400 and CC200, at 0 mm (`results/parcel_map.json`).
- Header check: all 1,102 files have 392 parcels, including all seven node parcels.
- Phenotype counts: 1,112 rows; 1,035 with files (505 autistic, 530 non-autistic); 20 sites; 884 with mean FD ≤ 0.2; 317 aged 18 or over; eyes open 765 / closed 347.

## Commands

```sh
python3 scripts/run_available.py --project P7-map        # atlas-only node mapping
python3 -m pytest tests/test_p7_connectivity.py
python3 scripts/freeze_preregistration.py --project P7  # once, right after registering
python3 scripts/run_available.py --project P7 --preregistration-url https://osf.io/XXXXX
```

## Before registering (moved from the plan)

- [ ] Add affiliation and ORCID (author name filled). Editing the plan changes its fingerprint, so update the OSF draft's "Statistical models" answer too.
- [ ] Confirm the node list (§4.2) and exclusion rules (§3.2); edit now or never.
- [x] Global-signal-regression set: approved and downloaded 29 Sep 2026 (sensitivity 1 kept).
- [ ] Run the code's tests (synthetic data only).
- [ ] Register on OSF, freeze, then run once.

**OSF draft (private, not registered):** https://osf.io/registries/drafts/6abc7b03e6c491a5f6b5f205/review. See `projects/osf_drafts/README.md`.
