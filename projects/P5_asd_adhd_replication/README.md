# P5 — autism, ADHD and multisensory imagery: a preregistered test of Arnold et al. (2026)

**State:** registered on OSF 10 Oct 2026 (https://osf.io/87udm, embargoed until 24 Nov 2026), plan frozen, registered analysis run once. Exploratory follow-ups added afterwards are listed below.

- Plan: [`protocol/preregistration.md`](protocol/preregistration.md) · deviations: [`protocol/deviations.md`](protocol/deviations.md)
- Data: New et al. (2026) Study 2 (OSF 2bdn6). The `neurodev2` checklist identifies ASD (n=150), ADHD-only (n=84) and other conditions (n=20) among 1,003 participants; the source paper analysed only the pooled indicator.
- Anchor: Arnold et al. (2026) public arrays, reused from P3.

## Commands

```sh
python3 scripts/run_available.py --project P5-plan    # safe now: power plan from Arnold + New group counts
python3 -m pytest tests/test_p5_replication.py        # synthetic data only
python3 scripts/freeze_preregistration.py --project P5             # once, right after registering
python3 scripts/run_available.py --project P5 --preregistration-url https://osf.io/XXXXX
```

`--project all` never runs P5. Without a registration URL, a freeze file, and an unchanged plan, `--project P5` exits with status 2 before loading any data.

## Before registering (moved from the plan)

- [ ] Fill in authors, affiliations, ORCIDs.
- [ ] Read the plan end to end; confirm hypotheses, order (§6.1) and exclusions (§3.2). Any edit must happen **now**.
- [ ] Confirm the Arnold "movement" column and New `motor` field measure comparable content, using Arnold's PSI-Q materials; revise §4.2 if not.
- [ ] Run `python3 -m pytest` (all pass; synthetic data only).
- [ ] Register on OSF (secondary data template), attaching this file, and paste the URL in the header.
- [ ] Run `python3 scripts/freeze_preregistration.py --project P5` on the uploaded text.
- [ ] Run the analysis **once**: `python3 scripts/run_available.py --project P5 --preregistration-url <URL>`.

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
