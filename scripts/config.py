"""VisCol vision provider configuration loader.

Reads only Claude Code Plugin-injected environment variables.
Never reads .env files. Never logs API key values.
"""

from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import urlsplit

ENV_BASE_URL = "CLAUDE_PLUGIN_OPTION_vision_base_url"
ENV_MODEL_ID = "CLAUDE_PLUGIN_OPTION_vision_model_id"
ENV_API_KEY = "CLAUDE_PLUGIN_OPTION_vision_api_key"

CONFIG_MISSING_MESSAGE = (
    "VisCol is installed but visual provider is not configured.\n"
    "Open /plugin and configure Vision API Base URL, Vision Model ID, and Vision API Key.\n"
    "Do not paste API keys into chat."
)

_CTRL = re.compile(r"[\x00-\x1f\x7f]")


def _strip(value: str | None) -> str:
    return (value or "").strip()


def validate_base_url(raw: str) -> tuple[bool, str]:
    """Return (ok, normalized_url_or_reason).

    Never raises: malformed ports, invalid IPv6 brackets, and other urlsplit
    ValueErrors are converted to a stable (False, reason) result.
    """
    if raw is None:
        return False, "empty"
    # Reject control characters / newlines before any stripping normalization.
    if _CTRL.search(raw):
        return False, "control_chars"
    url = raw.strip()
    if not url:
        return False, "empty"

    try:
        parts = urlsplit(url)
    except ValueError:
        return False, "parse"

    if parts.scheme not in ("https", "http"):
        return False, "scheme"

    try:
        if parts.username is not None or parts.password is not None:
            return False, "userinfo"
        if parts.query:
            return False, "query"
        if parts.fragment:
            return False, "fragment"
        host = (parts.hostname or "").lower()
        if not host:
            return False, "hostname"
        if parts.scheme == "http" and host not in ("127.0.0.1", "localhost"):
            return False, "http_non_local"
        # Accessing .port may raise ValueError for non-int / out-of-range ports.
        port = parts.port
    except ValueError:
        return False, "parse"

    if port is not None and not (1 <= port <= 65535):
        return False, "port"
    netloc = host
    if port is not None:
        netloc = f"{host}:{port}"
    # Preserve bracket form for IPv6 hosts in the normalized URL.
    if ":" in host and not host.startswith("["):
        netloc = f"[{host}]" if port is None else f"[{host}]:{port}"
    normalized = f"{parts.scheme}://{netloc}{parts.path or ''}"
    return True, normalized


def load_vision_config() -> dict[str, Any]:
    base_url = _strip(os.environ.get(ENV_BASE_URL))
    model_id = _strip(os.environ.get(ENV_MODEL_ID))
    api_key = _strip(os.environ.get(ENV_API_KEY))

    if not base_url or not model_id or not api_key:
        return {
            "ok": False,
            "error_code": "CONFIG_MISSING",
            "message": CONFIG_MISSING_MESSAGE,
        }

    ok, detail = validate_base_url(base_url)
    if not ok:
        return {
            "ok": False,
            "error_code": "CONFIG_INVALID_URL",
            "message": (
                "Vision API Base URL is invalid. Use an https:// OpenAI-compatible "
                "base URL without userinfo/query/fragment "
                "(http:// only allowed for localhost mock servers)."
            ),
        }

    return {
        "ok": True,
        "error_code": "CONFIG_OK",
        "base_url": detail,
        "model_id": model_id,
        "api_key": api_key,
    }


def api_key_status() -> str:
    """Return SET or NOT SET only — never the key or any identifying fragment."""
    return "SET" if _strip(os.environ.get(ENV_API_KEY)) else "NOT SET"
