# Fits, heat-set inserts, snap fits and materials

Confidence keys as in [dfam-rules.md](dfam-rules.md): [P] primary, [S] secondary, [U] unverified.
All clearances are **per side**.

## Clearance: there is no universal value

| Fit | Per-side clearance | Source |
|---|---|---|
| Snap-fit / interlocking parts, generic FDM | 0.5 mm | `hubs-snap` [S] |
| Press / sliding / free / print-in-place | 0.05 / 0.2 / 0.3 / 0.3 mm | `b123d-print` [S] |
| Hinges and sliding (Bambu H2D) | 0.15–0.2 mm; pin holes 0.2 mm | `ual-cci` [S] |
| Moving parts (Prusa) | at least 0.3 mm | `prusa-modeling` [P] |
| Print-in-place | about 0.3 mm | `rahix` [S] |

The values disagree because printers, profiles and materials disagree. Treat them as a range
to bracket, then measure.

## Coupon ladder (do this before a full part)

- Uncalibrated printer: print a fit coupon at **0.25 / 0.35 / 0.45 mm per side**, using the
  real mating part (or a printed copy) and the same orientation as the final part. This ladder
  is a starting heuristic carried over from the previous version of this skill and sits inside
  the published ranges above; it is not itself a sourced number.
- Allow for elephant foot (bottom layers), undersized holes and shrinkage. Record the result
  per printer + nozzle + material + profile and reuse it.
- Press-fit modelled envelopes may intentionally overlap their host. List those pairs
  explicitly (`interference_check.py --allow a:b`), separate from accidental collisions.

## Heat-set inserts

Guidance from CNC Kitchen [`cnck-tips` S, vendor-adjacent]:

- Blind hole about 1 mm longer than the insert; through holes need no extra length.
- Straight bore, no taper, usually no chamfer.
- Iron 10–20 °C above the print temperature (about 225 °C PLA, 245 °C PETG, 265 °C ABS).
  Press to about 90 % depth, then finish flush with a flat tool.

CNC Kitchen test, 2026-03 [`cnck-datasheets` S]:

- Printed holes came out about 0.25 mm under CAD size.
- For M3, a 4.2 mm CAD hole gave about 90 % of maximum strength; strength dropped sharply
  between 4.1 and 4.2 mm when drilled. For small inserts add 0.2–0.3 mm to the CAD bore.
- Pull-out about 1400 N in PLA, one setup: a trend, not a design value.

Bore table (CNC Kitchen data as re-published by a third party; **second-hand** [S]):

| Insert | Bore ⌀ | Blind depth | Min. wall around |
|---|---|---|---|
| M2 × 3 | 3.2 | 4.0 | 1.3 |
| M2.5 × 4 | 4.0 | 5.0 | 1.6 |
| M3 × 5.7 | 4.0 | 6.7 | 1.6 |
| M4 × 8.1 | 5.6 | 9.1 | 2.1 |
| M5 × 9.5 | 6.4 | 10.5 | 2.6 |
| M6 × 12.7 | 8.0 | 13.7 | 3.3 |

- **Conflict [U]:** another table from the same re-publisher gives M4 5.7 / M5 6.5 / M6 8.1 mm
  bores. The originals exist only as images. Use the supplier drawing for the exact SKU you buy.
- A ruthex M3 × 5.7 listing matches 4.0 / 6.7 / 1.6 (second-hand [S]). McMaster data: [U].
- Torque in PETG: about 1 N·m screwed directly into plastic vs about 3 N·m with heat-set
  inserts [`cnck-threads` S].

Rules:

- Choose the exact insert SKU before modelling the bore; then print a coupon that brackets
  the supplier bore by ±0.1–0.2 mm. State the verified bore and depth in the BOM.
- Every insert must be installable from an exposed face with the iron perpendicular. If the
  insert sits at the top of a tall boss, see [structure.md](structure.md) before accepting it.

## Cantilever snap fits

Root strain ε = 1.5 · h · Y / L² (h thickness, Y deflection, L length) [`mandarin3d` S, derived
from Bambu TDS and the Covestro method]:

| Material | Design strain |
|---|---|
| PLA | about 2 % |
| PETG | about 2.5 % |
| Frequently cycled | halve it |
| Bending across layers | halve it again |

A printed example: 1.2 mm thick, 9 mm long, about 2 % strain [`alexlenk` S].

## Materials: heat deflection

| Material | HDT @0.45 / @1.8 MPa (°C) | Source |
|---|---|---|
| PLA Basic | 57 / 54 | Bambu TDS V3.0 via a third-party summary [S] |
| PETG Basic | 71 / 68 | same [S] |
| ABS | 87 / 84 | same [S] |
| ASA | 100 / 92 | same [S] |
| PETG HF | 69 / 62, Tg 66 | `bambu-petg-hf-tds` [P] |

Enclosures near SBC heatsinks, drive bays or buck converters: check the local temperature
against HDT with margin, and prefer PETG/ASA over PLA for parts that carry load while warm.
