"""Task 8 TDD: placeholder scanner with self-scan safety."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

RC = Path(__file__).resolve().parents[1]
SCRIPTS = RC / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "placeholder_scan"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _reload():
    if "scan_placeholders" in sys.modules:
        del sys.modules["scan_placeholders"]
    return importlib.import_module("scan_placeholders")


def test_detects_real_todo_fixture():
    scan = _reload()
    FIXTURES.mkdir(parents=True, exist_ok=True)
    bad = FIXTURES / "needs_work.txt"
    marker = "TO" + "DO"
    bad.write_text(f"this file has {marker} item unfinished\n", encoding="utf-8")
    hits = scan.scan_file(bad, root=FIXTURES)
    assert hits
    assert hits[0]["rule"] in {"todo", "tbd", "placeholder"}


def test_scanner_source_does_not_self_hit():
    scan = _reload()
    src = SCRIPTS / "scan_placeholders.py"
    hits = scan.scan_file(src, root=RC)
    assert hits == [], hits


def test_allowlisted_docs_examples_do_not_false_positive(tmp_path):
    scan = _reload()
    # Documentation that mentions the scanner behavior without being unfinished work.
    f = tmp_path / "note.md"
    f.write_text(
        "The scanner looks for unfinished markers. Completed work has none.\n",
        encoding="utf-8",
    )
    assert scan.scan_file(f, root=tmp_path) == []
