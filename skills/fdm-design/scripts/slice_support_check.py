#!/usr/bin/env python3
"""Slice with supports FORCED ON and count what the slicer generated.

A part sliced with supports disabled always reports "0 support". That number
proves nothing. This script either

  1. slices a model with Bambu Studio or OrcaSlicer after writing a copy of
     your process profile with `enable_support = 1` and your threshold, or
  2. parses G-code you exported yourself (`--gcode file.gcode` or a sliced
     `.3mf`, which contains Metadata/plate_N.gcode),

then sums extrusion per feature type and prints a verdict.

Angle convention: --max-overhang is FROM VERTICAL (skill convention). Bambu /
Orca `support_threshold_angle` is FROM HORIZONTAL, so the script writes
`90 - max_overhang` (45 -> 45, 30 from horizontal = 60 from vertical).

Feature tags. Bambu Studio and OrcaSlicer write `; FEATURE: <name>`;
PrusaSlicer writes `;TYPE:<name>`. Matching is case-insensitive substring:
  support  : "support"   ("Support", "Support interface", "Support transition")
  overhang : "overhang"  ("Overhang wall")
  bridge   : "bridge"    ("Bridge", "Internal Bridge")
Confirmed in real G-code from Bambu Studio 02.09.01.70 (A1, 0.20 Standard, supports on): Support, Support interface,
Support transition, Overhang wall, Bridge. OrcaSlicer and PrusaSlicer names are
not yet confirmed. Every feature name found is printed, so check them once
against your slicer version and report differences upstream.

Verdict and exit codes:
  0 PASS          support enabled (confirmed from the G-code config block),
                  threshold matches, zero support extrusion
  1 FAIL          support extrusion found
  2 INCONCLUSIVE  supports disabled or not confirmable, threshold mismatch,
                  no feature comments, slicer missing or failed

Slicer CLI flags follow the vendors' CLI wiki pages (see references/sources.md).
They were not exercised by the test suite, which runs without a slicer.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

CATEGORIES = {"support": "support", "overhang": "overhang", "bridge": "bridge"}
FEATURE_RE = re.compile(r"^;\s*(?:FEATURE:|TYPE:)\s*(.+?)\s*$")
CONFIG_RE = re.compile(r"^;\s*([a-z_]+)\s*=\s*(.*?)\s*$")
SLICER_NAMES = ("bambu-studio", "BambuStudio", "bambu_studio", "orca-slicer", "OrcaSlicer", "orcaslicer")
# Default install locations (Windows, WSL view of Windows, macOS).
SLICER_PATHS = (
    r"C:\Program Files\Bambu Studio\bambu-studio.exe",  # validate: allow-install-path
    "/mnt/c/Program Files/Bambu Studio/bambu-studio.exe",  # validate: allow-install-path
    r"C:\Program Files\OrcaSlicer\orca-slicer.exe",  # validate: allow-install-path
    "/mnt/c/Program Files/OrcaSlicer/orca-slicer.exe",  # validate: allow-install-path
    "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio",
    "/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer",
)


def read_gcode(path: Path) -> str:
    if path.suffix.lower() == ".3mf":
        with zipfile.ZipFile(path) as zf:
            names = sorted(n for n in zf.namelist() if n.lower().endswith(".gcode"))
            if not names:
                raise SystemExit(f"{path}: no G-code inside (slice the plate before exporting)")
            return "\n".join(zf.read(n).decode("utf-8", errors="ignore") for n in names)
    return path.read_text(encoding="utf-8", errors="ignore")


def category(feature: str) -> str | None:
    low = feature.lower()
    for key, cat in CATEGORIES.items():
        if key in low:
            return cat
    return None


def parse(text: str) -> dict:
    features: dict[str, float] = {}
    longest_bridge = 0.0
    config: dict[str, str] = {}
    current = None
    relative_e = False
    e_pos = 0.0
    x = y = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(";"):
            m = FEATURE_RE.match(line)
            if m:
                current = m.group(1)
                features.setdefault(current, 0.0)
                continue
            m = CONFIG_RE.match(line)
            if m:
                config[m.group(1)] = m.group(2)
            continue
        code = line.split(";", 1)[0].split()
        if not code:
            continue
        cmd = code[0].upper()
        if cmd == "M83":
            relative_e = True
        elif cmd == "M82":
            relative_e = False
        elif cmd == "G92":
            for word in code[1:]:
                if word[0].upper() == "E":
                    e_pos = float(word[1:] or 0)
        elif cmd in ("G0", "G1", "G2", "G3"):
            args = {w[0].upper(): float(w[1:]) for w in code[1:] if len(w) > 1 and w[0].isalpha()
                    and _is_number(w[1:])}
            nx, ny = args.get("X", x), args.get("Y", y)
            de = 0.0
            if "E" in args:
                de = args["E"] if relative_e else args["E"] - e_pos
                e_pos = e_pos + args["E"] if relative_e else args["E"]
            if de > 0 and current is not None:
                features[current] += de
                if category(current) == "bridge" and None not in (x, y, nx, ny) and cmd in ("G0", "G1"):
                    longest_bridge = max(longest_bridge, math.hypot(nx - x, ny - y))
            x, y = nx, ny
    totals = {cat: 0.0 for cat in set(CATEGORIES.values())}
    for name, e in features.items():
        cat = category(name)
        if cat:
            totals[cat] += e
    return {"features_mm_filament": {k: round(v, 3) for k, v in features.items()},
            "totals_mm_filament": {k: round(v, 3) for k, v in totals.items()},
            "longest_bridge_move_mm": round(longest_bridge, 2),
            "config": {k: config[k] for k in ("enable_support", "support_type", "support_threshold_angle",
                                              "support_on_build_plate_only") if k in config}}


def _is_number(s: str) -> bool:
    try:
        float(s)
    except ValueError:
        return False
    return True


def verdict(parsed: dict, max_overhang: float | None) -> tuple[str, list[str]]:
    notes = []
    cfg = parsed["config"]
    if not parsed["features_mm_filament"]:
        return "inconclusive", ["no '; FEATURE:' or ';TYPE:' comments found: cannot tell support from part"]
    if parsed["totals_mm_filament"]["support"] > 0:
        return "fail", [f"support extrusion {parsed['totals_mm_filament']['support']} mm of filament"]
    enabled = cfg.get("enable_support")
    if enabled is None:
        return "inconclusive", ["enable_support not found in the G-code config block: "
                                "zero support cannot be trusted; confirm supports were ON"]
    if enabled.strip() not in ("1", "true"):
        return "inconclusive", [f"enable_support = {enabled}: supports were OFF, so zero support proves nothing"]
    if max_overhang is not None:
        want = 90.0 - max_overhang
        got = cfg.get("support_threshold_angle")
        if got is None or not _is_number(got):
            notes.append("support_threshold_angle not found; threshold unconfirmed")
            return "inconclusive", notes
        if abs(float(got) - want) > 0.5:
            return "inconclusive", [f"support_threshold_angle = {got} (from horizontal) but {want:g} expected "
                                    f"for {max_overhang:g} deg from vertical"]
    if cfg.get("support_on_build_plate_only", "0").strip() in ("1", "true"):
        notes.append("support_on_build_plate_only = 1: overhangs above the part get no support and are not counted")
        return "inconclusive", notes
    if parsed["totals_mm_filament"]["overhang"] > 0:
        notes.append("overhang-wall extrusion present: inspect those layers in the preview")
    if parsed["totals_mm_filament"]["bridge"] > 0:
        notes.append(f"bridges present, longest single move {parsed['longest_bridge_move_mm']} mm: "
                     "document every intentional bridge and its span")
    return "pass", notes


def find_slicer(explicit: str | None) -> str | None:
    if explicit:
        return explicit if Path(explicit).exists() or shutil.which(explicit) else None
    for name in SLICER_NAMES:
        hit = shutil.which(name)
        if hit:
            return hit
    for path in SLICER_PATHS:
        if Path(path).exists():
            return path
    return None


def slice_model(slicer: str, model: Path, machine: Path, process: Path, filament: Path,
                max_overhang: float, workdir: Path, dry_run: bool) -> Path | None:
    proc = json.loads(process.read_text(encoding="utf-8"))
    proc.update({"enable_support": "1", "support_threshold_angle": f"{90.0 - max_overhang:g}",
                 "support_on_build_plate_only": "0"})
    proc.setdefault("support_type", "normal(auto)")
    forced = workdir / f"forced_support_{process.name}"
    forced.write_text(json.dumps(proc, indent=2), encoding="utf-8")
    out3mf = workdir / f"{model.stem}_forced_support.3mf"
    cmd = [slicer, "--slice", "0", "--load-settings", f"{machine};{forced}", "--load-filaments", str(filament),
           "--outputdir", str(workdir), "--export-3mf", out3mf.name, str(model)]
    print("slicer command:", " ".join(f'"{c}"' if " " in c else c for c in cmd))
    if dry_run:
        return None
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not out3mf.exists():
        print(f"slicer failed (exit {result.returncode}):\n{result.stderr[-2000:]}", file=sys.stderr)
        return None
    return out3mf


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Slice with supports forced on, then count support extrusion.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--gcode", type=Path, help="existing .gcode or sliced .3mf to parse")
    src.add_argument("--model", type=Path, help="model to slice (needs --machine/--process/--filament)")
    ap.add_argument("--machine", type=Path)
    ap.add_argument("--process", type=Path)
    ap.add_argument("--filament", type=Path)
    ap.add_argument("--slicer", help="slicer executable (default: search PATH for Bambu Studio / OrcaSlicer)")
    ap.add_argument("--max-overhang", type=float, default=45.0, help="FROM VERTICAL (default 45)")
    ap.add_argument("--outdir", type=Path, help="where to write the forced profile and 3mf (default: temp dir)")
    ap.add_argument("--dry-run", action="store_true", help="print the slicer command and stop")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.model:
        missing = [n for n in ("machine", "process", "filament") if getattr(args, n) is None]
        if missing:
            print(f"error: --model needs --{', --'.join(missing)}", file=sys.stderr)
            return 2
        slicer = find_slicer(args.slicer)
        if slicer is None:
            print("INCONCLUSIVE: no Bambu Studio / OrcaSlicer executable found. Slice in the GUI with supports "
                  "ENABLED at the stated threshold, export G-code or a sliced 3mf, then rerun with --gcode.",
                  file=sys.stderr)
            return 2
        workdir = args.outdir or Path(tempfile.mkdtemp(prefix="fdm_support_"))
        workdir.mkdir(parents=True, exist_ok=True)
        sliced = slice_model(slicer, args.model, args.machine, args.process, args.filament,
                             args.max_overhang, workdir, args.dry_run)
        if sliced is None:
            return 0 if args.dry_run else 2
        source = sliced
    else:
        source = args.gcode
    try:
        parsed = parse(read_gcode(source))
    except (OSError, zipfile.BadZipFile, SystemExit) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    result, notes = verdict(parsed, args.max_overhang)
    report = {"source": str(source), "result": result, "notes": notes, **parsed,
              "unverified_tags": [], "max_overhang_from_vertical": args.max_overhang}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{source.name}: {result.upper()}")
        for n in notes:
            print(f"  - {n}")
        print(f"  config: {parsed['config'] or 'none found'}")
        print(f"  totals (mm of filament): {parsed['totals_mm_filament']}")
        print("  feature names seen (verify against your slicer): "
              + (", ".join(sorted(parsed['features_mm_filament'])) or "none"))
    return {"pass": 0, "fail": 1}.get(result, 2)


if __name__ == "__main__":
    sys.exit(main())
