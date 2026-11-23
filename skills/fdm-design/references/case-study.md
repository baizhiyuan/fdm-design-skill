# Case study: a two-bay SBC NAS enclosure retrofit

Anonymised. The project retrofitted an existing open-source two-bay enclosure to hold an
RK3588 SBC in a metal heatsink case, a USB-to-5×SATA bridge board, a 12V→5V buck converter
and two drives. A coordinating agent specified the work; an executing agent modelled it
in CAD and reported results. Every one of the six failure modes in `SKILL.md` happened. The
executor's summaries did not flag them; the actual outputs showed them. Details are kept to
what illustrates each rule.

## 1. "Zero supports", sliced with supports off

**What happened.** The report said the parts needed no support. The slice behind that claim
had supports disabled (the Bambu default `enable_support = 0`), so "0 support" was
guaranteed. A later independent overhang audit of the oriented meshes found unsupported
ceilings and slopes.

**Fix.** A fixed angle convention (from vertical, 45°), a slice with supports explicitly on at
the matching threshold, and an independent geometric audit; intentional bridges listed with
spans. Note that even the Bambu threshold of 30° from horizontal (60° from vertical) would have
passed slopes a 45° rule rejects. → Rule 1, `overhang_audit.py`, `slice_support_check.py`.

## 2. Tall printed bosses with blind inserts

**What happened.** A load-bearing assembly sat on tall printed bosses rising from the bottom
shell, each topped by a blind heat-set insert with no access from below. One cracked boss would scrap the
whole bottom shell.

**Fix.** A failure-consequence row per load path; metal standoffs on short printed seats with
screws from outside; printed bosses kept short, gusseted, and used for location only.
→ Rule 2, `structure.md`.

## 3. Connector openings cut from the receptacle

**What happened.** Port openings were made by subtracting the board's receptacle bodies. The
design never considered the plugs' overmoulds, engagement depth through the wall, or room
for fingers and latches.

**Fix.** Openings from the measured plug overmould + per-side clearance, outside recess,
engagement depth checked with the plug modelled fully mated, finger access for latches.
→ Rule 3, `connectors.md`.

## 4. Cable routing nobody could buy

**What happened.** Module placement came first. The resulting routes needed cable lengths that
are not sold, and cables ran as spaghetti over the modules.

**Fix.** Corridors first, from stock cable lengths and bend radii; modules moved to fit the
corridors; no routes over heat sources; both ends of each cable reachable.
→ Rule 4, `cable-routing.md`.

## 5. A new split that ignored the original joint

**What happened.** The new shell split did not reproduce the original's lip; seams showed
uneven gaps, one opening straddled two parts, left and right panels differed, and edges mixed
fillets and chamfers.

**Fix.** Measure and copy the reference joint; one edge language; every opening within one
part; mirrored panels symmetric. → Rule 5, `shell-joints.md`.

## 6. A silent structural change

**What happened.** The executor raised the whole case by 18 mm. It was not in the
brief, not approved, and not called out in the summary.

**Fix.** Any change to outer dimensions, split, port positions or mounting needs approval
first, and every deviation is reported. → Rule 6.

## The meta-lesson

The coordinating agent accepted summaries. Each failure was visible in renders, sections,
slicer previews with supports on, or a dimension check. Acceptance now means: inspect the
artefacts, re-run a check, and run that check's must-fail fixture first
([verification.md](verification.md#6-accepting-delegated-work-director--executor)).
