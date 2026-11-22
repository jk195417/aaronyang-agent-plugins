---
name: aaronyang-ms-atwork-download
description: Download every document from Morgan Stanley at Work (stock plan statements, trade and release confirmations, tax forms such as 1042-S, plan documents, RSU/ESPP reports, grant details) into a local folder with a manifest. Use when the user needs their equity compensation documents from Morgan Stanley at Work, wants new statements or confirmations after a vest or ESPP purchase, or needs cost-basis reports for taxes.
license: Apache-2.0
compatibility: Windows with Microsoft Edge and uv. The user signs in by hand (with MFA) in a dedicated Edge window.
---

# Morgan Stanley at Work download

Scripts are in `scripts/`; run with `uv run <script>`.

## Home folder

Personal settings live in a home folder, never in the plugin: `.env` (`MS_OUTPUT_DIR`, the folder that receives the documents) and `reports.toml` (report IDs from the site's Reports page).

- Pass `--home "${user_config.home}"` when that value is a real path; otherwise omit it. Scripts then use `$MS_ATWORK_HOME`, then `~/.config/ms-atwork`.
- Exit code 3 with `HOME_NOT_READY` means no usable home. Ask the user where it should go and whether to import an old `ms-atwork-downloader` checkout, then run `uv run scripts/config.py init [--home PATH] [--from-legacy PATH]` (it copies, never moves). Never choose a home folder without asking.

## Run

1. `uv run scripts/download.py` (or `--stage docs,tax,plan,reports,grants` for some stages; `--refresh-grants` after vesting status changes).
2. A dedicated Edge window opens with its own profile. Tell the user to sign in there; never ask for, read or store credentials. The script waits for the sign-in.
3. Report the summary it prints (new, skipped, duplicates, failures). On an expired session, ask the user to sign in again and rerun; finished items are skipped.
4. Ask the user to close the Edge window afterwards: it keeps a debugging port open on 127.0.0.1.

Output: documents in category folders under `MS_OUTPUT_DIR`, `manifest.csv` (rebuilt each run) and `.download_state.json` (what is done). Reports are keyed by the day they were run, so a later run adds a new copy.

Site behavior and known pitfalls, for fixing the script when the site changes: [references/site-notes.md](references/site-notes.md).
