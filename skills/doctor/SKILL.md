---
name: doctor
description: >
  Diagnose VisCol plugin install and vision provider configuration offline.
  Does not analyze image contents. 检查 VisCol 安装、Python 版本与 Vision 配置；
  不处理图片内容。
when_to_use: >
  Use when VisCol is unconfigured, misconfigured, or the user asks to check setup:
  /viscol:doctor, "VisCol 没法用", "检查视觉配置", "plugin not configured",
  "vision API key missing". Do not use for describing images, OCR, or UI compare.
user-invocable: true
disable-model-invocation: false
---

# VisCol Doctor

Offline install and configuration diagnostics only. **Do not analyze image contents.**

## Default command (inside Claude Code skill context)

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"
```

For a normal terminal outside the plugin session, use an absolute plugin path instead:

```bash
python "<plugin-path>/scripts/doctor.py"
```

Interpret `api_key` as only `SET` or `NOT SET`. Never print key values, lengths, prefixes, suffixes, or hashes.

If Base URL / Model ID / API Key are missing, instruct the user to open `/plugin` and enter them in the UI. **Never ask for or accept API keys in chat.** If enable/config prompts appear, pause for the user.

Checks include: plugin root, manifest, Python >= 3.10, config presence, endpoint format, scripts/schemas presence. Default mode performs **zero network** calls.

## Optional probe

`--probe` is blocked unless the user explicitly approves a minimal text-only connectivity check after you state hostname, model id, possible cost, and that no user images will be uploaded. Do not run probe in automated offline validation.
