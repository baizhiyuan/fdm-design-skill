"""scripts/validate.py: the repository passes, and the path scanner can fail."""
from __future__ import annotations

import importlib.util
import subprocess
import sys

from conftest import ROOT

spec = importlib.util.spec_from_file_location("validate", ROOT / "scripts" / "validate.py")
validate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate)


def test_repository_passes():
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py")],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_negative_local_paths_are_flagged(tmp_path):
    # built at runtime so this test file itself stays clean
    home = "/" + "home" + "/someone/project/part.stl"
    mount = "/" + "mnt" + "/c/" + "Us" + "ers/x"
    drive = "D" + ":" + "\\" + "cad\\part.step"
    (tmp_path / "notes.md").write_text(f"see {home}\nand {mount}\nand {drive}\n")
    found = validate.local_path_findings(tmp_path)
    assert len(found) == 3, found


def test_clean_text_is_not_flagged(tmp_path):
    (tmp_path / "ok.md").write_text("Install into ~/.claude/skills/fdm-design and run scripts/x.py\n")
    assert validate.local_path_findings(tmp_path) == []
