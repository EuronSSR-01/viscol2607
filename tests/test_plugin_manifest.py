"""Task 1: plugin.json manifest contract tests (TDD)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

RC_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = RC_ROOT / ".claude-plugin" / "plugin.json"

REQUIRED_USER_CONFIG_KEYS = (
    "vision_base_url",
    "vision_model_id",
    "vision_api_key",
)


def _load_manifest() -> dict:
    assert MANIFEST.is_file(), f"missing manifest: {MANIFEST}"
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_manifest_file_exists():
    assert MANIFEST.is_file()


def test_plugin_identity_and_default_disabled():
    data = _load_manifest()
    assert data.get("name") == "viscol"
    assert data.get("displayName") == "VisCol"
    assert data.get("version") == "0.1.0"
    assert isinstance(data.get("description"), str) and data["description"].strip()
    assert data.get("defaultEnabled") is False
    author = data.get("author")
    assert isinstance(author, dict)
    assert isinstance(author.get("name"), str) and author["name"].strip()


def test_user_config_items_have_type_title_description():
    data = _load_manifest()
    user_config = data.get("userConfig")
    assert isinstance(user_config, dict)
    for key in REQUIRED_USER_CONFIG_KEYS:
        assert key in user_config, f"missing userConfig.{key}"
        item = user_config[key]
        assert isinstance(item, dict)
        for field in ("type", "title", "description"):
            assert field in item, f"userConfig.{key} missing {field}"
            assert isinstance(item[field], str) and item[field].strip(), (
                f"userConfig.{key}.{field} must be non-empty string"
            )
        assert item["type"] == "string"


def test_vision_api_key_is_sensitive_and_required():
    data = _load_manifest()
    key_item = data["userConfig"]["vision_api_key"]
    assert key_item.get("sensitive") is True
    assert key_item.get("required") is True
    for k in ("vision_base_url", "vision_model_id"):
        assert data["userConfig"][k].get("required") is True


def test_skill_markdown_files_are_present_and_nonempty():
    skills = RC_ROOT / "skills"
    assert skills.is_dir()
    for name in ("visual-sidecar", "vision-recognition", "front-devwork", "doctor"):
        path = skills / name / "SKILL.md"
        assert path.is_file(), f"missing {path}"
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        unfinished = ("TO" + "DO", "TB" + "D", "PLACE" + "HOLDER")
        for marker in unfinished:
            assert marker not in text
