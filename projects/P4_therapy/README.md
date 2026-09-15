# P4 — imagery modality and perceived therapy effectiveness

**State:** stopped after a completed public-data feasibility audit; no inferential model is appropriate for the staged fields.

## Source and current audit

- [Mawtus et al. (2024), *Collabra: Psychology*](https://doi.org/10.1525/collabra.127416)
- Public sources: [Stage 2 OSF v7krh](https://osf.io/v7krh/), [download ZIP](https://files.osf.io/v1/resources/v7krh/providers/osfstorage/?zip=); [Stage 1 OSF uamcp](https://osf.io/uamcp/), [download ZIP](https://files.osf.io/v1/resources/uamcp/providers/osfstorage/?zip=)
- Run the aggregate-only audit with `python3 scripts/run_available.py --project P4`.

The quantitative file contains 2,815 rows and 80 columns. The overall treatment-effectiveness outcome is answered by 2,110 participants and has three response levels. Auditory imagery scores are present, but the auditory-therapy field has only one nonblank response level and is not an explicit use-versus-non-use measure. No modality-specific effectiveness outcome was identified. Interview transcript documents are not opened by the processing code.

## Decision and reopen conditions

The original paper already analyzes broad therapy categories. Repeating overall effectiveness against imagery capacity cannot identify whether auditory imagery ability matches auditory techniques. Do not duplicate one global outcome across several therapies or infer skipped questions mean no.

Reopen only if a permitted source supplies a treatment-level record that links (a) modality use and explicit non-use, (b) the same treatment's effectiveness rating, and (c) imagery capacity measured at a relevant time, with enough overlap to estimate the planned interaction. Until that data contract changes, keep this candidate stopped and move effort to P1, P2 access, or the P3 synthesis.

The exact aggregate audit is in `runs/latest/P4/p4_feasibility.json` after a full pipeline run.
