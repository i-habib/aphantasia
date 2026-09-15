#!/usr/bin/env python3
"""Print privacy-safe structural checks for the staged public datasets.

Only aggregate counts and instrument-column labels are emitted. Participant
rows, platform IDs, free-text answers, and interview contents stay in memory.
"""
from __future__ import annotations

import io
import importlib.util
import json
import re
import shutil
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
SAFE_CATEGORY = re.compile(r"^(?:-?\d+(?:\.\d+)?|yes|no|true|false|0|1|other|prefer not to say|not sure|unknown)$", re.I)
SCHEMA_TERMS = re.compile(r"autis|diagnos|formal|group|\bAQ\b|\bCATI\b|VVIQ", re.I)


def _safe_distribution(series: pd.Series) -> dict[str, Any]:
    values = series.dropna()
    clean = values.astype(str).str.strip()
    clean = clean[clean.ne("")]
    distinct = clean.nunique()
    result: dict[str, Any] = {"nonblank": int(len(clean)), "distinct": int(distinct)}
    if distinct <= 12 and all(SAFE_CATEGORY.fullmatch(value) for value in clean.unique()):
        counts = Counter(clean.str.lower())
        result["codes"] = {key: (count if count >= 5 else "<5") for key, count in sorted(counts.items())}
    else:
        result["levels_redacted"] = True
    numeric = pd.to_numeric(clean, errors="coerce")
    if len(clean) and numeric.notna().all():
        result["numeric_min"] = float(numeric.min())
        result["numeric_max"] = float(numeric.max())
    return result


def inspect_new() -> dict[str, Any]:
    archive_path = ROOT / "2bdn6-osfstorage-archive.zip"
    members = {
        1: "Analyses/Exp1.1003.txt",
        2: "Analyses/Exp3.1020.txt",
    }
    watched = ["nbact", "hp", "diag", "diag2", "isneurodev", "neurodev2", "age", "sex", "lastpage"]
    result: dict[str, Any] = {}
    with zipfile.ZipFile(archive_path) as archive:
        for study, member in members.items():
            with archive.open(member) as stream:
                frame = pd.read_csv(stream, sep="\t", dtype="string", keep_default_na=False, encoding="cp1252")
            fields = {col: _safe_distribution(frame[col]) for col in watched if col in frame.columns}
            attentiveness = pd.to_numeric(frame.get("nbact"), errors="coerce")
            excluded = int((attentiveness < 3).sum()) if attentiveness is not None else None
            retained = frame.loc[attentiveness.ge(3)]
            sex_outcome_cells = []
            if "sex" in retained and "diag" in retained:
                sex_values = retained["sex"].astype(str)
                outcome_values = pd.to_numeric(retained["diag"], errors="coerce")
                for index, level in enumerate(sorted(sex_values.unique()), start=1):
                    mask = sex_values == level
                    yes = int((outcome_values[mask] == 1).sum())
                    no = int((outcome_values[mask] == 0).sum())
                    sex_outcome_cells.append({"sex_level_index": index, "n": int(mask.sum()),
                                              "treatment_yes": yes if yes >= 5 else "<5",
                                              "treatment_no": no if no >= 5 else "<5"})
            result[f"study_{study}"] = {
                "raw_rows": int(len(frame)),
                "columns": int(len(frame.columns)),
                "quality_check_nbact_lt_3": excluded,
                "retained_if_nbact_ge_3": int(len(frame) - excluded) if excluded is not None else None,
                "treatment_yes_after_attention": int((pd.to_numeric(retained["diag"], errors="coerce") == 1).sum()) if "diag" in retained else None,
                "treatment_by_sex_level_index": sex_outcome_cells,
                "fields": fields,
            }
    return result


def inspect_arnold_headers() -> dict[str, Any]:
    path = ROOT / "Autism_Aphantasia_Data_FINAL.xlsx"
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall(f"{{{PKG_REL_NS}}}Relationship")}
        sheet = workbook.find(f"{{{MAIN_NS}}}sheets/{{{MAIN_NS}}}sheet")
        target = rel_map[sheet.attrib[f"{{{REL_NS}}}id"]]
        member = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_xml = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(node.text or "" for node in si.findall(f".//{{{MAIN_NS}}}t")) for si in shared_xml.findall(f"{{{MAIN_NS}}}si")]
        root = ET.fromstring(archive.read(member))
        first_row = root.find(f".//{{{MAIN_NS}}}sheetData/{{{MAIN_NS}}}row")
        labels: list[tuple[str, str]] = []
        if first_row is not None:
            for cell in first_row.findall(f"{{{MAIN_NS}}}c"):
                value = cell.find(f"{{{MAIN_NS}}}v")
                text = value.text if value is not None else ""
                if cell.attrib.get("t") == "s" and text:
                    text = shared[int(text)]
                inline = cell.find(f"{{{MAIN_NS}}}is")
                if inline is not None:
                    text = "".join(node.text or "" for node in inline.findall(f".//{{{MAIN_NS}}}t"))
                if text and (SCHEMA_TERMS.search(text) or cell.attrib.get("r", "") in {"A1", "B1", "C1", "D1", "F1", "G1", "H1"}):
                    labels.append((cell.attrib.get("r", "?"), re.sub(r"\s+", " ", text)[:180]))
        labels = labels[:36]
        dim = root.find(f"{{{MAIN_NS}}}dimension")
        row_count = len(root.findall(f".//{{{MAIN_NS}}}sheetData/{{{MAIN_NS}}}row"))
        return {"sheet": sheet.attrib.get("name"), "dimension": dim.attrib.get("ref") if dim is not None else None,
                "xml_rows": row_count, "matched_first_row_labels": labels}


def _matlab_matrix_shape(text: str, variable: str) -> list[int] | None:
    match = re.search(rf"(?ms)^\s*{re.escape(variable)}\s*=\s*\[(.*?)\]\s*;", text)
    if not match:
        return None
    rows = []
    for raw_line in match.group(1).splitlines():
        line = raw_line.split("%", 1)[0].strip()
        if not line:
            continue
        tokens = re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", line)
        if tokens:
            rows.append(len(tokens))
    if not rows:
        return [0, 0]
    return [len(rows), max(rows)] if len(set(rows)) == 1 else [len(rows), -1]


def inspect_arnold_code() -> dict[str, Any]:
    names = ["Control_PSIQ", "ASD_PSIQ", "AQ_Items", "Subscale_Scores", "ASD_Ages", "ASD_Genders", "CONTROL_AGEs", "CONTROL_Genders"]
    archive_path = ROOT / "Autism_Aphantasia_Analyses_code.zip"
    with zipfile.ZipFile(archive_path) as archive:
        member = "Autism_Aphantasia_Analyses_code.m"
        text = archive.read(member).decode("utf-8", errors="replace")
    return {"matrix_shapes": {name: _matlab_matrix_shape(text, name) for name in names},
            "group_thresholds": {name: int(value) for name, value in re.findall(r"(?m)^(Consistent_Threshold|Pronounced_Threshold)\s*=\s*(\d+);", text)}}


def runtime_capabilities() -> dict[str, Any]:
    modules = ["pypdf", "PyPDF2", "fitz", "pyreadstat", "openpyxl", "statsmodels", "patsy"]
    executables = ["Rscript", "pspp", "pdftotext"]
    return {"python_modules": {name: importlib.util.find_spec(name) is not None for name in modules},
            "executables": {name: shutil.which(name) is not None for name in executables}}


def main() -> int:
    report = {"new": inspect_new(), "arnold": inspect_arnold_headers(), "arnold_code": inspect_arnold_code(), "runtime": runtime_capabilities()}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
