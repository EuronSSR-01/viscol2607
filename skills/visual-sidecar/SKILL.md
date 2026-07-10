---
name: visual-sidecar
description: >
  Route visual work for Claude Code via VisCol. Use when the user needs image
  understanding, OCR, charts, UI screenshot review, visual diff, or frontend
  visual fixes. 在用户需要识图、OCR、图表、UI 截图评审、视觉对比或前端视觉修复时
  作为 VisCol 总入口与路由器。
when_to_use: >
  Trigger on: "look at this image", "what's in the screenshot", "OCR this",
  "compare these UIs", "帮我看看这张图", "识别文字", "对比设计稿和实现",
  "页面和设计不一样". Prefer this router when the task type is unclear.
  Do not use for pure text coding with no image/UI visual input.
user-invocable: true
disable-model-invocation: false
---

# VisCol Visual Sidecar

You are the VisCol router. You do **not** call vision HTTP APIs yourself and you never invent image contents.

## Configuration gate

Before any visual work, ensure the plugin vision provider is configured (Base URL, Model ID, API Key via `/plugin` UI only).

If configuration is missing or invalid:

1. Invoke `/viscol:doctor` (or run the doctor script below).
2. Tell the user to open `/plugin` and enter Base URL, Model ID, and API Key themselves.
3. **Never ask for, accept, or fill an API Key in chat.** If the UI prompts for these values, pause and wait for the user.

Doctor command:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"
```

## Routing

| User need | Route to |
|---|---|
| Photo/diagram/OCR/chart/receipt/non-UI document screenshot | `vision-recognition` |
| UI screenshot analysis, design-vs-actual, layout/CSS visual repair | `front-devwork` |
| Unclear visual task | stay here, decide, then hand off |
| Install/config failure | `doctor` |

Do not send ordinary describe/OCR tasks to `doctor`.

## Shared vision call protocol

Business skills must:

1. Ensure the requests directory exists (first use / after install) so Write does not fail:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/vision_client.py" --plugin-data-dir "${CLAUDE_PLUGIN_DATA}" --ensure-requests-dir
```

2. Explain upload risk (hostname, image count/types/sizes, third-party cost/privacy).
3. Get explicit user confirmation before sending images.
4. Use the structured **Write** tool to create a request JSON at:
   `${CLAUDE_PLUGIN_DATA}/requests/<CLAUDE_SESSION_ID>-<UUID>.json`
   Filename must match `<safe-session>-<uuid>.json`. JSON allowlist only: `task`, `image_paths`, `user_question`, `upload_confirmed`. **Must not contain api_key or other fields.**
5. Run only this fixed shell template:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/vision_client.py" --plugin-data-dir "${CLAUDE_PLUGIN_DATA}" --request-file "${CLAUDE_PLUGIN_DATA}/requests/<SESSION>-<UUID>.json"
```

6. Read stdout JSON. Never print secrets. The client deletes the request file in `finally` only after path-boundary validation succeeds.

## Evidence discipline

Preserve trusted facts vs uncertain claims. Do not invent numeric confidence without a downstream value. Prefer `null` confidence when unknown. After visual-driven edits, require verification with a new screenshot/pass when applicable.

See `references/routing.md` for details.
