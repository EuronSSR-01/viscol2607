"""Task 6: static validation of native Claude Code eval cases."""

from __future__ import annotations

from pathlib import Path

RC = Path(__file__).resolve().parents[1]
EVALS = RC / "evals"

REQUIRED_DIRS = {
    "should-trigger-en-image",
    "should-not-trigger-pure-text",
    "should-trigger-zh-ocr",
    "should-trigger-ui-compare",
    "should-trigger-zh-chart",
    "should-not-trigger-format-convert",
    "config-missing",
    "upload-unconfirmed",
    "prompt-injection-in-image",
    "doctor-not-for-describe",
    "should-trigger-en-ocr",
    "should-not-trigger-native-vision-claim",
}


def _case_dirs():
    return [p for p in EVALS.iterdir() if p.is_dir() and not p.name.startswith(".")]


def test_eval_cases_exist_minimum_coverage():
    names = {p.name for p in _case_dirs()}
    assert REQUIRED_DIRS.issubset(names)
    for d in _case_dirs():
        prompt = d / "prompt.md"
        case = d / "case.yaml"
        graders = list((d / "graders").glob("*.md")) if (d / "graders").is_dir() else []
        assert prompt.is_file() or case.is_file()
        if prompt.is_file():
            assert graders, f"{d.name} missing graders"


def test_cases_are_utf8_relative_and_private_free():
    for path in EVALS.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8")
        banned = "E:" + "\\VibeCoding"
        assert banned not in text
        assert "E:/" + "VibeCoding" not in text
        assert "sk-" not in text
        assert "total_cost_usd" not in text


def test_coverage_diff_report_exists():
    report = RC / "_work" / "evals-coverage-diff.md"
    assert report.is_file()
    text = report.read_text(encoding="utf-8")
    for needle in ("已保留", "新增", "发布前", "claude plugin eval"):
        assert needle in text
