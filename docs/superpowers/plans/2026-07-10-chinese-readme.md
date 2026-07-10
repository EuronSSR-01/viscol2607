# 中文 README 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 VisCol 增加与英文版结构一致、可相互切换的简体中文 README。

**Architecture:** 保留 `README.md` 作为 GitHub 默认首页，新增 `README.zh-CN.md` 作为逐节中文镜像。两份文件只在自然语言上不同，命令、变量、链接目标和安全约束保持一致。

**Tech Stack:** Markdown、Git、Python/pytest、Claude Code Plugin validator。

## Global Constraints

- 不改变任何插件运行时代码或配置。
- 不增加 Provider 专用配置或任何凭据示例。
- 中文版必须保留“不要在聊天中粘贴 API Key”、上传确认和第三方隐私/费用提示。
- 命令、路径占位形式、环境变量与英文版保持一致。

---

### Task 1: 建立双语 README

**Files:**
- Modify: `README.md`
- Create: `README.zh-CN.md`
- Modify: `docs/superpowers/specs/2026-07-10-chinese-readme-design.md`

**Interfaces:**
- Consumes: 当前 `README.md` 的章节、命令、链接和安全说明。
- Produces: 顶部互链的英文与简体中文 README；不产生运行时接口。

- [ ] **Step 1: 在英文 README 顶部添加语言切换**

在一级标题之后添加：

```markdown
English | [简体中文](README.zh-CN.md)
```

- [ ] **Step 2: 创建逐节对应的中文 README**

中文版顶部使用：

```markdown
[English](README.md) | 简体中文
```

章节依次为：`为什么需要 VisCol`、`内置技能`、`运行要求`、`配置（凭据由用户提供）`、`隐私、费用与图片上传`、`快速诊断`、`安装`、`许可证`、`本地过程文件`、`测试`。保留英文版全部代码块及链接目标，不翻译命令、变量名、文件名和错误状态值。

- [ ] **Step 3: 验证双语结构和链接**

运行：

```powershell
$en = Get-Content README.md -Raw
$zh = Get-Content README.zh-CN.md -Raw
if (-not $en.Contains('[简体中文](README.zh-CN.md)')) { throw 'English language link missing' }
if (-not $zh.Contains('[English](README.md)')) { throw 'Chinese language link missing' }
if (([regex]::Matches($en, '```')).Count -ne ([regex]::Matches($zh, '```')).Count) { throw 'Code fence count mismatch' }
```

预期：退出码 `0`，无异常。

- [ ] **Step 4: 运行发布门禁**

运行：

```powershell
python -m pytest tests -q
claude plugin validate . --strict
python scripts/scan_secrets.py .
python scripts/scan_placeholders.py .
```

预期：测试无失败，严格校验通过，两项扫描均为 `0 hits`。

- [ ] **Step 5: 提交并推送**

```powershell
git add README.md README.zh-CN.md docs/superpowers/specs/2026-07-10-chinese-readme-design.md docs/superpowers/plans/2026-07-10-chinese-readme.md
git commit -m "docs: add Simplified Chinese README"
git push origin main
```

预期：`origin/main` 与本地 `HEAD` SHA 一致，工作树干净。
