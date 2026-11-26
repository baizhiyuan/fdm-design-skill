# Repository guide for coding agents

This file orients AI coding agents (and human contributors) working **on** this repository.
For what the skills do at runtime, read `skills/fdm-design/SKILL.md` and
`skills/fdm-part-review/SKILL.md`; the subagents are in `agents/`.

| Path | Role | Rule |
|------|------|------|
| `skills/fdm-design/SKILL.md` | The skill | Under 200 lines (CI checks). Hard rules and workflow only; numbers go to `references/` |
| `skills/fdm-design/references/*.md` | Numbers and methods | Every number carries a source key from `sources.md` and a confidence |
| `skills/fdm-part-review/SKILL.md` | Review and acceptance pipeline for existing parts | Under 200 lines (CI checks). No design numbers inline; refer to `../fdm-design/references/` and `../fdm-design/scripts/` with the `../fdm-design/` prefix |
| `agents/*.md` | Specialist subagents shipped with the plugin | Frontmatter `name` matches the filename (CI checks). Review agents are read-only and return findings only; every number cites a reference and its confidence; the runner reports raw output and exit codes only. Name files as `${CLAUDE_PLUGIN_ROOT}/...` in inline code, not Markdown links |
| `skills/fdm-design/scripts/*.py` | Checks shipped with the skill | numpy required, trimesh/manifold3d optional; exit 0 pass, 1 fail, 2 inconclusive; never report "pass" when a check could not run |
| `tests/` | pytest suite | Each check has at least one fixture that must fail |
| `scripts/validate.py` | Repository consistency | File set, frontmatter, links, versions, README parity, no absolute local paths |
| `.claude-plugin/` | Plugin and marketplace manifests | Versions match each other and the newest CHANGELOG entry |

## Invariants

- Angles are measured from vertical everywhere; slicer thresholds are converted, never mixed.
- Clearances are per side.
- The case study stays anonymous: no names, local paths, usernames or private project names.
- Unverified items stay marked as unverified until a first-hand source or a measurement exists.

## After any change

```bash
.venv/bin/python scripts/validate.py
.venv/bin/python -m pytest -q tests
```

Bump `version` in both manifests (SemVer), add a `CHANGELOG.md` entry, and use Conventional
Commits.
