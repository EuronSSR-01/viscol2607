"""Task 4: routing expectations from skill docs (offline contract)."""

from __future__ import annotations

from pathlib import Path

from frontmatter_util import load_skill_frontmatter, skill_body

RC = Path(__file__).resolve().parents[1]
SKILLS = RC / "skills"


def test_config_missing_routes_to_doctor():
    body = skill_body(SKILLS / "visual-sidecar" / "SKILL.md").lower()
    assert "doctor" in body
    assert "config" in body or "unconfigured" in body or "not configured" in body


def test_general_image_prefers_vision_recognition_not_doctor():
    vr = load_skill_frontmatter(SKILLS / "vision-recognition" / "SKILL.md")
    doc = load_skill_frontmatter(SKILLS / "doctor" / "SKILL.md")
    vr_blob = vr["description"] + vr["when_to_use"]
    doc_blob = doc["description"] + doc["when_to_use"]
    assert ("OCR" in vr_blob) or ("photo" in vr_blob.lower()) or ("识图" in vr_blob)
    assert ("does not analyze image contents" in doc_blob.lower()) or ("不处理图片内容" in doc_blob)
    assert "describe this photo" not in doc_blob.lower()


def test_ui_tasks_map_to_front_devwork():
    fd = load_skill_frontmatter(SKILLS / "front-devwork" / "SKILL.md")
    blob = fd["description"] + fd["when_to_use"]
    assert ("UI" in blob) or ("设计" in blob)
    assert ("compare" in blob.lower()) or ("对比" in blob)


def test_sidecar_is_router():
    fm = load_skill_frontmatter(SKILLS / "visual-sidecar" / "SKILL.md")
    blob = fm["description"] + fm["when_to_use"]
    assert ("route" in blob.lower()) or ("路由" in blob)
