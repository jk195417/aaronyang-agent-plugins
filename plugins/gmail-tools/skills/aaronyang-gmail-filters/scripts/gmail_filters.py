# /// script
# requires-python = ">=3.12"
# dependencies = ["google-api-python-client", "google-auth-oauthlib", "tomli-w"]
# ///
"""Keep Gmail filters in sync with <home>/filters.toml (the source of truth).

  uv run gmail_filters.py export [--force]      write the current Gmail filters to filters.toml
  uv run gmail_filters.py plan [--count]        diff filters.toml against Gmail and lint it
  uv run gmail_filters.py apply --yes [--prune] [--no-backfill] [--backfill-trash]
  uv run gmail_filters.py audit [--days 1]      list recent mail that is out of the inbox but unlabeled

One rule with several actions becomes one Gmail filter per action (split = false keeps
them together). apply only creates unless --prune is given, always backs up the current
filters first, and refuses to run without --yes so the plan is reviewed before anything changes.
Scopes: gmail.settings.basic and gmail.modify, stored in token_filters.json.
"""

import argparse
import json
import re
import sys
import tomllib
from datetime import datetime
from pathlib import Path

from gmail_home import gmail_service, require_home

SCOPES = [
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/gmail.modify",
]
TOKEN = "token_filters.json"
FILTERS = "filters.toml"

# filters.toml criteria key -> Gmail API criteria key
CRITERIA = {
    "from": "from",
    "to": "to",
    "subject": "subject",
    "query": "query",
    "negated_query": "negatedQuery",
    "has_attachment": "hasAttachment",
    "exclude_chats": "excludeChats",
    "size": "size",
    "size_comparison": "sizeComparison",
}
# Boolean actions -> (add|remove, system label)
FLAG_ACTIONS = {
    "archive": ("remove", "INBOX"),
    "mark_read": ("remove", "UNREAD"),
    "star": ("add", "STARRED"),
    "trash": ("add", "TRASH"),
    "never_spam": ("remove", "SPAM"),
}
DESTRUCTIVE = {("remove", "INBOX"), ("add", "TRASH")}
SYSTEM = {"INBOX", "UNREAD", "STARRED", "TRASH", "SPAM", "IMPORTANT", "SENT", "DRAFT", "CHAT"}


# ---------- model ----------

def as_list(value) -> list:
    if value in (None, "", []):
        return []
    return list(value) if isinstance(value, list) else [value]


def criteria_of(rule: dict) -> dict:
    out = {}
    for key, api in CRITERIA.items():
        value = rule.get(key)
        if value not in (None, "", False, 0):
            out[api] = value
    return out


def criteria_key(criteria: dict) -> tuple:
    return tuple(sorted((k, str(v)) for k, v in criteria.items() if v not in (None, "", False, 0)))


def rule_atoms(rule: dict) -> list[tuple[str, str]]:
    atoms = [("add", name) for name in as_list(rule.get("label"))]
    atoms += [("remove", name) for name in as_list(rule.get("remove_label"))]
    for key, atom in FLAG_ACTIONS.items():
        if rule.get(key):
            atoms.append(atom)
    if "important" in rule:
        atoms.append(("add" if rule["important"] else "remove", "IMPORTANT"))
    if rule.get("category"):
        atoms.append(("add", "CATEGORY_" + str(rule["category"]).upper()))
    if rule.get("forward"):
        atoms.append(("forward", rule["forward"]))
    return atoms


def desired_filters(rules: list[dict]) -> list[dict]:
    """Expand rules into filters: one per action unless split = false."""
    out = []
    for index, rule in enumerate(rules, 1):
        criteria = criteria_of(rule)
        atoms = rule_atoms(rule)
        groups = [atoms] if rule.get("split") is False else [[a] for a in atoms]
        for group in groups:
            out.append({"rule": index, "name": rule.get("name", ""), "criteria": criteria, "atoms": group})
    return out


def filter_key(criteria: dict, atoms) -> tuple:
    return (criteria_key(criteria), tuple(sorted(atoms)))


def actual_atoms(action: dict, id_to_name: dict) -> list[tuple[str, str]]:
    atoms = [("add", id_to_name.get(i, i)) for i in action.get("addLabelIds", [])]
    atoms += [("remove", id_to_name.get(i, i)) for i in action.get("removeLabelIds", [])]
    if action.get("forward"):
        atoms.append(("forward", action["forward"]))
    return atoms


def atoms_to_rule_fields(atoms) -> dict:
    fields: dict = {}
    reverse = {atom: key for key, atom in FLAG_ACTIONS.items()}
    for atom in atoms:
        kind, value = atom
        if atom in reverse:
            fields[reverse[atom]] = True
        elif value == "IMPORTANT":
            fields["important"] = kind == "add"
        elif kind == "add" and value.startswith("CATEGORY_"):
            fields["category"] = value.removeprefix("CATEGORY_").lower()
        elif kind == "forward":
            fields["forward"] = value
        else:
            fields.setdefault("label" if kind == "add" else "remove_label", []).append(value)
    for key in ("label", "remove_label"):
        if key in fields and len(fields[key]) == 1:
            fields[key] = fields[key][0]
    return fields


def export_rules(actual: list[dict], id_to_name: dict) -> list[dict]:
    """Group Gmail filters by criteria; single-action filters with equal criteria merge into one rule."""
    api_to_key = {api: key for key, api in CRITERIA.items()}
    merged: dict[tuple, dict] = {}
    rules: list[dict] = []
    for f in actual:
        criteria = f.get("criteria", {})
        atoms = actual_atoms(f.get("action", {}), id_to_name)
        base = {api_to_key[k]: v for k, v in criteria.items() if k in api_to_key}
        if len(atoms) == 1:
            key = criteria_key(criteria)
            if key not in merged:
                merged[key] = {**base, "_atoms": []}
                rules.append(merged[key])
            if atoms[0] not in merged[key]["_atoms"]:
                merged[key]["_atoms"].append(atoms[0])
        else:
            rules.append({**base, "_atoms": atoms, "split": False})
    out = []
    for rule in rules:
        atoms = rule.pop("_atoms")
        out.append({**rule, **atoms_to_rule_fields(atoms)})
    return out


def has_positive_query(query: str) -> bool:
    q = re.sub(r"-\{[^}]*\}|-\([^)]*\)|-\"[^\"]*\"|-\S+", " ", query or "")
    q = re.sub(r"\b(OR|AND)\b|[(){}\"]", " ", q)
    return bool(q.strip())


def has_positive_criteria(criteria: dict) -> bool:
    return any(criteria.get(k) for k in ("from", "to", "subject", "hasAttachment", "size")) or has_positive_query(
        criteria.get("query", "")
    )


def search_query(criteria: dict) -> str:
    parts = []
    for key in ("from", "to", "subject"):
        if criteria.get(key):
            parts.append(f"{key}:({criteria[key]})")
    if criteria.get("query"):
        parts.append(criteria["query"])
    if criteria.get("negatedQuery"):
        parts.append(f"-{{{criteria['negatedQuery']}}}")
    if criteria.get("hasAttachment"):
        parts.append("has:attachment")
    if criteria.get("size"):
        parts.append(f"{'larger' if criteria.get('sizeComparison') == 'larger' else 'smaller'}:{criteria['size']}")
    return " ".join(parts)


def lint(rules: list[dict], desired: list[dict], label_names: set[str]) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for index, rule in enumerate(rules, 1):
        where = f"rule {index}" + (f" ({rule['name']})" if rule.get("name") else "")
        unknown = set(rule) - set(CRITERIA) - set(FLAG_ACTIONS) - {
            "name", "label", "remove_label", "important", "category", "forward", "split"}
        if unknown:
            errors.append(f"{where}: unknown keys {sorted(unknown)}")
        criteria = criteria_of(rule)
        atoms = rule_atoms(rule)
        if not criteria:
            errors.append(f"{where}: no criteria; it would match every email")
        if not atoms:
            errors.append(f"{where}: no actions")
        if any(a in DESTRUCTIVE for a in atoms) and not has_positive_criteria(criteria):
            errors.append(f"{where}: archives or trashes without a positive sender, subject or query term")
        for kind, name in atoms:
            if kind == "add" and name not in SYSTEM and not name.startswith("CATEGORY_") and name not in label_names:
                warnings.append(f"{where}: label {name!r} does not exist and will be created")
    seen: dict[tuple, int] = {}
    for f in desired:
        key = filter_key(f["criteria"], f["atoms"])
        if key in seen:
            warnings.append(f"rule {f['rule']}: duplicates a filter from rule {seen[key]}")
        seen.setdefault(key, f["rule"])
    return errors, warnings


# ---------- Gmail ----------

def load_rules(home: Path) -> list[dict]:
    path = home / FILTERS
    if not path.exists():
        sys.exit(f"Missing {path}; run export first or copy assets/filters.example.toml")
    with path.open("rb") as f:
        return tomllib.load(f).get("rules", [])


def fetch(service):
    labels = service.users().labels().list(userId="me").execute(num_retries=8).get("labels", [])
    filters = service.users().settings().filters().list(userId="me").execute(num_retries=8).get("filter", [])
    return filters, {lab["id"]: lab["name"] for lab in labels}


def backup(home: Path, filters: list, id_to_name: dict) -> Path:
    folder = home / "backups"
    folder.mkdir(exist_ok=True)
    path = folder / f"filters-{datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps({"filters": filters, "labels": id_to_name}, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def diff(desired: list[dict], actual: list[dict], id_to_name: dict):
    actual_by_key = {filter_key(f.get("criteria", {}), actual_atoms(f.get("action", {}), id_to_name)): f for f in actual}
    desired_keys = set()
    create = []
    for f in desired:
        key = filter_key(f["criteria"], f["atoms"])
        if key in desired_keys:
            continue
        desired_keys.add(key)
        if key not in actual_by_key:
            create.append(f)
    extra = [f for key, f in actual_by_key.items() if key not in desired_keys]
    return create, extra, len(desired_keys) - len(create)


def matching_ids(service, query: str, limit: int) -> list[str]:
    ids, token = [], None
    while len(ids) < limit:
        resp = service.users().messages().list(
            userId="me", q=query, pageToken=token, maxResults=min(500, limit - len(ids))
        ).execute(num_retries=8)
        ids += [m["id"] for m in resp.get("messages", [])]
        token = resp.get("nextPageToken")
        if not token:
            break
    return ids


def describe(criteria: dict, atoms) -> str:
    acts = ", ".join(f"{k} {v}" for k, v in atoms)
    return f"{search_query(criteria)}  =>  {acts}"


# ---------- commands ----------

def cmd_export(service, home: Path, force: bool) -> int:
    path = home / FILTERS
    if path.exists() and not force:
        print(f"{path} exists; rerun with --force to overwrite it")
        return 2
    import tomli_w

    actual, id_to_name = fetch(service)
    print(f"backup: {backup(home, actual, id_to_name)}")
    rules = export_rules(actual, id_to_name)
    header = (
        "# Gmail filters, source of truth for gmail_filters.py. One rule may list several actions;\n"
        "# each becomes its own Gmail filter unless split = false.\n\n"
    )
    path.write_text(header + tomli_w.dumps({"rules": rules}), encoding="utf-8")
    print(f"wrote {len(rules)} rules covering {len(actual)} filters to {path}")
    return 0


def cmd_plan(service, home: Path, count: bool, show_lint=True):
    rules = load_rules(home)
    desired = desired_filters(rules)
    actual, id_to_name = fetch(service)
    errors, warnings = lint(rules, desired, set(id_to_name.values()))
    create, extra, same = diff(desired, actual, id_to_name)
    print(f"unchanged {same}, to create {len(create)}, not in filters.toml {len(extra)}")
    for f in create:
        hits = ""
        if count:
            n = len(matching_ids(service, search_query(f["criteria"]), 500))
            hits = f"  [{'500+' if n >= 500 else n} existing matches]"
        print(f"  + rule {f['rule']}: {describe(f['criteria'], f['atoms'])}{hits}")
    for f in extra:
        print(f"  - (prune only) {describe(f.get('criteria', {}), actual_atoms(f.get('action', {}), id_to_name))}")
    if show_lint:
        for w in warnings:
            print(f"warning: {w}")
        for e in errors:
            print(f"error: {e}")
    return rules, desired, actual, id_to_name, create, extra, errors


def cmd_apply(service, home: Path, args) -> int:
    _, _, actual, id_to_name, create, extra, errors = cmd_plan(service, home, count=False)
    if errors:
        print("lint errors; nothing changed")
        return 1
    if not args.yes:
        print("dry run: show this plan to the user, then rerun with --yes")
        return 2
    print(f"backup: {backup(home, actual, id_to_name)}")
    name_to_id = {name: i for i, name in id_to_name.items()}
    api = service.users()
    for f in create:
        for kind, name in f["atoms"]:
            if kind == "add" and name not in name_to_id:
                label = api.labels().create(userId="me", body={"name": name}).execute(num_retries=8)
                name_to_id[name] = label["id"]
                print(f"created label {name}")
        action: dict = {}
        for kind, name in f["atoms"]:
            if kind == "forward":
                action["forward"] = name
            else:
                action.setdefault("addLabelIds" if kind == "add" else "removeLabelIds", []).append(name_to_id.get(name, name))
        api.settings().filters().create(userId="me", body={"criteria": f["criteria"], "action": action}).execute(num_retries=8)
        line = f"created rule {f['rule']}: {describe(f['criteria'], f['atoms'])}"
        trash = ("add", "TRASH") in f["atoms"]
        if not args.no_backfill and (not trash or args.backfill_trash) and "forward" not in action:
            ids = matching_ids(service, search_query(f["criteria"]), args.backfill_limit)
            body = {k: v for k, v in action.items() if k in ("addLabelIds", "removeLabelIds")}
            for i in range(0, len(ids), 1000):
                api.messages().batchModify(userId="me", body={"ids": ids[i:i + 1000], **body}).execute(num_retries=8)
            line += f"  [applied to {len(ids)} existing]"
        print(line)
    if args.prune:
        for f in extra:
            api.settings().filters().delete(userId="me", id=f["id"]).execute(num_retries=8)
            print(f"deleted {describe(f.get('criteria', {}), actual_atoms(f.get('action', {}), id_to_name))}")
    elif extra:
        print(f"{len(extra)} Gmail filters are not in filters.toml; kept (use --prune to delete)")
    print("next: run audit to spot-check recent mail")
    return 0


def cmd_audit(service, days: int) -> int:
    query = f"newer_than:{days}d -in:inbox -in:sent -in:drafts -in:chats -in:spam -in:trash"
    ids = matching_ids(service, query, 500)
    flagged = []
    for message_id in ids:
        msg = service.users().messages().get(
            userId="me", id=message_id, format="metadata", metadataHeaders=["From", "Subject"]
        ).execute(num_retries=8)
        if not any(label.startswith("Label_") for label in msg.get("labelIds", [])):
            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            flagged.append((headers.get("From", ""), headers.get("Subject", "")))
    print(f"{len(ids)} messages out of the inbox in the last {days} day(s); {len(flagged)} have no user label")
    for sender, subject in flagged:
        print(f"  ! {sender} | {subject}")
    return 1 if flagged else 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Sync Gmail filters with filters.toml")
    parser.add_argument("--home", help="gmail-tools home folder")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("export").add_argument("--force", action="store_true")
    sub.add_parser("plan").add_argument("--count", action="store_true", help="count existing matches per new filter")
    p = sub.add_parser("apply")
    p.add_argument("--yes", action="store_true", help="the user approved the plan")
    p.add_argument("--prune", action="store_true", help="also delete Gmail filters missing from filters.toml")
    p.add_argument("--no-backfill", action="store_true", help="do not apply new filters to existing mail")
    p.add_argument("--backfill-trash", action="store_true", help="also apply trash filters to existing mail")
    p.add_argument("--backfill-limit", type=int, default=5000)
    sub.add_parser("audit").add_argument("--days", type=int, default=1)
    args = parser.parse_args()

    home = require_home(args.home, ["credentials.json"])
    service = gmail_service(home, SCOPES, TOKEN)
    if args.cmd == "export":
        return cmd_export(service, home, args.force)
    if args.cmd == "plan":
        return 1 if cmd_plan(service, home, args.count)[-1] else 0
    if args.cmd == "apply":
        return cmd_apply(service, home, args)
    return cmd_audit(service, args.days)


if __name__ == "__main__":
    raise SystemExit(main())
