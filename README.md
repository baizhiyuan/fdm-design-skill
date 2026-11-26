<p align="center">
  <img src="https://img.shields.io/badge/Claude_Code-Plugin-D97757?style=for-the-badge&labelColor=F0EEE6" alt="Claude Code plugin">
  <img src="https://img.shields.io/badge/version-0.2.0-C15F3C?style=for-the-badge&labelColor=F0EEE6" alt="version 0.2.0">
  <img src="https://img.shields.io/badge/status-pre--release-B8860B?style=for-the-badge&labelColor=F0EEE6" alt="status: pre-release">
  <img src="https://img.shields.io/badge/license-MIT-788C5D?style=for-the-badge&labelColor=F0EEE6" alt="MIT license">
</p>

<p align="center"><strong>Design FDM parts that print the first time and can be repaired the second time.</strong></p>

<p align="center">
  <a href="#what-it-does">What it does</a> ·
  <a href="#the-six-hard-rules">Hard rules</a> ·
  <a href="#the-checks">Checks</a> ·
  <a href="#the-agents">Agents</a> ·
  <a href="#install">Install</a> ·
  <a href="#limits">Limits</a> ·
  <a href="README.zh.md">中文</a>
</p>

---

`fdm-design` is a Claude Code skill for designing, revising and reviewing parts printed on
FDM/FFF printers, with a focus on electronics enclosures, mounts and multi-part shells. It is
CAD-agnostic (SolidWorks, Fusion, Onshape, FreeCAD, OpenSCAD, CadQuery, build123d). Examples
assume a Bambu Lab A1/X1 with a 0.4 mm nozzle and PETG or PLA; the rules take the printer,
nozzle and material as parameters.

## What it does

- A short [`SKILL.md`](skills/fdm-design/SKILL.md) (under 200 lines): fixed conventions, six
  hard rules, a ten-step workflow and pointers.
- Nine reference files with the numbers, each tagged with its source and confidence
  (primary, secondary or unverified): DfAM rules, fits and heat-set inserts, structure,
  connectors, cable routing, shell joints, verification, sources and an anonymised case study.
- Four Python checks that the assistant (or you) can run on exported meshes and G-code.
- A second skill, [`fdm-part-review`](skills/fdm-part-review/SKILL.md), for accepting parts
  that already exist (exported meshes, sliced plates, renders, delegated CAD work): machine
  checks with negative fixtures first, three review lanes, a verdict that restates every
  claim at its verified level.
- Four specialist subagents (plugin install only): printability, structural and integration
  reviewers, and a verification runner.

Conventions the skill enforces: angles are measured **from vertical** (slicers measure their
support threshold from horizontal, and the skill converts); clearances are **per side**; every
dimension is tagged measured / datasheet / reference / placeholder; every claim is tagged
CAD-verified / sliced / printed.

## The six hard rules

Each comes from a failure that happened in a real retrofit
([case study](skills/fdm-design/references/case-study.md)).

| # | Failure | Rule |
|---|---|---|
| 1 | "Zero supports", from a slice with supports disabled | A support-free claim needs a slice with supports **enabled** at the stated threshold AND an independent geometric audit; bridges listed with spans |
| 2 | Tall printed bosses with blind inserts: one crack scraps the shell | Failure-consequence analysis per load path; replaceable metal standoffs or through-bolts from outside; printed bosses locate or carry light loads |
| 3 | Connector openings cut from the receptacle | Openings from the plug overmould + per-side clearance, engagement depth, lead-in, finger and latch access; measure real cables |
| 4 | Cable lengths nobody sells, cables over modules | Route corridors first from stock lengths and bend radii; no routes over heat sources; both ends reachable |
| 5 | Shell split ignoring the reference joint | Copy the reference lip/tongue; one edge language; every opening within one part; symmetric panels |
| 6 | Silent structural change (the case grew 18 mm) | Outer dimensions, splits, port positions and mounting need explicit approval; every deviation reported |

Plus one rule for delegated work: **a check must be able to fail**, and acceptance inspects the
actual outputs (renders, sections, slicer preview with supports on), not the executor's summary.

## The checks

All in [`skills/fdm-design/scripts/`](skills/fdm-design/scripts/). Python 3.10+ and numpy;
trimesh and manifold3d are optional. Exit codes: 0 pass, 1 fail, 2 inconclusive or error.

| Script | Checks |
|---|---|
| `overhang_audit.py` | Downward faces beyond the overhang limit off the bed; horizontal ceilings classified as bridge (with estimated span), cantilever (ledges, counterbore rings) or floating; text or JSON |
| `slice_support_check.py` | Slices with Bambu Studio / OrcaSlicer after forcing supports on at the threshold, or parses your exported G-code / 3MF; refuses to pass when supports were off or the threshold differs |
| `mesh_check.py` | Watertight, winding, outward normals, body count, build volume |
| `interference_check.py` | Pairwise intersection volume (exact with manifold3d, otherwise reported as inconclusive), with an allow-list for intentional press fits |

```bash
python skills/fdm-design/scripts/overhang_audit.py part.stl --max-overhang 45 --max-bridge 10
python skills/fdm-design/scripts/slice_support_check.py --gcode plate_1.gcode --max-overhang 45
python skills/fdm-design/scripts/mesh_check.py part.stl --printer a1
python skills/fdm-design/scripts/interference_check.py shell.stl board.stl plug.stl
```

The test suite runs every check against fixtures that must fail: a cantilever ledge, a 59°
ramp, a counterbore ring without a sacrificial layer, a floating island, a supports-off
G-code, overlapping boxes, an open mesh.

## The agents

Shipped in [`agents/`](agents/) and used by both skills.

| Agent | Lane | Returns | Tools |
|---|---|---|---|
| `fdm-printability-reviewer` | Orientation, overhangs, bridges, walls, edges, holes, fits | Findings table, bridge list, raw output of the geometric checks it ran | Read, Grep, Glob, Bash |
| `fdm-structural-engineer` | Load paths, failure consequence, fasteners, materials under load | Failure-consequence table per load path, findings table | Read, Grep, Glob |
| `fdm-integration-engineer` | Connector openings, cable corridors, assembly order, shell joints | Findings table, connector and cable table | Read, Grep, Glob |
| `fdm-verification-runner` | Runs the four checks, negative fixture first | Raw stdout and exit code per run, claim levels supported | Bash, Read, Grep, Glob |

The review lanes return findings with a cited reference and confidence and never edit files;
the runner returns raw output, not judgements. Agents install through the plugin route only;
a copied skill falls back to separate passes per lane.

## Install

### As a plugin

Enter these slash commands one at a time:

```
/plugin marketplace add baizhiyuan/fdm-design-skill
```

```
/plugin install fdm-design@fdm-design-skill
```

### By copying the skill

```bash
git clone https://github.com/baizhiyuan/fdm-design-skill.git
mkdir -p ~/.claude/skills
cp -r fdm-design-skill/skills/fdm-design fdm-design-skill/skills/fdm-part-review ~/.claude/skills/
python3 -m pip install numpy            # optional: trimesh manifold3d
```

Copy both directories: `fdm-part-review` reads its references and scripts through relative
`../fdm-design/` paths. The subagents are not installed this way.

The skill loads when a request is about FDM-printed parts. To check what is installed:
`ls ~/.claude/skills/fdm-design` or `/plugin` in Claude Code.

## Limits

- Not for resin, CNC or injection moulding.
- Numbers marked unverified in [`sources.md`](skills/fdm-design/references/sources.md) are
  open: HDMI overmould sizes, SATA bend radius, literal G-code tag names for support and
  overhang walls, two conflicting heat-set insert tables for M4 to M6, material shrinkage.
- The slicer CLI invocation follows the vendors' documentation and has not been exercised in
  CI (no slicer there); G-code parsing is tested on synthetic files.
- The overhang audit estimates bridge spans from sampled points; it does not predict sag,
  curl or cooling quality. Print a coupon.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python scripts/validate.py
.venv/bin/python -m pytest -q tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md).

## License & Acknowledgements

Released under the [MIT License](LICENSE).

Ideas adapted, with thanks, from these MIT / MIT-0 projects (no text or code copied
verbatim; details in [`sources.md`](skills/fdm-design/references/sources.md)):

- [alexlenk/3d-printing](https://github.com/alexlenk/3d-printing): approval for every
  deviation, a negative test for every check, printed connector numbers.
- [gjaloyan/print3d-designer](https://github.com/gjaloyan/print3d-designer): slicer CLI
  pitfalls, normal-based overhang tiers, PETG overhang and bridge data.
- [KD5RYN/b123d-print](https://github.com/KD5RYN/b123d-print): numbered rules, fit table,
  bridge default, the fix order for overhangs.
- [pthompson8594/openscad-skill](https://github.com/pthompson8594/openscad-skill): self-tests
  with planted defects.
- [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad): separate concerns,
  slicing in the loop.

Design data from Bambu Lab, Prusa Research, Stratasys, USB-IF, TIA, CNC Kitchen, Hubs and
others is cited per number in the reference files.

**Disclaimer.** This is an independent community project. It is not affiliated with, authorised
by, or endorsed by Anthropic, Bambu Lab or any vendor named here.
