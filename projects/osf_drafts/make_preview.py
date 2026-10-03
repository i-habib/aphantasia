"""Render both OSF drafts' answers (from the JSON files) as one readable HTML page."""
import html, json, re
from pathlib import Path

HERE = Path(__file__).parent
PAGES = [("Study Information", [("72-2", "Research questions"), ("72-4", "Hypotheses")]),
         ("Data Description", [("72-7", "Datasets used"), ("72-9", "Data availability"), ("72-14", "Data access"), ("72-16", "Data identifiers"),
                               ("72-18", "Access date"), ("72-20", "Data collection procedures"), ("72-24", "Codebook")]),
         ("Variables", [("72-29", "Manipulated variables"), ("72-33", "Measured variables"), ("72-35", "Missing data"), ("72-37", "Unit of analysis"),
                        ("72-39", "Statistical outliers"), ("72-41", "Sampling weights")]),
         ("Knowledge of Data", [("72-44", "Prior publication / dissemination"), ("72-46", "Prior knowledge")]),
         ("Analyses", [("72-49", "Statistical models"), ("72-51", "Effect size"), ("72-53", "Statistical power"), ("72-55", "Inference criteria"),
                       ("72-57", "Assumption violation / model non-convergence"), ("72-59", "Reliability and robustness testing"), ("72-61", "Exploratory analysis")])]
DRAFTS = [("P5", "Questionnaire study: autism, ADHD and multisensory imagery", "p5_osf_responses.json", "6abc78217bf6140b0157b646",
           "Social and Behavioral Sciences › Psychology › Cognitive Psychology"),
          ("P7", "Brain connectivity study: fusiform imagery node in ABIDE", "p7_osf_responses.json", "6abc7b03e6c491a5f6b5f205",
           "Life Sciences › Neuroscience and Neurobiology › Cognitive Neuroscience")]


def fmt(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"(\[ADD PUBLIC REPOSITORY LINK\])", r"<mark>\1</mark>", text)
    return text.replace("\n", "<br>")


body, toc = [], []
for code, label, file, draft_id, subjects in DRAFTS:
    data = json.loads((HERE / file).read_text())
    answers = data["responses"]
    toc.append(f'<a href="#{code}">{code} · {html.escape(label)}</a>')
    body.append(f'<section id="{code}"><h2><span class="tag">{code}</span> {html.escape(label)}</h2>'
                f'<p class="meta">Private OSF draft · not registered · <a href="https://osf.io/registries/drafts/{draft_id}/review">open in OSF</a></p>'
                f'<h3>1 · Metadata</h3><dl><dt>Title</dt><dd>{fmt(data["title"])}</dd><dt>Description</dt><dd>{fmt(data["description"])}</dd>'
                f'<dt>Contributors</dt><dd>Ivan Habib</dd><dt>License</dt><dd>CC0 1.0 Universal</dd>'
                f'<dt>Subjects</dt><dd>{html.escape(subjects)}</dd><dt>Tags</dt><dd>{", ".join(map(html.escape, data["tags"]))}</dd></dl>')
    for number, (page, fields) in enumerate(PAGES, start=2):
        body.append(f"<h3>{number} · {page}</h3><dl>" + "".join(f"<dt>{name}</dt><dd>{fmt(answers.get(key, '(blank)'))}</dd>" for key, name in fields) + "</dl>")
    body.append("</section>")

CSS = """:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6b6a65;--line:#e4e1d8;--card:#fff;--accent:#2f5d8a;--mark:#fff1a8}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161615;--fg:#ecebe6;--muted:#a3a19a;--line:#33322f;--card:#1f1f1d;--accent:#8db6e0;--mark:#5c4f10}}
:root[data-theme="dark"]{--bg:#161615;--fg:#ecebe6;--muted:#a3a19a;--line:#33322f;--card:#1f1f1d;--accent:#8db6e0;--mark:#5c4f10}
body{background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,-apple-system,sans-serif;margin:0;padding:0 16px}
main{max-width:820px;margin:0 auto;padding:32px 0 80px}h1{font-size:1.6rem;margin:0 0 4px}.sub{color:var(--muted);margin:0 0 20px}
nav{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:28px}a{color:var(--accent)}
section{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 22px;margin-bottom:28px}
h2{font-size:1.25rem;margin:0}.tag{background:var(--accent);color:var(--card);border-radius:6px;padding:1px 8px;font-size:.9rem;margin-right:6px}
.meta{color:var(--muted);font-size:.9rem;margin:6px 0 10px}h3{font-size:1rem;margin:26px 0 8px;padding-top:12px;border-top:1px solid var(--line);color:var(--accent)}
dt{font-weight:600;margin-top:14px}dd{margin:4px 0 0;overflow-wrap:anywhere}mark{background:var(--mark);color:inherit;padding:0 3px;border-radius:3px}"""
page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>OSF Draft Preview</title><style>{CSS}</style></head><body><main><h1>OSF registration drafts</h1>"
        f'<p class="sub">What is saved in the two private drafts, checked against OSF. Nothing is left to fill in except your affiliation and ORCID on OSF.</p>'
        f'<nav>{" · ".join(toc)}</nav>{"".join(body)}</main></body></html>')
(HERE / "drafts_preview.html").write_text(page)
print("written", len(page))
