"""Minimal YAML-ish frontmatter loader for tests (stdlib only)."""

from __future__ import annotations

from pathlib import Path


def load_skill_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"{path} missing frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise AssertionError(f"{path} unterminated frontmatter")
    block = text[4:end]
    data: dict = {}
    key = None
    acc: list[str] = []
    for line in block.splitlines():
        if key and (line.startswith("  ") or line.startswith("\t")):
            acc.append(line.strip())
            continue
        if key is not None:
            data[key] = _coerce("\n".join(acc).strip())
            key = None
            acc = []
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip()
        if v in (">", "|", ""):
            key = k
            acc = []
        else:
            data[k] = _coerce(v.strip().strip('"').strip("'"))
    if key is not None:
        data[key] = _coerce("\n".join(acc).strip())
    return data


def _coerce(value: str):
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def skill_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---\n", 4)
    return text[end + 5 :]
