---
name: aaronyang-file-archiving
description: File, rename, deduplicate and clean up personal files — a cloud drive, the Downloads folder, scans, receipts, statements — safely and consistently. Use when the user asks to organize or archive files, clear out Downloads, decide where a file belongs, keep yearly records, or build an index of archived documents.
license: Apache-2.0
---

# File archiving

This is the method. The user's own map — which folders exist, the naming format, special places — lives in the instruction file of the folder being organized (AGENTS.md or CLAUDE.md, including parent folders); read it first and let it win where the two differ.

## Structure

Organize by how actionable things are (PARA, Tiago Forte): Projects (dated folders for things with an end), Areas (long-running responsibilities), Resources, Archive (finished or inactive), plus an Inbox for files not yet filed. Put a file where the user will look for it next, not where it came from.

## Filing a batch (Downloads, an inbox folder, a dump of scans)

1. Inventory by name, type, size and dates. Open a file only when its name does not tell what it is.
2. Sort into three groups and show them as a table before changing anything:
   - **Already archived**: a file with the same SHA-256 exists at the destination → remove the source.
   - **Clear destination**: propose the folder and the new name.
   - **Unclear**: ask; never guess at what a file is or whose it is.
3. After approval, move as copy → verify SHA-256 → delete the source to the recycle bin.
4. Report what moved where under which name, what was deleted, and what was left and why.

## Rules

- **Names**: follow the folder's convention. Date a file by the document's own date, not its modified time; say when a date is inferred. Do not batch-rename old files, and never rename files that a program generated or references.
- **Evidence is append-only**: statements, receipts, invoices, tax filings, contracts and confirmations are never edited or renamed. For a password-protected file, save a decrypted copy beside it and keep the original.
- **Yearly records** (reimbursements, tax, statements) get one subfolder per year, chosen by the document's year, not the day it was filed or paid.
- **One version**: once a document is final, remove the draft. Keep older versions only on purpose, with the date in the name.
- **Sensitive documents** (IDs, certificates, health records) go only where the user keeps them protected; never into a shared folder. If moving them needs the user's own sign-in, leave them in the inbox and say so.
- **Deleting**: use the recycle bin. Permanent deletion needs explicit approval of the exact list. If files outside your command disappear, report them.
- **Cloud-only files**: do not trigger mass downloads to compare them; compare only local copies and say what was not checked.

## Indexes

- Do not build a drive-wide index; search finds files, and a big index goes stale.
- Where a program writes files, it also writes a manifest (CSV: one row per file with source, dates, hash) as the source of truth. A view for people (a spreadsheet, a table) is generated from the manifest and never edited by hand.
- Classify through the manifest or index, not by moving program-written files into category folders.
- Keep databases such as SQLite out of synced folders; sync clients and lock files corrupt them.
