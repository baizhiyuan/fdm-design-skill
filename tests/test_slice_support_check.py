"""slice_support_check.py: G-code parsing and the verdict, with NEGATIVE cases.

No slicer is needed: these tests feed synthetic G-code. The feature names
used here mirror the documented formats; whether a given slicer version writes
exactly these strings is confirmed for Bambu Studio and unverified for other slicers.
"""
from __future__ import annotations

import zipfile

from conftest import load_script

mod = load_script("slice_support_check")

BODY = """M83
; FEATURE: Outer wall
G1 X0 Y0 F3000
G1 X10 Y0 E0.5
; FEATURE: Bridge
G1 X10 Y0
G1 X10 Y8 E0.4
"""
SUPPORT = """; FEATURE: Support
G1 X20 Y0
G1 X25 Y0 E0.3
"""


def config(enable="1", threshold="45", plate_only="0"):
    return (f"; CONFIG_BLOCK_START\n; enable_support = {enable}\n; support_type = normal(auto)\n"
            f"; support_threshold_angle = {threshold}\n; support_on_build_plate_only = {plate_only}\n"
            "; CONFIG_BLOCK_END\n")


def run(tmp_path, text, *extra, name="part.gcode"):
    path = tmp_path / name
    path.write_text(text)
    return mod.main(["--gcode", str(path), *extra])


def test_clean_with_supports_on_passes(tmp_path):
    assert run(tmp_path, BODY + config()) == 0


def test_negative_support_extrusion_fails(tmp_path):
    assert run(tmp_path, BODY + SUPPORT + config()) == 1


def test_negative_zero_support_with_supports_off_is_not_a_pass(tmp_path):
    # failure mode 1: "0 support" from a slice with supports disabled
    assert run(tmp_path, BODY + config(enable="0")) == 2


def test_negative_missing_config_is_not_a_pass(tmp_path):
    assert run(tmp_path, BODY) == 2


def test_negative_lax_threshold_is_not_a_pass(tmp_path):
    # Bambu default 30 from horizontal = 60 from vertical; asked for 45 from vertical
    assert run(tmp_path, BODY + config(threshold="30"), "--max-overhang", "45") == 2


def test_threshold_conversion_matches(tmp_path):
    assert run(tmp_path, BODY + config(threshold="30"), "--max-overhang", "60") == 0


def test_negative_build_plate_only_is_not_a_pass(tmp_path):
    assert run(tmp_path, BODY + config(plate_only="1")) == 2


def test_negative_no_feature_comments_is_inconclusive(tmp_path):
    assert run(tmp_path, "G1 X0 Y0\nG1 X10 Y0 E1\n" + config()) == 2


def test_prusa_type_comments_and_absolute_e(tmp_path):
    text = ("M82\nG92 E0\n;TYPE:External perimeter\nG1 X0 Y0\nG1 X5 Y0 E1.0\n"
            ";TYPE:Support material\nG1 X9 Y0 E1.5\n" + config())
    parsed = mod.parse(text)
    assert parsed["totals_mm_filament"]["support"] == 0.5
    assert run(tmp_path, text) == 1


def test_bridge_length_is_measured():
    parsed = mod.parse(BODY + config())
    assert parsed["longest_bridge_move_mm"] == 8.0
    assert parsed["totals_mm_filament"]["bridge"] == 0.4


def test_reads_gcode_inside_3mf(tmp_path):
    path = tmp_path / "plate.3mf"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("Metadata/plate_1.gcode", BODY + SUPPORT + config())
    assert mod.main(["--gcode", str(path)]) == 1


def test_missing_slicer_is_inconclusive(tmp_path, monkeypatch):
    monkeypatch.setattr(mod.shutil, "which", lambda name: None)
    for name in ("m.stl", "machine.json", "process.json", "fil.json"):
        (tmp_path / name).write_text("{}")
    code = mod.main(["--model", str(tmp_path / "m.stl"), "--machine", str(tmp_path / "machine.json"),
                     "--process", str(tmp_path / "process.json"), "--filament", str(tmp_path / "fil.json")])
    assert code == 2


def test_forced_profile_turns_support_on(tmp_path):
    proc = tmp_path / "process.json"
    proc.write_text('{"enable_support": "0", "support_threshold_angle": "30"}')
    mod.slice_model("slicer", tmp_path / "m.stl", tmp_path / "machine.json", proc, tmp_path / "f.json",
                    45.0, tmp_path, dry_run=True)
    forced = (tmp_path / "forced_support_process.json").read_text()
    assert '"enable_support": "1"' in forced and '"support_threshold_angle": "45"' in forced
