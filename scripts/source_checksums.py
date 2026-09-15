#!/usr/bin/env python3
"""Print SHA-256 fingerprints for the staged source files only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "2bdn6-osfstorage-archive.zip",
    "Autism_Aphantasia_Data_FINAL.xlsx",
    "Autism_Aphantasia_Analyses_code.zip",
    "h24vm-osfstorage-archive.zip",
    "v7krh-osfstorage-archive.zip",
    "uamcp-osfstorage-archive.zip",
]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> int:
    result = {}
    for name in FILES:
        path = ROOT / name
        result[name] = {"bytes": path.stat().st_size, "sha256": digest(path)} if path.exists() else {"status": "missing"}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
