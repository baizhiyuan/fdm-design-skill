"""Shared fixtures: tiny generated meshes, written as binary STL to a temp dir."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "fdm-design" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_stl(path: Path, tris: np.ndarray) -> Path:
    tris = np.asarray(tris, dtype="<f4").reshape(-1, 3, 3)
    dt = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec = np.zeros(len(tris), dtype=dt)
    rec["v"] = tris
    with open(path, "wb") as fh:
        fh.write(b"fixture".ljust(80, b" "))
        fh.write(np.uint32(len(tris)).tobytes())
        fh.write(rec.tobytes())
    return path


def voxel_mesh(occ: np.ndarray, pitch: float = 1.0, origin=(0.0, 0.0, 0.0)) -> np.ndarray:
    """Watertight, outward-wound surface of a boolean voxel grid occ[x, y, z]."""
    occ = np.pad(np.asarray(occ, dtype=bool), 1)
    tris = []
    # for each axis and direction: (axis, sign, quad corners as offsets in the other two axes)
    for axis in range(3):
        u, v = [a for a in range(3) if a != axis]
        for sign in (1, -1):
            shifted = np.roll(occ, -sign, axis=axis)
            faces = np.argwhere(occ & ~shifted)
            for idx in faces:
                base = idx.astype(float) - 1.0
                plane = base[axis] + (1.0 if sign > 0 else 0.0)
                corners = []
                for du, dv in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    p = np.zeros(3)
                    p[axis] = plane
                    p[u] = base[u] + du
                    p[v] = base[v] + dv
                    corners.append(p)
                c = np.array(corners)
                # orient so the normal points along sign * axis
                n = np.cross(c[1] - c[0], c[2] - c[0])
                if np.sign(n[axis]) != sign:
                    c = c[::-1]
                tris.append([c[0], c[1], c[2]])
                tris.append([c[0], c[2], c[3]])
    return np.asarray(tris) * pitch + np.asarray(origin)


def extrude_xz(polygon, depth: float) -> np.ndarray:
    """Extrude a convex XZ polygon (counter-clockwise seen from -Y) along +Y."""
    pts = np.asarray(polygon, dtype=float)
    front = np.column_stack([pts[:, 0], np.zeros(len(pts)), pts[:, 1]])
    back = front + np.array([0.0, depth, 0.0])
    tris = []
    for i in range(1, len(pts) - 1):
        tris.append([front[0], front[i], front[i + 1]])
        tris.append([back[0], back[i + 1], back[i]])
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        tris.append([front[i], back[i], back[j]])
        tris.append([front[i], back[j], front[j]])
    tris = np.asarray(tris)
    # make the winding outward (positive signed volume)
    vol = np.einsum("ij,ij->i", tris[:, 0], np.cross(tris[:, 1], tris[:, 2])).sum()
    if vol < 0:
        tris = tris[:, ::-1]
    return tris


def box(size, origin=(0.0, 0.0, 0.0)) -> np.ndarray:
    return voxel_mesh(np.ones((1, 1, 1), dtype=bool), 1.0) * np.asarray(size, dtype=float) + np.asarray(origin)


@pytest.fixture
def stl(tmp_path):
    def _write(name: str, tris) -> Path:
        return write_stl(tmp_path / name, tris)
    return _write
