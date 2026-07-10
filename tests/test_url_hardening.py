"""Failing tests for tightened Base URL rules."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

RC = Path(__file__).resolve().parents[1]
SCRIPTS = RC / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _reload_config():
    if "config" in sys.modules:
        del sys.modules["config"]
    return importlib.import_module("config")


def _reload_vc():
    for name in ("vision_client", "config"):
        if name in sys.modules:
            del sys.modules[name]
    return importlib.import_module("vision_client")


@pytest.mark.parametrize(
    "url",
    [
        "https://user:pass@example.com/v1",
        "https://example.com/v1?x=1",
        "https://example.com/v1#frag",
        "https://example.com/v1\n",
        "https:///v1",
        "http://example.com/v1",
    ],
)
def test_validate_base_url_rejects_unsafe(url):
    cfg = _reload_config()
    ok, _ = cfg.validate_base_url(url)
    assert ok is False


def test_normalize_uses_urlsplit_and_no_duplicate():
    vc = _reload_vc()
    assert (
        vc.normalize_chat_completions_url("https://example.com/v1")
        == "https://example.com/v1/chat/completions"
    )
    assert (
        vc.normalize_chat_completions_url("https://example.com/v1/")
        == "https://example.com/v1/chat/completions"
    )
    assert (
        vc.normalize_chat_completions_url("https://example.com/v1/chat/completions")
        == "https://example.com/v1/chat/completions"
    )


def test_normalize_rejects_userinfo_and_query():
    vc = _reload_vc()
    with pytest.raises(ValueError):
        vc.normalize_chat_completions_url("https://u:p@example.com/v1")
    with pytest.raises(ValueError):
        vc.normalize_chat_completions_url("https://example.com/v1?q=1")
