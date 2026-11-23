# DfAM rules for FDM

Design-for-additive rules that do not depend on the part's function. Every number has a source
key from [sources.md](sources.md) and a confidence:
**[P]** primary source (vendor profile, standard, datasheet), **[S]** secondary (blog, other
skill, forum), **[U]** unverified or no quantitative source. Calibrate with a coupon before you
trust any of them on a new printer/material pair.

## Line width and wall thickness

| Item | Value | Source |
|---|---|---|
| Bambu default line width, 0.4 nozzle | outer wall 0.42 mm, inner wall 0.45 mm | `bambu-common` [P] |
| Bambu default walls / shells | 2 walls, 3 top + 3 bottom layers | `bambu-common` [P] |
| Prusa line width, 0.4 nozzle | 0.45 mm; 1/2/3/4 perimeters ≈ 0.45 / 0.9 / 1.35 / 1.8 mm | `prusa-modeling` [P] |
| Thickness between 1 and 2 perimeters | does not print cleanly (gap fill or dropped) | `prusa-modeling` [P], `print3d-designer` [S] |
| Features thinner than 2 × line width | may be silently dropped by the slicer | `print3d-designer` [S] |
| Minimum rib, 0.4 nozzle | 0.8 mm | `print3d-designer` [S] |

Rules:

- Make load-bearing walls a whole multiple of the line width you will actually slice with.
  With 0.42/0.45 mm lines, about 1.8 mm is a four-perimeter starting point and about 2.6–2.7 mm
  a six-perimeter one (arithmetic from the Bambu defaults; the slicer adjusts spacing, so
  check the toolpath preview).
- Ribs that carry load: 1.35–1.8 mm (3–4 Prusa perimeters) is a reasonable start [S/arith].
- Layer height sets the Z step. Keep measured fit dimensions exact; round non-critical floors
  and shoulders to whole layers when there is room.

## Overhangs

| Statement | Source |
|---|---|
| Overhangs "up to 45°" print without support | `hubs-fdm` [S] |
| Generally 45–60°, newer Prusa hotends up to about 75° | `prusa-modeling` [P for Prusa hardware] |
| PETG test: ≥ 45° from horizontal safe, 30–45° slight sag, < 30° needs support or bridging | `print3d-designer` [S] |
| Default 45° from vertical; prefer, in order: re-orient → chamfer → split → teardrop → support | `b123d-print` [S] |
| Bambu `support_threshold_angle` default 30, measured from horizontal; `enable_support` default 0 | `bambu-common`, `bambu-wiki-support` [P] |

Rules:

- Use the skill convention: angles **from vertical**, limit 45° unless a coupon on this
  printer/material shows otherwise. Convert slicer thresholds: `from_vertical = 90 − slicer`.
- Edges facing the bed get a 45° chamfer, not a fillet (a fillet's lowest band is a near-
  horizontal overhang) [`prusa-modeling`, `print3d-designer` S]. A 0.3–0.5 mm 45° chamfer on
  the bottom edge also hides elephant foot [`print3d-designer` S].
- Rising portal roofs (openings in vertical walls): gable or chamfer.
- **Never design a face exactly at the threshold.** Faces modelled at exactly 45° with a 45°
  slicer threshold were supported by Bambu Studio 02.09.01.70 (rounding puts them on the wrong
  side): side-wall vent slot roofs grew support columns from the bed to 25 mm. Keep a margin:
  roofs and lead-ins ≤ 40° from vertical (35° recommended) with a flat apex ≤ 0.8 mm
  [field observation, this skill's case study; check on your slicer].

## Bridges

| Statement | Source |
|---|---|
| Bridges "less than 5 mm" print without sag | `hubs-fdm` [S] |
| PETG bridges about 10 mm | `print3d-designer` [S] |
| Default maximum bridge 10 mm; cavities that need support removal at least 5 mm | `b123d-print` [S] |
| Bambu labels a 100 % overhanging wall "Overhang wall" without a warning | `bambu-wiki-bridge` [P], `print3d-designer` [S] |

Rules:

- `overhang_audit.py --max-bridge` defaults to 10 mm; lower it to 5 mm when appearance matters
  or the material bridges poorly. Every intentional bridge is listed with its span in the
  design notes.
- A ceiling anchored on one side only is a **cantilever**, not a bridge, whatever its width.

## Horizontal holes and teardrops

- Small horizontal holes: 90° teardrop (point up). Large holes (about ⌀10 and up): flat top,
  roof 0.4 mm above the theoretical circle [`rahix` S].
- Use a teardrop or truncated gable where it clears the connector or moving part; otherwise
  keep the bridge short and document it.

## Counterbores and holes on the bed face

- A counterbore opening onto the bed face leaves an annular ceiling with nothing under its
  inner edge: a cantilever ring. Fix it in CAD with a **two-layer orthogonal bridge**: the
  first layer leaves two bridges about one layer thick across the counterbore; the second
  layer leaves a square whose side equals the hole diameter; then the round hole continues
  normally [`rahix` S]. Or model a one-layer **sacrificial membrane** and drill it after
  printing [`hackaday-sacrificial` S].
- OrcaSlicer can do this in the slicer ("Bridge counterbore hole": partially bridged or
  sacrificial layer) [`orca-bridging` P for Orca]. If you rely on the slicer feature, say so;
  the geometric audit will still report the ring.
- Heat-set inserts installed from the back side through a bridged hole are unreliable: molten
  plastic is pushed into the bore [`rahix` S].

## Dimensional effects

| Item | Value | Source |
|---|---|---|
| A1 0.20 mm Standard `elefant_foot_compensation` | 0.075 mm | `bambu-a1-020` [P] |
| Bambu `xy_hole_compensation` default | 0 | `bambu-common` [P] |
| Prusa achievable precision | "at least 0.2 mm" | `prusa-modeling` [P] |
| Per-face tolerance; clearance should be ≥ 2 × printer tolerance | about ±0.1 mm | `rahix` [S] |
| Strength in the ideal orientation vs worst | about 3 × | `rahix` [S] |
| Shrinkage percentages per material | not found from the vendor | [U] |

- If the slicer applies hole or XY compensation, model nominal sizes; otherwise the
  correction is applied twice (second-hand advice, [U]).

## Orientation

- Decide orientation per part before detailing. Large flat shells usually print on their
  outside face, with pockets and mounting holes facing up.
- Put flat retention tabs in the bed plane so bending runs along continuous perimeters.
- Vertical pins thinner than about ⌀5 mm are weak [`hubs-fdm` S]; avoid relying on thin
  Z-loaded snap tabs for repeated service.
- Ribs print best standing up so the load runs along the extruded lines [`innostation` S].
