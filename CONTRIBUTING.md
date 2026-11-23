# Contributing

Contributions are welcome: corrected or better-sourced numbers, coupon results from real
printers, new must-fail fixtures, slicer compatibility reports and documentation fixes.

## Getting started

1. Fork the repository and create a feature branch from `main`.
2. Make your change. See [`AGENTS.md`](AGENTS.md) for what to keep in sync.
3. Run the checks below; both must pass.
4. Add a [`CHANGELOG.md`](CHANGELOG.md) entry and bump the version in both manifests.
5. Open a pull request explaining the change and its evidence.

## Guidelines

- **Every number needs a source and a confidence.** Add it to
  [`sources.md`](skills/fdm-design/references/sources.md) with a key, and tag it where it is
  used: primary, secondary or unverified. Coupon results are welcome: say printer, nozzle,
  material, profile and how you measured.
- **Licences.** Ideas from other projects are fine with credit. Copy text or code only from
  MIT / MIT-0 / similarly permissive sources, with attribution. Never copy from PolyForm,
  FSL, GPL or unlicensed repositories.
- **Every check can fail.** A new or changed check ships with a fixture that must fail it.
- **Keep `SKILL.md` under 200 lines.** Detail goes into `references/`.
- **No personal data or local paths** in any file (`validate.py` checks paths).
- **Bilingual READMEs.** `README.md` and `README.zh.md` keep the same heading structure.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`,
`refactor:`, `test:`, `chore:`.

## Local validation

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python scripts/validate.py
.venv/bin/python -m pytest -q tests
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
