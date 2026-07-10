# Changelog

## 0.1.0 — GitHub release candidate

- Self-contained Claude Code Plugin (`viscol`) with four skills
- Plugin `userConfig` for Base URL / Model ID / API Key (`sensitive`)
- Shared stdlib vision client with `--request-file` protocol and localhost mock tests
- Explicit `--plugin-data-dir` on vision_client (CLI preferred over env inheritance)
- Base URL validation fail-closed on malformed ports / IPv6 without raising
- Offline doctor; native eval cases (static only in this build)
- MIT License and public repository metadata for `EuronSSR-01/viscol2607`
