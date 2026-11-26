# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-11-26

### Added
- Second skill `skills/fdm-part-review/SKILL.md`: an acceptance pipeline for parts that
  already exist (exported meshes, sliced plates, renders, delegated CAD work). Machine checks
  first, each preceded by its must-fail fixture; three specialist review lanes in parallel
  (or three separate passes without the agents); a merged verdict that restates every claim
  at its verified level and treats any unapproved deviation from the brief as a BLOCK.
- Four specialist subagents in `agents/`: `fdm-printability-reviewer`,
  `fdm-structural-engineer` and `fdm-integration-engineer` (read-only review lanes returning
  findings with cited evidence and a "Not checked" list) and `fdm-verification-runner` (runs
  the four scripts, negative fixture first, and reports raw output and exit codes).
- `skills/fdm-design/SKILL.md`: a "Specialist lanes" table mapping each agent to its workflow
  steps; the lane that authored geometry never approves it.
- `scripts/validate.py`: checks both skills (line budget, frontmatter, named files including
  `../fdm-design/` paths), agent frontmatter (name matches filename, description present) and
  every `${CLAUDE_PLUGIN_ROOT}/` path an agent names; `agents/` is part of the shipped set.

## [0.1.2] - 2026-11-24

### Changed
- dfam-rules: never model faces exactly at the support threshold; keep roofs ≤ 40° from
  vertical (observed: 45° roofs at a 45° threshold were supported).
- structure: engagement criteria differ for nuts vs inserts; bed-face hex nut pockets with a
  sacrificial layer as the preferred replaceable mount.

## [0.1.1] - 2026-11-23

### Changed

- Confirmed the G-code feature names (Support, Support interface, Support transition,
  Overhang wall, Bridge) against real sliced output from Bambu Studio 02.09.01.70
  (A1, 0.20 Standard, supports on); the parser correctly failed two plates that need supports.
- `slice_support_check.py` also looks in default install locations (Windows, WSL, macOS).
- Hard rule 5 now requires reproducing every mounting point of kept reference parts, checked
  with an overlaid hole map.

## [0.1.0] - 2026-11-23

First version. Supersedes a 27-line single-file enclosure skill; its good parts are kept
(orientation first, walls as line-width multiples, 45° chamfers, teardrops, the 0.25 / 0.35 /
0.45 mm fit coupon ladder, insert bore verification, assembly-order check, stating whether a
result is CAD-verified, sliced or printed).

### Added
- `skills/fdm-design/SKILL.md`: fixed conventions (angles from vertical, per-side clearances,
  tagged dimensions, claim levels), six hard rules from a real retrofit's failure modes,
  verification rules for delegated work, a ten-step workflow.
- Nine reference files: `dfam-rules`, `fits-and-inserts`, `structure`, `connectors`,
  `cable-routing`, `shell-joints`, `verification`, `sources` (every URL with licence and
  confidence) and an anonymised `case-study`.
- Scripts: `overhang_audit.py` (numpy only; slopes, bridges with estimated span, cantilevers,
  floating ceilings; JSON output), `slice_support_check.py` (forces supports on, parses
  `; FEATURE:` / `;TYPE:` G-code, refuses to pass when supports were off), `mesh_check.py`,
  `interference_check.py` (exact with manifold3d, otherwise inconclusive).
- Tests with must-fail fixtures for every script; `scripts/validate.py` repository checks
  (frontmatter, file set, links, versions, README parity, no absolute local paths); CI.

### Known gaps
- Unverified: HDMI overmould
  sizes, SATA bend radius and stock lengths, conflicting M4 to M6 insert bores, material
  shrinkage. The slicer CLI path was not run against a real slicer.

[0.2.0]: https://github.com/baizhiyuan/fdm-design-skill/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/baizhiyuan/fdm-design-skill/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/baizhiyuan/fdm-design-skill/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/baizhiyuan/fdm-design-skill/releases/tag/v0.1.0
