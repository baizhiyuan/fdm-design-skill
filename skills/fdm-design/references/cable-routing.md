# Cable routing

Confidence keys as in [dfam-rules.md](dfam-rules.md). Route first, place modules second.

## Method

1. **List every cable** with its purchasable stock lengths, outer diameter (measured), plug
   type at each end and bend radius.
2. **Draw corridors in CAD** as swept envelopes: diameter + slack, with bend radius ≥ the
   table below, from plug exit to plug exit. Include the straight section behind each plug
   before the first bend.
3. **Place modules so each corridor length equals a stock length** (plus a little service
   slack). Do not design a route that needs a 137 mm cable nobody sells.
4. **Keep corridors off heat sources and fan inlets**: SBC heatsinks, drive surfaces, buck
   converters, and the air path from inlet to outlet.
5. **Both ends accessible**: a finger can reach every latch, and each cable can be unplugged
   without removing another module.
6. Put the opening where the cable ends, with empty floor in front of it [`alexlenk` S].
7. Add clips or channels so cables do not rest on modules. Review a render from above with
   the lid off: "spaghetti over modules" is a failed layout.

## Bend radius and length data

| Cable | Data | Source |
|---|---|---|
| UTP (twisted pair) | bend radius ≥ 4 × cable diameter (shielded: 8 ×) | TIA/EIA-568-B.1 §10.2.1.1 [`tia-568` P] |
| SATA internal | maximum cable length 1 m; connector mating cycles 50 | SATA 3.x specification [P, as quoted] |
| SATA bend radius | not in the specification; 15–20 mm or 3–4 × diameter are vendor/retail statements | [U] |
| SATA stock lengths | common lengths must be checked with suppliers | [U] |
| FFC 0.5 mm pitch | R10 mm used in a Molex flex-life test; 0.25 pitch R4 | [`molex-ffc` P]; a **test condition**, not a minimum bend radius |
| USB-C, HDMI, DC | no bend radius data collected; measure the cable or use the vendor datasheet | [U] |

## Rules of thumb that need no number

- Flat cables bend only across their flat face; plan twists where there is room.
- A right-angle plug changes the corridor start, not the bend radius of the cable behind it.
- Short internal jumpers are the stiffest: give them the straightest path.
- Power and drive cables are often the thickest; route them first.
