---
name: fdm-design
description: "Use when designing, revising or reviewing parts to be printed on an FDM/FFF printer (Bambu Lab, Prusa, Creality, Voron and others), especially electronics enclosures, mounts, brackets and multi-part shells, in any CAD tool (SolidWorks, Fusion, Onshape, FreeCAD, OpenSCAD, CadQuery, build123d). Covers print orientation, overhangs and bridges, wall and fit allowances, heat-set inserts, load paths and failure consequences, connector openings, cable routing, shell joints, and how to verify a 'no supports' or 'fits' claim before anyone prints. Not for resin, CNC or injection moulding."
---

# FDM Design

Design printable parts that work on the first print and survive service. Rules are
parameterised by printer, nozzle and material; examples assume a Bambu Lab A1/X1, a 0.4 mm
nozzle and PETG or PLA. Numbers live in `references/` with their source and confidence.
Never present a number from memory as a fact: cite the reference, measure, or mark it
`unverified`.

## Conventions (fixed; state them in every design note)

- **Angles are measured from vertical.** 0° is a wall, 90° is a horizontal ceiling. Default
  overhang limit: 45° from vertical. Bambu Studio / OrcaSlicer `support_threshold_angle` is
  measured **from horizontal** (`from_vertical = 90 − slicer_value`); the Bambu default of 30
  supports only faces beyond 60° from vertical, so it hides overhangs a 45° rule would flag.
- **Clearances are per side**, never total.
- **Every dimension carries a tag:** `measured` (calipers, on the user's part), `datasheet`
  (with link), `reference` (from `references/`, with its confidence) or `placeholder`.
- **Every claim carries a level:** `CAD-verified`, `sliced` (which slicer, profile, supports
  on/off, threshold) or `printed`. Never upgrade a level you did not reach.

## Hard rules (the six failure modes this skill exists to prevent)

1. **No "support-free" claim without two independent checks.** A slice with supports
   disabled reporting "0 support" proves nothing. A support-free claim needs BOTH
   (a) a slice with supports explicitly ENABLED at the stated threshold, showing zero support
   extrusion (`scripts/slice_support_check.py`), AND (b) a geometric audit of the oriented
   mesh that passes (`scripts/overhang_audit.py`). List every intentional bridge with its span.
   If either check could not run, say "not verified", not "support-free".
2. **Ask "what is scrapped if this breaks?" for every load path.** A tall printed boss with a
   blind heat-set insert and no access from below turns one cracked boss into a scrapped
   shell. Prefer replaceable metal standoffs or through-bolts reachable from outside. Printed
   bosses locate or carry light loads only, with broad roots, fillets or gussets. Counterbores
   on the bed face need a modelled sacrificial layer or two-layer bridge
   (`references/structure.md`).
3. **Connector openings come from the PLUG, not the receptacle.** Never boolean-cut the
   socket body. Use the mating plug's overmould envelope + per-side clearance, check the
   engagement depth through the wall, add a lead-in chamfer and finger/latch access. Measure
   the user's actual cables; internal right-angle plugs need wall clearance plus their bend
   envelope (`references/connectors.md`).
4. **Route cables before placing modules.** Draw cable corridors first using purchasable stock
   lengths and bend radii, then place modules so each route equals a stock length. No routes
   over heat sources or fan inlets; latch and finger access at both ends
   (`references/cable-routing.md`).
5. **Shell joints copy the reference.** When retrofitting or extending an existing design,
   measure and reproduce its lip/tongue-and-groove, edge treatment and gap. Reproduce every
   mounting point and fastener of the parts you keep: extract the reference's hole map
   (sections of the original meshes), overlay it on yours, and account for each hole as
   matched, moved with approval, or intentionally unused. One edge language
   across all parts; every opening lies entirely within one part; mirrored panels stay
   symmetric unless the user approves otherwise (`references/shell-joints.md`).
6. **No silent structural changes.** Any change to outer dimensions, split lines, port
   positions, mounting pattern or the user's stated layout needs explicit approval first.
   Report every deviation from the brief, with the reason, even when approved.

## Verification you can trust

- **Every check must be able to fail.** Before relying on a check, run it once on a fixture
  that must fail (a cantilever, overlapping solids, a supports-off G-code). A check that
  cannot fail proves nothing. The test suite in this repository does exactly that.
- **Inspect outputs, not summaries.** When one agent (or person) directs and another executes,
  acceptance means looking at the actual artefacts: renders from several angles, section cuts
  through bosses, joints and connector openings, the slicer preview with supports on, and the
  raw check output. An executor's "all checks pass" is a claim to verify, not evidence.
- Report what was checked as well as what was found, including checks that were skipped.

## Workflow

1. **Brief.** Collect printer, nozzle, material, slicer profile; photos and drawings of every
   component; the user's actual cables and plugs; purchase constraints (stock cable lengths,
   standoff and insert SKUs). Ask before guessing; mark guesses `placeholder`.
2. **Layout for approval.** Module positions, cable corridors (rule 4), port positions,
   split lines and outer dimensions. Get explicit approval before detailed modelling (rule 6).
3. **Orientation first.** Choose each part's print orientation before adding ribs, bosses,
   holes and overhangs. Large shells usually print on their outside face with pockets up.
   Put screw-to-screw bending loads along continuous XY perimeters, not across layers.
4. **Structure.** Failure-consequence pass per load path (rule 2); choose fasteners by buying
   dimension (thread, length under head, standoff length, insert SKU) before modelling pockets.
5. **Openings and joints.** Plug-envelope openings (rule 3); joints matched to the reference
   (rule 5); one edge treatment.
6. **DfAM detailing** (`references/dfam-rules.md`): walls as whole multiples of line width;
   45° chamfers instead of fillets on bed-facing edges; teardrop or flat-topped horizontal
   holes; short, documented bridges; insert bores vertical where possible.
7. **Fits** (`references/fits-and-inserts.md`): per-side clearances from a coupon, not from a
   table. For an uncalibrated printer print a ladder at 0.25 / 0.35 / 0.45 mm per side. Verify
   insert bore and depth against the supplier drawing, then a coupon. Do not double-compensate
   if the slicer applies hole/XY compensation.
8. **Assembly check.** Start from the open shell: every part can enter in order, every insert
   can be heated from an exposed face, every screw has tool access, every plug can be inserted
   and released, and the assembly comes apart without prying.
9. **Verify** (`references/verification.md`): mesh check, overhang audit, forced-support slice,
   interference with plugs at full engagement and fasteners at final depth. Negative test each
   check once. Inspect renders and sections yourself.
10. **Deliver.** Native CAD, oriented watertight meshes in mm, BOM with purchasable parts,
    assembly order, list of deviations and approvals, list of intentional bridges, and each
    claim's level (CAD-verified / sliced / printed). Recommend a coupon before the full part.

## Scripts

All in `scripts/`, Python 3.10+, numpy required; trimesh and manifold3d optional. Run with
`--help`. Exit codes: 0 pass, 1 fail, 2 inconclusive or error. Treat 2 as "not verified".

| Script | What it proves | What it does not prove |
|---|---|---|
| `overhang_audit.py part.stl [--max-overhang 45 --max-bridge 10 --json]` | No downward face beyond the limit off the bed; ceilings classified as bridge (with span), cantilever or floating | Sag, curl or cooling quality; first-layer adhesion |
| `slice_support_check.py --gcode plate.gcode` or `--model ... --machine/--process/--filament` | The slicer, with supports forced on at the threshold, generated zero support | That the tag names match slicers other than Bambu Studio (confirmed there; others unverified) |
| `mesh_check.py part.stl --printer a1` | Watertight, consistent winding, outward normals, one body, fits the build volume | Wall thickness, printability |
| `interference_check.py a.stl b.stl ... [--allow a.stl:b.stl]` | Pairwise solid intersection volume (exact with manifold3d; bounding boxes otherwise, reported as inconclusive) | Clearance margins, motion, assembly order |

## References

- `references/dfam-rules.md` — line width, walls, overhangs, bridges, teardrops, counterbore bridging, elephant foot
- `references/fits-and-inserts.md` — clearance tables, coupon ladder, heat-set insert bores, snap-fit strain, material HDT
- `references/structure.md` — bosses and standoffs, failure-consequence table, replaceable load paths
- `references/connectors.md` — plug envelopes (USB-C, HDMI, RJ45, keystone, DC barrel) and what must be measured
- `references/cable-routing.md` — bend radii, stock lengths, corridor modelling
- `references/shell-joints.md` — lips, tongue and groove, split lines, gap budget, edge language
- `references/verification.md` — slicer CLI recipes, G-code feature parsing, angle conversion, negative tests, acceptance review
- `references/case-study.md` — an anonymised retrofit where all six failure modes happened
- `references/sources.md` — every source, licence and confidence level
