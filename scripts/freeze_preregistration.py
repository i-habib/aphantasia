"""Record the SHA-256 of a project's plan exactly as registered.

Run once, immediately after uploading the plan to the registry:

    python3 scripts/freeze_preregistration.py --project P5
    python3 scripts/freeze_preregistration.py --project P7

The project's analysis refuses to run if the plan changes afterwards.
Record later changes in that project's deviations log rather than editing the plan.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aphantasia.p5 import PLAN_PATH as P5_PLAN, plan_digest  # noqa: E402
from aphantasia.p7 import PLAN_PATH as P7_PLAN  # noqa: E402

PLANS = {"P5": P5_PLAN, "P7": P7_PLAN}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", choices=sorted(PLANS), required=True)
    plan = PLANS[parser.parse_args().project]
    target = ROOT / plan.with_name("preregistration.sha256")
    if target.exists():
        print(f"{target.relative_to(ROOT)} already exists; a registered plan is frozen once. Delete it only if the registration was withdrawn.")
        return 1
    digest = plan_digest(ROOT, plan)
    target.write_text(f"{digest}  {plan.name}\n", encoding="utf-8")
    print(f"Frozen {plan} at SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
