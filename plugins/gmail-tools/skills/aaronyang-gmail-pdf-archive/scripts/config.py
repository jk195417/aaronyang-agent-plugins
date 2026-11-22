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
