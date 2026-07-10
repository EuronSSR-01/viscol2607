"""Task 7: public docs contract tests."""

from __future__ import annotations

import json
from pathlib import Path

RC = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = (
    "README.md",
    "INSTALL_AGENT.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    ".gitignore",
    ".gitattributes",
)


def test_required_docs_exist():
    for name in REQUIRED_DOCS:
        assert (RC / name).is_file(), name


def test_readme_key_statements():
    text = (RC / "README.md").read_text(encoding="utf-8")
    for needle in (
        "Claude Code",
        "OpenAI-compatible",
        "/chat/completions",
        "Python >= 3.10",
        "/plugin",
        "Do not paste API keys into chat",
        "visual-sidecar",
        "vision-recognition",
        "front-devwork",
        "doctor",
        "_work",
        "LICENSE",
        "GitHub",
    ):
        assert needle in text
    assert "does not include vision-recognition" not in text.lower()
    banned = "E:" + "\\VibeCoding"
    assert banned not in text
    assert "E:/" + "VibeCoding" not in text
    assert "sk-" not in text


def test_install_agent_steps():
    text = (RC / "INSTALL_AGENT.md").read_text(encoding="utf-8")
    for needle in (
        "Python",
        "~/.claude/skills/viscol",
        "claude plugin validate",
        "--strict",
        "claude plugin list --json",
        "/plugin",
        "API Key",
        "must not",
        "/viscol:doctor",
    ):
        assert needle in text
    assert "paste" in text.lower() or "聊天" in text


def test_gitignore_excludes_work_and_env():
    text = (RC / ".gitignore").read_text(encoding="utf-8")
    assert "_work/" in text
    assert ".env" in text


def test_mit_license_and_repository_metadata():
    license_text = (RC / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in license_text
    assert "Copyright (c) 2026 EuronSSR-01" in license_text

    manifest = json.loads((RC / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["license"] == "MIT"
    assert manifest["repository"] == "https://github.com/EuronSSR-01/viscol2607"
    assert manifest["homepage"] == "https://github.com/EuronSSR-01/viscol2607"


def test_security_mentions_upload_and_keys():
    text = (RC / "SECURITY.md").read_text(encoding="utf-8")
    assert "third-party" in text.lower() or "第三方" in text
    assert "SET" in text and "NOT SET" in text
