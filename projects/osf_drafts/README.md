# OSF registration drafts (private, not registered)

Both drafts use OSF's *Secondary Data Preregistration* template. They were created 29 Sep 2026 in Ivan Habib's OSF account with no linked project. Every answer was verified against these JSON files by SHA-256. Answers were rewritten in plain language on 30 Sep–1 Oct 2026; the first wording is kept in `*_v1.json`.

| Project | Draft (review page) | Plan file SHA-256 quoted in the draft |
|---|---|---|
| P5 | https://osf.io/registries/drafts/6abc78217bf6140b0157b646/review | `18202a92002326c904aecfb369e3dd27dfca3b2d1382b045d250bea4f9157928` |
| P7 | https://osf.io/registries/drafts/6abc7b03e6c491a5f6b5f205/review | `7c077ebc698825bd516ff69ee99296b4434c518964b1346a73fa3bb10d04a6bd` |

`p5_osf_responses.json` / `p7_osf_responses.json` hold the exact answers (OSF field keys 72-2 … 72-61).

**If you edit a plan file** (for example, to add an affiliation), its SHA-256 changes. Update the hash in that draft's "Statistical models" answer before registering, then run `freeze_preregistration.py`. The code checks the frozen hash against the file.
