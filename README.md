# VisCol

English | [简体中文](README.zh-CN.md)

VisCol is a **Claude Code Plugin** that gives coding agents reliable visual understanding through a **user-provided OpenAI-compatible multimodal** API (`/chat/completions`).

V1 supports **Claude Code only**.

## Why

Some strong coding agents lack native vision. VisCol routes visual work, requires evidence discipline, and calls a shared vision client — without guessing pixels and without shipping author API keys.

## Built-in skills

This plugin is self-contained. It includes:

- `visual-sidecar` — router / collaboration entry
- `vision-recognition` — general images, OCR, charts
- `front-devwork` — UI screenshot analysis and design-vs-actual compare
- `doctor` — offline install/config diagnostics

You do **not** need to install any author-private skills.

## Requirements

- Claude Code with Plugin support (recommend versions that honor `defaultEnabled` / `userConfig`)
- **Python >= 3.10**
- Runtime: **Python standard library only** (no pip runtime deps)

## Configure (user-owned credentials)

Enable the plugin and open `/plugin`. Provide:

1. Vision API Base URL
2. Vision Model ID
3. Vision API Key (sensitive)

**Do not paste API keys into chat.** Agents must not ask for, accept, or fill keys in conversation. If the UI prompts for configuration, pause and let the user type values in `/plugin`.

End users do **not** use `.env` for the standard path.

## Privacy, cost, and uploads

Images are sent to **your** configured third-party provider. That may incur fees and is subject to the provider’s privacy policy. VisCol requires explicit confirmation before upload (hostname, image count, types, sizes). V1 has **no** local screenshot redaction helper and **no** raw response saving.

## Quick doctor

Inside a Claude Code skill/plugin context you may use `${CLAUDE_PLUGIN_ROOT}`. In a normal terminal, run:

```bash
python "<plugin-path>/scripts/doctor.py"
```

API key status is only `SET` / `NOT SET`.

Before the first vision Write, create the requests directory. Always pass `--plugin-data-dir` explicitly (do not rely on Bash inheriting `CLAUDE_PLUGIN_DATA`):

```bash
python "<plugin-path>/scripts/vision_client.py" --plugin-data-dir "<plugin-data-path>" --ensure-requests-dir
```

Inside Claude Code skill templates, use:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/vision_client.py" --plugin-data-dir "${CLAUDE_PLUGIN_DATA}" --ensure-requests-dir
```

(`CLAUDE_PLUGIN_DATA` is substituted by Claude Code into the command text; the CLI flag carries that path into Python. The env var remains a manual-run fallback only.)

## Install

See [INSTALL_AGENT.md](INSTALL_AGENT.md) for an agent-executable install playbook.

```bash
git clone https://github.com/EuronSSR-01/viscol2607.git
```

GitHub repository: [EuronSSR-01/viscol2607](https://github.com/EuronSSR-01/viscol2607)

## License

Released under the [MIT License](LICENSE). Copyright (c) 2026 EuronSSR-01.

## Local process artifacts

`_work/` is machine-local process data and is gitignored. It is not part of the public package.

## Testing

```bash
python -m pytest tests -v
claude plugin validate . --strict
```

Default tests are offline (localhost mock only). Real Provider E2E and `claude plugin eval` are release-gate opt-in steps.
