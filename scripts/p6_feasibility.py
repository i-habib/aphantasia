"""P6 feasibility: can the Neurosynth imagery map be summarised on ENIGMA's 68 regions?

Prints coverage checks only. It deliberately prints no region-level imagery
values and never compares the imagery map with the ENIGMA autism map, so the
P6 analysis plan can still be written blind to the result.

Uses NumPy and the standard library only (no nibabel). Sampling is a coarse
nearest-voxel lookup at fsaverage5 vertex coordinates, treated as MNI space;
the registered analysis must use a proper fsaverage→MNI152 transform.
"""
from __future__ import annotations

import base64
import gzip
import struct
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "projects" / "P6_imagery_brainmaps" / "data_raw"
# ENIGMA parcel_to_surface: 68 DK values fill these of the 71 sorted aparc_fsa5
# labels (0 = medial wall; 4 and 39 = left/right corpus callosum).
DK68_LABEL_INDEX = list(range(1, 4)) + list(range(5, 39)) + list(range(40, 71))


def read_gifti_coords(path: Path) -> np.ndarray:
    array = ET.parse(path).getroot().find("DataArray")
    if array.get("Intent") != "NIFTI_INTENT_POINTSET":
        raise ValueError(f"{path.name}: first DataArray is not a point set")
    raw = base64.b64decode(array.find("Data").text.strip())
    if array.get("Encoding") == "GZipBase64Binary":
        raw = zlib.decompress(raw)
    return np.frombuffer(raw, dtype="<f4").reshape(int(array.get("Dim0")), int(array.get("Dim1")))


def read_nifti(path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = gzip.decompress(path.read_bytes())
    if struct.unpack("<i", data[:4])[0] != 348:
        raise ValueError("Only little-endian NIfTI-1 is supported")
    dims = struct.unpack("<8h", data[40:56])
    datatype = struct.unpack("<h", data[70:72])[0]
    vox_offset = int(struct.unpack("<f", data[108:112])[0])
    sform_code = struct.unpack("<h", data[254:256])[0]
    srow = np.array(struct.unpack("<12f", data[280:328])).reshape(3, 4)
    if sform_code <= 0:
        raise ValueError("NIfTI has no sform; cannot map to MNI coordinates")
    dtype = {2: "u1", 4: "<i2", 8: "<i4", 16: "<f4", 64: "<f8"}[datatype]
    shape = dims[1:1 + dims[0]]
    volume = np.frombuffer(data, dtype=dtype, offset=vox_offset, count=int(np.prod(shape))).reshape(shape, order="F")
    affine = np.vstack([srow, [0, 0, 0, 1]])
    return volume.astype(float), affine


def main() -> int:
    enigma = pd.read_csv(RAW / "enigma" / "asd_meta-analysis_case-controls_CortThick.csv")
    labels = np.loadtxt(RAW / "enigma" / "aparc_fsa5.csv").astype(int)
    coords = np.vstack([read_gifti_coords(RAW / "enigma" / "fsa5_lh.gii"), read_gifti_coords(RAW / "enigma" / "fsa5_rh.gii")])
    volume, affine = read_nifti(RAW / "neurosynth" / "imagery_association-test_z.nii.gz")

    assert len(enigma) == 68 and enigma["Structure"].is_unique, "ENIGMA map must have 68 unique regions"
    assert coords.shape[0] == labels.size, "surface vertices and labels must align"
    unique_labels = np.unique(labels)
    assert unique_labels.size == 71, "aparc_fsa5 must have 71 labels"

    ijk = np.rint((np.linalg.inv(affine) @ np.c_[coords, np.ones(len(coords))].T)[:3].T).astype(int)
    inside = np.all((ijk >= 0) & (ijk < np.array(volume.shape)), axis=1)
    sampled = np.zeros(len(coords))
    sampled[inside] = volume[ijk[inside, 0], ijk[inside, 1], ijk[inside, 2]]

    region_label = unique_labels[DK68_LABEL_INDEX]
    nonzero_fraction = np.array([np.mean(sampled[labels == lab] != 0) for lab in region_label])
    vertices = np.array([np.sum(labels == lab) for lab in region_label])

    print(f"ENIGMA autism map: 68 regions; n controls {enigma['n_controls'].min()}-{enigma['n_controls'].max()}, "
          f"n autistic {enigma['n_patients'].min()}-{enigma['n_patients'].max()}")
    print(f"Imagery map: shape {volume.shape}, voxel size {np.abs(np.diag(affine)[:3])} mm, "
          f"nonzero voxels {int(np.sum(volume != 0))} ({np.mean(volume != 0):.2%}); thresholded (FDR 0.01) map")
    print(f"Surface: {len(coords)} vertices, {inside.mean():.1%} fall inside the volume")
    print(f"Vertices per region: min {vertices.min()}, median {int(np.median(vertices))}")
    print(f"Regions with any imagery signal: {int(np.sum(nonzero_fraction > 0))}/68; "
          f"with >=10% of vertices nonzero: {int(np.sum(nonzero_fraction >= 0.10))}/68")
    print(f"Share of all cortical vertices with nonzero imagery signal: {np.mean(sampled[labels > 0] != 0):.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
