# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Unverified: literal G-code names of support and overhang-wall features, HDMI overmould
  sizes, SATA bend radius and stock lengths, conflicting M4 to M6 insert bores, material
  shrinkage. The slicer CLI path was not run against a real slicer.

[0.1.0]: https://github.com/baizhiyuan/fdm-design-skill/releases/tag/v0.1.0
