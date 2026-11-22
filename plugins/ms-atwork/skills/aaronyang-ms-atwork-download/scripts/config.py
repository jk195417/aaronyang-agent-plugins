# /// script
# requires-python = ">=3.12"
# dependencies = ["python-dotenv"]
# ///
"""Locate the ms-atwork home folder and read its .env and reports.toml.

The home folder holds the personal settings: .env (MS_OUTPUT_DIR) and reports.toml.
Lookup order: --home, then $MS_ATWORK_HOME, then ~/.config/ms-atwork. A missing or
unprepared home is never created silently: scripts exit with code 3 and HOME_NOT_READY
so the agent can ask the user first. `uv run config.py init [--home PATH] [--from-legacy PATH]`
creates it, optionally copying .env and reports.toml from an old ms-atwork-downloader checkout.
"""

import argparse
import os
import shutil
import sys
import tomllib
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_HOME = Path.home() / ".config" / "ms-atwork"
ENV_VAR = "MS_ATWORK_HOME"
NOT_READY_EXIT = 3
NEEDED = [".env", "reports.toml"]
_home: Path | None = None


def _usable(value: str | None) -> bool:
    # An unset Claude Code userConfig value may arrive empty or as a literal placeholder.
    return bool(value) and "${" not in value


def resolve_home(cli_home: str | None = None) -> tuple[Path, str]:
    if _usable(cli_home):
        return Path(cli_home).expanduser(), "--home"
    env = os.environ.get(ENV_VAR)
    if _usable(env):
        return Path(env).expanduser(), ENV_VAR
    return DEFAULT_HOME, "default"


def use_home(cli_home: str | None) -> Path:
    """Select the home folder for this run, or exit with HOME_NOT_READY."""
    global _home
    home, source = resolve_home(cli_home)
    missing = [name for name in NEEDED if not (home / name).exists()]
    if missing:
        print(
            f"HOME_NOT_READY: ms-atwork home {home} (from {source}) is missing: {', '.join(missing)}.\n"
            "Ask the user where the home folder should be (default ~/.config/ms-atwork) and whether to "
            "import an old ms-atwork-downloader folder, then run config.py init.",
            file=sys.stderr,
        )
        raise SystemExit(NOT_READY_EXIT)
    _home = home
    load_dotenv(home / ".env")
    return home


def output_dir() -> Path:
    value = os.environ.get("MS_OUTPUT_DIR", "").strip()
    if not value:
        sys.exit(f"MS_OUTPUT_DIR is not set in {_home / '.env'}")
    return Path(value)


def load_reports() -> list[tuple[str, str]]:
    path = _home / "reports.toml"
    with path.open("rb") as f:
        entries = tomllib.load(f).get("reports", [])
    if not entries:
        sys.exit(f"{path} has no [[reports]]")
    return [(e["name"], str(e["id"])) for e in entries]


def init(home: Path, legacy: Path | None) -> int:
    home.mkdir(parents=True, exist_ok=True)
    print(f"home: {home}")
    for name in NEEDED:
        dst = home / name
        if dst.exists():
            print(f"kept existing {name}")
        elif legacy and (legacy / name).exists():
            shutil.copy2(legacy / name, dst)  # copy, never move
            print(f"copied {name}")
        else:
            print(f"missing {name}: create it from assets/ (env.example, reports.example.toml)")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="ms-atwork home folder")
    ap.add_argument("cmd", choices=["where", "init"])
    ap.add_argument("--home")
    ap.add_argument("--from-legacy", type=Path)
    args = ap.parse_args()
    home, source = resolve_home(args.home)
    if args.cmd == "where":
        print(f"{home} (from {source}; exists={home.exists()})")
        raise SystemExit(0)
    raise SystemExit(init(home, args.from_legacy))
