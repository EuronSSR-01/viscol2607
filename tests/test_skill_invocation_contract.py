"""Task 4: invocation contract — fixed shell template + request-file."""

from __future__ import annotations

from pathlib import Path

RC = Path(__file__).resolve().parents[1]


def test_business_skills_document_fixed_shell_template():
    for name in ("visual-sidecar", "vision-recognition", "front-devwork"):
        text = (RC / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        assert '--plugin-data-dir "${CLAUDE_PLUGIN_DATA}" --ensure-requests-dir' in text
        assert (
            'python "${CLAUDE_PLUGIN_ROOT}/scripts/vision_client.py" '
            '--plugin-data-dir "${CLAUDE_PLUGIN_DATA}" --request-file '
            '"${CLAUDE_PLUGIN_DATA}/requests/<SESSION>-<UUID>.json"'
        ) in text
        assert "upload_confirmed" in text
        assert "api_key" not in text.lower() or "must not contain api_key" in text.lower() or "不得包含" in text


def test_doctor_uses_doctor_script():
    text = (RC / "skills" / "doctor" / "SKILL.md").read_text(encoding="utf-8")
    assert 'python "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"' in text
    assert "--probe" in text  # documented as requiring approval
