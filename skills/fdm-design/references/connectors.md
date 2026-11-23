# Connector openings

Confidence keys as in [dfam-rules.md](dfam-rules.md). The receptacle on the board is the
wrong reference: the part that has to pass through your wall is the **plug and its
overmould**, held by fingers.

## Method

1. **Start from the mating plug envelope** (overmould width × height, plus strain relief and
   latch), not the receptacle body. Never make the opening by boolean-subtracting the socket.
2. **Add per-side clearance** (from your fit coupon; see
   [fits-and-inserts.md](fits-and-inserts.md)) and a **lead-in chamfer** on the outside.
3. **Check engagement depth.** Model the plug fully mated. The overmould stops at the outside
   of the wall or in a recess; the distance from that stop to the receptacle's mating datum
   must be less than the plug's insertion length. A thick flat wall can stop the plug short
   of latching.
4. **Finger and latch access.** RJ45 tabs, locking USB-C, SATA latches and HDMI need room to
   grip and release. Model a finger envelope; if the wall is thick, recess around the opening.
5. **Measure the user's actual cables.** Overmoulds vary by brand far beyond any standard.
   Record measured sizes with the tag `measured`.
6. **Internal right-angle plugs** need clearance to the wall plus their cable bend envelope
   (see [cable-routing.md](cable-routing.md)).
7. **Probe it.** In CAD, push the plug envelope to full engagement and run
   `interference_check.py`; then move it 0.05 mm further in: it should now collide with its
   stop. If it does not, the stop is not where you think [`crimpdeq-pr` S].

## Data

| Connector | Data | Source |
|---|---|---|
| USB-C plug overmould | max 12.35 W × 6.5 H mm; plug length 6.65 ± 0.10 mm | USB-IF Type-C compliance document [`usbc-compliance` P] |
| USB-C plug overmould, later revision | 12.85 × 7.0 mm (an ECN is said to relax the limit) | [U] |
| USB-C wall practice | outside recess 13.65 × 7.8 mm (12.85 × 7.0 + 0.4 per side); recess floor 0.3 mm in front of the receptacle face; receptacle datum A 6.20 mm inside the opening | [`crimpdeq-pr` S]; same failure reported in [`count-fidget-issue` S] |
| USB-C, printed and tested | cutout 10 × 4.5, outside recess 13 × 7.5, 0.8 mm wall left; engagement about 5.8 / 6.6 mm; a flat 2 mm wall allowed only about 4.6 mm engagement and "some cables won't latch" | [`alexlenk` S] |
| HDMI Type A | plug shell 13.9 × 4.45 mm; receptacle opening 14 × 4.55 mm | HDMI 1.3/1.4 specification, as quoted [S]. **No public maximum for the overmould: measure.** Cable bend guidance in the spec figure: [U] |
| RJ45 8P8C plug | about 22.48 × 11.68 × 8.00 mm; boots are not standardised | [`wiki-modular` S]; measure the boot |
| Keystone jack | front 14.5 × 16.0 mm; flat-panel snap-in cutout about 14.5–14.7 × 19–19.7 mm | [`wiki-keystone` S], forum and vendor pages; medium confidence |
| DC 5521 panel jack | ⌀8 mm hole, about 16 mm free behind the panel | [`alexlenk` S] ("measure yours") |
| Space around boards | 10 mm finger zone around each board; 28 mm above boards with Dupont headers | [`alexlenk` S] |

## Openings and the shell

- An opening lies entirely within one part. Never let a split line cross a connector opening
  (see [shell-joints.md](shell-joints.md)).
- Keep the wall around a port at least as thick as the surrounding wall, or rib it: plugs are
  pushed and levered.
- Port positions are a structural decision: moving one needs the user's approval.
