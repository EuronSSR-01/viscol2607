"""Task 3 / hardened: endpoint normalization and request-file vision client."""

from __future__ import annotations

import base64
import importlib
import json
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
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
VALID_UUID = "00000000-0000-4000-8000-000000000001"


def _reload():
    for name in ("vision_client", "providers.openai_compatible", "providers", "config"):
        if name in sys.modules:
            del sys.modules[name]
    return importlib.import_module("vision_client")


def _req_path(plugin_data: Path, session: str = "sessABC") -> Path:
    d = plugin_data / "requests"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{session}-{VALID_UUID}.json"


@pytest.fixture()
def png_file(tmp_path: Path) -> Path:
    p = tmp_path / "a.png"
    p.write_bytes(PNG_BYTES)
    return p


def test_normalize_endpoint_appends_once():
    vc = _reload()
    assert vc.normalize_chat_completions_url("https://api.example.com/v1") == (
        "https://api.example.com/v1/chat/completions"
    )
    assert vc.normalize_chat_completions_url("https://api.example.com/v1/") == (
        "https://api.example.com/v1/chat/completions"
    )
    assert (
        vc.normalize_chat_completions_url("https://api.example.com/v1/chat/completions")
        == "https://api.example.com/v1/chat/completions"
    )
    assert (
        vc.normalize_chat_completions_url("https://api.example.com/v1/chat/completions/")
        == "https://api.example.com/v1/chat/completions"
    )


def test_reject_file_scheme():
    vc = _reload()
    with pytest.raises(ValueError):
        vc.normalize_chat_completions_url("file:///tmp/x")


def test_request_filename_rejects_traversal():
    vc = _reload()
    assert vc.is_safe_request_filename(f"sessABC-{VALID_UUID}.json") is True
    assert vc.is_safe_request_filename("../evil.json") is False
    assert vc.is_safe_request_filename("a;rm.json") is False
    assert vc.is_safe_request_filename("a b.json") is False
    assert vc.is_safe_request_filename("nosess-not-a-uuid.json") is False


def test_missing_upload_confirmation_zero_network(monkeypatch, png_file, tmp_path):
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_base_url", "http://127.0.0.1:9")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_model_id", "vision-model")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", FAKE_KEY)
    plugin_data = tmp_path / "pdata"
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))
    vc = _reload()
    req = {
        "task": "describe",
        "image_paths": [str(png_file)],
        "user_question": "what is this?",
        "upload_confirmed": False,
    }
    req_path = _req_path(plugin_data)
    req_path.write_text(json.dumps(req), encoding="utf-8")
    called = {"n": 0}

    def boom(*a, **k):
        called["n"] += 1
        raise AssertionError("must not network")

    monkeypatch.setattr(vc, "post_chat_completions", boom)
    result = vc.run_request_file(str(req_path))
    assert result["ok"] is False
    assert result["error_code"] == "UPLOAD_NOT_CONFIRMED"
    assert called["n"] == 0
    assert not req_path.exists()


def test_config_missing_before_network(monkeypatch, png_file, tmp_path):
    for k in (
        "CLAUDE_PLUGIN_OPTION_vision_base_url",
        "CLAUDE_PLUGIN_OPTION_vision_model_id",
        "CLAUDE_PLUGIN_OPTION_vision_api_key",
    ):
        monkeypatch.delenv(k, raising=False)
    plugin_data = tmp_path / "pdata"
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))
    vc = _reload()
    req = {
        "task": "describe",
        "image_paths": [str(png_file)],
        "user_question": "x",
        "upload_confirmed": True,
    }
    req_path = _req_path(plugin_data, "sessCFG")
    req_path.write_text(json.dumps(req), encoding="utf-8")
    result = vc.run_request_file(str(req_path))
    assert result["ok"] is False
    assert result["error_code"] == "CONFIG_MISSING"
    assert not req_path.exists()


def test_rejects_non_image_extension_spoof(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_base_url", "http://127.0.0.1:9")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_model_id", "vision-model")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", FAKE_KEY)
    plugin_data = tmp_path / "pdata"
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))
    vc = _reload()
    fake = tmp_path / "x.png"
    fake.write_bytes(b"not-an-image")
    req = {
        "task": "describe",
        "image_paths": [str(fake)],
        "user_question": "x",
        "upload_confirmed": True,
    }
    req_path = _req_path(plugin_data, "sessIMG")
    req_path.write_text(json.dumps(req), encoding="utf-8")
    result = vc.run_request_file(str(req_path))
    assert result["ok"] is False
    assert result["error_code"] == "INVALID_IMAGE"
    assert not req_path.exists()


def test_mock_server_roundtrip(monkeypatch, png_file, tmp_path):
    captured = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            captured["path"] = self.path
            captured["auth"] = self.headers.get("Authorization")
            captured["body"] = json.loads(body.decode("utf-8"))
            payload = {
                "choices": [
                    {"message": {"content": json.dumps({"description": "ok-fixture"})}}
                ]
            }
            data = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, fmt, *args):
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        monkeypatch.setenv(
            "CLAUDE_PLUGIN_OPTION_vision_base_url", f"http://127.0.0.1:{port}/v1"
        )
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_model_id", "vision-model")
        monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", FAKE_KEY)
        plugin_data = tmp_path / "pdata"
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))
        vc = _reload()
        req = {
            "task": "describe",
            "image_paths": [str(png_file)],
            "user_question": "describe",
            "upload_confirmed": True,
        }
        req_path = _req_path(plugin_data, "sessMOCK")
        req_path.write_text(json.dumps(req), encoding="utf-8")
        result = vc.run_request_file(str(req_path))
        assert result["ok"] is True
        assert result["model"] == "vision-model"
        assert FAKE_KEY not in json.dumps(result)
        assert captured["path"].endswith("/chat/completions")
        assert captured["auth"] == f"Bearer {FAKE_KEY}"
        assert captured["body"]["model"] == "vision-model"
        content = captured["body"]["messages"][0]["content"]
        assert any(
            isinstance(part, dict)
            and part.get("type") == "image_url"
            and str(part.get("image_url", {}).get("url", "")).startswith(
                "data:image/png;base64,"
            )
            for part in content
        )
        assert not req_path.exists()
        assert "raw" not in result
    finally:
        server.shutdown()


def test_no_save_raw_flag_exists():
    vc = _reload()
    assert vc.SAVE_RAW_SUPPORTED is False


def test_no_redact_screenshot_module():
    assert not (SCRIPTS / "redact_screenshot.py").exists()
