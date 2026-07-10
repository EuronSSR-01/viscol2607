# Contributing

## Scope

Contributions target the Claude Code Plugin under this directory. Do not commit `_work/`, `.env`, real credentials, or private eval result metadata.

## Dev setup

- Python >= 3.10
- `pip install -e ".[dev]"` (pytest only; runtime stays stdlib-only)

## Checks before PR

```bash
claude plugin validate . --strict
python -m pytest tests -v
python scripts/scan_secrets.py .
python scripts/scan_placeholders.py .
```

## Design constraints

- OpenAI-compatible `/chat/completions` only in V1
- `--request-file` protocol; no shell interpolation of user prompts/paths
- No `redact_screenshot.py`, no `--save-raw` in V1
