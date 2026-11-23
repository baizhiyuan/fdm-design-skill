#!/usr/bin/env python3
"""Mesh sanity check before slicing: watertight, consistent winding, outward
normals, body count, degenerate faces and build volume.

Works with numpy alone for STL files (edge-based checks). trimesh, when
installed, is used only to load other formats.

Build volume: pass --build-volume X Y Z (mm), or --printer a1 for the Bambu
Lab A1 (256 x 256 x 256 mm; see references/sources.md). Other presets are not
bundled on purpose: read your printer's datasheet.

Exit codes: 0 pass, 1 a check failed, 2 usage or input error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from overhang_audit import components, index_mesh, load_triangles  # noqa: E402

PRINTERS = {"a1": (256.0, 256.0, 256.0)}


def check(tris: np.ndarray, build_volume: tuple[float, float, float] | None = None,
          max_bodies: int = 1) -> dict:
    verts, faces = index_mesh(tris)
    tri = verts[faces]
    cross = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    area = np.linalg.norm(cross, axis=1) / 2.0
    degenerate = int((area < 1e-9).sum())

    directed = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    undirected = np.sort(directed, axis=1)
    _, inv, counts = np.unique(undirected, axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    boundary_edges = int((counts == 1).sum())
    nonmanifold_edges = int((counts > 2).sum())
    watertight = boundary_edges == 0 and nonmanifold_edges == 0
    # consistent winding: each shared edge is used once in each direction
    _, dcounts = np.unique(directed, axis=0, return_counts=True)
    winding_consistent = bool(watertight and (dcounts == 1).all())

    owner = np.tile(np.arange(len(faces)), 3)
    order = np.argsort(inv, kind="stable")
    si, so = inv[order], owner[order]
    same = si[1:] == si[:-1]
    pairs = np.stack([so[:-1][same], so[1:][same]], axis=1)
    bodies = int(len(np.unique(components(len(faces), pairs)))) if len(faces) else 0

    signed_volume = float(np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6.0)
    lo, hi = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)
    size = (hi - lo).round(3).tolist()

    problems = []
    if not watertight:
        problems.append(f"not watertight: {boundary_edges} open edge(s), {nonmanifold_edges} non-manifold edge(s)")
    elif not winding_consistent:
        problems.append("inconsistent winding (some faces are flipped)")
    if watertight and signed_volume <= 0:
        problems.append("normals point inward (negative volume): flip the mesh")
    if degenerate:
        problems.append(f"{degenerate} degenerate (zero-area) face(s)")
    if bodies > max_bodies:
        problems.append(f"{bodies} separate bodies (expected at most {max_bodies}): floating parts or unmerged booleans")
    if build_volume is not None:
        over = [f"{axis} {s:g} > {b:g}" for axis, s, b in zip("XYZ", size, build_volume) if s > b]
        if over:
            problems.append("exceeds build volume: " + ", ".join(over))
    return {
        "checked": ["watertight", "winding", "outward normals", "degenerate faces", "body count"]
                   + (["build volume"] if build_volume else []),
        "faces": int(len(faces)), "watertight": watertight, "winding_consistent": winding_consistent,
        "volume_mm3": round(abs(signed_volume), 2), "bodies": bodies, "size_mm": size,
        "problems": problems, "result": "fail" if problems else "pass",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mesh sanity check before slicing.")
    ap.add_argument("meshes", nargs="+")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--printer", choices=sorted(PRINTERS), help="build-volume preset")
    group.add_argument("--build-volume", type=float, nargs=3, metavar=("X", "Y", "Z"))
    ap.add_argument("--max-bodies", type=int, default=1)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    volume = PRINTERS[args.printer] if args.printer else (tuple(args.build_volume) if args.build_volume else None)

    reports = {}
    for path in args.meshes:
        try:
            reports[path] = check(load_triangles(path), volume, args.max_bodies)
        except (OSError, SystemExit) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        for path, r in reports.items():
            print(f"{Path(path).name}: {r['result'].upper()}  bodies {r['bodies']}  size {r['size_mm']} mm  "
                  f"volume {r['volume_mm3']} mm3")
            for p in r["problems"]:
                print(f"  - {p}")
            if volume is None:
                print("  (build volume not checked: pass --printer or --build-volume)")
    return 1 if any(r["result"] == "fail" for r in reports.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
