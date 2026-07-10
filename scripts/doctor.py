"""VisCol offline doctor diagnostics.

Default mode never opens network connections.
API key status is only SET / NOT SET.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from config import (
    ENV_BASE_URL,
    ENV_MODEL_ID,
    api_key_status,
    load_vision_config,
    validate_base_url,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_SCRIPTS = (
    "scripts/config.py",
    "scripts/doctor.py",
    "scripts/vision_client.py",
    "scripts/providers/openai_compatible.py",
)


def _python_ok() -> tuple[bool, str]:
    ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ok = sys.version_info >= (3, 10)
    return ok, ver


def _path_ok(rel: str) -> bool:
    return (PLUGIN_ROOT / rel).exists()


def run_doctor() -> dict[str, Any]:
    python_ok, python_version = _python_ok()
    cfg = load_vision_config()

    base_raw = (os.environ.get(ENV_BASE_URL) or "").strip()
    model_raw = (os.environ.get(ENV_MODEL_ID) or "").strip()

    base_set = bool(base_raw)
    model_set = bool(model_raw)
    endpoint_format_ok = False
    if base_set:
        endpoint_format_ok, _ = validate_base_url(base_raw)

    manifest = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    manifest_ok = False
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_ok = (
                isinstance(data, dict)
                and data.get("name") == "viscol"
                and isinstance(data.get("userConfig"), dict)
            )
        except Exception:
            manifest_ok = False

    scripts_ok = all(_path_ok(p) for p in REQUIRED_SCRIPTS)
    schemas_dir_exists = (PLUGIN_ROOT / "schemas").is_dir() and any(
        (PLUGIN_ROOT / "schemas").glob("*.schema.json")
    )

    report: dict[str, Any] = {
        "plugin_root_exists": PLUGIN_ROOT.is_dir(),
        "manifest_ok": manifest_ok,
        "python_ok": python_ok,
        "python_version": python_version,
        "base_url_set": base_set,
        "model_id_set": model_set,
        "api_key": api_key_status(),
        "endpoint_format_ok": endpoint_format_ok,
        "scripts_ok": scripts_ok,
        "schemas_dir_exists": schemas_dir_exists,
        "config_error_code": cfg.get("error_code"),
        "network_probe": "skipped_default_offline",
    }
    return report


def is_healthy(report: dict[str, Any]) -> bool:
    return bool(
        report.get("python_ok")
        and report.get("manifest_ok")
        and report.get("config_error_code") == "CONFIG_OK"
        and report.get("base_url_set")
        and report.get("model_id_set")
        and report.get("api_key") == "SET"
        and report.get("endpoint_format_ok")
        and report.get("scripts_ok")
        and report.get("schemas_dir_exists")
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--probe" in argv:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error_code": "PROBE_REQUIRES_EXPLICIT_USER_APPROVAL",
                    "message": (
                        "Doctor probe is disabled in default mode. "
                        "Do not run --probe unless the user explicitly approved "
                        "a minimal text-only connectivity check."
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    report = run_doctor()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if is_healthy(report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
