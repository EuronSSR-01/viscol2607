"""Request-file protocol safety tests."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

RC = Path(__file__).resolve().parents[1]
SCRIPTS = RC / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

VALID_UUID = "00000000-0000-4000-8000-000000000099"


def test_request_json_must_not_contain_api_key_field(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_base_url", "http://127.0.0.1:9")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_model_id", "m")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", "sk-test-fake-key-not-real")
    plugin_data = tmp_path / "pdata"
    monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(plugin_data))
    for name in ("vision_client", "config"):
        if name in sys.modules:
            del sys.modules[name]
    vc = importlib.import_module("vision_client")
    req_dir = plugin_data / "requests"
    req_dir.mkdir(parents=True)
    req_path = req_dir / f"sessREQ-{VALID_UUID}.json"
    req_path.write_text(
        json.dumps(
            {
                "task": "describe",
                "image_paths": [],
                "user_question": "x",
                "upload_confirmed": True,
                "api_key": "should-be-rejected-field-not-a-provider-key",
            }
        ),
        encoding="utf-8",
    )
    result = vc.run_request_file(str(req_path))
    assert result["ok"] is False
    assert result["error_code"] == "INVALID_REQUEST_FILE"
    assert not req_path.exists()
