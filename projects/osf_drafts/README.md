# OSF registration drafts (private, not registered)

Both drafts use OSF's *Secondary Data Preregistration* template. They were created 29 Sep 2026 in Ivan Habib's OSF account with no linked project. Every answer was verified against these JSON files by SHA-256. Answers were rewritten in plain language on 30 Sep–1 Oct 2026; the first wording is kept in `*_v1.json`.

| Project | Draft (review page) | Plan file SHA-256 quoted in the draft |
|---|---|---|
| P5 | https://osf.io/registries/drafts/6abc78217bf6140b0157b646/review | `8a90ff1edef1573660b29e90666d1e8eae8f369cab70b2a9cdec97a9c0d57635` |
| P7 | https://osf.io/registries/drafts/6abc7b03e6c491a5f6b5f205/review | `337b7efe5f70b3f756950d5ea9d2005bfb88b724401217671191658e55e34e7c` |

`p5_osf_responses.json` / `p7_osf_responses.json` hold the exact answers (OSF field keys 72-2 … 72-61).

**If you edit a plan file** (for example, to add an affiliation), its SHA-256 changes. Update the hash in that draft's "Statistical models" answer before registering, then run `freeze_preregistration.py`. The code checks the frozen hash against the file.
