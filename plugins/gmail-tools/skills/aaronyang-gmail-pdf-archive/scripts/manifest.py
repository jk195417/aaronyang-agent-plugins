"""<home>/data/manifest.csv: one row per downloaded attachment, the source of truth for the archive.

Download fills in the email details; decrypt adds the encryption state and export path.
Rows are keyed by the saved file name, so reruns only fill in missing fields.
"""

import csv
import hashlib
import os
from pathlib import Path

FIELDS = [
    "file",           # saved name: DATE_TARGET_MESSAGEID8_ORIGINALNAME
    "month",          # data month YYYY-MM (the month before the email arrived)
    "target",         # name in targets.toml
    "received_at",    # local time the email arrived
    "message_id",     # full Gmail message ID
    "sender",
    "subject",
    "attachment",     # original attachment name
    "size",           # downloaded size in bytes
    "sha256",         # SHA-256 of the downloaded (possibly encrypted) file
    "downloaded_at",
    "encrypted",      # whether the original needed a password: yes / no
    "decrypted_sha256",
    "decrypted_at",
    "exported_to",    # export path, empty when not exported
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Manifest:
    def __init__(self, path: Path):
        self.path = path
        self.rows: dict[str, dict[str, str]] = {}
        if path.exists():
            with path.open(encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    self.rows[row["file"]] = {k: row.get(k, "") or "" for k in FIELDS}
        self.changed = False

    def get(self, file: str) -> dict[str, str]:
        return self.rows.get(file, {})

    def update(self, file: str, **values) -> None:
        """Fill in or update fields; None or empty values never overwrite existing ones."""
        row = self.rows.setdefault(file, {k: "" for k in FIELDS} | {"file": file})
        for key, value in values.items():
            if key not in FIELDS:
                raise KeyError(key)
            if value in (None, ""):
                continue
            value = str(value)
            if row[key] != value:
                row[key] = value
                self.changed = True

    def save(self) -> None:
        if not self.changed:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".csv.tmp")
        with tmp.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, FIELDS)
            writer.writeheader()
            for file in sorted(self.rows, key=lambda k: (self.rows[k]["month"], k)):
                writer.writerow(self.rows[file])
        os.replace(tmp, self.path)
        self.changed = False
