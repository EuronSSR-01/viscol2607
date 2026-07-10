"""Task 4: skill frontmatter and anti-overlap routing contract tests."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from frontmatter_util import load_skill_frontmatter

RC = Path(__file__).resolve().parents[1]
SKILLS = RC / "skills"
NAMES = ("visual-sidecar", "vision-recognition", "front-devwork", "doctor")


@pytest.fixture(scope="module")
def skill_files():
    return {n: SKILLS / n / "SKILL.md" for n in NAMES}


def test_all_skill_files_exist(skill_files):
    for n, p in skill_files.items():
        assert p.is_file(), f"missing {n}"


def test_frontmatter_fields(skill_files):
    for n, p in skill_files.items():
        fm = load_skill_frontmatter(p)
        assert fm.get("name") == n
        assert isinstance(fm.get("description"), str) and fm["description"].strip()
        assert isinstance(fm.get("when_to_use"), str) and fm["when_to_use"].strip()
        assert fm.get("user-invocable") is True
        assert "disable-model-invocation" in fm
        blob = fm["description"] + "\n" + fm["when_to_use"]
        assert re.search(r"[A-Za-z]", blob)
        assert re.search(r"[\u4e00-\u9fff]", blob)


def test_doctor_model_invocable(skill_files):
    fm = load_skill_frontmatter(skill_files["doctor"])
    assert fm.get("disable-model-invocation") is False


def test_no_user_config_api_key_interpolation(skill_files):
    for p in skill_files.values():
        text = p.read_text(encoding="utf-8")
        assert "${user_config.vision_api_key}" not in text


def test_skills_use_plugin_root_and_request_file(skill_files):
    for n, p in skill_files.items():
        text = p.read_text(encoding="utf-8")
        assert "${CLAUDE_PLUGIN_ROOT}" in text
        if n != "doctor":
            assert "--request-file" in text
            assert "Write" in text or "write a request" in text.lower()


def test_no_author_absolute_paths(skill_files):
    banned_a = "E:" + "\\VibeCoding"
    banned_b = "E:/" + "VibeCoding"
    for p in skill_files.values():
        text = p.read_text(encoding="utf-8")
        assert banned_a not in text
        assert banned_b not in text
