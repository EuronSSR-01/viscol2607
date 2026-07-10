"""Task 2: doctor offline diagnostics tests (TDD)."""

from __future__ import annotations

import importlib
import json
import socket
import sys
from pathlib import Path

import pytest

RC = Path(__file__).resolve().parents[1]
SCRIPTS = RC / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

FAKE_KEY = "sk-test-fake-key-not-real"


def _reload_doctor():
    for name in ("doctor", "config"):
        if name in sys.modules:
            del sys.modules[name]
    return importlib.import_module("doctor")


def test_doctor_reports_not_set_without_leaking_key(monkeypatch):
    for k in (
        "CLAUDE_PLUGIN_OPTION_vision_base_url",
        "CLAUDE_PLUGIN_OPTION_vision_model_id",
        "CLAUDE_PLUGIN_OPTION_vision_api_key",
    ):
        monkeypatch.delenv(k, raising=False)
    doc = _reload_doctor()
    report = doc.run_doctor()
    assert report["api_key"] == "NOT SET"
    blob = json.dumps(report, ensure_ascii=False)
    assert FAKE_KEY not in blob
    assert "length" not in blob.lower() or report["api_key"] == "NOT SET"


def test_doctor_reports_set_without_value_length_prefix(monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_base_url", "https://example.com/v1")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_model_id", "vision-model")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", FAKE_KEY)
    doc = _reload_doctor()
    report = doc.run_doctor()
    assert report["api_key"] == "SET"
    blob = json.dumps(report, ensure_ascii=False)
    assert FAKE_KEY not in blob
    assert "sk-test" not in blob
    assert str(len(FAKE_KEY)) not in blob


def test_doctor_requires_python_310(monkeypatch):
    doc = _reload_doctor()
    report = doc.run_doctor()
    assert "python_ok" in report
    assert report["python_ok"] is True
    assert report["python_version"].startswith("3.")


def test_doctor_default_makes_zero_network_calls(monkeypatch):
    calls = {"n": 0}

    def boom(*args, **kwargs):
        calls["n"] += 1
        raise AssertionError("doctor must not open network sockets by default")

    monkeypatch.setattr(socket, "create_connection", boom)
    monkeypatch.setattr(socket.socket, "connect", boom, raising=False)
    for k in (
        "CLAUDE_PLUGIN_OPTION_vision_base_url",
        "CLAUDE_PLUGIN_OPTION_vision_model_id",
        "CLAUDE_PLUGIN_OPTION_vision_api_key",
    ):
        monkeypatch.delenv(k, raising=False)
    doc = _reload_doctor()
    doc.run_doctor()
    assert calls["n"] == 0
