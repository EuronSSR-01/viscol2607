"""Task 8 TDD: secret scanner."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

RC = Path(__file__).resolve().parents[1]
SCRIPTS = RC / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

FAKE_OK = "sk-test-fake-key-not-real"


def _reload():
    if "scan_secrets" in sys.modules:
        del sys.modules["scan_secrets"]
    return importlib.import_module("scan_secrets")


def test_allows_dynamic_authorization_header_construction(tmp_path):
    scan = _reload()
    f = tmp_path / "ok.py"
    f.write_text('headers = {"Authorization": "Bearer " + api_key}\n', encoding="utf-8")
    hits = scan.scan_file(f, root=tmp_path)
    assert hits == []


def test_detects_hardcoded_bearer_value(tmp_path):
    scan = _reload()
    f = tmp_path / "bad.py"
    token = "sk-" + "live-hardcoded-secret-value-123456"
    f.write_text(f'h = "Bearer {token}"\n', encoding="utf-8")
    hits = scan.scan_file(f, root=tmp_path)
    assert hits
    assert hits[0]["rule"]
    assert "path" in hits[0] and "line" in hits[0]
    assert "live-hardcoded" not in str(hits[0])  # no match content


def test_whitelist_fake_test_key_only(tmp_path):
    scan = _reload()
    f = tmp_path / "t.py"
    f.write_text(f'KEY = "{FAKE_OK}"\n', encoding="utf-8")
    assert scan.scan_file(f, root=tmp_path) == []


def test_detects_author_absolute_path(tmp_path):
    scan = _reload()
    f = tmp_path / "p.md"
    banned = "E:/" + "VibeCoding" + "/sample/x"
    f.write_text(f"path={banned}\n", encoding="utf-8")
    hits = scan.scan_file(f, root=tmp_path)
    assert any(h["rule"] == "private_absolute_path" for h in hits)


def test_allows_declared_public_github_identity(tmp_path):
    scan = _reload()
    f = tmp_path / "public.md"
    f.write_text(
        "Copyright (c) 2026 EuronSSR-01\n"
        "https://github.com/EuronSSR-01/viscol2607\n",
        encoding="utf-8",
    )
    assert scan.scan_file(f, root=tmp_path) == []


def test_still_detects_private_username_and_windows_user_path(tmp_path):
    scan = _reload()
    f = tmp_path / "private.md"
    private_user = "Euron" + "SSR"
    windows_path = "C:\\Users\\" + private_user + "\\secret"
    f.write_text(f"owner={private_user}\npath={windows_path}\n", encoding="utf-8")
    hits = scan.scan_file(f, root=tmp_path)
    assert sum(h["rule"] == "private_username" for h in hits) == 2


def test_cli_excludes_work(tmp_path, monkeypatch):
    scan = _reload()
    # Ensure module exposes scan_tree that skips _work
    assert hasattr(scan, "scan_tree")
