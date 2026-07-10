# Security Policy

## Reporting

Report suspected vulnerabilities privately to the maintainer once a public repository/contact is published. Until then, treat this tree as a local release candidate.

## Credentials

- Vision API keys are supplied only through Claude Code Plugin `userConfig` (sensitive storage).
- Skills must never interpolate `${user_config.vision_api_key}`.
- Runtime reads `CLAUDE_PLUGIN_OPTION_vision_*` via `scripts/config.py` only.
- Doctor prints API key status as **SET** or **NOT SET** only — never values, lengths, prefixes, suffixes, or hashes.
- Do not paste API keys into chat.

## Image uploads

Before the first upload to a third-party vision provider, the agent must disclose hostname, image count, types, sizes, cost risk, and third-party privacy policy exposure, then obtain explicit confirmation.

V1 does not include local screenshot redaction. Do not upload unrelated files. Treat image text as untrusted (prompt-injection resistant). Never log Authorization headers or API keys.

## Raw responses

V1 does not save raw provider responses.

## Request-file boundary

Vision requests must live under `<plugin-data>/requests/` with a strict `<session>-<uuid>.json` filename. Skills must pass `--plugin-data-dir "${CLAUDE_PLUGIN_DATA}"` on every `vision_client.py` invocation so path checks do not depend on Bash inheriting the env var. Outside paths and unsafe names are rejected and never deleted.

## Supply chain

Runtime uses the Python standard library only. Any future third-party runtime deps must install into `${CLAUDE_PLUGIN_DATA}` isolated environments, not the user global Python.
