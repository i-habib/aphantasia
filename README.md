# Aphantasia association research programme

This repository contains reproducible scaffolding and aggregate-only first-pass analyses for public aphantasia datasets. The active priority is **P3 (autism and imagery)**, followed by **P1 (multisensory imagery and reported treatment)**. **P2 (NZAVS)** is access-dependent and **P4 (therapy modality matching)** is stopped because the public file lacks a linked modality-specific outcome.

## Run the available analyses

From the repository root, using the globally installed user-site package:

```sh
python3 -m aphantasia.cli --project all
python3 -m pytest
```

The pipeline reads the staged public archives in memory and writes only aggregate outputs under `runs/latest/`. Source fingerprints and licensing/provenance notes are in [`DATA_SOURCES.md`](DATA_SOURCES.md); the execution sequence is in [`execution-roadmap.md`](execution-roadmap.md); current exploratory results are in [`RESULTS_SUMMARY.md`](RESULTS_SUMMARY.md).

Raw archives, participant identifiers, open responses, interview transcripts, and generated run products are excluded by `.gitignore`. Check each repository's reuse terms before redistributing source material.

