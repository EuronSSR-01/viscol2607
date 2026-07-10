"""RED: malformed Base URLs must not raise; Doctor must emit JSON + CONFIG_INVALID_URL."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

RC = Path(__file__).resolve().parents[1]
SCRIPTS = RC / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

FAKE_KEY = "sk-test-fake-key-not-real"

MALFORMED_URLS = [
    "https://example.com:bad/v1",
    "https://example.com:70000/v1",
    "https://[::1/v1",
]


def _reload_config():
    if "config" in sys.modules:
        del sys.modules["config"]
    return importlib.import_module("config")


@pytest.mark.parametrize("url", MALFORMED_URLS)
def test_validate_base_url_malformed_returns_false_no_raise(url):
    cfg = _reload_config()
    ok, reason = cfg.validate_base_url(url)
    assert ok is False
    assert isinstance(reason, str) and reason


@pytest.mark.parametrize("url", MALFORMED_URLS)
def test_load_vision_config_malformed_url_no_crash(monkeypatch, url):
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_base_url", url)
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_model_id", "vision-model")
    monkeypatch.setenv("CLAUDE_PLUGIN_OPTION_vision_api_key", FAKE_KEY)
    cfg = _reload_config()
    out = cfg.load_vision_config()
    assert out["ok"] is False
    assert out["error_code"] == "CONFIG_INVALID_URL"


@pytest.mark.parametrize("url", MALFORMED_URLS)
def test_doctor_subprocess_malformed_url_json_nonzero_no_traceback(url):
    env = {
        "CLAUDE_PLUGIN_OPTION_vision_base_url": url,
        "CLAUDE_PLUGIN_OPTION_vision_model_id": "vision-model",
        "CLAUDE_PLUGIN_OPTION_vision_api_key": FAKE_KEY,
        "PYTHONUTF8": "1",
    }
    # Inherit PATH etc. but override vision options; strip real keys if present.
    full = dict(**{k: v for k, v in __import__("os").environ.items() if not k.startswith("CLAUDE_PLUGIN_OPTION_")})
    full.update(env)
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "doctor.py")],
        cwd=str(RC),
        env=full,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode != 0
    combined = (proc.stdout or "") + (proc.stderr or "")
    assert "Traceback" not in combined
    assert "ValueError" not in combined
    data = json.loads(proc.stdout)
    assert data.get("config_error_code") == "CONFIG_INVALID_URL"
    assert data.get("endpoint_format_ok") is False
