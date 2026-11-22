# /// script
# requires-python = ">=3.12"
# dependencies = ["tomli-w"]
# ///
"""Offline checks for gmail_filters.py: uv run tests/test_gmail_filters.py"""

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugins/gmail-tools/skills/aaronyang-gmail-filters/scripts"))

import tomli_w  # noqa: E402

import gmail_filters as g  # noqa: E402

LABELS = {"Label_1": "Banks", "Label_2": "行銷", "INBOX": "INBOX", "UNREAD": "UNREAD"}


def api(criteria, add=(), remove=(), fid="f"):
    action = {}
    if add:
        action["addLabelIds"] = list(add)
    if remove:
        action["removeLabelIds"] = list(remove)
    return {"id": fid, "criteria": criteria, "action": action}


def test_split_and_roundtrip():
    rules = [{"from": "news@shop.example", "label": "行銷", "archive": True}]
    desired = g.desired_filters(rules)
    assert [f["atoms"] for f in desired] == [[("add", "行銷")], [("remove", "INBOX")]]
    actual = [api({"from": "news@shop.example"}, add=["Label_2"], fid="a"),
              api({"from": "news@shop.example"}, remove=["INBOX"], fid="b")]
    create, extra, same = g.diff(desired, actual, LABELS)
    assert (len(create), len(extra), same) == (0, 0, 2)
    exported = g.export_rules(actual, LABELS)
    assert exported == [{"from": "news@shop.example", "label": "行銷", "archive": True}]
    # export -> toml -> load gives the same filters
    again = tomllib.loads(tomli_w.dumps({"rules": exported}))["rules"]
    assert g.diff(g.desired_filters(again), actual, LABELS)[:2] == ([], [])


def test_multi_action_filter_kept_together():
    actual = [api({"from": "x@y.example"}, add=["Label_1"], remove=["INBOX", "UNREAD"])]
    rules = g.export_rules(actual, LABELS)
    assert rules == [{"from": "x@y.example", "split": False, "label": "Banks", "archive": True, "mark_read": True}]
    assert g.diff(g.desired_filters(rules), actual, LABELS)[:2] == ([], [])


def test_diff_create_and_extra():
    rules = [{"from": "a@b.example", "label": "Banks"}]
    actual = [api({"from": "old@b.example"}, add=["Label_1"])]
    create, extra, same = g.diff(g.desired_filters(rules), actual, LABELS)
    assert len(create) == 1 and len(extra) == 1 and same == 0


def test_lint_blocks_archive_without_positive_criteria():
    # The 2026-11-05 incident: a skip-inbox filter whose only sender terms were negated.
    rules = [{"query": "-{from:(a@b.example OR c@d.example)}", "archive": True}]
    errors, _ = g.lint(rules, g.desired_filters(rules), set(LABELS.values()))
    assert any("positive" in e for e in errors)
    ok = [{"query": "list:news.example -{subject:urgent}", "archive": True}]
    assert not g.lint(ok, g.desired_filters(ok), set(LABELS.values()))[0]


def test_lint_other_checks():
    rules = [{"label": "Banks"}, {"from": "a@b.example"}, {"from": "a@b.example", "label": "New", "colour": "red"}]
    errors, warnings = g.lint(rules, g.desired_filters(rules), set(LABELS.values()))
    assert any("no criteria" in e for e in errors)
    assert any("no actions" in e for e in errors)
    assert any("unknown keys" in e for e in errors)
    assert any("'New'" in w for w in warnings)


def test_search_query():
    q = g.search_query({"from": "a@b.example", "subject": "帳單", "negatedQuery": "廣告", "hasAttachment": True})
    assert q == "from:(a@b.example) subject:(帳單) -{廣告} has:attachment"


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for test in tests:
        test()
        print(f"ok {test.__name__}")
    print(f"{len(tests)} passed")
