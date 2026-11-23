#!/usr/bin/env python3
"""Pairwise interference check for parts placed in one assembly coordinate frame.

Export every part (shell halves, PCBs, connector and plug envelopes at full
engagement, fasteners at final depth) as separate meshes in the SAME frame,
then run:

    python interference_check.py shell_bottom.stl board.stl usbc_plug.stl \
        --allow board.stl:insert_m3.stl

For each pair the axis-aligned bounding boxes are compared first. Overlapping
pairs are then intersected exactly when trimesh + manifold3d are installed
(`pip install trimesh manifold3d`). Without them the script says so and reports
the pair as POSSIBLE (exit 2): a bounding-box overlap is not proof of a
collision, and the absence of one is the only thing it proves.

--allow A:B lists intentional overlaps (press fits, heat-set insert bores,
modelled thread engagement). They are reported separately, never silently.

Exit codes: 0 no interference, 1 interference found, 2 inconclusive or error.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from overhang_audit import load_triangles  # noqa: E402


def exact_engine():
    try:
        import manifold3d  # noqa: F401,PLC0415
        import trimesh  # noqa: PLC0415
    except ImportError:
        return None
    return trimesh


def aabb(tris: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    pts = tris.reshape(-1, 3)
    return pts.min(0), pts.max(0)


def check(parts: dict[str, np.ndarray], allow: set[frozenset] | None = None,
          tol_mm3: float = 0.001, use_exact: bool = True) -> dict:
    allow = allow or set()
    trimesh = exact_engine() if use_exact else None
    boxes = {name: aabb(t) for name, t in parts.items()}
    meshes = {}
    if trimesh is not None:
        for name, t in parts.items():
            m = trimesh.Trimesh(vertices=t.reshape(-1, 3), faces=np.arange(len(t) * 3).reshape(-1, 3))
            m.merge_vertices()
            meshes[name] = m
    pairs = []
    for a, b in itertools.combinations(parts, 2):
        (alo, ahi), (blo, bhi) = boxes[a], boxes[b]
        overlap = np.minimum(ahi, bhi) - np.maximum(alo, blo)
        entry = {"a": a, "b": b, "allowed": frozenset((a, b)) in allow}
        if (overlap <= 0).any():
            entry.update(status="clear", method="bounding box")
        elif trimesh is None:
            entry.update(status="possible", method="bounding box only",
                         note="bounding boxes overlap; install trimesh + manifold3d for an exact check")
        else:
            try:
                common = meshes[a].intersection(meshes[b])
                vol = 0.0 if common.is_empty else float(common.volume)
            except Exception as exc:  # noqa: BLE001 - report engine failures instead of hiding them
                entry.update(status="possible", method="boolean failed", note=str(exc))
            else:
                entry.update(status="interference" if vol > tol_mm3 else "clear",
                             method="exact boolean (manifold3d)", volume_mm3=round(vol, 4))
        pairs.append(entry)
    hard = [p for p in pairs if p["status"] == "interference" and not p["allowed"]]
    unsure = [p for p in pairs if p["status"] == "possible" and not p["allowed"]]
    result = "fail" if hard else ("inconclusive" if unsure else "pass")
    return {"engine": "manifold3d" if trimesh else "bounding boxes only", "pairs": pairs, "result": result}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Pairwise interference check (same coordinate frame).")
    ap.add_argument("meshes", nargs="+")
    ap.add_argument("--allow", action="append", default=[], metavar="A:B",
                    help="intentional overlap between files A and B (repeatable)")
    ap.add_argument("--tol", type=float, default=0.001, help="ignore intersections below this volume (mm3)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if len(args.meshes) < 2:
        print("error: need at least two meshes", file=sys.stderr)
        return 2
    try:
        parts = {Path(p).name: load_triangles(p) for p in args.meshes}
    except (OSError, SystemExit) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    allow = {frozenset(Path(x).name for x in item.split(":", 1)) for item in args.allow}
    report = check(parts, allow, args.tol)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"engine: {report['engine']}  result: {report['result'].upper()}")
        for p in report["pairs"]:
            tag = " (allowed)" if p["allowed"] else ""
            vol = f"  {p['volume_mm3']} mm3" if "volume_mm3" in p else ""
            note = f"  [{p['note']}]" if "note" in p else ""
            print(f"  {p['a']} x {p['b']}: {p['status']}{tag}{vol}  via {p['method']}{note}")
    return {"pass": 0, "fail": 1}.get(report["result"], 2)


if __name__ == "__main__":
    sys.exit(main())
