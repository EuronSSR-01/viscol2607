# INSTALL_AGENT.md — Agent install playbook for VisCol

This document is an executable task brief for a Claude Code Agent installing VisCol for a human user.

## Hard rules

- Agents must not ask the user to paste an API Key into chat.
- Agents must not accept or autofill API Keys from chat.
- If `/plugin` or enable flow prompts for Base URL / Model ID / API Key, **pause** and let the user enter values in the UI.
- Do not call real vision APIs during install verification beyond offline `doctor` unless the user explicitly approves a probe later.

## Steps

1. **Check versions**
   - Confirm Claude Code supports plugins (`claude plugin --help`).
   - Confirm `python --version` reports **Python >= 3.10**.

2. **Place the plugin**
   - Copy or clone this plugin directory to the user skills location:
     - POSIX: `~/.claude/skills/viscol`
     - Windows: `%USERPROFILE%\.claude\skills\viscol`
   - Repository: `https://github.com/EuronSSR-01/viscol2607`

```bash
git clone https://github.com/EuronSSR-01/viscol2607.git "<user-skills-path>/viscol"
```

3. **Strict validate**

```bash
claude plugin validate "<plugin-path>" --strict
```

Must exit 0 with zero warnings.

4. **Discover actual plugin id**

```bash
claude plugin list --json
```

Record the real id (candidate form often looks like `viscol@skills-dir`, but **trust list output**).

5. **Enable (candidate CLI)**

```bash
claude plugin enable viscol@skills-dir --scope user
```

If the actual id differs, use the id from step 4. If enable triggers sensitive config prompts, **stop chatting about secrets** and guide the user to `/plugin`.

6. **Reload**
   - Run `/reload-plugins` or restart Claude Code if skills do not appear.

7. **Configure in UI**
   - Ask the user to open `/plugin`.
   - User enters Vision API Base URL, Vision Model ID, and Vision API Key themselves.

8. **Doctor (offline)**

```bash
/viscol:doctor
```

or from a normal terminal:

```bash
python "<plugin-path>/scripts/doctor.py"
```

Confirm `api_key` is `SET` or `NOT SET` only; Python ok; manifest ok; config healthy.

Before first vision request Write, ensure the requests directory exists. Always pass `--plugin-data-dir` explicitly:

```bash
python "<plugin-path>/scripts/vision_client.py" --plugin-data-dir "<plugin-data-path>" --ensure-requests-dir
```

Skill fixed templates use Claude Code substitution:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/vision_client.py" --plugin-data-dir "${CLAUDE_PLUGIN_DATA}" --ensure-requests-dir
```

Do not assume a Bash-launched Python process inherits `CLAUDE_PLUGIN_DATA` in `os.environ`.

9. **Use business skills**
   - `/viscol:visual-sidecar`
   - `/viscol:vision-recognition`
   - `/viscol:front-devwork`

Only after doctor looks healthy and the user understands upload confirmation rules.
