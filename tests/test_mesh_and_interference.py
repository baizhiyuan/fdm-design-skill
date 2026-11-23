"""mesh_check.py and interference_check.py, with NEGATIVE fixtures."""
from __future__ import annotations

import importlib.util

import numpy as np
import pytest

from conftest import box, extrude_xz, load_script, voxel_mesh

mesh_mod = load_script("mesh_check")
inter_mod = load_script("interference_check")
HAS_MANIFOLD = (importlib.util.find_spec("manifold3d") is not None
                and importlib.util.find_spec("trimesh") is not None)


# --- mesh_check ------------------------------------------------------------------------------
def test_cube_is_clean(stl):
    assert mesh_mod.main([str(stl("cube.stl", box((10, 10, 10)))), "--printer", "a1"]) == 0


def test_extruded_fixture_is_clean(stl):
    tris = extrude_xz([(0, 0), (5, 0), (15, 6), (15, 9), (0, 9)], 8.0)
    report = mesh_mod.check(tris)
    assert report["result"] == "pass", report["problems"]


def test_negative_open_mesh_fails(stl):
    tris = box((10, 10, 10))[:-1]
    report = mesh_mod.check(tris)
    assert not report["watertight"] and report["result"] == "fail"


def test_negative_flipped_face_fails():
    tris = box((10, 10, 10)).copy()
    tris[0] = tris[0][::-1]
    report = mesh_mod.check(tris)
    assert report["watertight"] and not report["winding_consistent"]


def test_negative_inside_out_fails():
    report = mesh_mod.check(box((10, 10, 10))[:, ::-1])
    assert any("inward" in p for p in report["problems"])


def test_negative_two_bodies_fail():
    tris = np.concatenate([box((5, 5, 5)), box((5, 5, 5), origin=(20, 0, 0))])
    report = mesh_mod.check(tris)
    assert report["bodies"] == 2 and report["result"] == "fail"


def test_negative_too_big_for_build_volume(stl):
    path = stl("big.stl", box((300, 10, 10)))
    assert mesh_mod.main([str(path), "--printer", "a1"]) == 1


# --- interference_check ----------------------------------------------------------------------
def test_separated_boxes_are_clear(stl):
    a = stl("a.stl", box((10, 10, 10)))
    b = stl("b.stl", box((10, 10, 10), origin=(12, 0, 0)))
    assert inter_mod.main([str(a), str(b)]) == 0


def test_negative_overlapping_boxes_report_interference(stl):
    a = stl("a.stl", box((10, 10, 10)))
    b = stl("b.stl", box((10, 10, 10), origin=(5, 0, 0)))
    code = inter_mod.main([str(a), str(b)])
    if HAS_MANIFOLD:
        assert code == 1
    else:
        assert code == 2      # bounding-box only: reported as possible, never as clear


def test_negative_overlap_without_exact_engine_is_inconclusive_not_clear():
    parts = {"a": box((10, 10, 10)), "b": box((10, 10, 10), origin=(5, 0, 0))}
    report = inter_mod.check(parts, use_exact=False)
    assert report["result"] == "inconclusive"
    assert report["pairs"][0]["status"] == "possible"


@pytest.mark.skipif(not HAS_MANIFOLD, reason="manifold3d not installed")
def test_exact_intersection_volume():
    parts = {"a": box((10, 10, 10)), "b": box((10, 10, 10), origin=(5, 0, 0))}
    report = inter_mod.check(parts)
    assert report["pairs"][0]["status"] == "interference"
    assert abs(report["pairs"][0]["volume_mm3"] - 500.0) < 1e-3


@pytest.mark.skipif(not HAS_MANIFOLD, reason="manifold3d not installed")
def test_overlapping_bounding_boxes_but_no_solid_overlap_is_clear():
    # a block sitting in the notch of an L: the boxes overlap, the solids do not
    occ = np.ones((10, 10, 10), dtype=bool)
    occ[5:, 5:, :] = False
    parts = {"l": voxel_mesh(occ), "b": box((3, 3, 10), origin=(6, 6, 0))}
    report = inter_mod.check(parts)
    assert report["pairs"][0]["method"].startswith("exact")
    assert report["result"] == "pass"


def test_allowed_pair_is_listed_not_failed(stl):
    a = stl("boss.stl", box((10, 10, 10)))
    b = stl("insert.stl", box((4, 4, 4), origin=(3, 3, 6)))
    code = inter_mod.main([str(a), str(b), "--allow", "boss.stl:insert.stl"])
    assert code == 0
