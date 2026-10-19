"""Aggregate-only reconciliation of Arnold workbook scores and MATLAB arrays."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aphantasia.datasets import _matlab_arrays  # noqa: E402


def main():
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    workbook = ROOT / "Autism_Aphantasia_Data_FINAL.xlsx"
    with zipfile.ZipFile(workbook) as z:
        strings = ["".join(n.itertext()) for n in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("s:si", ns)]
        source_rows = ET.fromstring(z.read("xl/worksheets/sheet1.xml")).findall(".//s:row", ns)
        def read(row):
            cells = {}
            for c in row:
                v = c.find("s:v", ns)
                if v is not None:
                    value = v.text
                    if c.attrib.get("t") == "s":
                        value = strings[int(value)]
                    cells["".join(t for t in c.attrib["r"] if t.isalpha())] = value
            return cells
        header = read(source_rows[0])
        data = [read(row) for row in source_rows[1:]]
    score_labels = ["PSIQ - V", "PSIQ - A", "PSIQ - S", "PSIQ - Tas", "PSIQ - Tou", "PSIQ - B"]
    columns = [next(k for k, v in header.items() if v == label) for label in score_labels]
    aq_col = next(k for k, v in header.items() if v == "AQ")
    age_col = next(k for k, v in header.items() if v.startswith("How old are you?"))
    attention_col = next(k for k, v in header.items() if v == "Attention Checks")
    def numeric(row, cols):
        try:
            return tuple(float(row[k]) for k in cols)
        except (ValueError, KeyError, TypeError):
            return None
    scores = [numeric(row, columns) for row in data]
    with zipfile.ZipFile(ROOT / "Autism_Aphantasia_Analyses_code.zip") as z:
        arrays = _matlab_arrays(z.read("Autism_Aphantasia_Analyses_code.m").decode())
    target = arrays["ASD_PSIQ"]
    target_aq = arrays["AQ_Items"].sum(axis=1)
    target_age = arrays["ASD_Ages"].ravel()
    score_counter = Counter(v for v in scores if v is not None)
    target_counter = Counter(map(tuple, target))
    combined = [numeric(row, [*columns, aq_col, age_col]) for row in data]
    full_counter = Counter(v for v in combined if v is not None)
    target_full = Counter(tuple([*s, q, age]) for s, q, age in zip(target, target_aq, target_age))
    missing_scores = sum((target_counter - score_counter).values())
    missing_full = sum((target_full - full_counter).values())
    retained = [row for row, score in zip(data, scores) if score is not None]
    attention_distribution = Counter(row.get(attention_col, "missing") for row in retained)
    remaining = target_full.copy()
    matched_attention = Counter()
    for row, signature in zip(data, combined):
        if remaining[signature] > 0:
            matched_attention[row.get(attention_col, "missing")] += 1
            remaining[signature] -= 1
    result = {
        "workbook_sha256": hashlib.sha256(workbook.read_bytes()).hexdigest(),
        "workbook_rows": len(data), "workbook_header_columns": len(header),
        "workbook_numeric_six_score_rows": len(retained), "code_autism_rows": len(target),
        "missing_code_score_vectors_from_workbook_multiset": missing_scores,
        "missing_code_score_AQ_age_vectors_from_workbook_multiset": missing_full,
        "attention_distribution_numeric_score_rows": dict(attention_distribution),
        "attention_distribution_matched_code_rows": dict(matched_attention),
        "score_columns": dict(zip(score_labels, columns)),
        "body_item_headers": [v for k, v in header.items() if v.startswith("Imagine the bodily sensation of...")],
        "control_provenance": "Not established by this autism-only workbook; full source methods still needed.",
        "participant_rows_written": False,
        "interpretation": "Numerical multiset matching establishes score provenance, not participant identities or independent recruitment."
    }
    out = ROOT / "projects/P5_asd_adhd_replication/review/validation"
    out.mkdir(parents=True, exist_ok=True)
    (out / "workbook_reconciliation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
