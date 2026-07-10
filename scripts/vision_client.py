"""VisCol shared vision client — OpenAI-compatible multimodal API.

Invocation contract for Claude Code skills:
1. Ensure requests dir exists (see ensure_requests_dir / Skill docs).
2. Write a request JSON via the structured Write tool to:
   ${CLAUDE_PLUGIN_DATA}/requests/<SESSION>-<UUID>.json
3. Run ONLY this fixed shell template (always pass --plugin-data-dir explicitly):
   python "${CLAUDE_PLUGIN_ROOT}/scripts/vision_client.py" --plugin-data-dir "${CLAUDE_PLUGIN_DATA}" --request-file "${CLAUDE_PLUGIN_DATA}/requests/<SESSION>-<UUID>.json"

Request JSON allowlist only: task, image_paths, user_question, upload_confirmed.
Keys are loaded only from Plugin env via config.py. V1 has no --save-raw / redaction.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from config import load_vision_config, validate_base_url
from providers.openai_compatible import post_json

SAVE_RAW_SUPPORTED = False

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_TOTAL_IMAGE_BYTES = 30 * 1024 * 1024
TASK_IMAGE_COUNTS = {
    "describe": (1, 4),
    "ocr": (1, 2),
    "compare": (2, 3),
    "ui_extract": (1, 1),
    "ui_compare": (2, 3),
}

REQUEST_ALLOWED_KEYS = frozenset({"task", "image_paths", "user_question", "upload_confirmed"})
SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "vision_api_key",
        "password",
        "token",
        "secret",
    }
)

# <session>-<uuid>.json — session is safe charset; uuid is RFC-like hex form.
REQUEST_FILENAME = re.compile(
    r"^[A-Za-z0-9._-]{1,128}-"
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    r"\.json$"
)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
WEBP_RIFF = b"RIFF"
WEBP_WEBP = b"WEBP"


def is_safe_request_filename(name: str) -> bool:
    if not name or name != Path(name).name:
        return False
    if ".." in name or "/" in name or "\\" in name:
        return False
    if any(ch in name for ch in " \t\r\n;|&$`'\""):
        return False
    return bool(REQUEST_FILENAME.match(name))


def resolve_plugin_data_root(plugin_data: str | None = None) -> Path:
    """Resolve plugin data root.

    Explicit CLI/arg value wins. Environment CLAUDE_PLUGIN_DATA is only a
    manual-run fallback and must not be required when --plugin-data-dir is set.
    """
    raw = plugin_data if plugin_data is not None else os.environ.get("CLAUDE_PLUGIN_DATA")
    if not raw or not str(raw).strip():
        raise ValueError("plugin data dir is not set (pass --plugin-data-dir or CLAUDE_PLUGIN_DATA)")
    return Path(raw).expanduser().resolve()


def ensure_requests_dir(plugin_data: str | None = None) -> Path:
    """Create <plugin-data>/requests if missing. Cross-platform mkdir."""
    root = resolve_plugin_data_root(plugin_data)
    req = root / "requests"
    req.mkdir(parents=True, exist_ok=True)
    return req.resolve()


def requests_dir(plugin_data: str | None = None) -> Path:
    return (resolve_plugin_data_root(plugin_data) / "requests").resolve()


def normalize_chat_completions_url(raw: str) -> str:
    ok, detail = validate_base_url(raw)
    if not ok:
        raise ValueError(detail)
    parts = urlsplit(detail)
    path = parts.path or ""
    if path.endswith("/"):
        path = path[:-1]
    if path.endswith("/chat/completions"):
        new_path = path
    else:
        new_path = path + "/chat/completions"
    return urlunsplit((parts.scheme, parts.netloc, new_path, "", ""))


def detect_image_mime(data: bytes) -> str | None:
    if data.startswith(PNG_MAGIC):
        return "image/png"
    if data.startswith(JPEG_MAGIC):
        return "image/jpeg"
    if len(data) >= 12 and data[:4] == WEBP_RIFF and data[8:12] == WEBP_WEBP:
        return "image/webp"
    return None


def validate_images(task: str, image_paths: list[str]) -> tuple[list[dict[str, Any]] | None, str | None]:
    if task not in TASK_IMAGE_COUNTS:
        return None, "INVALID_REQUEST_FILE"
    lo, hi = TASK_IMAGE_COUNTS[task]
    if not isinstance(image_paths, list) or not (lo <= len(image_paths) <= hi):
        return None, "INVALID_IMAGE"
    loaded: list[dict[str, Any]] = []
    total = 0
    for raw_path in image_paths:
        p = Path(raw_path)
        if not p.is_file():
            return None, "INVALID_IMAGE"
        size = p.stat().st_size
        if size <= 0 or size > MAX_IMAGE_BYTES:
            return None, "INVALID_IMAGE"
        total += size
        if total > MAX_TOTAL_IMAGE_BYTES:
            return None, "INVALID_IMAGE"
        data = p.read_bytes()
        mime = detect_image_mime(data)
        if mime is None:
            return None, "INVALID_IMAGE"
        b64 = base64.b64encode(data).decode("ascii")
        loaded.append(
            {
                "path": str(p),
                "mime": mime,
                "data_uri": f"data:{mime};base64,{b64}",
            }
        )
    return loaded, None


def build_messages(user_question: str, images: list[dict[str, Any]]) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [{"type": "text", "text": user_question or "Analyze the image(s)."}]
    for img in images:
        content.append({"type": "image_url", "image_url": {"url": img["data_uri"]}})
    return [{"role": "user", "content": content}]


def post_chat_completions(url: str, api_key: str, model: str, messages: list[dict[str, Any]]) -> dict[str, Any]:
    headers = {"Authorization": "Bearer " + api_key}
    payload = {"model": model, "messages": messages}
    return post_json(url, headers, payload)


def _contains_sensitive(obj: Any) -> bool:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in SENSITIVE_KEYS:
                return True
            if _contains_sensitive(v):
                return True
    elif isinstance(obj, list):
        return any(_contains_sensitive(x) for x in obj)
    return False


def _validate_request_object(req: Any) -> str | None:
    if not isinstance(req, dict):
        return "INVALID_REQUEST_FILE"
    if set(req.keys()) - REQUEST_ALLOWED_KEYS:
        return "INVALID_REQUEST_FILE"
    if _contains_sensitive(req):
        return "INVALID_REQUEST_FILE"
    return None


def run_request_file(request_path: str, plugin_data: str | None = None) -> dict[str, Any]:
    path = Path(request_path)
    cleanup_allowed = False
    result: dict[str, Any] = {"ok": False, "error_code": "INVALID_REQUEST_FILE"}
    try:
        # Filename check before any resolve/unlink decisions.
        if not is_safe_request_filename(path.name):
            result = {
                "ok": False,
                "error_code": "INVALID_REQUEST_FILE",
                "message": "unsafe or nonconforming request filename",
            }
            return result

        try:
            allowed = requests_dir(plugin_data)
        except ValueError:
            result = {
                "ok": False,
                "error_code": "INVALID_REQUEST_FILE",
                "message": "plugin data dir is not set (pass --plugin-data-dir or CLAUDE_PLUGIN_DATA)",
            }
            return result

        try:
            resolved = path.resolve()
        except Exception:
            result = {"ok": False, "error_code": "INVALID_REQUEST_FILE", "message": "cannot resolve path"}
            return result

        if resolved.parent != allowed:
            result = {
                "ok": False,
                "error_code": "INVALID_REQUEST_FILE",
                "message": "request file must live in <plugin-data>/requests",
            }
            return result

        if not resolved.is_file():
            result = {"ok": False, "error_code": "INVALID_REQUEST_FILE", "message": "request file missing"}
            return result

        # Boundary OK — cleanup permitted even if later processing fails.
        cleanup_allowed = True
        path = resolved

        try:
            req = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            result = {"ok": False, "error_code": "INVALID_REQUEST_FILE", "message": "invalid json"}
            return result

        bad = _validate_request_object(req)
        if bad:
            result = {"ok": False, "error_code": bad, "message": "request schema/allowlist failed"}
            return result

        cfg = load_vision_config()
        if not cfg.get("ok"):
            result = {
                "ok": False,
                "error_code": cfg.get("error_code", "CONFIG_MISSING"),
                "message": cfg.get("message", ""),
            }
            return result

        if req.get("upload_confirmed") is not True:
            result = {
                "ok": False,
                "error_code": "UPLOAD_NOT_CONFIRMED",
                "message": (
                    "Upload not confirmed. Tell the user the provider hostname, image count, "
                    "types and sizes, third-party privacy/cost risk, then set upload_confirmed=true "
                    "only after explicit confirmation."
                ),
            }
            return result

        task = req.get("task")
        image_paths = req.get("image_paths") or []
        user_question = req.get("user_question") or ""
        if not isinstance(task, str) or not isinstance(user_question, str):
            result = {"ok": False, "error_code": "INVALID_REQUEST_FILE"}
            return result

        images, err = validate_images(task, image_paths)
        if err:
            result = {"ok": False, "error_code": err}
            return result

        try:
            endpoint = normalize_chat_completions_url(cfg["base_url"])
        except ValueError:
            result = {"ok": False, "error_code": "CONFIG_INVALID_URL"}
            return result

        messages = build_messages(user_question, images or [])
        try:
            raw = post_chat_completions(endpoint, cfg["api_key"], cfg["model_id"], messages)
        except Exception:
            result = {"ok": False, "error_code": "NETWORK_ERROR"}
            return result

        text = ""
        try:
            text = raw["choices"][0]["message"]["content"]
        except Exception:
            text = ""
        result = {
            "ok": True,
            "error_code": None,
            "model": cfg["model_id"],
            "result": text,
        }
        return result
    finally:
        if cleanup_allowed:
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VisCol vision client")
    parser.add_argument(
        "--plugin-data-dir",
        default="",
        help="Plugin data root (preferred over CLAUDE_PLUGIN_DATA env)",
    )
    parser.add_argument("--request-file", default="", help="Path to request JSON")
    parser.add_argument(
        "--ensure-requests-dir",
        action="store_true",
        help="Create <plugin-data>/requests and print the path",
    )
    known, unknown = parser.parse_known_args(argv)
    if any(a in {"--save-raw", "--raw-dir"} for a in (unknown or [])):
        print(
            json.dumps(
                {
                    "ok": False,
                    "error_code": "RAW_DISABLED",
                    "message": "V1 does not support saving raw provider responses.",
                },
                ensure_ascii=False,
            )
        )
        return 2
    plugin_data = known.plugin_data_dir.strip() or None
    if known.ensure_requests_dir:
        try:
            path = ensure_requests_dir(plugin_data)
        except ValueError as e:
            print(json.dumps({"ok": False, "error_code": "INVALID_REQUEST_FILE", "message": str(e)}))
            return 1
        print(str(path))
        return 0
    if not known.request_file:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error_code": "INVALID_REQUEST_FILE",
                    "message": "provide --request-file or --ensure-requests-dir",
                }
            )
        )
        return 1
    out = run_request_file(known.request_file, plugin_data=plugin_data)
    print(json.dumps(out, ensure_ascii=False))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
