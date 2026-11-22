# /// script
# requires-python = ">=3.12"
# dependencies = ["google-api-python-client", "google-auth-oauthlib"]
# ///
"""Download PDF attachments from the senders in targets.toml into <home>/data/encrypted/YYYY-MM.

Read-only Gmail access (gmail.readonly, token.json). --month is the data month:
2026-09 fetches emails received in October 2026.

  uv run download_pdfs.py --month 2026-09 --dry-run   # list what would be downloaded
  uv run download_pdfs.py --month 2026-09             # download; existing files are skipped
"""

import argparse
import base64
import re
import sys
from datetime import datetime

from config import load_targets
from gmail_home import gmail_service, require_home
from manifest import Manifest, sha256

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def month_window(month: str) -> tuple[str, str]:
    year, mon = map(int, month.split("-"))
    start = (year + 1, 1) if mon == 12 else (year, mon + 1)
    end = (start[0] + 1, 1) if start[1] == 12 else (start[0], start[1] + 1)
    return f"{start[0]}/{start[1]:02d}/01", f"{end[0]}/{end[1]:02d}/01"


def list_message_ids(service, query: str) -> list[str]:
    ids, token = [], None
    while True:
        resp = service.users().messages().list(userId="me", q=query, pageToken=token).execute(num_retries=8)
        ids += [m["id"] for m in resp.get("messages", [])]
        token = resp.get("nextPageToken")
        if not token:
            return ids


def walk_parts(part: dict):
    yield part
    for child in part.get("parts", []):
        yield from walk_parts(child)


def attachment_bytes(service, message_id: str, part: dict) -> bytes:
    body = part["body"]
    data = body.get("data")
    if not data:
        data = service.users().messages().attachments().get(
            userId="me", messageId=message_id, id=body["attachmentId"]
        ).execute(num_retries=8)["data"]
    return base64.urlsafe_b64decode(data)


def header(msg: dict, name: str) -> str:
    for h in msg["payload"].get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def safe_name(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\r\n]', "_", name).strip()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Download PDFs listed in targets.toml from Gmail")
    parser.add_argument("--month", required=True, help="data month, YYYY-MM")
    parser.add_argument("--home", help="gmail-tools home folder")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", args.month):
        parser.error("--month must be YYYY-MM")

    home = require_home(args.home, ["credentials.json", "targets.toml"])
    targets = load_targets(home)
    service = gmail_service(home, SCOPES, "token.json")
    after, before = month_window(args.month)
    inbox = home / "data" / "encrypted" / args.month
    inbox.mkdir(parents=True, exist_ok=True)
    archive = home / "data" / "decrypted" / args.month
    manifest = Manifest(home / "data" / "manifest.csv")
    saved = skipped = 0

    for target in targets.values():
        query = f"from:{target.sender} after:{after} before:{before} filename:pdf"
        if target.subject:
            query += f' subject:"{target.subject}"'
        ids = list_message_ids(service, query)
        print(f"[{target.name}] {len(ids)} emails")
        for message_id in ids:
            msg = service.users().messages().get(userId="me", id=message_id, format="full").execute(num_retries=8)
            received = datetime.fromtimestamp(int(msg["internalDate"]) / 1000)
            date = received.strftime("%Y-%m-%d")
            for part in walk_parts(msg["payload"]):
                filename = part.get("filename") or ""
                if not filename.lower().endswith(".pdf"):
                    continue
                name = safe_name(f"{date}_{target.name}_{message_id[:8]}_{filename}")
                exists = (inbox / name).exists() or (archive / name).exists()
                if args.dry_run:
                    print(f"  {'skip (exists)' if exists else 'would download'} {name}")
                    continue
                if exists:
                    skipped += 1
                    print(f"  skip (exists) {name}")
                    downloaded_at = None
                else:
                    (inbox / name).write_bytes(attachment_bytes(service, message_id, part))
                    saved += 1
                    print(f"  downloaded {name}")
                    downloaded_at = datetime.now().isoformat(timespec="seconds")
                original = inbox / name
                manifest.update(
                    name,
                    month=args.month,
                    target=target.name,
                    received_at=received.isoformat(timespec="seconds"),
                    message_id=message_id,
                    sender=header(msg, "From"),
                    subject=header(msg, "Subject"),
                    attachment=filename,
                    size=original.stat().st_size if original.exists() else None,
                    sha256=sha256(original) if original.exists() and not manifest.get(name).get("sha256") else None,
                    downloaded_at=downloaded_at,
                )
        manifest.save()  # save per target so an interruption loses little

    manifest.save()
    print(f"downloaded {saved}, skipped {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
