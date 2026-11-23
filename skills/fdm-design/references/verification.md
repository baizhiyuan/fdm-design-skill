# Verification

What to run, what each result means, and how to accept work you did not do yourself.

## Claim levels

| Level | Meaning | Required evidence |
|---|---|---|
| CAD-verified | Geometry checks passed on exported meshes | Script output (mesh, overhang, interference), sections and renders |
| Sliced | A slicer accepted it with stated settings | Slicer + version, printer and process profile, supports ON/OFF, threshold, support volume, bridge list |
| Printed | A physical part was made and checked | Photo or measurement; what was fitted to what |

Never write "support-free", "fits" or "works" without the level and its evidence.

## Angle convention

The skill measures angles **from vertical** (0° wall, 90° ceiling). Bambu Studio and
OrcaSlicer measure `support_threshold_angle` **from horizontal**: surfaces flatter than the
threshold get support [`bambu-wiki-support` P]. Convert with `from_vertical = 90 − slicer`.

| Skill limit (from vertical) | Slicer `support_threshold_angle` |
|---|---|
| 45° | 45 |
| 50° | 40 |
| 60° | 30 (Bambu default) |

## 1. Mesh check

`python scripts/mesh_check.py part.stl --printer a1` (A1 build volume 256 mm per axis
[S: research notes; confirm on the vendor spec page]; pass `--build-volume X Y Z` for other printers).
Watertight, consistent winding, outward normals, one body, fits.

## 2. Geometric overhang audit (slicer-independent)

`python scripts/overhang_audit.py part_oriented.stl --max-overhang 45 --max-bridge 10 --json`

- Export each part **in print orientation**.
- Slope findings: faces beyond the limit. Ceiling findings: `bridge` (anchored on two sides,
  with estimated span), `cantilever` (one-sided: ledges, counterbore rings) or `floating`.
- Spans are estimates from sampled points (about ±0.5 mm). For L-shaped or annular regions
  check the reported box and look at the part.
- A pass does not prove good surface quality; it proves nothing hangs beyond the stated limit.

## 3. Slice with supports forced on

Bambu Studio and OrcaSlicer share a CLI [`bambu-cli` P, `orca-cli` P]:

```bash
bambu-studio --slice 0 \
  --load-settings "machine.json;process_forced_support.json" \
  --load-filaments "filament.json" \
  --outputdir out --export-3mf part_forced.3mf part.stl
```

- `process_forced_support.json` is your process profile with `enable_support = 1`,
  `support_threshold_angle = 90 − limit`, `support_on_build_plate_only = 0`.
  `slice_support_check.py --model ...` writes it for you; `--dry-run` prints the command.
- Profiles must be flattened (no unresolved `inherits`) and `compatible_printers` must point at
  the system ancestor preset; `--arrange 1` rotates parts, so leave it off for oriented parts
  [`print3d-designer` S].
- No slicer on the machine? Slice in the GUI with supports enabled at the threshold, export
  G-code or a sliced 3MF, then: `python scripts/slice_support_check.py --gcode plate.gcode`.
- Feature tags: Bambu/Orca write `; FEATURE: <name>`, PrusaSlicer `;TYPE:<name>`. "Support",
  "Support interface", "Support transition", "Overhang wall" and "Bridge" are confirmed in
  real G-code from Bambu Studio 02.09.01.70 (A1, 0.20 Standard, supports on); OrcaSlicer/PrusaSlicer names are not yet confirmed. The script
  matches substrings and prints every name it sees so you can check once.
- The script refuses to pass when `enable_support` is 0 or absent, the threshold does not
  match, or `support_on_build_plate_only` is on.
- OrcaSlicer may have `--export-statistics` [U]. PrusaSlicer: `--support-material
  --export-gcode`, then look for `;TYPE:Support material`; its CLI support detection has an
  open bug report [`prusa-cli-bug` S].

## 4. Interference and engagement

`python scripts/interference_check.py shell.stl board.stl plug_usbc.stl --allow boss.stl:insert.stl`

- Export all parts in one assembly frame. Plugs at full engagement, screws at final depth.
- Exact volumes need `pip install trimesh manifold3d`; without them overlapping bounding boxes
  are reported as POSSIBLE and the run is inconclusive (exit 2), never as clear.
- Intentional overlaps (insert interference, press fits) go in `--allow`, and are listed.
- Plug probe: also test the plug moved 0.05 mm further in; it must collide with its stop.

## 5. Negative tests (a check that cannot fail proves nothing)

Before trusting any check on a new setup, run it on something that must fail:

| Check | Must-fail fixture |
|---|---|
| overhang audit | a cantilever ledge; a 60° ramp at `--max-overhang 45` |
| forced-support slice | G-code with `enable_support = 0` (must be inconclusive, not pass) |
| interference | two overlapping boxes |
| mesh check | a cube with one face deleted |

`tests/` in this repository contains all of these. Idea from [`alexlenk` S]; reporting
"what was checked as well as what was found" from [`cad-khana`, idea only].

## 6. Accepting delegated work (director / executor)

When one agent or person specifies and another executes:

- The executor's summary is a claim. Accept on artefacts: raw check output, renders from
  several sides, section cuts through each boss, joint and connector opening, the slicer
  preview with supports on.
- Re-run at least one check yourself, and run its negative fixture first.
- Compare against the brief: outer dimensions, split lines, port positions, mounting pattern.
  Any unapproved change is a failure even if every check passes.
- Write the acceptance as: what you inspected, what you re-ran, what you did not check.
