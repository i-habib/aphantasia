"""Minimal NIfTI-1 reader (NumPy + standard library; no nibabel dependency)."""
from __future__ import annotations

import gzip
import struct
from pathlib import Path

import numpy as np

_DTYPES = {2: "u1", 4: "<i2", 8: "<i4", 16: "<f4", 64: "<f8", 512: "<u2", 768: "<u4"}


def read_nifti(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return (volume, 4x4 voxel-to-world affine) from a .nii or .nii.gz file (sform, else qform-free pixdim)."""
    data = path.read_bytes()
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    if struct.unpack("<i", data[:4])[0] != 348:
        raise ValueError(f"{path.name}: only little-endian NIfTI-1 is supported")
    dims = struct.unpack("<8h", data[40:56])
    datatype = struct.unpack("<h", data[70:72])[0]
    pixdim = struct.unpack("<8f", data[76:108])
    vox_offset = int(struct.unpack("<f", data[108:112])[0])
    scl_slope, scl_inter = struct.unpack("<2f", data[112:120])
    sform_code = struct.unpack("<h", data[254:256])[0]
    if datatype not in _DTYPES:
        raise ValueError(f"{path.name}: unsupported NIfTI datatype {datatype}")
    shape = dims[1:1 + dims[0]]
    volume = np.frombuffer(data, dtype=_DTYPES[datatype], offset=vox_offset,
                           count=int(np.prod(shape))).reshape(shape, order="F").astype(float)
    if scl_slope not in (0.0, 1.0):
        volume = volume * scl_slope + scl_inter
    if sform_code > 0:
        affine = np.vstack([np.array(struct.unpack("<12f", data[280:328])).reshape(3, 4), [0, 0, 0, 1]])
    else:
        raise ValueError(f"{path.name}: no sform; cannot map voxels to MNI coordinates")
    return volume, affine


def world_to_voxel(affine: np.ndarray, xyz: np.ndarray) -> np.ndarray:
    points = np.atleast_2d(np.asarray(xyz, dtype=float))
    return (np.linalg.inv(affine) @ np.c_[points, np.ones(len(points))].T)[:3].T


def voxel_to_world(affine: np.ndarray, ijk: np.ndarray) -> np.ndarray:
    points = np.atleast_2d(np.asarray(ijk, dtype=float))
    return (affine @ np.c_[points, np.ones(len(points))].T)[:3].T
