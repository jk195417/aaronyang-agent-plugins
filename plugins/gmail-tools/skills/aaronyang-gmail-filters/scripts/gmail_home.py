# /// script
# requires-python = ">=3.12"
# dependencies = ["google-api-python-client", "google-auth-oauthlib"]
# ///
"""Locate the gmail-tools home folder and build Gmail API clients.

The home folder holds everything personal: credentials.json, tokens, .env,
targets.toml, filters.toml and the data/ folder. Code never lives there and
the folder is never part of the plugin.

Lookup order: --home, then $GMAIL_TOOLS_HOME, then ~/.config/gmail-tools.
A missing or unprepared home is never created silently: scripts exit with
code 3 and a HOME_NOT_READY message so the agent can ask the user first.

  uv run gmail_home.py where [--home PATH]
  uv run gmail_home.py init [--home PATH] [--from-legacy PATH]

Note: this file is copied into every gmail-tools skill; keep the copies identical.
"""

import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path

DEFAULT_HOME = Path.home() / ".config" / "gmail-tools"
ENV_VAR = "GMAIL_TOOLS_HOME"
NOT_READY_EXIT = 3
# What `init --from-legacy` copies from an old gmail-pdf-archiver checkout.
LEGACY_FILES = ["credentials.json", "token.json", ".env", "targets.toml"]


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


def require_home(cli_home: str | None, needed: list[str]) -> Path:
    """Return the home folder, or exit with HOME_NOT_READY if it lacks a needed file."""
    home, source = resolve_home(cli_home)
    missing = [name for name in needed if not (home / name).exists()]
    if missing:
        print(
            f"HOME_NOT_READY: gmail-tools home {home} (from {source}) is missing: {', '.join(missing)}.\n"
            "Ask the user where the home folder should be (default ~/.config/gmail-tools) and whether to "
            "import an old gmail-pdf-archiver folder, then run gmail_home.py init.",
            file=sys.stderr,
        )
        raise SystemExit(NOT_READY_EXIT)
    return home


def gmail_service(home: Path, scopes: list[str], token_name: str):
    """Gmail API client; each tool keeps its own token so scopes stay separate."""
    from google.auth.exceptions import RefreshError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    client_file = home / "credentials.json"
    token_file = home / token_name
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            creds = None
    if not creds or not creds.valid:
        if not client_file.exists():
            sys.exit(f"Missing {client_file}; see references/setup.md")
        creds = InstalledAppFlow.from_client_secrets_file(client_file, scopes).run_local_server(port=0)
    token_file.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def init(home: Path, legacy: Path | None) -> int:
    home.mkdir(parents=True, exist_ok=True)
    (home / "data").mkdir(exist_ok=True)
    print(f"home: {home}")
    if not legacy:
        print("Created. Next: put credentials.json here and create targets.toml / filters.toml (see references/setup.md).")
        return 0
    # Copy, never move: the old folder stays untouched until the user retires it.
    copied = skipped = 0
    for name in LEGACY_FILES:
        src, dst = legacy / name, home / name
        if not src.exists():
            continue
        if dst.exists():
            skipped += 1
            print(f"kept existing {name}")
            continue
        shutil.copy2(src, dst)
        copied += 1
    legacy_data = legacy / "tmp"
    for src in sorted(p for p in legacy_data.rglob("*") if p.is_file()) if legacy_data.exists() else []:
        rel = src.relative_to(legacy_data)
        if rel.parts[0] not in ("encrypted", "decrypted") and rel.name != "manifest.csv":
            continue
        dst = home / "data" / rel
        if dst.exists():
            if _digest(dst) != _digest(src):
                print(f"CONFLICT (left as is): {rel}")
            skipped += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if _digest(dst) != _digest(src):
            print(f"COPY MISMATCH: {rel}")
            return 1
        copied += 1
    print(f"copied {copied} files, skipped {skipped}; the legacy folder was not changed")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="gmail-tools home folder")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("where", "init"):
        p = sub.add_parser(name)
        p.add_argument("--home")
    sub.choices["init"].add_argument("--from-legacy", type=Path, help="old gmail-pdf-archiver checkout to copy from")
    args = parser.parse_args()
    home, source = resolve_home(args.home)
    if args.cmd == "where":
        print(f"{home} (from {source}; exists={home.exists()})")
        return 0
    return init(home, args.from_legacy)


if __name__ == "__main__":
    raise SystemExit(main())
