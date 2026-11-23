# Structure: load paths, bosses and what breaks

Confidence keys as in [dfam-rules.md](dfam-rules.md).

## Failure-consequence analysis (do this for every load path)

For each thing that carries load (a board, a drive cage, a heavy heatsink, a panel that gets
pushed when a plug is inserted), fill in one row:

| Load path | Load (static / insertion / drop) | What breaks first | What is scrapped if it breaks | Repair | Accept? |
|---|---|---|---|---|---|
| Drive cage → 4 printed bosses → bottom shell | drive mass, insertion force | boss root (layer line) | whole bottom shell | none: inserts are blind, no access from below | **No** |
| Drive cage → 4 metal standoffs → through-bolts from below | same | standoff thread or printed seat | one standoff | unscrew from outside, replace | Yes |

The question is not "is it strong enough?" but "**when it fails, what do we lose and can we
fix it from outside?**". A design where the weakest, most likely-to-fail feature is integral
to the largest, slowest-to-print part fails this test.

## Rules

1. **Prefer replaceable metal for real loads.** Brass/steel standoffs, through-bolts with nuts
   or inserts reachable from the outside, captive nuts in pockets that can be re-seated. A
   damaged fastener should cost one fastener, not a shell. [U: an engineering principle; no
   quantitative source was found.]
2. **Printed bosses locate or carry light loads.** Use them for alignment, cable clips, light
   PCBs. Give them broad roots: root fillet R1.5–3 or triangular gussets, and merge them into
   walls where possible [`sovol-bosses` S, `stratasys-fdm` P]. Bosses usually fail at the
   root, along a layer line [`sovol-bosses` S].
3. **Tall printed bosses are suspect.** Height multiplies the bending moment at the root, and a
   blind insert at the top cannot be replaced once the shell is closed. If a tall boss is
   unavoidable: gusset it to the nearest wall, make the insert accessible from below (through
   hole + counterbore), or replace the boss with a metal standoff screwed into a short printed
   seat.
4. **Bending across layers is the weak direction.** Orient so screw-to-screw bending runs along
   XY perimeters. Ribs carry load best when printed upright [`innostation` S].
5. **Stratasys' FDM guide:** bosses, ribs and gussets need not be thinned as in injection
   moulding; support bosses with gussets or ribs [`stratasys-fdm` P].
6. **Counterbores on the bed face** need a sacrificial or two-layer bridge
   ([dfam-rules.md](dfam-rules.md#counterbores-and-holes-on-the-bed-face)); otherwise the
   screw-head seat is a sagging ring exactly where clamp load is applied.
7. **Thread engagement.** Calculate the stack: screw length under head − clamped thickness −
   standoff/insert entry = engagement. Check tip clearance at the bottom of blind threads; for
   factory blind threads, measure usable depth or use the supplier drawing; if unknown, give a
   safe first-trial screw length.

## Fastener choice before geometry

Pick buying dimensions first: thread and pitch, length under head, head and washer diameter,
standoff length and thread type (M-F, F-F), insert SKU. Model pockets around those, not the
other way round. Put them in the BOM with a purchasable source.
