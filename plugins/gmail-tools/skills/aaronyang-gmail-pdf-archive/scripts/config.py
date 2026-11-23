"""Read <home>/targets.toml: which PDFs to download and which password key each uses."""

import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_NAME = "targets.toml"


@dataclass(frozen=True)
class Target:
    name: str
    sender: str
    subject: str = ""
    passwords: tuple[str, ...] = ()

    @property
    def password_envs(self) -> list[str]:
        return [f"PDF_PASSWORD_{key.upper()}" for key in self.passwords]


def load_targets(home: Path) -> dict[str, Target]:
    config = home / CONFIG_NAME
    if not config.exists():
        sys.exit(f"Missing {config}; copy assets/targets.example.toml there and edit it")
    with config.open("rb") as f:
        entries = tomllib.load(f).get("targets", [])
    if not entries:
        sys.exit(f"{config} has no [[targets]]")

    targets: dict[str, Target] = {}
    for entry in entries:
        name = entry.get("name", "")
        sender = entry.get("from", "")
        password = entry.get("password", [])
        passwords = tuple([password] if isinstance(password, str) else password)
        # File names use _ as the separator, so a target name cannot contain it.
        if not name or re.search(r'[_\\/:*?"<>|\s]', name):
            sys.exit(f"Invalid target name {name!r}: no spaces, underscores or characters invalid in file names")
        if name in targets:
            sys.exit(f"Duplicate target name: {name}")
        if not sender:
            sys.exit(f"Target {name} has no from")
        if not all(re.fullmatch(r"[A-Za-z0-9_]+", key) for key in passwords):
            sys.exit(f"Target {name}: password keys may contain only letters, digits and _")
        targets[name] = Target(name, sender, entry.get("subject", ""), passwords)
    return targets


def target_statuses(home: Path) -> dict[str, str]:
    """Name -> "active" for [[targets]] entries, "retired" for entries commented out (# name = "...")."""
    text = (home / CONFIG_NAME).read_text(encoding="utf-8")
    active = {entry.get("name", "") for entry in tomllib.loads(text).get("targets", [])} - {""}
    retired = set(re.findall(r'^#\s*name\s*=\s*"([^"]+)"', text, re.M)) - active
    return {name: "active" for name in active} | {name: "retired" for name in retired}


def write_targets_csv(home: Path, path: Path) -> bool:
    """Write name,status for every target so other tools need not read targets.toml.

    The file is rewritten only when its content changes; returns whether it did.
    """
    statuses = target_statuses(home)
    text = "name,status\n" + "".join(f"{name},{statuses[name]}\n" for name in sorted(statuses))
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".csv.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)
    return True
