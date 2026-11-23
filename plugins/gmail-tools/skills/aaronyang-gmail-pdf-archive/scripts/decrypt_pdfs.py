# /// script
# requires-python = ">=3.12"
# dependencies = ["pikepdf", "python-dotenv"]
# ///
"""Decrypt <home>/data/encrypted/YYYY-MM into <home>/data/decrypted/YYYY-MM.

Each file uses the password key its target names in targets.toml; the passwords
live in <home>/.env and are never printed.

  uv run decrypt_pdfs.py --month 2026-09
  uv run decrypt_pdfs.py --month 2026-09 --export-path "D:/backup/pdfs"   # also copy to PATH/YYYY-MM,
                                                                         # with manifest.csv and targets.csv in PATH
  uv run decrypt_pdfs.py --month 2026-09 --delete-originals              # delete verified encrypted files
"""

import argparse
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import pikepdf
from dotenv import load_dotenv

from config import Target, load_targets, write_targets_csv
from gmail_home import require_home
from manifest import Manifest, sha256


class PasswordConfigError(Exception):
    pass


def passwords_for(src: Path, targets: dict[str, Target]) -> list[str]:
    # File names are DATE_TARGET_MESSAGEID_ORIGINALNAME.
    parts = src.name.split("_", 2)
    target = targets.get(parts[1]) if len(parts) == 3 else None
    if target is None:
        raise PasswordConfigError("file name matches no target in targets.toml")
    if not target.passwords:
        raise PasswordConfigError(f"target {target.name} has no password key")
    missing = [env for env in target.password_envs if not os.environ.get(env)]
    if missing:
        raise PasswordConfigError(f".env is missing {', '.join(missing)}")
    return [os.environ[env] for env in target.password_envs]


def open_pdf(src: Path, targets: dict[str, Target]) -> pikepdf.Pdf:
    try:
        return pikepdf.open(src)
    except pikepdf.PasswordError:
        pass
    for password in passwords_for(src, targets):
        try:
            return pikepdf.open(src, password=password)
        except pikepdf.PasswordError:
            continue
    raise pikepdf.PasswordError("wrong password")


def decrypt_one(src: Path, dst: Path, targets: dict[str, Target]) -> Path:
    with open_pdf(src, targets) as pdf:
        pdf.save(dst)
    # The output must open without a password and have pages.
    with pikepdf.open(dst) as check:
        if check.is_encrypted or len(check.pages) == 0:
            dst.unlink()
            raise ValueError("output failed verification")
    return dst


def is_encrypted(src: Path) -> bool:
    try:
        with pikepdf.open(src):
            return False
    except pikepdf.PasswordError:
        return True


def record(manifest: Manifest, month: str, src: Path, dst: Path, decrypted_now: bool) -> None:
    """Write the decryption result to the manifest; existing fields are not recomputed."""
    row = manifest.get(dst.name)
    values = {"month": month}
    if not row.get("encrypted") and src.exists():
        try:
            values["encrypted"] = "yes" if is_encrypted(src) else "no"
        except (pikepdf.PdfError, OSError):
            pass
    if decrypted_now or not row.get("decrypted_sha256"):
        values["decrypted_sha256"] = sha256(dst)
    if decrypted_now:
        values["decrypted_at"] = datetime.now().isoformat(timespec="seconds")
    manifest.update(dst.name, **values)


def export_files(out_dir: Path, export_dir: Path) -> int:
    export_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src in sorted(out_dir.glob("*.pdf")):
        dst = export_dir / src.name
        if not dst.exists():
            shutil.copy2(src, dst)
            copied += 1
    return copied


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Decrypt downloaded PDFs")
    parser.add_argument("--month", required=True, help="data month, YYYY-MM")
    parser.add_argument("--home", help="gmail-tools home folder")
    parser.add_argument("--export-path", help="also copy to PATH/YYYY-MM; default EXPORT_PATH in .env")
    parser.add_argument("--delete-originals", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", args.month):
        parser.error("--month must be YYYY-MM")

    home = require_home(args.home, ["targets.toml"])
    load_dotenv(home / ".env")
    export_path = args.export_path or os.environ.get("EXPORT_PATH") or None
    targets = load_targets(home)
    data = home / "data"
    inbox = data / "encrypted" / args.month
    inbox.mkdir(parents=True, exist_ok=True)
    sources = sorted(inbox.glob("*.pdf"))
    out_dir = data / "decrypted" / args.month
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = data / "manifest.csv"
    manifest = Manifest(manifest_path)
    failed = 0
    for src in sources:
        if (out_dir / src.name).exists():
            print(f"skip (exists) {src.name}")
            record(manifest, args.month, src, out_dir / src.name, decrypted_now=False)
            continue
        try:
            dst = decrypt_one(src, out_dir / src.name, targets)
        except PasswordConfigError as e:
            failed += 1
            print(f"failed {src.name}: {e}")
            continue
        except pikepdf.PasswordError:
            failed += 1
            print(f"failed {src.name}: wrong password")
            continue
        except (pikepdf.PdfError, ValueError, OSError) as e:
            failed += 1
            print(f"failed {src.name}: {type(e).__name__}")
            continue
        record(manifest, args.month, src, dst, decrypted_now=True)
        if args.delete_originals:
            src.unlink()
        print(f"done {src.name}")

    print(f"{len(sources)} files, {failed} failed")

    if export_path:
        export_root = Path(export_path)
        export_dir = export_root / args.month
        print(f"exported {export_files(out_dir, export_dir)} to {export_dir}")
        for f in sorted(out_dir.glob("*.pdf")):
            if (export_dir / f.name).exists():
                manifest.update(f.name, month=args.month, exported_to=str(export_dir / f.name))
        manifest.save()
        # Keep a copy of the manifest and the target list next to the export for indexes and other tools.
        if manifest_path.exists():
            shutil.copy2(manifest_path, export_root / "manifest.csv")
        write_targets_csv(home, export_root / "targets.csv")
    manifest.save()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
