"""Failing tests for request-file path boundary and cleanup safety."""

from __future__ import annotations

import base64
import importlib
import json
import os
import sys
import uuid
from pathlib import Path

import pytest

RC = Path(__file__).resolve().parents[1]
SCRIPTS = RC / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

FAKE_KEY = "sk-test-fake-key-not-real"
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _reload():
    for name in ("vision_client", "providers.openai_compatible", "providers", "config"):
        if name in sys.modules:
            del sys.modules[name]
    return importlib.import_module("vision_client")


def _set_cfg(monkeypatch, base: str = "http://127.0.0.1:9"):
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_base_url", base)
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_model_id", "vision-model")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", FAKE_KEY)


def _valid_name(session: str = "sessABC123") -> str:
    return f"{session}-{uuid.UUID('00000000-0000-4000-8000-000000000001')}.json"


def test_illegal_filename_existing_file_is_not_unlinked(tmp_path, monkeypatch):
    _set_cfg(monkeypatch)
    plugin_data = tmp_path / "pdata"
    req_dir = plugin_data / "requests"
    req_dir.mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))
    vc = _reload()
    bad = req_dir / "evil;rm.json"
    bad.write_text("{}", encoding="utf-8")
    result = vc.run_request_file(str(bad))
    assert result["ok"] is False
    assert result["error_code"] == "INVALID_REQUEST_FILE"
    assert bad.exists(), "illegal filename must not be unlinked"


def test_outside_requests_dir_not_read_or_deleted(tmp_path, monkeypatch):
    _set_cfg(monkeypatch)
    plugin_data = tmp_path / "pdata"
    req_dir = plugin_data / "requests"
    req_dir.mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))
    vc = _reload()
    outside = tmp_path / "outside" / _valid_name()
    outside.parent.mkdir(parents=True)
    outside.write_text(
        json.dumps(
            {
                "task": "describe",
                "image_paths": ["x.png"],
                "user_question": "q",
                "upload_confirmed": True,
            }
        ),
        encoding="utf-8",
    )
    result = vc.run_request_file(str(outside))
    assert result["ok"] is False
    assert result["error_code"] == "INVALID_REQUEST_FILE"
    assert outside.exists(), "outside requests dir must not be deleted"


def test_valid_request_in_dir_deleted_after_success(tmp_path, monkeypatch):
    _set_cfg(monkeypatch, base="http://127.0.0.1:9")
    plugin_data = tmp_path / "pdata"
    req_dir = plugin_data / "requests"
    req_dir.mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))
    png = tmp_path / "a.png"
    png.write_bytes(PNG_BYTES)
    vc = _reload()

    def fake_post(*a, **k):
        return {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(vc, "post_chat_completions", fake_post)
    req_path = req_dir / _valid_name()
    req_path.write_text(
        json.dumps(
            {
                "task": "describe",
                "image_paths": [str(png)],
                "user_question": "q",
                "upload_confirmed": True,
            }
        ),
        encoding="utf-8",
    )
    result = vc.run_request_file(str(req_path))
    assert result["ok"] is True
    assert not req_path.exists()


def test_valid_request_deleted_after_config_error(tmp_path, monkeypatch):
    for k in (
        "CLAUDE_PLUGIN_OPTION_vision_base_url",
        "CLAUDE_PLUGIN_OPTION_vision_model_id",
        "CLAUDE_PLUGIN_OPTION_vision_api_key",
    ):
        monkeypatch.delenv(k, raising=False)
    plugin_data = tmp_path / "pdata"
    req_dir = plugin_data / "requests"
    req_dir.mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))
    vc = _reload()
    req_path = req_dir / _valid_name()
    req_path.write_text(
        json.dumps(
            {
                "task": "describe",
                "image_paths": ["missing.png"],
                "user_question": "q",
                "upload_confirmed": True,
            }
        ),
        encoding="utf-8",
    )
    result = vc.run_request_file(str(req_path))
    assert result["ok"] is False
    assert result["error_code"] == "CONFIG_MISSING"
    assert not req_path.exists()


def test_symlink_escape_rejected_without_delete(tmp_path, monkeypatch):
    _set_cfg(monkeypatch)
    plugin_data = tmp_path / "pdata"
    req_dir = plugin_data / "requests"
    req_dir.mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))
    outside = tmp_path / "escape" / _valid_name()
    outside.parent.mkdir(parents=True)
    outside.write_text("{}", encoding="utf-8")
    link = req_dir / _valid_name("sessLINK01")
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink not available on this platform/user")
    vc = _reload()
    result = vc.run_request_file(str(link))
    assert result["ok"] is False
    assert result["error_code"] == "INVALID_REQUEST_FILE"
    assert outside.exists()
    # link itself should not be unlinked when boundary fails
    assert link.exists() or link.is_symlink()


def test_filename_must_match_session_uuid_pattern(tmp_path, monkeypatch):
    _set_cfg(monkeypatch)
    plugin_data = tmp_path / "pdata"
    req_dir = plugin_data / "requests"
    req_dir.mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))
    vc = _reload()
    bad = req_dir / "nosess-not-a-uuid.json"
    bad.write_text("{}", encoding="utf-8")
    result = vc.run_request_file(str(bad))
    assert result["ok"] is False
    assert result["error_code"] == "INVALID_REQUEST_FILE"
    assert bad.exists()


def test_request_json_allowlist_rejects_extra_fields(tmp_path, monkeypatch):
    _set_cfg(monkeypatch)
    plugin_data = tmp_path / "pdata"
    req_dir = plugin_data / "requests"
    req_dir.mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))
    vc = _reload()
    req_path = req_dir / _valid_name()
    req_path.write_text(
        json.dumps(
            {
                "task": "describe",
                "image_paths": ["a.png"],
                "user_question": "q",
                "upload_confirmed": True,
                "extra": 1,
            }
        ),
        encoding="utf-8",
    )
    result = vc.run_request_file(str(req_path))
    assert result["ok"] is False
    assert result["error_code"] == "INVALID_REQUEST_FILE"
    assert not req_path.exists()


def test_nested_sensitive_field_rejected(tmp_path, monkeypatch):
    _set_cfg(monkeypatch)
    plugin_data = tmp_path / "pdata"
    req_dir = plugin_data / "requests"
    req_dir.mkdir(parents=True)
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))
    vc = _reload()
    req_path = req_dir / _valid_name()
    req_path.write_text(
        json.dumps(
            {
                "task": "describe",
                "image_paths": ["a.png"],
                "user_question": "q",
                "upload_confirmed": True,
                "meta": {"api_key": "nope"},
            }
        ),
        encoding="utf-8",
    )
    # extra field meta also violates allowlist
    result = vc.run_request_file(str(req_path))
    assert result["ok"] is False
    assert result["error_code"] == "INVALID_REQUEST_FILE"


def test_ensure_requests_dir_helper(tmp_path, monkeypatch):
    plugin_data = tmp_path / "pdata"
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))
    vc = _reload()
    path = vc.ensure_requests_dir()
    assert path.is_dir()
    assert path.resolve() == (plugin_data / "requests").resolve()
