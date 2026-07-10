# VisCol

[English](README.md) | 简体中文

VisCol 是一个 **Claude Code 插件**，通过**用户自行提供的 OpenAI 兼容多模态** API（`/chat/completions`），为编码智能体提供可靠的视觉理解能力。

V1 仅支持 **Claude Code**。

## 为什么需要 VisCol

一些能力很强的编码智能体不具备原生识图能力。VisCol 负责路由视觉任务、要求遵循证据原则，并调用共享视觉客户端——不猜测图片内容，也不会随项目分发作者的 API Key。

## 内置技能

本插件可独立使用，内置以下技能：

- `visual-sidecar` — 路由器与协作入口
- `vision-recognition` — 通用图片、OCR 和图表识别
- `front-devwork` — UI 截图分析，以及设计稿与实际实现对比
- `doctor` — 离线安装与配置诊断

你**不需要**安装作者私有的任何技能。

## 运行要求

- 支持插件的 Claude Code（建议使用能够正确处理 `defaultEnabled` / `userConfig` 的版本）
- **Python >= 3.10**
- 运行时仅使用 **Python 标准库**（不需要通过 pip 安装运行时依赖）

## 配置（凭据由用户提供）

启用插件并打开 `/plugin`，填写：

1. 视觉模型 API Base URL
2. 视觉模型 Model ID
3. 视觉模型 API Key（敏感信息）

**不要在聊天中粘贴 API Key。** Agent 不得在对话中索要、接收或代填 Key。如果界面提示填写这些配置，Agent 必须暂停，由用户在 `/plugin` 中自行输入。

标准使用方式下，最终用户**不使用** `.env`。

## 隐私、费用与图片上传

图片会发送到**你所配置的第三方 Provider**。这可能产生费用，并受该 Provider 隐私政策约束。VisCol 要求上传前明确确认 Provider 主机名、图片数量、类型和大小。V1 **不提供**本地截图脱敏工具，也**不会保存** Provider 原始响应。

## 快速诊断

在 Claude Code 技能/插件上下文中，可以使用 `${CLAUDE_PLUGIN_ROOT}`。在普通终端中运行：

```bash
python "<plugin-path>/scripts/doctor.py"
```

API Key 状态只会显示为 `SET` / `NOT SET`。

首次写入视觉请求前，需要创建 requests 目录。始终显式传入 `--plugin-data-dir`，不要依赖 Bash 子进程继承 `CLAUDE_PLUGIN_DATA`：

```bash
python "<plugin-path>/scripts/vision_client.py" --plugin-data-dir "<plugin-data-path>" --ensure-requests-dir
```

在 Claude Code 技能命令模板中使用：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/vision_client.py" --plugin-data-dir "${CLAUDE_PLUGIN_DATA}" --ensure-requests-dir
```

（Claude Code 会在命令文本中替换 `CLAUDE_PLUGIN_DATA`；CLI 参数负责把该路径传入 Python。环境变量仅作为手动运行时的后备方式。）

## 安装

可由 Agent 执行的安装说明见 [INSTALL_AGENT.md](INSTALL_AGENT.md)。

```bash
git clone https://github.com/EuronSSR-01/viscol2607.git
```

GitHub 仓库：[EuronSSR-01/viscol2607](https://github.com/EuronSSR-01/viscol2607)

## 许可证

本项目采用 [MIT License](LICENSE) 发布。Copyright (c) 2026 EuronSSR-01。

## 本地过程文件

`_work/` 保存本机过程数据，已加入 gitignore，不属于公开发布包。

## 测试

```bash
python -m pytest tests -v
claude plugin validate . --strict
```

默认测试全部离线运行（只使用 localhost mock）。真实 Provider E2E 和 `claude plugin eval` 是发布门禁中的可选步骤。
