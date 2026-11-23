#!/usr/bin/env python3
"""Geometric overhang audit for an FDM part, independent of any slicer.

The mesh must already be in its print orientation (Z up, the face that sits on
the bed at the lowest Z). Units are millimetres.

Angle convention (fixed for the whole fdm-design skill): angles are measured
FROM VERTICAL. 0 deg is a vertical wall, 90 deg is a horizontal ceiling facing
down. Bambu Studio / OrcaSlicer `support_threshold_angle` is measured from
horizontal, so `from_vertical = 90 - slicer_threshold`; the Bambu default of 30
therefore only supports faces steeper than 60 deg from vertical.

What it reports (downward-facing faces that do not sit on the bed):

* slope regions: faces tilted more than --max-overhang from vertical but not
  horizontal. Each connected region is a finding with area, Z range and XY box.
* ceiling regions: horizontal downward faces (within --ceiling-tol). Each
  region's boundary edges are classified as anchored (the neighbouring face
  goes DOWN, i.e. material below) or free. Then:
    - no anchored edge                -> "floating"  (an island in the air)
    - two or more anchored chains, or
      one closed anchored loop with no
      free edge                       -> "bridge", span = 2 x the largest
                                         distance from any point to an anchor
    - otherwise (one-sided)           -> "cantilever" (ledges, counterbore
                                         rings without a sacrificial layer)
  A bridge passes when span <= --max-bridge. A cantilever passes only when its
  reach <= --max-cantilever (default 0: any one-sided ceiling fails).

Spans are estimates from sampled points, accurate to about --sample-step.
Exit codes: 0 pass, 1 findings, 2 usage or input error.

Dependencies: numpy. trimesh is used only to load non-STL formats.
The original idea (downward normals, bed exclusion, Z-band clustering) is the
common technique also used by print3d-designer's check_model.py (MIT); this
file is an independent implementation.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

MERGE_DECIMALS = 4          # vertex merge grid: 0.1 micrometre
Z_BAND_MM = 1.0             # height clustering band for the summary


# --------------------------------------------------------------------------- loading
def load_triangles(path: str | Path) -> np.ndarray:
    """Return an (N, 3, 3) float array of triangles. STL natively, others via trimesh."""
    path = Path(path)
    if path.suffix.lower() != ".stl":
        try:
            import trimesh  # noqa: PLC0415 - optional dependency
        except ImportError as exc:
            raise SystemExit(f"{path}: only STL is supported without trimesh ({exc})")
        mesh = trimesh.load(str(path), force="mesh")
        return np.asarray(mesh.triangles, dtype=float)
    data = path.read_bytes()
    if len(data) >= 84:
        count = int(np.frombuffer(data[80:84], "<u4")[0])
        if len(data) == 84 + 50 * count:
            dt = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
            return np.frombuffer(data, dt, count=count, offset=84)["v"].astype(float)
    text = data.decode("utf-8", errors="ignore")
    verts = [list(map(float, line.split()[1:4])) for line in text.splitlines()
             if line.strip().startswith("vertex")]
    if not verts or len(verts) % 3:
        raise SystemExit(f"{path}: not a readable STL")
    return np.asarray(verts, dtype=float).reshape(-1, 3, 3)


def index_mesh(tris: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Merge coincident vertices. Returns (vertices, faces)."""
    flat = np.round(tris.reshape(-1, 3), MERGE_DECIMALS)
    verts, inverse = np.unique(flat, axis=0, return_inverse=True)
    return verts, inverse.reshape(-1, 3)


def edge_table(faces: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (edges (E,2) sorted vertex ids, edge_faces (E,2) with -1 for missing)."""
    raw = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    owner = np.tile(np.arange(len(faces)), 3)
    raw.sort(axis=1)
    edges, inv = np.unique(raw, axis=0, return_inverse=True)
    inv = inv.ravel()
    edge_faces = np.full((len(edges), 2), -1, dtype=np.int64)
    order = np.argsort(inv, kind="stable")
    sorted_inv, sorted_owner = inv[order], owner[order]
    first = np.r_[True, sorted_inv[1:] != sorted_inv[:-1]]
    edge_faces[sorted_inv[first], 0] = sorted_owner[first]
    second = ~first
    # only the first two faces per edge are kept (non-manifold edges are rare in CAD exports)
    keep = second & np.r_[False, first[:-1]]
    edge_faces[sorted_inv[keep], 1] = sorted_owner[keep]
    return edges, edge_faces


# --------------------------------------------------------------------------- helpers
def components(n: int, pairs: np.ndarray) -> np.ndarray:
    """Union-find over n items; returns a label per item."""
    parent = np.arange(n)

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b in pairs:
        ra, rb = find(int(a)), find(int(b))
        if ra != rb:
            parent[ra] = rb
    return np.array([find(i) for i in range(n)])


def sample_triangles(tri: np.ndarray, step: float) -> np.ndarray:
    """Barycentric grid samples inside each triangle, spacing about `step`."""
    pts = []
    for t in tri:
        longest = max(np.linalg.norm(t[1] - t[0]), np.linalg.norm(t[2] - t[1]), np.linalg.norm(t[0] - t[2]))
        k = int(min(max(math.ceil(longest / step), 1), 80))
        i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1), indexing="ij")
        m = (i + j) <= k
        a, b = i[m] / k, j[m] / k
        c = 1.0 - a - b
        pts.append(a[:, None] * t[0] + b[:, None] * t[1] + c[:, None] * t[2])
    return np.concatenate(pts) if pts else np.zeros((0, 3))


def point_segment_distance(points: np.ndarray, seg_a: np.ndarray, seg_b: np.ndarray) -> np.ndarray:
    """Minimum XY distance from each point to any segment (chunked)."""
    out = np.full(len(points), np.inf)
    p2 = points[:, :2]
    a2, b2 = seg_a[:, :2], seg_b[:, :2]
    ab = b2 - a2
    denom = np.maximum((ab ** 2).sum(1), 1e-12)
    for start in range(0, len(p2), 4096):
        p = p2[start:start + 4096, None, :]
        t = np.clip(((p - a2) * ab).sum(2) / denom, 0.0, 1.0)
        closest = a2 + t[..., None] * ab
        out[start:start + 4096] = np.sqrt(((p - closest) ** 2).sum(2)).min(1)
    return out


def bbox(points: np.ndarray) -> dict:
    lo, hi = points.min(0), points.max(0)
    return {"x": [round(float(lo[0]), 2), round(float(hi[0]), 2)],
            "y": [round(float(lo[1]), 2), round(float(hi[1]), 2)],
            "z": [round(float(lo[2]), 2), round(float(hi[2]), 2)]}


# --------------------------------------------------------------------------- audit
def audit(tris: np.ndarray, max_overhang: float = 45.0, max_bridge: float = 10.0,
          max_cantilever: float = 0.0, bed_tol: float = 0.1, ceiling_tol: float = 2.0,
          angle_tol: float = 0.5, min_area: float = 1.0, sample_step: float = 0.5) -> dict:
    tris = tris - np.array([0.0, 0.0, tris[:, :, 2].min()])
    verts, faces = index_mesh(tris)
    tri = verts[faces]
    cross = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    area = np.linalg.norm(cross, axis=1) / 2.0
    nz = cross[:, 2] / np.maximum(2.0 * area, 1e-12)
    # angle from vertical for downward faces: 0 = wall, 90 = ceiling
    angle = np.degrees(np.arcsin(np.clip(-nz, -1.0, 1.0)))
    zmax = tri[:, :, 2].max(1)
    valid = area > 1e-9
    on_bed = zmax <= bed_tol
    ceiling = valid & ~on_bed & (angle >= 90.0 - ceiling_tol)
    slope = valid & ~on_bed & ~ceiling & (angle > max_overhang + angle_tol)

    edges, edge_faces = edge_table(faces)
    both = (edge_faces >= 0).all(1)
    pairs_all = edge_faces[both]

    findings: list[dict] = []

    # slope regions
    idx = np.flatnonzero(slope)
    if len(idx):
        local = -np.ones(len(faces), dtype=np.int64)
        local[idx] = np.arange(len(idx))
        p = pairs_all[slope[pairs_all[:, 0]] & slope[pairs_all[:, 1]]]
        labels = components(len(idx), local[p]) if len(p) else np.arange(len(idx))
        for lab in np.unique(labels):
            fids = idx[labels == lab]
            a = float(area[fids].sum())
            if a < min_area:
                continue
            findings.append({
                "kind": "slope", "status": "fail", "area_mm2": round(a, 2),
                "max_angle_from_vertical_deg": round(float(angle[fids].max()), 1),
                "bbox": bbox(tri[fids].reshape(-1, 3)),
                "advice": "chamfer to <= the overhang limit, re-orient, split, or support",
            })

    # ceiling regions
    idx = np.flatnonzero(ceiling)
    if len(idx):
        local = -np.ones(len(faces), dtype=np.int64)
        local[idx] = np.arange(len(idx))
        fz = tri[:, :, 2].mean(1)
        p = pairs_all[ceiling[pairs_all[:, 0]] & ceiling[pairs_all[:, 1]]]
        p = p[np.abs(fz[p[:, 0]] - fz[p[:, 1]]) < 0.01]
        labels = components(len(idx), local[p]) if len(p) else np.arange(len(idx))
        for lab in np.unique(labels):
            fids = idx[labels == lab]
            a = float(area[fids].sum())
            if a < min_area:
                continue
            findings.append(classify_ceiling(fids, tri, faces, verts, edges, edge_faces, ceiling,
                                             a, max_bridge, max_cantilever, sample_step))

    bands: dict[int, float] = {}
    for f in findings:
        band = int(f["bbox"]["z"][0] // Z_BAND_MM)
        bands[band] = bands.get(band, 0.0) + f["area_mm2"]
    failed = [f for f in findings if f["status"] == "fail"]
    return {
        "convention": "angles from vertical; 0 = wall, 90 = horizontal ceiling",
        "parameters": {"max_overhang_deg": max_overhang, "max_bridge_mm": max_bridge,
                       "max_cantilever_mm": max_cantilever, "bed_tol_mm": bed_tol,
                       "ceiling_tol_deg": ceiling_tol, "min_area_mm2": min_area},
        "checked": {"faces": int(len(faces)), "downward_faces_off_bed": int((valid & ~on_bed & (nz < 0)).sum()),
                    "height_mm": round(float(tri[:, :, 2].max()), 2)},
        "findings": findings,
        "z_bands_mm2": {f"{b * Z_BAND_MM:g}-{(b + 1) * Z_BAND_MM:g}": round(v, 2) for b, v in sorted(bands.items())},
        "result": "fail" if failed else "pass",
    }


def classify_ceiling(fids, tri, faces, verts, edges, edge_faces, ceiling, area_mm2,
                     max_bridge, max_cantilever, sample_step) -> dict:
    in_region = np.zeros(len(faces), dtype=bool)
    in_region[fids] = True
    f0, f1 = edge_faces[:, 0], edge_faces[:, 1]
    r0 = (f0 >= 0) & in_region[np.maximum(f0, 0)]
    r1 = (f1 >= 0) & in_region[np.maximum(f1, 0)]
    boundary = np.flatnonzero(r0 ^ r1)
    z = float(tri[fids][:, :, 2].mean())
    anchored = []
    free = []
    for e in boundary:
        other = f1[e] if r0[e] else f0[e]
        if other < 0:
            free.append(e)     # open mesh edge: treat as unsupported
            continue
        third = [v for v in faces[other] if v not in edges[e]]
        if third and verts[third[0], 2] < z - 1e-3:
            anchored.append(e)
        else:
            free.append(e)
    region_pts = tri[fids].reshape(-1, 3)
    base = {"z_mm": round(z, 2), "area_mm2": round(area_mm2, 2), "bbox": bbox(region_pts)}
    if not anchored:
        return {**base, "kind": "floating", "status": "fail",
                "advice": "nothing below this ceiling: support it, re-orient or split the part"}
    anchored = np.array(anchored)
    seg = edges[anchored]
    by_vertex: dict[int, list[int]] = {}
    for i, (va, vb) in enumerate(seg):
        by_vertex.setdefault(int(va), []).append(i)
        by_vertex.setdefault(int(vb), []).append(i)
    links = [(ids[0], other) for ids in by_vertex.values() for other in ids[1:]]
    chains = components(len(anchored), np.array(links, dtype=np.int64).reshape(-1, 2))
    n_chains = len(np.unique(chains))
    samples = sample_triangles(tri[fids], sample_step)
    reach = float(point_segment_distance(samples, verts[seg[:, 0]], verts[seg[:, 1]]).max())
    is_bridge = n_chains >= 2 or (n_chains == 1 and not free)
    if is_bridge:
        span = 2.0 * reach
        ok = span <= max_bridge
        return {**base, "kind": "bridge", "status": "pass" if ok else "fail",
                "estimated_span_mm": round(span, 2), "anchor_chains": n_chains,
                "advice": ("document this bridge and its span in the design notes" if ok else
                           "bridge longer than --max-bridge: shorten, add a rib, re-orient or support")}
    ok = reach <= max_cantilever
    return {**base, "kind": "cantilever", "status": "pass" if ok else "fail",
            "estimated_reach_mm": round(reach, 2), "anchor_chains": n_chains,
            "advice": ("one-sided ceiling (ledge, or counterbore ring without a sacrificial layer): "
                       "chamfer the underside, model a sacrificial or two-layer bridge, re-orient or support")}


# --------------------------------------------------------------------------- CLI
def format_text(name: str, report: dict) -> str:
    lines = [f"{name}: {report['result'].upper()}  ({len(report['findings'])} region(s); "
             f"limit {report['parameters']['max_overhang_deg']:g} deg from vertical, "
             f"bridge <= {report['parameters']['max_bridge_mm']:g} mm)"]
    for f in report["findings"]:
        extra = ""
        if "estimated_span_mm" in f:
            extra = f" span~{f['estimated_span_mm']} mm"
        elif "estimated_reach_mm" in f:
            extra = f" reach~{f['estimated_reach_mm']} mm"
        elif "max_angle_from_vertical_deg" in f:
            extra = f" max {f['max_angle_from_vertical_deg']} deg"
        b = f["bbox"]
        lines.append(f"  [{f['status']}] {f['kind']:<10} z {b['z'][0]}-{b['z'][1]}  area {f['area_mm2']} mm2"
                     f"{extra}  x {b['x'][0]}..{b['x'][1]} y {b['y'][0]}..{b['y'][1]}")
        if f["status"] == "fail":
            lines.append(f"      -> {f['advice']}")
    lines.append(f"  checked: {report['checked']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("meshes", nargs="+", help="oriented STL (or any trimesh format), mm, Z up")
    ap.add_argument("--max-overhang", type=float, default=45.0,
                    help="largest allowed angle FROM VERTICAL (default 45)")
    ap.add_argument("--max-bridge", type=float, default=10.0,
                    help="largest allowed bridge span in mm (default 10; calibrate per printer/material)")
    ap.add_argument("--max-cantilever", type=float, default=0.0,
                    help="largest allowed one-sided ceiling reach in mm (default 0)")
    ap.add_argument("--bed-tol", type=float, default=0.1, help="faces wholly below this Z are on the bed")
    ap.add_argument("--ceiling-tol", type=float, default=2.0, help="degrees from horizontal counted as ceiling")
    ap.add_argument("--min-area", type=float, default=1.0, help="ignore regions smaller than this (mm2)")
    ap.add_argument("--sample-step", type=float, default=0.5, help="span sampling step (mm)")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = ap.parse_args(argv)

    reports = {}
    for path in args.meshes:
        try:
            tris = load_triangles(path)
        except (OSError, SystemExit) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        reports[path] = audit(tris, args.max_overhang, args.max_bridge, args.max_cantilever, args.bed_tol,
                              args.ceiling_tol, 0.5, args.min_area, args.sample_step)
    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        print("\n".join(format_text(Path(p).name, r) for p, r in reports.items()))
    return 1 if any(r["result"] == "fail" for r in reports.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
