"""Exploratory P5 follow-up in Dance, Ward & Simner (2021, Perception), OSF h24vm.

Not in the registered plan. Asks whether autistic traits (AQ total without item 3)
go with weaker imagery among people who HAVE visual imagery, using Experiment 1's
non-aphantasic group, and repeats this in the aphantasic group and Experiment 2.

Experiment 1 recruited people with and without aphantasia, so the two groups are
analysed separately rather than pooled.

Needs pyreadstat to read the SPSS files:
    python3 -m pip install pyreadstat
    python3 scripts/p5_dance_traits.py
Writes aggregate results only, to runs/latest/P5/p5_dance_traits.json.
"""
from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

import pyreadstat
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "h24vm-osfstorage-archive.zip"
PSIQ = {"visual": "PSIQ_VISUAL_SCORE", "auditory": "PSIQ_AUDITORY_SCORE", "smell": "PSIQ_OLFACTORY_SCORE",
        "taste": "PSIQ_TASTE_SCORE", "touch": "PSIQ_TACTILE_SCORE", "body": "PSIQ_BODY_SENSATION_SCORE",
        "feeling": "PSIQ_FEELING_SCORE"}
SIX = ["visual", "auditory", "smell", "taste", "touch", "body"]
AQ = "AQ_score_minus_Q3"


def _read(member: str):
    with zipfile.ZipFile(ARCHIVE) as archive, tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / Path(member).name
        path.write_bytes(archive.read(member))
        frame, _ = pyreadstat.read_sav(str(path))
    return frame


def _rho(x, y) -> dict:
    result = spearmanr(x, y, nan_policy="omit")
    return {"rho": float(result.statistic), "p": float(result.pvalue)}


def main() -> int:
    exp1 = _read("Data/Exp1_SensoryImagerySensitivityData.sav").rename(columns={v: k for k, v in PSIQ.items()})
    exp2 = _read("Data/Exp2_ImageryAndGSQData.sav").dropna(subset=[AQ, "VVIQ1"])
    out = {"label": "exploratory; not in the registered plan", "source": "Dance, Ward & Simner (2021), OSF h24vm",
           "scales": "Psi-Q sense scores 0-10; AQ total without item 3"}
    for code, name in ((0, "exp1_non_aphantasic"), (1, "exp1_aphantasic")):
        group = exp1.loc[exp1["aphantasia"].eq(code)].dropna(subset=[AQ])
        block = {"n": int(len(group)), "aq_mean": float(group[AQ].mean()),
                 "six_sense_mean": _rho(group[AQ], group[SIX].mean(axis=1))}
        block.update({sense: _rho(group[AQ], group[sense]) for sense in PSIQ})
        out[name] = block
    out["exp2_general_population_vviq"] = {"n": int(len(exp2)), **_rho(exp2[AQ], exp2["VVIQ1"])}
    target = ROOT / "runs" / "latest" / "P5" / "p5_dance_traits.json"
    target.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
