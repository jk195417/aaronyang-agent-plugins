---
name: aaronyang-gmail-filters
description: Manage Gmail filters as code — export existing filters to filters.toml, design new rules, preview and lint the diff, apply it with backfill to existing mail, and audit recent mail for over-archiving. Use when the user wants new Gmail filters or labels, wants to change or clean up filters, asks which senders need rules, or suspects mail is being archived wrongly.
license: Apache-2.0
compatibility: Needs uv and a Google Cloud OAuth client (Desktop app) with the Gmail API enabled.
---

# Gmail filters as code

`<home>/filters.toml` is the source of truth; Gmail is changed only through `scripts/gmail_filters.py` (run with `uv run`). Home-folder lookup, `--home "${user_config.home}"` and the `HOME_NOT_READY` (exit code 3) handling are the same as in the gmail-pdf-archive skill: ask the user before creating or choosing a home.

The first run asks the user to authorize `gmail.settings.basic` and `gmail.modify` in the browser; the token goes to `token_filters.json`, separate from the read-only archive token.

## Workflow

1. No `filters.toml` yet: `export` writes the current Gmail filters there (and a JSON backup). Then `plan` must show nothing to create and nothing missing; if it does, stop and report.
2. Design changes with the user, following [references/design.md](references/design.md). Look at real mail first: exact sender addresses and the subjects each one sends.
3. Edit `filters.toml` (format in [references/format.md](references/format.md)). Change only the rules involved.
4. `plan --count`: show the user every filter to create and its existing match count. A Chinese subject term with 0 matches usually means Gmail tokenizes it differently; search Gmail for a shorter term.
5. Only after the user approves that plan: `apply --yes`. New filters are applied to existing mail too (`--no-backfill` to skip; trash rules need `--backfill-trash`). Deleting Gmail filters missing from `filters.toml` needs `--prune` and the user's explicit approval of that list.
6. `audit --days 1` (wider after big changes): mail outside the inbox without a user label means a filter is archiving too much. Report each one.

Lint errors block `apply`; never work around them by editing Gmail directly. Backups are in `<home>/backups/`.

## One-off cleanup

Archiving or relabeling old mail without a lasting rule is not a filter: use the Gmail connector or UI, and list what will change before doing it.
