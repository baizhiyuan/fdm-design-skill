---
name: fdm-part-review
description: "Use when reviewing, auditing or accepting an FDM/FFF part that already exists — an exported STL/3MF/STEP, sliced G-code or 3MF, renders/screenshots, or delegated CAD work returned by another agent or person — including verifying claims like 'support-free', 'fits' or 'ready to print'. Not for designing new parts: use fdm-design for that."
---

# FDM Part Review

Accept or reject an FDM part someone else (or an earlier pass) produced. The rules and numbers
are those of the `fdm-design` skill; this skill is the acceptance pipeline. It holds no
numbers of its own: every number comes from `../fdm-design/references/` with its confidence
key, from a measurement, or is marked `unverified`.

## Conventions (fixed; restate them in the verdict)

- **Angles are measured from vertical.** 0° is a wall, 90° is a ceiling. Slicer thresholds
  are measured from horizontal: `from_vertical = 90 − slicer_value`.
- **Clearances are per side**, never total.
- **Every dimension carries a tag:** `measured`, `datasheet`, `reference` or `placeholder`.
  Untagged dimensions are treated as `placeholder`.
- **Every claim carries a level:** `CAD-verified`, `sliced` or `printed`. The level is what
  the evidence you inspected supports, not what the author wrote.

## Inputs to collect

Ask for anything missing; list what never arrived under "Not checked".

1. **Artefacts in print orientation**: one mesh per part (STL or 3MF, mm, Z up, bed face at
   lowest Z), the assembly in one frame with plugs fully mated and screws at final depth,
   native CAD or STEP if available, sliced G-code or 3MF, renders and section cuts.
2. **The brief or reference design**: outer dimensions, split lines, port positions, mounting
   pattern, approved deviations, reference hole map.
3. **Machine**: printer, nozzle, material, slicer and version, process profile, support
   threshold.
4. **The author's claims**, each with the level the author states (for example "support-free,
   sliced in Bambu Studio, supports on at 45"). Write them down before checking anything.

## Stage 1: machine checks first

Cheap and objective, so they run before any judgement. Scripts live in
`../fdm-design/scripts/` (Python 3.10+, numpy; trimesh and manifold3d optional). Exit codes:
0 pass, 1 fail, 2 inconclusive or error. **Before each check, run its must-fail fixture and
show it failing** (`../fdm-design/references/verification.md` section 5).

| Order | Check | Must-fail fixture first |
|---|---|---|
| 1 | `../fdm-design/scripts/mesh_check.py part.stl --printer a1` | cube with one face deleted |
| 2 | `../fdm-design/scripts/overhang_audit.py part.stl --max-overhang 45 --max-bridge 10` | cantilever ledge; 60° ramp at 45 |
| 3 | `../fdm-design/scripts/interference_check.py shell.stl board.stl plug.stl` | two overlapping boxes |
| 4 | `../fdm-design/scripts/slice_support_check.py --gcode plate.gcode` (or `--model`) | G-code with `enable_support = 0` (must be 2) |

When installed as the plugin, delegate Stage 1 to the `fdm-verification-runner` agent; it
returns raw output and exit codes per check. Keep the raw output for the verdict.

## Stage 2: three specialist lanes, in parallel

Give each lane the same package: the artefacts, the brief, the machine settings, the author's
claims and the Stage 1 raw output. Run them in parallel with the plugin agents:

| Agent | Lane |
|---|---|
| `fdm-printability-reviewer` | orientation, overhangs, bridges, walls, edges, holes, fits |
| `fdm-structural-engineer` | load paths, failure consequence, fasteners, materials under load |
| `fdm-integration-engineer` | connector openings, cables, assembly order, shell joints |

Each returns a findings table with cited evidence and a "Not checked" list, and edits nothing.

**Without the agents** (the skill was copied, not installed as a plugin): make three separate
passes, one per lane, in sequence, never one merged pass. Read the lane's references directly
before each pass:

- Printability: `../fdm-design/references/dfam-rules.md`,
  `../fdm-design/references/fits-and-inserts.md`, `../fdm-design/references/verification.md`
- Structural: `../fdm-design/references/structure.md`,
  `../fdm-design/references/fits-and-inserts.md`, `../fdm-design/references/dfam-rules.md`
- Integration: `../fdm-design/references/connectors.md`,
  `../fdm-design/references/cable-routing.md`, `../fdm-design/references/shell-joints.md`

## Stage 3: merge

1. Deduplicate findings that name the same location and problem; keep the highest severity.
2. Spot-check any finding you doubt against its cited reference. A finding whose citation does
   not say what the finding claims is dropped or downgraded, and the drop is reported.
3. Compare the artefacts with the brief yourself: outer dimensions, split lines, port
   positions, mounting pattern, reference hole map.
4. Inspect the artefacts yourself: renders from several sides, section cuts through each boss,
   joint and connector opening, the slicer preview with supports ON.

## Verdict format

```text
Verdict: ACCEPT | REJECT
Conventions: angles from vertical; clearances per side.

Findings by severity
  BLOCK  | location | problem | evidence | fix
  WARN   | ...
  NOTE   | ...

Claims (author's level -> verified level, evidence)
  "support-free"  sliced -> not verified (overhang audit exit 1; forced-support slice not run)
  "fits"          printed -> CAD-verified (interference exit 0, plugs at full engagement)

Deviations from the brief
  each change, approved (by whom, when) or UNAPPROVED

Not checked
  each item, with the reason
```

Reject when any BLOCK remains. **Any unapproved deviation from the brief is a BLOCK**, even if
every check passes.

## Rules

1. **The author's summary is a claim, not evidence.** "All checks pass" counts for nothing
   until you have seen the raw output.
2. **Never upgrade a claim level.** A part that was sliced but not printed is at most
   `sliced`; a claim with no inspected evidence is "not verified".
3. **Exit 2 is "not verified"**, never "pass". A check that did not run is listed, not
   assumed.
4. **Support-free needs both** a passing forced-support slice and a passing geometric audit
   (fdm-design hard rule 1). With only one, the claim is "not verified".
5. **Inspect the artefacts yourself.** Renders, sections and the slicer preview with supports
   on; a reviewer's or runner's summary is also a claim.
6. **Review does not redesign.** Suggested fixes stay local to findings; layout changes go back
   to the author through `fdm-design`.
