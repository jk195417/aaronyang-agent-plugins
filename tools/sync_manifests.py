# /// script
# requires-python = ">=3.12"
# dependencies = ["jsonschema"]
# ///
"""Derive Agent Plugins 1.0 manifests from the Claude Code manifests and check the repo.

Single source of truth: plugins/<name>/.claude-plugin/plugin.json.
Derived:            plugins/<name>/plugin.json (https://agent-plugins.org)

  uv run tools/sync_manifests.py           write derived files, then check
  uv run tools/sync_manifests.py --check   change nothing; exit 1 on any problem (for CI)

Checks: derived manifests are up to date and valid against the Agent Plugins schema,
every plugin is listed in .claude-plugin/marketplace.json with the same description,
and every SKILL.md follows the Agent Skills naming rules (https://agentskills.io/specification).
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
# Keys Agent Plugins 1.0 allows besides $schema; Claude-only keys are dropped.
PORTABLE_KEYS = ["name", "version", "description", "author", "homepage", "repository", "license", "keywords"]
AUTHOR_KEYS = ["name", "email", "url"]
SKILL_NAME = re.compile(r"^(?!.*--)[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")


def dump(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def derive(claude: dict) -> dict:
    out = {"$schema": SCHEMA_URL}
    for key in PORTABLE_KEYS:
        if key not in claude:
            continue
        value = claude[key]
        if key == "author":
            value = {k: value[k] for k in AUTHOR_KEYS if k in value}
        out[key] = value
    return out


def load_schema():
    try:
        with urllib.request.urlopen(SCHEMA_URL, timeout=15) as resp:
            return json.load(resp)
    except OSError as exc:
        print(f"warning: could not fetch schema, skipping schema validation ({exc})")
        return None


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="only check; exit 1 on any problem")
    args = parser.parse_args()

    problems: list[str] = []
    schema = load_schema()
    validator = None
    if schema:
        from jsonschema import Draft202012Validator
        validator = Draft202012Validator(schema)

    market = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    listed = {p["name"]: p for p in market.get("plugins", [])}

    for plugin_dir in sorted(p for p in PLUGINS.iterdir() if p.is_dir()):
        source = plugin_dir / ".claude-plugin" / "plugin.json"
        if not source.exists():
            problems.append(f"{plugin_dir.name}: missing .claude-plugin/plugin.json")
            continue
        claude = json.loads(source.read_text(encoding="utf-8"))
        name = claude.get("name")
        if name != plugin_dir.name:
            problems.append(f"{plugin_dir.name}: plugin name {name!r} does not match its folder")

        derived = derive(claude)
        target = plugin_dir / "plugin.json"
        current = target.read_text(encoding="utf-8") if target.exists() else None
        if current != dump(derived):
            if args.check:
                problems.append(f"{name}: plugin.json is out of date; run without --check")
            else:
                target.write_text(dump(derived), encoding="utf-8", newline="\n")
                print(f"wrote {target.relative_to(ROOT)}")
        if validator:
            for err in validator.iter_errors(derived):
                problems.append(f"{name}: plugin.json schema: {err.message}")

        entry = listed.pop(name, None)
        if entry is None:
            problems.append(f"{name}: not listed in marketplace.json")
        elif entry.get("description") != claude.get("description"):
            problems.append(f"{name}: marketplace.json description differs from plugin.json")

        for skill_md in sorted(plugin_dir.glob("skills/*/SKILL.md")):
            folder = skill_md.parent.name
            fm = frontmatter(skill_md)
            skill_name = fm.get("name", "")
            if skill_name != folder:
                problems.append(f"{name}: skill {folder}: name {skill_name!r} must match its folder")
            if not SKILL_NAME.match(skill_name) or len(skill_name) > 64:
                problems.append(f"{name}: skill {folder}: invalid name {skill_name!r}")
            description = fm.get("description", "")
            if not 1 <= len(description) <= 1024:
                problems.append(f"{name}: skill {folder}: description must be 1-1024 characters")

    for stale in listed:
        problems.append(f"{stale}: listed in marketplace.json but has no plugin folder")

    for problem in problems:
        print(f"error: {problem}")
    if not problems:
        print("ok")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
