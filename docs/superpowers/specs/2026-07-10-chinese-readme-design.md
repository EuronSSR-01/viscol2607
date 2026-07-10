# Chinese README design

## Goal

Add a maintained Simplified Chinese entry point for VisCol without changing plugin behavior or weakening any security guidance.

## Structure

- Keep `README.md` as the default English landing page.
- Add `README.zh-CN.md` as a section-for-section Simplified Chinese translation.
- Add a language switch at the top of both files: `English | 简体中文`.
- Keep commands, filenames, environment variables, model/API terminology, links, and security requirements technically identical across both versions.

## Scope

Translate the existing README only. Do not add new features, provider-specific setup, credentials, release tags, or unrelated documentation changes.

## Verification

- Confirm both language links resolve to repository files.
- Compare headings and code blocks so the two versions remain structurally aligned.
- Run plugin strict validation, the test suite, secret scanning, and placeholder scanning.
- Require a clean Git diff containing only the approved documentation files and this design record.
