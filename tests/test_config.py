"""Task 2: config loader contract tests (TDD)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

RC = Path(__file__).resolve().parents[1]
SCRIPTS = RC / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

FAKE_KEY = "sk-test-fake-key-not-real"


def _reload_config():
    if "config" in sys.modules:
        del sys.modules["config"]
    return importlib.import_module("config")


def test_missing_all_config_returns_config_missing(monkeypatch):
    for k in (
        "CLAUDE_PLUGIN_OPTION_vision_base_url",
        "CLAUDE_PLUGIN_OPTION_vision_model_id",
        "CLAUDE_PLUGIN_OPTION_vision_api_key",
    ):
        monkeypatch.delenv(k, raising=False)
    cfg = _reload_config()
    result = cfg.load_vision_config()
    assert result["ok"] is False
    assert result["error_code"] == "CONFIG_MISSING"
    assert "Do not paste API keys into chat" in result["message"]


def test_partial_missing_key_is_config_missing(monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_base_url", "https://example.com/v1")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_model_id", "vision-model")
    monkeypatch.delenv("CLAUDE_PLUGIN_OPTION_vision_api_key", raising=False)
    cfg = _reload_config()
    result = cfg.load_vision_config()
    assert result["ok"] is False
    assert result["error_code"] == "CONFIG_MISSING"


def test_complete_config_ok(monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_base_url", "https://example.com/v1")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_model_id", "vision-model")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", FAKE_KEY)
    cfg = _reload_config()
    result = cfg.load_vision_config()
    assert result["ok"] is True
    assert result["error_code"] == "CONFIG_OK"
    assert result["base_url"] == "https://example.com/v1"
    assert result["model_id"] == "vision-model"
    assert result["api_key"] == FAKE_KEY


def test_invalid_url_rejected(monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_base_url", "file:///tmp/x")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_model_id", "vision-model")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", FAKE_KEY)
    cfg = _reload_config()
    result = cfg.load_vision_config()
    assert result["ok"] is False
    assert result["error_code"] == "CONFIG_INVALID_URL"


def test_does_not_read_dotenv_file(monkeypatch, tmp_path):
    # Even if a .env exists nearby, config must ignore it.
    env_file = RC / ".env"
    created = False
    if not env_file.exists():
        env_file.write_text(
            "CLAUDE_PLUGIN_OPTION_vision_api_key=dotenv-fake-value-not-a-provider-key\n",
            encoding="utf-8",
        )
        created = True
    try:
        for k in (
            "CLAUDE_PLUGIN_OPTION_vision_base_url",
            "CLAUDE_PLUGIN_OPTION_vision_model_id",
            "CLAUDE_PLUGIN_OPTION_vision_api_key",
        ):
            monkeypatch.delenv(k, raising=False)
        cfg = _reload_config()
        result = cfg.load_vision_config()
        assert result["ok"] is False
        assert result["error_code"] == "CONFIG_MISSING"
        assert "dotenv-fake-value" not in str(result)
    finally:
        if created and env_file.exists():
            env_file.unlink()


def test_error_message_never_contains_api_key(monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_base_url", "not-a-url")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_model_id", "m")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", FAKE_KEY)
    cfg = _reload_config()
    result = cfg.load_vision_config()
    blob = json_dumps(result)
    assert FAKE_KEY not in blob


def json_dumps(obj) -> str:
    import json

    return json.dumps(obj, ensure_ascii=False)
