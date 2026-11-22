---
name: aaronyang-gmail-pdf-archive
description: Download PDF attachments (bank and card statements, bills, receipts, invoices) from chosen Gmail senders, decrypt password-protected ones, and archive them by month with a manifest. Use when the user wants statements or receipts collected from Gmail, a new sender added to the archive, a month backfilled, or a list of what has been archived.
license: CC-BY-SA-4.0
compatibility: Needs uv and a Google Cloud OAuth client (Desktop app) with the Gmail API enabled.
---

# Gmail PDF archive

Scripts are in `scripts/` next to this file; run each with `uv run <script>` (dependencies are declared inline), never `uv run python`.

## Home folder

Personal files live in one home folder, never in the plugin: `credentials.json`, `token.json`, `.env` (PDF passwords, `EXPORT_PATH`), `targets.toml`, and `data/` (`encrypted/`, `decrypted/`, `manifest.csv`).

- Pass `--home "${user_config.home}"` to every script when that value is a real path; otherwise omit `--home`. Scripts then use `$GMAIL_TOOLS_HOME`, then `~/.config/gmail-tools`.
- A script that exits with code 3 and prints `HOME_NOT_READY` found no usable home. Ask the user where it should go (offer the default) and whether to import an old `gmail-pdf-archiver` checkout, then run `uv run scripts/gmail_home.py init [--home PATH] [--from-legacy PATH]`. It copies and verifies; it never changes the old folder. Never create or pick a home folder without asking.
- Never print or read out `.env`, `token.json` or `credentials.json`. The user types passwords into `.env` themselves.

First-time setup (OAuth client, file formats): [references/setup.md](references/setup.md).

## Monthly run

`--month` is the data month: `2026-09` fetches emails received in October 2026.

1. `uv run scripts/download_pdfs.py --month YYYY-MM --dry-run` and show the user what will be downloaded.
2. `uv run scripts/download_pdfs.py --month YYYY-MM`
3. `uv run scripts/decrypt_pdfs.py --month YYYY-MM` (copies to `EXPORT_PATH/YYYY-MM` when set, with `manifest.csv` beside it).
4. Report downloaded, skipped and failed counts. A wrong or missing password is the user's to fix in `.env`.

Both scripts are idempotent; rerun them to backfill.

## Adding a sender

Find real examples in Gmail first and use the exact sender address, plus a subject phrase when one address sends several kinds of mail. Add a `[[targets]]` entry, run a dry run for a month that should match, and ask the user to add any new password key to `.env`.

## Archive rules

- `manifest.csv` is the source of truth; any index for people is generated from it, never edited by hand.
- Exported files are original evidence: never rename, move or edit them. Classify through the manifest, not by moving files into folders (the next run would export them again).
- Deleting an archived file means removing it from the export, `data/` and the manifest together; ask first.
