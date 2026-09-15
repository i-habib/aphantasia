"""Command line runner for the public-data aphantasia analyses."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .datasets import audit_mawtus_feasibility, load_arnold_code, load_new_studies
from .models import run_p1, run_p3


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def run_all(root: Path, output: Path) -> dict:
    result: dict = {}
    p1_frame, p1_flow = load_new_studies(root / "2bdn6-osfstorage-archive.zip")
    result["P1"] = run_p1(p1_frame, output / "P1")
    _write_json(output / "P1" / "p1_source_flow.json", p1_flow)

    group_frame, author_code_frame, trait_frame, p3_source = load_arnold_code(root / "Autism_Aphantasia_Analyses_code.zip")
    result["P3"] = run_p3(group_frame, trait_frame, output / "P3", author_code_frame)
    _write_json(output / "P3" / "p3_source_flow.json", p3_source)

    p4 = audit_mawtus_feasibility(root / "v7krh-osfstorage-archive.zip")
    _write_json(output / "P4" / "p4_feasibility.json", p4)
    result["P4"] = {"status": p4["decision"], "artifacts": [str(output / "P4" / "p4_feasibility.json")]}
    result["P2"] = {"status": "blocked_awaiting_access", "reason": "NZAVS linked extract and permission are not available."}
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the staged, aggregate-only aphantasia analyses.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Workspace containing the staged public archives (defaults to the current directory).")
    parser.add_argument("--output", type=Path, default=None, help="Aggregate-only output directory; defaults to ROOT/runs/latest.")
    parser.add_argument("--project", choices=["all", "P1", "P3", "P4"], default="all")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    output = (args.output or root / "runs" / "latest").resolve()
    if args.project == "all":
        result = run_all(root, output)
    elif args.project == "P1":
        frame, flow = load_new_studies(root / "2bdn6-osfstorage-archive.zip")
        result = {"P1": run_p1(frame, output / "P1")}
        _write_json(output / "P1" / "p1_source_flow.json", flow)
    elif args.project == "P3":
        group_frame, author_code_frame, trait_frame, source = load_arnold_code(root / "Autism_Aphantasia_Analyses_code.zip")
        result = {"P3": run_p3(group_frame, trait_frame, output / "P3", author_code_frame)}
        _write_json(output / "P3" / "p3_source_flow.json", source)
    else:
        p4 = audit_mawtus_feasibility(root / "v7krh-osfstorage-archive.zip")
        _write_json(output / "P4" / "p4_feasibility.json", p4)
        result = {"P4": {"status": p4["decision"], "artifacts": [str(output / "P4" / "p4_feasibility.json")]}}
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"Aggregate-only results: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
