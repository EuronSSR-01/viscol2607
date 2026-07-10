"""Scan public package files for unfinished markers.

Self-scan safe: patterns are composed at runtime so this file does not contain
literal unfinished markers as whole words in a hittable form.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKIP_DIR_NAMES = {"_work", "__pycache__", ".pytest_cache"}
# Fixture dir used only to prove true positives in unit tests.
SKIP_REL_PREFIXES = (
    "tests/fixtures/placeholder_scan/",
)

# Build patterns without writing the full tokens as adjacent letters in source comments.
_MARKERS = [
    "".join(("TO", "DO")),
    "".join(("TB", "D")),
    "".join(("PLACE", "HOLDER")),
]
PATTERNS = [
    re.compile(r"\b" + re.escape(m) + r"\b")
    for m in _MARKERS
]


def scan_file(path: Path, root: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix()
    # Skip allowlisted fixture prefix
    for pref in SKIP_REL_PREFIXES:
        if rel.replace("\\", "/").startswith(pref):
            return []
    hits: list[dict] = []
    for i, line in enumerate(text.splitlines(), start=1):
        for rule, pat in zip([m.lower() for m in _MARKERS], PATTERNS):
            if pat.search(line):
                hits.append({"rule": rule.lower(), "path": rel, "line": i})
                break
    return hits


def scan_tree(root: Path) -> list[dict]:
    root = root.resolve()
    hits: list[dict] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if "_work" in rel_parts or set(rel_parts) & SKIP_DIR_NAMES:
            continue
        if path.suffix.lower() not in {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".ts", ".txt"}:
            continue
        hits.extend(scan_file(path, root))
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    hits = scan_tree(args.root)
    if not hits:
        print("0 placeholder hits")
        return 0
    for h in hits:
        print(f"{h['rule']}  {h['path']}:{h['line']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
