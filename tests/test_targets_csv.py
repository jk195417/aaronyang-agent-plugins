# /// script
# requires-python = ">=3.12"
# ///
"""Offline checks for the targets.csv export: uv run tests/test_targets_csv.py"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugins/gmail-tools/skills/aaronyang-gmail-pdf-archive/scripts"))

from config import target_statuses, write_targets_csv  # noqa: E402

TOML = '''# name      Used in file names. No spaces or underscores.

[[targets]]
name = "bank-a-card"
from = "statements@bank-a.example"

# [[targets]]
# name = "old-bank"
# from = "old@bank.example"

#name="bank-a-card"

[[targets]]
name = "utility-bill"
from = "billing@utility.example"
'''


def test_statuses_and_csv():
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        (home / "targets.toml").write_text(TOML, encoding="utf-8")
        assert target_statuses(home) == {"bank-a-card": "active", "utility-bill": "active", "old-bank": "retired"}
        out = home / "export" / "targets.csv"
        assert write_targets_csv(home, out) is True
        assert out.read_text(encoding="utf-8") == (
            "name,status\nbank-a-card,active\nold-bank,retired\nutility-bill,active\n")
        assert write_targets_csv(home, out) is False  # unchanged content is not rewritten
        assert not list(out.parent.glob("*.tmp"))


if __name__ == "__main__":
    test_statuses_and_csv()
    print("ok")
