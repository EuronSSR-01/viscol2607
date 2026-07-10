"""Scan release-candidate public files for secret-like literals and private paths.

Output only: rule, relative path, line number. Never print match text.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WHITELIST_EXACT = {
    "sk-test-fake-key-not-real",
}

SKIP_DIR_NAMES = {"_work", "__pycache__", ".pytest_cache", "node_modules"}

BEARER_LITERAL = re.compile(r"(?i)Bearer\s+(?:sk|tp)-[A-Za-z0-9\-_]{12,}")
KEY_LITERAL = re.compile(r"(?<![A-Za-z0-9])(?:sk|tp)-[A-Za-z0-9\-_]{16,}")
AKIA = re.compile(r"(?<![A-Za-z0-9])AKIA[A-Z0-9]{16}")
PRIVATE_PATH = re.compile(
    r"(?i)"
    + re.escape("E:")
    + r"[/\\]+"
    + re.escape("Vibe")
    + re.escape("Coding")
    + r"|"
    + r"/"
    + re.escape("Users")
    + r"/[^/\s\"']+/"
    + r"|"
    + r"/"
    + re.escape("home")
    + r"/[^/\s\"']+/"
)
# EuronSSR-01 is the repository owner's deliberately public GitHub identity.
# Continue rejecting the bare local username, including Windows user paths.
PRIVATE_USER = re.compile(
    r"(?i)\b" + re.escape("Euron") + re.escape("SSR") + r"\b(?!-01\b)"
)
DYNAMIC_AUTH = re.compile(
    r"""Authorization["']\s*:\s*["']Bearer\s*["']\s*\+"""
)


def scan_file(path: Path, root: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    hits: list[dict] = []
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.name
    for i, line in enumerate(text.splitlines(), start=1):
        if BEARER_LITERAL.search(line) and not DYNAMIC_AUTH.search(line):
            keys = [m.group(0) for m in KEY_LITERAL.finditer(line)]
            if not keys or any(k not in WHITELIST_EXACT for k in keys):
                # Bearer with non-whitelist credential
                if not all(k in WHITELIST_EXACT for k in KEY_LITERAL.findall(line) or []):
                    # finditer groups - fix
                    key_vals = [m.group(0) for m in KEY_LITERAL.finditer(line)]
                    if key_vals and all(k in WHITELIST_EXACT for k in key_vals):
                        pass
                    else:
                        hits.append({"rule": "hardcoded_bearer", "path": rel, "line": i})

        key_vals = [m.group(0) for m in KEY_LITERAL.finditer(line)]
        if key_vals and not all(k in WHITELIST_EXACT for k in key_vals):
            hits.append({"rule": "key_like_literal", "path": rel, "line": i})

        if AKIA.search(line):
            hits.append({"rule": "aws_akia", "path": rel, "line": i})
        if PRIVATE_PATH.search(line):
            hits.append({"rule": "private_absolute_path", "path": rel, "line": i})
        if PRIVATE_USER.search(line):
            hits.append({"rule": "private_username", "path": rel, "line": i})
    return hits


def scan_tree(root: Path) -> list[dict]:
    root = root.resolve()
    hits: list[dict] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if "_work" in rel_parts or any(p in SKIP_DIR_NAMES for p in rel_parts):
            continue
        if path.suffix.lower() not in {
            ".py",
            ".md",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ts",
            ".txt",
            ".example",
            ".gitignore",
            ".gitattributes",
            ".html",
            ".css",
            ".sh",
            ".ps1",
            ".bat",
            ".cmd",
            ".xml",
            ".ini",
            ".cfg",
        } and path.name not in {".gitignore", ".gitattributes"}:
            continue
        hits.extend(scan_file(path, root))
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args(argv)
    hits = scan_tree(args.root)
    if not hits:
        print("0 secret-like hits")
        return 0
    for h in hits:
        print(f"{h['rule']}  {h['path']}:{h['line']}  [value redacted]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
