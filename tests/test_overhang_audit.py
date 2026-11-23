"""overhang_audit.py: positive and NEGATIVE fixtures.

A check that cannot fail proves nothing, so most tests here are fixtures that
MUST fail the audit.
"""
from __future__ import annotations

import json

import numpy as np

from conftest import box, extrude_xz, load_script, voxel_mesh

audit_mod = load_script("overhang_audit")


def run(path, *extra):
    return audit_mod.main([str(path), *map(str, extra)])


def kinds(report, status=None):
    return [f["kind"] for f in report["findings"] if status is None or f["status"] == status]


# --- fixtures --------------------------------------------------------------------------------
def cantilever():
    occ = np.zeros((15, 4, 12), dtype=bool)
    occ[0:4, :, :] = True          # column on the bed
    occ[4:15, :, 9:12] = True      # 11 mm arm sticking out at z = 9
    return voxel_mesh(occ)


def window(span=6):
    occ = np.zeros((8 + span, 3, 10), dtype=bool)
    occ[0:4, :, :] = True
    occ[4 + span:, :, :] = True
    occ[4:4 + span, :, 6:10] = True    # beam over a gap of `span` mm at z = 6
    return voxel_mesh(occ)


def counterbore(sacrificial: bool):
    occ = np.ones((12, 12, 6), dtype=bool)
    occ[3:9, 3:9, 0:2] = False                     # head recess from the bed face
    occ[5:7, 5:7, (3 if sacrificial else 2):6] = False   # screw hole above
    return voxel_mesh(occ)


def ramp(rise):
    # underside from (5, 0) to (15, rise): slope from horizontal = atan(rise / 10)
    return extrude_xz([(0, 0), (5, 0), (15, rise), (15, rise + 3), (0, rise + 3)], 8.0)


# --- tests -----------------------------------------------------------------------------------
def test_plain_cube_passes(stl):
    path = stl("cube.stl", box((10, 10, 10)))
    assert run(path) == 0
    report = audit_mod.audit(audit_mod.load_triangles(path))
    assert report["result"] == "pass" and report["findings"] == []


def test_negative_cantilever_fails(stl):
    path = stl("cantilever.stl", cantilever())
    assert run(path) == 1
    report = audit_mod.audit(audit_mod.load_triangles(path))
    (finding,) = [f for f in report["findings"] if f["status"] == "fail"]
    assert finding["kind"] == "cantilever"
    assert finding["z_mm"] == 9.0
    assert abs(finding["estimated_reach_mm"] - 11.0) < 0.6


def test_cantilever_still_fails_with_huge_bridge_limit(stl):
    # a one-sided ledge is not a bridge, whatever the bridge limit
    path = stl("cantilever.stl", cantilever())
    assert run(path, "--max-bridge", 1000) == 1


def test_short_bridge_passes_and_is_reported(stl):
    path = stl("window.stl", window(6))
    assert run(path, "--max-bridge", 10) == 0
    report = audit_mod.audit(audit_mod.load_triangles(path), max_bridge=10)
    (finding,) = report["findings"]
    assert finding["kind"] == "bridge" and finding["status"] == "pass"
    assert abs(finding["estimated_span_mm"] - 6.0) < 0.6


def test_negative_long_bridge_fails(stl):
    path = stl("window.stl", window(6))
    assert run(path, "--max-bridge", 4) == 1


def test_negative_counterbore_ring_fails_without_sacrificial_layer(stl):
    path = stl("cb.stl", counterbore(sacrificial=False))
    assert run(path) == 1
    report = audit_mod.audit(audit_mod.load_triangles(path))
    assert kinds(report, "fail") == ["cantilever"]


def test_counterbore_with_sacrificial_layer_is_a_bridge(stl):
    path = stl("cb_sac.stl", counterbore(sacrificial=True))
    report = audit_mod.audit(audit_mod.load_triangles(path), max_bridge=10)
    assert kinds(report) == ["bridge"] and report["result"] == "pass"


def test_negative_floating_island_fails(stl):
    tris = np.concatenate([box((10, 10, 2)), box((4, 4, 2), origin=(3, 3, 5))])
    path = stl("float.stl", tris)
    report = audit_mod.audit(audit_mod.load_triangles(path))
    assert "floating" in kinds(report, "fail")


def test_negative_59_degree_ramp_fails_at_45(stl):
    path = stl("ramp59.stl", ramp(6))      # atan(6/10) = 31 deg from horizontal = 59 from vertical
    assert run(path, "--max-overhang", 45) == 1


def test_lax_slicer_style_threshold_hides_the_same_ramp(stl):
    # Bambu default support_threshold_angle 30 (from horizontal) = 60 from vertical:
    # the ramp that fails at 45 passes here. This is failure mode #1 in miniature.
    path = stl("ramp59.stl", ramp(6))
    assert run(path, "--max-overhang", 60) == 0


def test_45_degree_chamfer_passes(stl):
    path = stl("ramp45.stl", ramp(10))
    assert run(path, "--max-overhang", 45) == 0


def test_json_output_is_parseable(stl, capsys):
    path = stl("cantilever.stl", cantilever())
    assert run(path, "--json") == 1
    data = json.loads(capsys.readouterr().out)
    assert data[str(path)]["result"] == "fail"
    assert data[str(path)]["convention"].startswith("angles from vertical")


def test_unreadable_input_returns_2(tmp_path):
    bad = tmp_path / "bad.stl"
    bad.write_text("not a mesh")
    assert run(bad) == 2
