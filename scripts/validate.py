#!/usr/bin/env python3
"""Repository consistency checks (run locally or in CI).

Checks: the shipped file set, SKILL.md frontmatter and line budget, files that SKILL.md
names under references/ and scripts/ exist, relative links in Markdown resolve, balanced code
fences, valid JSON manifests, version agreement between plugin.json, marketplace.json and the
CHANGELOG, the install line and heading structure of both READMEs, and no absolute local paths
(home directories, WSL mounts, Windows drive paths) anywhere in the repository.

Usage: python3 scripts/validate.py   (exit 1 on any failure)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = "skills/fdm-design"
SKILL = f"{SKILL_DIR}/SKILL.md"
SKILL_MAX_LINES = 200
SHIPPED = {
    SKILL,
    *(f"{SKILL_DIR}/references/{n}.md" for n in (
        "dfam-rules", "fits-and-inserts", "structure", "connectors", "cable-routing",
        "shell-joints", "verification", "sources", "case-study")),
    *(f"{SKILL_DIR}/scripts/{n}.py" for n in (
        "overhang_audit", "slice_support_check", "mesh_check", "interference_check")),
}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".omc", "node_modules"}
TEXT_SUFFIXES = {".md", ".py", ".json", ".yml", ".yaml", ".txt", ".toml", ".cfg", ".sh", ""}
# Patterns are written so that this file does not match itself.
ALLOW_MARKER = "# validate: allow-install-path"

LOCAL_PATH_PATTERNS = [
    (re.compile(r"/h[o]me/[A-Za-z0-9_.-]+"), "home directory path"),
    (re.compile(r"/U[s]ers/[A-Za-z0-9_.-]+"), "macOS home path"),
    (re.compile(r"/m[n]t/[a-z]/"), "WSL drive mount"),
    (re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:\\\\?[A-Za-z_]"), "Windows drive path"),
]
errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def read(rel: str, root: Path = ROOT) -> str:
    return (root / rel).read_text(encoding="utf-8")


def repo_files(root: Path = ROOT):
    for path in sorted(root.rglob("*")):
        if path.is_file() and not (set(path.relative_to(root).parts) & SKIP_DIRS):
            yield path


def check_file_set() -> None:
    present = {str(p.relative_to(ROOT)) for p in (ROOT / "skills").rglob("*")
               if p.is_file() and "__pycache__" not in p.parts}
    for rel in sorted(SHIPPED - present):
        fail(f"{rel}: missing")
    for rel in sorted(present - SHIPPED):
        fail(f"{rel}: not in the shipped file set (update SHIPPED in scripts/validate.py if intended)")


def check_skill() -> None:
    text = read(SKILL)
    lines = text.count("\n") + 1
    if lines >= SKILL_MAX_LINES:
        fail(f"{SKILL}: {lines} lines, must stay under {SKILL_MAX_LINES}")
    parts = text.split("---", 2)
    if not text.startswith("---") or len(parts) < 3:
        fail(f"{SKILL}: no YAML frontmatter")
        return
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        fail(f"{SKILL}: frontmatter does not parse ({exc})")
        return
    if not isinstance(meta, dict) or not meta.get("description"):
        fail(f"{SKILL}: frontmatter needs a description")
    elif meta.get("name") != Path(SKILL_DIR).name:
        fail(f"{SKILL}: frontmatter name {meta.get('name')!r} != directory {Path(SKILL_DIR).name!r}")
    for ref in sorted(set(re.findall(r"(?:references|scripts)/[\w.-]+\.(?:md|py)", text))):
        if not (ROOT / SKILL_DIR / ref).exists():
            fail(f"{SKILL}: names {ref}, which does not exist")


def strip_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def check_markdown() -> None:
    for path in repo_files():
        if path.suffix != ".md":
            continue
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        if text.count("```") % 2:
            fail(f"{rel}: unbalanced code fences")
        for a, b in re.findall(r'(?:src|href)="([^"]+)"|\]\(([^)\s]+)\)', strip_code(text)):
            target = (a or b).strip("<>").split("#", 1)[0]
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target):
                continue
            if not (path.parent / target).exists():
                fail(f"{rel}: broken relative link {target}")


def check_json() -> None:
    for rel in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
        try:
            json.loads(read(rel))
        except Exception as exc:  # noqa: BLE001 - report any parse failure
            fail(f"{rel}: invalid JSON ({exc})")


def check_versions() -> None:
    try:
        plugin = json.loads(read(".claude-plugin/plugin.json"))
        market = json.loads(read(".claude-plugin/marketplace.json"))
    except Exception:  # noqa: BLE001 - already reported by check_json
        return
    version = plugin.get("version")
    if plugin.get("name") != Path(SKILL_DIR).name:
        fail(f".claude-plugin/plugin.json: name {plugin.get('name')!r} != skill {Path(SKILL_DIR).name!r}")
    for entry in market.get("plugins", []):
        if entry.get("version") != version:
            fail(f".claude-plugin/marketplace.json: version {entry.get('version')} != plugin.json {version}")
        if entry.get("name") != plugin.get("name"):
            fail(f".claude-plugin/marketplace.json: plugin name {entry.get('name')!r} != {plugin.get('name')!r}")
    changelog = read("CHANGELOG.md")
    top = re.search(r"^## \[([0-9][^\]]*)\]", changelog, re.M)
    if not top or top.group(1) != version:
        fail(f"CHANGELOG.md: newest entry {top.group(1) if top else 'missing'} != plugin.json {version}")
    if f"[{version}]: " not in changelog:
        fail(f"CHANGELOG.md: no link reference for [{version}]")
    install = f"/plugin install {plugin.get('name')}@{market.get('name')}"
    for rel in ("README.md", "README.zh.md"):
        text = read(rel)
        if install not in text:
            fail(f"{rel}: no '{install}' line")
        badge = re.search(r"badge/version-([0-9.]+)-", text)
        if not badge or badge.group(1) != version:
            fail(f"{rel}: version badge {badge.group(1) if badge else 'missing'} != {version}")


def check_readme_pair() -> None:
    def levels(t: str) -> list[str]:
        return re.findall(r"^(#{2,3}) ", re.sub(r"```.*?```", "", t, flags=re.S), re.M)
    if levels(read("README.md")) != levels(read("README.zh.md")):
        fail("README.md and README.zh.md heading structure differs")


def local_path_findings(root: Path = ROOT) -> list[str]:
    found = []
    for path in repo_files(root):
        if path.suffix not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            # Vendor default install locations may be listed when marked explicitly.
            if line.rstrip().endswith(ALLOW_MARKER):
                continue
            for pattern, what in LOCAL_PATH_PATTERNS:
                if pattern.search(line):
                    found.append(f"{path.relative_to(root)}:{n}: {what}: {line.strip()[:80]}")
                    break
    return found


def check_local_paths() -> None:
    for item in local_path_findings():
        fail(item)


def main() -> int:
    for check in (check_file_set, check_skill, check_markdown, check_json, check_versions,
                  check_readme_pair, check_local_paths):
        check()
    if errors:
        print("\n".join(f"FAIL {e}" for e in errors))
        print(f"\n{len(errors)} problem(s)")
        return 1
    print("validate: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
