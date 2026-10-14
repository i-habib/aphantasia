"""Push P8 Kaggle sessions: shards that each compute a share of the profile pieces, or the session that assembles them.

    python3 scripts/p8_kaggle_push.py shards profile_size 1/3 2/3 3/3
    python3 scripts/p8_kaggle_push.py assemble ivanhabib/p8-aphantasia-taxometrics ivanhabib/p8-aphantasia-shard-1-3 ...

Each shard is its own private kernel (p8-aphantasia-shard-<name>) using the same code and the private dataset
`p8-aphantasia-bundle`. The assembling session (p8-aphantasia-assemble) takes the listed kernels' outputs as inputs,
so it starts with every piece they saved and computes only what is left.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "runs" / "kaggle_p8" / "push"
DATASET = "ivanhabib/p8-aphantasia-bundle"


def push(slug: str, title: str, shard: str, sources: list[str]) -> None:
    folder = STAGE / slug
    folder.mkdir(parents=True, exist_ok=True)
    code = (ROOT / "scripts" / "p8_kaggle.py").read_text()
    code, count = re.subn(r'^SHARD = ""$', f'SHARD = "{shard}"', code, flags=re.M)
    script = (ROOT / "scripts" / "p8_taxometrics.R").read_bytes()
    code, replaced = re.subn(r'^R_SCRIPT_B64 = ""$', lambda _: f'R_SCRIPT_B64 = "{base64.b64encode(script).decode()}"', code, flags=re.M)
    assert count == 1 and replaced == 1
    print(slug, "R script SHA-256", hashlib.sha256(script).hexdigest())
    (folder / "p8_kaggle.py").write_text(code)
    meta = {"id": f"ivanhabib/{slug}", "title": title, "code_file": "p8_kaggle.py", "language": "python",
            "kernel_type": "script", "is_private": True, "enable_gpu": False, "enable_tpu": False, "enable_internet": True,
            "dataset_sources": [DATASET], "kernel_sources": sources, "competition_sources": [], "model_sources": []}
    (folder / "kernel-metadata.json").write_text(json.dumps(meta, indent=2))
    done = subprocess.run(["kaggle", "kernels", "push", "-p", str(folder)], capture_output=True, text=True)
    print(slug, (done.stdout + done.stderr).strip().splitlines()[-1:] or "")


def main(argv: list[str]) -> int:
    if argv[:1] == ["shards"]:
        for shard in argv[1:]:
            name = shard.replace("/", "-").replace("_", "-").replace(":", "-")
            push(f"p8-aphantasia-shard-{name}", f"P8 Aphantasia Shard {name}", shard, [])
        return 0
    if argv[:1] == ["assemble"]:
        push("p8-aphantasia-assemble", "P8 Aphantasia Assemble", "", argv[1:])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
