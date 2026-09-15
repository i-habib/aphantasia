#!/usr/bin/env python3
"""Privacy-conscious structural audit of source archives already in this workspace.

Reports hashes, archive members, tabular headers/dimensions, and missingness
counts only. It does not print or extract participant-level values.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SHEET_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _xlsx_audit(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_map = {item.attrib["Id"]: item.attrib["Target"] for item in relationships}
        sheets = []
        for item in workbook.findall("m:sheets/m:sheet", SHEET_NS):
            target = rel_map[item.attrib[f"{{{SHEET_NS['r']}}}id"]]
            member = target.lstrip("/") if target.startswith("/") else "xl/" + target
            root = ET.fromstring(archive.read(member))
            dimension = root.find("m:dimension", SHEET_NS)
            rows = root.findall(".//m:sheetData/m:row", SHEET_NS)
            # This source may have participant responses in its first row, so
            # the structural audit deliberately records no cell values.
            sheets.append({"sheet": item.attrib["name"], "dimension": dimension.attrib.get("ref") if dimension is not None else None,
                           "row_elements": len(rows)})
    return {"kind": "xlsx", "sheets": sheets}


def _csv_audit_from_zip(path: Path, member: str) -> dict[str, Any]:
    import pandas as pd
    with zipfile.ZipFile(path) as archive, archive.open(member) as stream:
        frame = pd.read_csv(stream, dtype="string", keep_default_na=False)
    missing = {column: int(frame[column].eq("").sum()) for column in frame.columns if frame[column].eq("").any()}
    return {"kind": "csv", "member": member, "rows": int(len(frame)), "columns": list(map(str, frame.columns)),
            "duplicate_column_names": int(frame.columns.duplicated().sum()), "blank_counts": missing}


def _text_archive_audit(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        members = []
        for info in archive.infolist():
            item: dict[str, Any] = {"name": info.filename, "size": info.file_size}
            suffix = Path(info.filename).suffix.lower()
            if suffix in {".csv", ".tsv", ".tab"}:
                raw = archive.read(info)
                sample = raw[:4096].decode("utf-8-sig", errors="replace")
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
                except csv.Error:
                    dialect = csv.excel
                rows = csv.reader(io.StringIO(raw.decode("utf-8-sig", errors="replace")), dialect)
                item["columns"] = next(rows, [])
                item["data_rows"] = sum(1 for _ in rows)
            elif suffix in {".txt", ".md", ".r", ".py", ".m", ".do", ".sps"}:
                text = archive.read(info).decode("utf-8", errors="replace")
                if "Analyses/Exp" in info.filename and suffix == ".txt":
                    sample = text[:4096]
                    try:
                        dialect = csv.Sniffer().sniff(sample, delimiters="\t,;")
                    except csv.Error:
                        dialect = csv.excel_tab
                    rows = csv.reader(io.StringIO(text), dialect)
                    item["columns"] = next(rows, [])
                    item["data_rows"] = sum(1 for _ in rows)
                elif suffix in {".r", ".py", ".m", ".do", ".sps"}:
                    clues = [line.strip()[:260] for line in text.splitlines() if re.search(r"read\.(csv|table)|read_sav|load\(|\.sav|\.xlsx|\.csv|\.txt|read_excel|import pandas|File\s*=", line, re.I)]
                    if clues:
                        item["data_io_references"] = clues[:40]
                elif info.filename.lower() == "readme":
                    item["text"] = text[:5000]
            elif suffix == ".docx":
                # The archive contains interview transcripts. Never inspect or
                # emit their text as part of a dataset inventory.
                item["content_status"] = "not_read_interview_or_document_content"
            members.append(item)
    return {"kind": "zip", "members": members}


def audit(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"root": str(root), "sources": {}}
    files = {
        "p1_new": (root / "2bdn6-osfstorage-archive.zip", "zip"),
        "p3_arnold": (root / "Autism_Aphantasia_Data_FINAL.xlsx", "xlsx"),
        "p3_arnold_code": (root / "Autism_Aphantasia_Analyses_code.zip", "zip"),
        "p3_dance": (root / "h24vm-osfstorage-archive.zip", "zip"),
        "p4_mawtus": (root / "v7krh-osfstorage-archive.zip", "zip"),
        "p4_mawtus_stage1": (root / "uamcp-osfstorage-archive.zip", "zip"),
    }
    for name, (path, kind) in files.items():
        if not path.is_file():
            result["sources"][name] = {"status": "missing", "path": str(path)}
            continue
        detail = _xlsx_audit(path) if kind == "xlsx" else _text_archive_audit(path)
        detail.update({"status": "present_unverified_provenance", "path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)})
        result["sources"][name] = detail
    mawtus = result["sources"].get("p4_mawtus", {})
    csv_members = [item["name"] for item in mawtus.get("members", []) if item["name"].lower().endswith(".csv")]
    if len(csv_members) == 1:
        result["sources"]["p4_mawtus"]["tabular_audit"] = _csv_audit_from_zip(files["p4_mawtus"][0], csv_members[0])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "private" / "source-audit.json")
    args = parser.parse_args()
    report = audit(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    legacy_output = ROOT / "reports" / "source-audit.json"
    if legacy_output != args.output and legacy_output.exists():
        legacy_output.unlink()
    # Keep the console output useful and compact; the detailed schema report is
    # private under reports/private/ and raw participant values are never shown.
    for name, source in report["sources"].items():
        if source.get("status") == "missing":
            print(f"{name}: missing")
            continue
        digest = str(source.get("sha256", ""))[:12]
        summary = [f"{name}: {source.get('bytes', 0)} bytes", f"sha256={digest}"]
        if source.get("kind") == "xlsx":
            summary.extend(f"{sheet['sheet']}: {sheet.get('row_elements', 0)} rows" for sheet in source.get("sheets", []))
        elif source.get("kind") == "zip":
            summary.append(f"{len(source.get('members', []))} archive members")
        table = source.get("tabular_audit")
        if table:
            summary.append(f"tabular={table.get('rows', 0)} rows x {len(table.get('columns', []))} columns")
        print("; ".join(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
