"""RED: --plugin-data-dir must work without CLAUDE_PLUGIN_DATA in the process env."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

RC = Path(__file__).resolve().parents[1]
SCRIPTS = RC / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _reload_vc():
    for name in ("vision_client", "config"):
        if name in sys.modules:
            del sys.modules[name]
    return importlib.import_module("vision_client")


def _strip_plugin_data_env(env: dict[str, str]) -> dict[str, str]:
    out = {k: v for k, v in env.items() if k != "CLAUDE_PLUGIN_DATA"}
    out.pop("CLAUDE_PLUGIN_DATA", None)
    return out


def test_ensure_requests_dir_via_cli_without_env(tmp_path):
    plugin_data = tmp_path / "pdata"
    plugin_data.mkdir()
    env = _strip_plugin_data_env(dict(os.environ))
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "vision_client.py"),
            "--plugin-data-dir",
            str(plugin_data),
            "--ensure-requests-dir",
        ],
        cwd=str(RC),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    req = (plugin_data / "requests").resolve()
    assert req.is_dir()
    assert Path(proc.stdout.strip()).resolve() == req


def test_request_file_boundary_via_cli_without_env(tmp_path, monkeypatch):
    """In-process: CLI-resolved plugin_data root gates path checks."""
    monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
    vc = _reload_vc()
    plugin_data = tmp_path / "pdata"
    req_dir = plugin_data / "requests"
    req_dir.mkdir(parents=True)
    name = f"sess-{uuid.uuid4()}.json"
    inside = req_dir / name
    inside.write_text(
        json.dumps(
            {
                "task": "describe",
                "image_paths": [],
                "user_question": "x",
                "upload_confirmed": False,
            }
        ),
        encoding="utf-8",
    )
    # Boundary OK path: should pass filename+dir checks then fail later on images/config —
    # but must NOT be INVALID_REQUEST_FILE for path boundary.
    out = vc.run_request_file(str(inside), plugin_data=str(plugin_data))
    # Boundary accepted → later stage error (upload gate / config / images), not path reject.
    assert out.get("error_code") in {
        "INVALID_IMAGE",
        "CONFIG_MISSING",
        "CONFIG_INVALID_URL",
        "UPLOAD_NOT_CONFIRMED",
    }


def test_outside_request_file_rejected_and_not_deleted_via_cli(tmp_path):
    plugin_data = tmp_path / "pdata"
    (plugin_data / "requests").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    name = f"sess-{uuid.uuid4()}.json"
    victim = outside / name
    victim.write_text('{"task":"describe","image_paths":[],"user_question":"x","upload_confirmed":false}', encoding="utf-8")

    env = _strip_plugin_data_env(dict(os.environ))
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "vision_client.py"),
            "--plugin-data-dir",
            str(plugin_data),
            "--request-file",
            str(victim),
        ],
        cwd=str(RC),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode != 0
    data = json.loads(proc.stdout)
    assert data.get("ok") is False
    assert data.get("error_code") == "INVALID_REQUEST_FILE"
    assert victim.is_file(), "outside request file must not be deleted"


def test_unsafe_filename_not_deleted_via_cli(tmp_path):
    plugin_data = tmp_path / "pdata"
    req = plugin_data / "requests"
    req.mkdir(parents=True)
    bad = req / "not-a-uuid.json"
    bad.write_text("{}", encoding="utf-8")

    env = _strip_plugin_data_env(dict(os.environ))
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "vision_client.py"),
            "--plugin-data-dir",
            str(plugin_data),
            "--request-file",
            str(bad),
        ],
        cwd=str(RC),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode != 0
    data = json.loads(proc.stdout)
    assert data.get("error_code") == "INVALID_REQUEST_FILE"
    assert bad.is_file()


def test_cli_plugin_data_dir_overrides_env(tmp_path, monkeypatch):
    wrong = tmp_path / "wrong"
    right = tmp_path / "right"
    (wrong / "requests").mkdir(parents=True)
    right.mkdir()
    env = dict(os.environ)
    env["CLAUDE_PLUGIN_DATA"] = str(wrong)
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "vision_client.py"),
            "--plugin-data-dir",
            str(right),
            "--ensure-requests-dir",
        ],
        cwd=str(RC),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0
    assert (right / "requests").is_dir()
    assert Path(proc.stdout.strip()).resolve() == (right / "requests").resolve()
