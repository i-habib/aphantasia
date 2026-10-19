# P5 — autism, ADHD and multisensory imagery: a preregistered test of Arnold et al. (2026)

**State, 17 October 2026:** registered on OSF 10 Oct 2026 (https://osf.io/87udm; locally recorded embargo until 24 Nov 2026, live status not reverified). Plan frozen; registered analysis and original outputs preserved. Submission audit reproduced all 156 estimate rows exactly and independently validated five Firth fits against R brglm2. **Working submission package prepared; not ready to submit.**

Start with [`submission/README.md`](submission/README.md) and [`review/submission_audit_2026-10-17.md`](review/submission_audit_2026-10-17.md). The working PDF is `output/pdf/p5_submission_review.pdf` at the repository root. Full draft as of 18 October 2026 (registered replication plus an exploratory section showing the gap sits among people reporting absent imagery). Source permissions, ethics documentation, author declarations and Arnold comparison recruitment remain unresolved.

**Measurement correction:** Arnold's sixth component is bodily sensation, whereas New's is motor imagery. The registered plan's crosswalk was wrong. The frozen plan is unchanged; the deviation log records the correction and a post-registration five-sense sensitivity. The broad adjusted difference remains similar (-0.435 versus the registered -0.422 comparison-group SD), but the analysis is a conceptual replication. No secondary test supports autism specificity or a selectively larger mean smell/taste deficit after Holm correction.

- Plan: [`protocol/preregistration.md`](protocol/preregistration.md) · deviations: [`protocol/deviations.md`](protocol/deviations.md)
- Data: New et al. (2026) Study 2 (OSF 2bdn6). The `neurodev2` checklist identifies ASD (n=150), ADHD-only (n=84) and other conditions (n=20) among 1,003 participants; the source paper analysed only the pooled indicator.
- Anchor: Arnold et al. (2026) public arrays, reused from P3.

## Commands

```sh
python3 -m pytest tests/test_p5_replication.py        # synthetic data only
python3 scripts/p5_submission_audit.py --r-library /private/tmp/p5-r-library
python3 scripts/p5_provenance_audit.py
python3 scripts/p5_five_sense_check.py
python3 scripts/p5_descriptive_tables.py
MPLCONFIGDIR=/private/tmp/p5-matplotlib python3 scripts/build_p5_submission.py
```

`--project all` never runs P5. Without a registration URL, a freeze file, and an unchanged plan, `--project P5` exits with status 2 before loading any data.

## Registration history

The original pre-registration checklist included confirming the sixth-domain equivalence. That check did not catch the mismatch before freezing. It was resolved during the 17 October submission audit and is disclosed in the deviations log. Do not refreeze or edit the registered plan to remove the error. Audit reruns go to the separate review directory, preserving the original `runs/latest/P5` files.

**Registration:** https://osf.io/87udm. Draft records are in `projects/osf_drafts/`.

## Exploratory follow-ups (not in the registered plan)

Added 10 Oct 2026, after the registered results were seen. Report them as exploratory.

```sh
python3 scripts/p5_exploratory.py --preregistration-url https://osf.io/87udm   # New et al. + Arnold et al.
python3 scripts/p5_dance_traits.py                                             # Dance, Ward & Simner (2021); needs pyreadstat
```

- E1 answering style: floor and top-score rates per sense, in both studies.
- E2 H1 among people who passed every attention check.
- E3 where the gap sits: H1 among people with some imagery in all six senses; percentile differences (both studies).
- E4 emotion, voice and inner-body imagery (New et al. only).
- E5 H1 adjusted for current treatment and education.
- E6 the empathy item, and H1 adjusted for it.
- Autism vs ADHD on having no imagery in at least one sense.
- Dance et al.: AQ vs imagery within people with and without aphantasia.
