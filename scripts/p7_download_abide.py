"""Download ABIDE I Preprocessed ROI time series, phenotype file and ROI atlases for P7.

Source: the public FCP-INDI S3 bucket (ABIDE Preprocessed, C-PAC pipeline) and
the preprocessed-connectomes-project/abide GitHub repository. All participants
are downloaded; motion exclusions are applied later by the registered plan.
Downloads resume (files with matching size are skipped). Nothing here opens
time-series contents or compares diagnostic groups.

    python3 scripts/p7_download_abide.py                          # primary set
    python3 scripts/p7_download_abide.py --strategy filt_global   # GSR sensitivity set
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "projects" / "P7_fin_connectivity_abide" / "data_raw" / "abide"
BUCKET = "https://s3.amazonaws.com/fcp-indi"
PREFIX = "data/Projects/ABIDE_Initiative/Outputs/cpac/{strategy}/{derivative}/"
PHENOTYPE = "data/Projects/ABIDE_Initiative/Phenotypic_V1_0b_preprocessed1.csv"
GITHUB_TREE = "https://api.github.com/repos/preprocessed-connectomes-project/abide/git/trees/HEAD?recursive=1"
GITHUB_RAW = "https://raw.githubusercontent.com/preprocessed-connectomes-project/abide/{sha}/{path}"
S3 = {"s": "http://s3.amazonaws.com/doc/2006-03-01/"}


def _get(url: str, attempts: int = 5) -> bytes:
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                return response.read()
        except OSError:
            if attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def list_objects(prefix: str) -> list[tuple[str, int]]:
    objects: list[tuple[str, int]] = []
    token = None
    while True:
        query = {"list-type": "2", "prefix": prefix, **({"continuation-token": token} if token else {})}
        root = ET.fromstring(_get(f"{BUCKET}?{urllib.parse.urlencode(query)}"))
        objects += [(c.find("s:Key", S3).text, int(c.find("s:Size", S3).text)) for c in root.findall("s:Contents", S3)]
        if root.find("s:IsTruncated", S3).text != "true":
            return objects
        token = root.find("s:NextContinuationToken", S3).text


def _download(key: str, size: int, target: Path) -> str:
    if target.exists() and target.stat().st_size == size:
        return "skipped"
    target.parent.mkdir(parents=True, exist_ok=True)
    data = _get(f"{BUCKET}/{urllib.parse.quote(key)}")
    if len(data) != size:
        raise OSError(f"size mismatch for {key}: {len(data)} != {size}")
    temporary = target.with_suffix(target.suffix + ".part")
    temporary.write_bytes(data)
    temporary.replace(target)
    return "downloaded"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch_atlases() -> dict[str, str]:
    tree = json.loads(_get(GITHUB_TREE))
    sha = tree["sha"]
    wanted = [item["path"] for item in tree["tree"]
              if item["type"] == "blob" and "resources/abide_rois" in item["path"] and ("cc400" in item["path"].lower() or "cc200" in item["path"].lower())]
    hashes = {"abide_github_tree_sha": sha}
    for path in wanted:
        target = OUT / "atlases" / Path(path).name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_get(GITHUB_RAW.format(sha=sha, path=urllib.parse.quote(path))))
        hashes[target.name] = sha256(target)
    return hashes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default="filt_noglobal", choices=["filt_noglobal", "filt_global"])
    parser.add_argument("--derivative", default="rois_cc400", choices=["rois_cc400", "rois_cc200"])
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    phenotype = OUT / "Phenotypic_V1_0b_preprocessed1.csv"
    phenotype.parent.mkdir(parents=True, exist_ok=True)
    phenotype.write_bytes(_get(f"{BUCKET}/{PHENOTYPE}"))

    prefix = PREFIX.format(strategy=args.strategy, derivative=args.derivative)
    objects = list_objects(prefix)
    folder = OUT / "cpac" / args.strategy / args.derivative
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda item: _download(item[0], item[1], folder / Path(item[0]).name), objects))

    listing = "\n".join(f"{Path(key).name}\t{size}" for key, size in sorted(objects))
    manifest = {
        "downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": f"{BUCKET}/{prefix}",
        "files": len(objects), "bytes": sum(size for _, size in objects),
        "downloaded": results.count("downloaded"), "skipped_existing": results.count("skipped"),
        "timeseries_listing_sha256": hashlib.sha256(listing.encode()).hexdigest(),
        "phenotype_url": f"{BUCKET}/{PHENOTYPE}", "phenotype_sha256": sha256(phenotype),
        "atlases": fetch_atlases(),
    }
    (OUT / f"manifest_{args.strategy}_{args.derivative}.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "atlases"}, indent=2))
    print("atlases:", ", ".join(k for k in manifest["atlases"] if k != "abide_github_tree_sha"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
