# P8: is aphantasia a separate group or the low end of a continuum?

**State:** plan drafted 11 Oct 2026; not registered. No taxometric analysis has been run on real data.

- Plan: [`protocol/preregistration.md`](protocol/preregistration.md); changes: [`protocol/deviations.md`](protocol/deviations.md)
- Code: `scripts/p8_taxometrics.R` (RTaxometrics 3.2.1), gate in `src/aphantasia/p8.py`
- Data (in `data_raw/`, not in git):
  - `monzel2026_total_data_set.Rdata`: Aphantasia Network VVIQ items, 35,467 people (OSF 8fn9v, view-only link from Monzel et al. 2026). SHA-256 `2f601bff…5e6`.
  - `dance2021_prevalence.sav`: Dance et al. (2022) unselected VVIQ items, 1,004 people (OSF mxyv9). SHA-256 `43512d39…633`.
  - New et al. (2026) surveys: the `2bdn6` archive at the repo root.

## Commands

```sh
Rscript scripts/p8_taxometrics.R --selftest            # simulated data, seconds
Rscript scripts/p8_taxometrics.R --selftest --full     # simulated taxometric runs, ~6 min
python3 -m pytest tests/test_p8_taxometrics.py
python3 scripts/freeze_preregistration.py --project P8   # once, right after registering
python3 scripts/run_available.py --project P8 --preregistration-url <URL>   # several hours
```

Needs R 4.5 or later with `RTaxometrics` 3.2.1 and `jsonlite`.

## Before registering

- [ ] Read the plan; any edit must happen now.
- [ ] Check reuse terms for the Aphantasia Network data (shared through a view-only OSF link in Monzel et al. 2026); cite the dataset and consider contacting the authors.
- [ ] Register on OSF, freeze, then run once.
