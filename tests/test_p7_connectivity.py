"""P7 tests: synthetic data, plus header-only and phenotype-count checks on real files.

No test computes connectivity from real ABIDE time series or compares groups.
"""
from __future__ import annotations

import gzip
import json
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aphantasia.cli import main  # noqa: E402
from aphantasia.models import AnalysisStop  # noqa: E402
from aphantasia.p5 import Registration  # noqa: E402
from aphantasia.p7 import (  # noqa: E402
    DATA,
    LEFT_TARGETS,
    NODES,
    analyse,
    apply_exclusions,
    map_nodes,
    person_edges,
    run_p7,
)

REAL = ROOT / DATA


def _write_nifti(path: Path, volume: np.ndarray, affine: np.ndarray) -> None:
    header = bytearray(348)
    struct.pack_into("<i", header, 0, 348)
    struct.pack_into("<8h", header, 40, 3, *volume.shape, 1, 1, 1, 1)
    struct.pack_into("<h", header, 70, 16)  # float32
    struct.pack_into("<h", header, 72, 32)
    struct.pack_into("<8f", header, 76, 1, 2, 2, 2, 1, 1, 1, 1)
    struct.pack_into("<f", header, 108, 352.0)
    struct.pack_into("<2f", header, 112, 1.0, 0.0)
    struct.pack_into("<h", header, 254, 4)
    struct.pack_into("<12f", header, 280, *affine[:3].reshape(-1))
    header[344:348] = b"n+1\0"
    path.write_bytes(gzip.compress(bytes(header) + b"\0" * 4 + volume.astype("<f4").tobytes(order="F")))


def _synthetic_atlas(directory: Path) -> Path:
    """2-mm MNI grid with one 4-voxel cube parcel per node plus 20 far 'other' parcels."""
    affine = np.array([[2, 0, 0, -90], [0, 2, 0, -126], [0, 0, 2, -72], [0, 0, 0, 1]], dtype=float)
    volume = np.zeros((91, 109, 91))
    inverse = np.linalg.inv(affine)
    for label, xyz in enumerate(NODES.values(), start=1):
        i, j, k = np.rint(inverse @ np.r_[xyz, 1])[:3].astype(int)
        volume[i - 1:i + 2, j - 1:j + 2, k - 1:k + 2] = label
    for extra in range(20):
        volume[10 + extra * 3:12 + extra * 3, 90:92, 70:72] = 100 + extra
    path = directory / "atlas.nii.gz"
    _write_nifti(path, volume, affine)
    return path


def test_map_nodes_assigns_each_coordinate_to_its_own_parcel():
    with tempfile.TemporaryDirectory() as directory:
        mapping = map_nodes(_synthetic_atlas(Path(directory)))
    assert [entry["parcel"] for entry in mapping["nodes"].values()] == list(range(1, len(NODES) + 1))
    assert all(entry["distance_mm"] == 0 for entry in mapping["nodes"].values())


def test_map_nodes_stops_when_coordinate_is_far_from_atlas():
    with tempfile.TemporaryDirectory() as directory:
        path = _synthetic_atlas(Path(directory))
        with pytest.raises(AnalysisStop) as stop:
            map_nodes(path, {"nowhere": (0.0, 0.0, 0.0)})
    assert stop.value.code == "node_outside_atlas"


def _node_map() -> dict:
    nodes = {name: {"parcel": index, "mni": list(xyz), "distance_mm": 0.0} for index, (name, xyz) in enumerate(NODES.items(), start=1)}
    centroids = {index: list(xyz) for index, xyz in enumerate(NODES.values(), start=1)}
    centroids.update({100 + e: [60.0, 60.0, 60.0 + e] for e in range(20)})
    return {"nodes": nodes, "parcel_centroids_mni": centroids}


def _series(rng: np.random.Generator, coupling: float, n: int = 200) -> pd.DataFrame:
    shared = rng.normal(size=n)
    columns = {}
    for index in range(1, len(NODES) + 1):
        weight = coupling if index <= 4 else 0.3
        columns[index] = weight * shared + rng.normal(size=n)
    for extra in range(20):
        columns[100 + extra] = 0.2 * shared + rng.normal(size=n)
    return pd.DataFrame(columns)


def test_person_edges_recovers_fisher_z_and_rejects_flat_node():
    rng = np.random.default_rng(1)
    series = _series(rng, coupling=1.0, n=5000)
    edges = person_edges(series, _node_map())
    expected = np.arctanh(1.0 / 2.0)  # corr of (s+e1, s+e2) with unit variances = 0.5
    assert edges["edge_left_pmd_mfg"] == pytest.approx(expected, abs=0.05)
    assert edges["specificity"] == pytest.approx(edges["primary_left_mean"] - edges["fin_other_mean"])
    series[1] = 0.0
    assert person_edges(series, _node_map()) is None


def _synthetic_frame(effect: float, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for site in range(8):
        for autism in (0, 1):
            for _ in range(40):
                age = rng.uniform(8, 40)
                edges = person_edges(_series(rng, coupling=1.0 + effect * autism, n=150), _node_map())
                rows.append({"autism": float(autism), "age": age, "age_sq": (age - 20) ** 2,
                             "fd": rng.uniform(0.02, 0.2), "sex": rng.choice(["1", "2"], p=[0.8, 0.2]),
                             "eyes": rng.choice(["1", "2"]), "site": f"S{site}", "fiq": rng.normal(105, 12),
                             "ADOS_TOTAL": rng.integers(7, 20) if autism else np.nan, **edges})
    return pd.DataFrame(rows)


def test_analyse_detects_reduced_coupling_and_writes_aggregates_only():
    registration = Registration(url="https://osf.io/synthetic", plan_sha256="0" * 64)
    with tempfile.TemporaryDirectory() as directory:
        result = analyse(_synthetic_frame(effect=-0.6), [{"step": "synthetic", "n": 640}], Path(directory), registration=registration)
        diagnostics = json.loads(Path(next(p for p in result["artifacts"] if p.endswith(".json"))).read_text(encoding="utf-8"))
        estimates = pd.read_csv(next(p for p in result["artifacts"] if p.endswith(".csv")))
    assert diagnostics["details"]["H1"]["estimate"] < 0
    assert diagnostics["details"]["H1"]["ci95"][1] < 0
    assert diagnostics["details"]["interpretation"] in {"reduced_and_specific", "reduced_not_specific"}
    assert set(diagnostics["details"]["secondary_holm"]) == {"H2_specificity", *[f"edge_{n}" for n in LEFT_TARGETS], "lateralisation"}
    assert diagnostics["contains_participant_rows"] is False
    assert set(estimates["term"]) <= {"autism", "autism_x_age"}


def test_analyse_null_effect_is_not_called_reduced():
    registration = Registration(url="https://osf.io/synthetic", plan_sha256="0" * 64)
    with tempfile.TemporaryDirectory() as directory:
        result = analyse(_synthetic_frame(effect=0.0, seed=11), [], Path(directory), registration=registration)
        diagnostics = json.loads(Path(next(p for p in result["artifacts"] if p.endswith(".json"))).read_text(encoding="utf-8"))
    assert diagnostics["details"]["interpretation"] in {"inconclusive", "equivalent_to_null", "increased", "reduced_not_specific", "reduced_and_specific"}
    assert "equivalence" in diagnostics["details"]["H1"]


def test_run_p7_and_cli_refuse_without_registration():
    with pytest.raises(AnalysisStop):
        run_p7(ROOT, Path(tempfile.mkdtemp()), registration="https://osf.io/x")  # type: ignore[arg-type]
    with tempfile.TemporaryDirectory() as directory:
        assert main(["--project", "P7", "--root", directory]) == 2


@pytest.mark.skipif(not (REAL / "Phenotypic_V1_0b_preprocessed1.csv").exists(), reason="ABIDE not downloaded")
def test_real_exclusion_flow_counts_are_monotone():
    phenotype = pd.read_csv(REAL / "Phenotypic_V1_0b_preprocessed1.csv")
    has_file = phenotype["FILE_ID"] != "no_filename"
    _frame, flow = apply_exclusions(phenotype, has_file)
    counts = [step["n"] for step in flow]
    assert counts[0] == 1112 and counts == sorted(counts, reverse=True)
