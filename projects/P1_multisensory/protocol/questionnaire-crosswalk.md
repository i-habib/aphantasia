# P1 questionnaire crosswalk

This audit records the source wording used for the treatment and neurodevelopmental fields. It was completed from the PDF files inside the public New et al. OSF archive (`2bdn6-osfstorage-archive.zip`) on 14 September 2026. The PDFs were text-extracted locally with `scripts/extract_pdf_text.swift`; no participant-level responses were written.

| Study | Source field | PDF location | Verified wording / branch | Pipeline coding |
|---|---|---|---|---|
| Study 1 | `diag` | `Questionnaires/Study1.Questionnaires.pdf`, p. 4 | “Are you currently receiving treatment for a neurologic or psychiatric condition?” Response choices are “No, I am not currently receiving treatment” and “Yes, I am currently receiving treatment.” | No = 0; Yes = 1; other/skip = missing |
| Study 1 | `diag2` | `Questionnaires/Study1.Questionnaires.pdf`, p. 4 | “What treatment do you receive?” This open follow-up is displayed only after the Yes branch (`DIAG.NAOK == "02"`). | Excluded from all models |
| Study 2 | `diag` | `Questionnaires/Study2.Questionnaires.pdf`, p. 5 | The same current-treatment question and No/Yes response wording as Study 1. | No = 0; Yes = 1; other/skip = missing |
| Study 2 | `isneurodev` | `Questionnaires/Study2.Questionnaires.pdf`, p. 3 | “Have you ever been diagnosed with, or strongly suspected to have, a neurodevelopmental disorder such as Autism Spectrum Disorder (ASD), Attention-Deficit/Hyperactivity Disorder (ADHD), or a learning disability?” | Kept as one broad diagnosed-or-strongly-suspected secondary outcome; not relabeled as autism or ADHD |

The `diag` crosswalk is therefore confirmed rather than provisional. The treatment outcome is a current-treatment status item, not a diagnosis, symptom-severity measure, treatment type, or causal exposure. `diag2` is intentionally excluded because it is open text and structurally conditioned on a Yes response. The Study 2 neurodevelopmental field is retained only as the broad outcome stated above.

