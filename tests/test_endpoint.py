"""Endpoint helper tests."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

RC = Path(__file__).resolve().parents[1]
SCRIPTS = RC / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def test_http_non_local_rejected_in_normalize():
    if "vision_client" in sys.modules:
        del sys.modules["vision_client"]
    vc = importlib.import_module("vision_client")
    try:
        vc.normalize_chat_completions_url("http://example.com/v1")
        raised = False
    except ValueError:
        raised = True
    assert raised
