"""OpenAI-compatible multimodal chat/completions provider (stdlib only)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float = 60.0) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    req.add_header("User-Agent", "VisCol/1.0")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        # Do not include response headers that may carry auth echoes.
        detail = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP_{e.code}:{detail}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"URL_ERROR:{type(e.reason).__name__}") from None
