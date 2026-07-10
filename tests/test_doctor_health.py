"""Failing tests for strict doctor health exit criteria."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

RC = Path(__file__).resolve().parents[1]
SCRIPTS = RC / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

FAKE_KEY = "sk-test-fake-key-not-real"


def _reload():
    for name in ("doctor", "config"):
        if name in sys.modules:
            del sys.modules[name]
    return importlib.import_module("doctor")


def test_main_nonzero_when_only_api_key_set(monkeypatch, capsys):
    monkeypatch.delenv("CLAUDE_PLUGIN_OPTION_vision_base_url", raising=False)
    monkeypatch.delenv("CLAUDE_PLUGIN_OPTION_vision_model_id", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", FAKE_KEY)
    doc = _reload()
    code = doc.main([])
    assert code != 0
    out = capsys.readouterr().out
    assert FAKE_KEY not in out
    report = json.loads(out)
    assert report["api_key"] == "SET"
    assert report["base_url_set"] is False


def test_main_nonzero_when_base_url_invalid(monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_base_url", "file:///tmp")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_model_id", "m")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", FAKE_KEY)
    doc = _reload()
    assert doc.main([]) != 0


def test_main_nonzero_when_model_missing(monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_base_url", "https://example.com/v1")
    monkeypatch.delenv("CLAUDE_PLUGIN_OPTION_vision_model_id", raising=False)
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", FAKE_KEY)
    doc = _reload()
    assert doc.main([]) != 0


def test_scripts_ok_false_if_vision_client_missing(monkeypatch, tmp_path):
    doc = _reload()
    monkeypatch.setattr(doc, "PLUGIN_ROOT", tmp_path)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "config.py").write_text("#", encoding="utf-8")
    (tmp_path / "scripts" / "doctor.py").write_text("#", encoding="utf-8")
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "viscol", "userConfig": {}}), encoding="utf-8"
    )
    (tmp_path / "schemas").mkdir()
    report = doc.run_doctor()
    assert report["scripts_ok"] is False


def test_scripts_ok_false_if_provider_missing(monkeypatch, tmp_path):
    doc = _reload()
    monkeypatch.setattr(doc, "PLUGIN_ROOT", tmp_path)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "config.py").write_text("#", encoding="utf-8")
    (scripts / "doctor.py").write_text("#", encoding="utf-8")
    (scripts / "vision_client.py").write_text("#", encoding="utf-8")
    (scripts / "providers").mkdir()
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "viscol", "userConfig": {}}), encoding="utf-8"
    )
    (tmp_path / "schemas").mkdir()
    report = doc.run_doctor()
    assert report["scripts_ok"] is False


def test_main_nonzero_when_schemas_missing(monkeypatch, tmp_path):
    doc = _reload()
    monkeypatch.setattr(doc, "PLUGIN_ROOT", tmp_path)
    scripts = tmp_path / "scripts" / "providers"
    scripts.mkdir(parents=True)
    for name in ("config.py", "doctor.py", "vision_client.py"):
        (tmp_path / "scripts" / name).write_text("#", encoding="utf-8")
    (tmp_path / "scripts" / "providers" / "openai_compatible.py").write_text("#", encoding="utf-8")
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "viscol", "userConfig": {}}), encoding="utf-8"
    )
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_base_url", "https://example.com/v1")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_model_id", "m")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", FAKE_KEY)
    assert doc.main([]) != 0


def test_main_zero_when_fully_healthy(monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_base_url", "https://example.com/v1")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_model_id", "vision-model")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", FAKE_KEY)
    doc = _reload()
    assert doc.main([]) == 0
