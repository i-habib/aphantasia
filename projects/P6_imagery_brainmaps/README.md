# P6 — imagery and autism brain maps (feasibility)

**State:** feasibility checked 29 September 2026. No imagery-map × autism-map comparison has been computed; keep it that way until a plan is registered.

## Downloaded sources (`data_raw/`, git-ignored)

| File | Source | SHA-256 |
|---|---|---|
| `enigma/asd_meta-analysis_case-controls_CortThick.csv` | ENIGMA Toolbox, MICA-MNI/ENIGMA @ `b08974b` (`enigmatoolbox/datasets/summary_statistics`) | `ee076971be6688bc99106fce4a7198a3bd927d183adb245f9810d6f71efe4f29` |
| `enigma/asd_mega-analysis_case-controls_CortThick.csv` | same | `af4e609ec7e2e5422defbaa0c7f94ce72d9b3f3494ed095e455ba302b7a4ff03` |
| `enigma/asd_meta-analysis_case-controls_SubVol.csv` | same | `b2b0b02c260ec87c6ab22f40e6162ab8a475dab373390be1edd465910ca62066` |
| `enigma/aparc_fsa5.csv`, `fsa5_lh.gii`, `fsa5_rh.gii` | same repo, `datasets/parcellations` and `datasets/surfaces` | — |
| `neurosynth/imagery_association-test_z.nii.gz` | Neurosynth term "imagery", association test, image 162 (FDR 0.01 thresholded) | — |

ENIGMA autism cortical thickness: Cohen's d for 68 Desikan–Killiany regions (meta-analysis, about 1,060 autistic vs 975 controls). Cite the ENIGMA ASD working group (van Rooij et al., 2018) and the ENIGMA Toolbox (Larivière et al., 2021, *Nature Methods*).

## Feasibility result (`python3 scripts/p6_feasibility.py`)

- The regions align: ENIGMA's 68 regions map onto the fsaverage5 labels, and every surface vertex falls inside the imagery volume.
- The imagery map is thin at this resolution: only 15/68 regions have at least 10% of vertices with signal (36/68 have any), and 8.2% of cortex carries signal. That's because the Neurosynth map is pre-thresholded, and the term "imagery" also pulls in motor imagery studies.
- Verdict: technically feasible, but weak as a standalone paper; see `literature-review.md` §E. Use it as a supplement. If pursued, get an unthresholded imagery map (NeuroQuery, or recompute with NiMARE) and use a proper fsaverage→MNI transform (neuromaps) instead of the coarse nearest-voxel lookup.

## Stronger biological test identified: FIN–prefrontal connectivity in ABIDE (proposed P7)

See `literature-review.md` §B. ABIDE Preprocessed ROI time series are openly downloadable from the FCP-INDI S3 bucket. Not yet downloaded: this needs the user's go-ahead and agreement to ABIDE's data-use terms.
