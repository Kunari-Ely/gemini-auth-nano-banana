# gemini-auth-nano-banana

中文

`gemini-auth-nano-banana` 是一个通用 agent skill，既能帮助 AI 为 Gemini / Nano Banana 优化图像提示词，也能在本地环境支持时，直接通过已登录的 Gemini Web 会话调用 Nano Banana 风格的图像编辑与生成能力，不需要 API key。

它适用于 Codex、Claude Code、OpenClaw、Antigravity 等平台，核心流程是：

- 把需求整理成结构化 JSON prompt brief
- 生成更适合 Nano Banana 的自然语言提示词
- 在支持的环境中直接调用 Gemini Web 出图

最简安装方式

直接让你的 AI agent 安装这个仓库即可，例如对支持仓库安装的 agent 说：

```text
Install the skill from https://github.com/Kunari-Ely/gemini-auth-nano-banana
```

如果 agent 支持从 GitHub 仓库直接安装 skill，这是最简单的方式。

功能：

- 直接调用 Gemini Web 的 Nano Banana 风格图像能力
- 使用 Google 账号登录态，而不是 Gemini API key
- 支持文字加一张或多张参考图
- 参考 `awesome-nano-banana-pro-prompts` 优化提示词
- 支持跨平台的 JSON prompt brief 工作流

快速开始：

```bash
uv run ./scripts/optimize_prompt.py --goal "Create a crouching transparent-background character image" --subject "same anime girl from the reference image" --style "anime-manga" --use-case "character" --reference "/path/to/image.png::base"
```

直接执行生成：

```bash
uv run ./scripts/generate_image.py --prompt "your optimized prompt" --input "/path/to/source.png" --output "result.png"
```

要求：

- 安装 `uv`
- 若要直接调用 Gemini Web，本机需已登录 `gemini.google.com`，或准备好 cookies 文件

English

`gemini-auth-nano-banana` is a general-purpose agent skill that can both optimize image prompts for Gemini / Nano Banana and, when the local environment supports it, directly call Gemini Web for Nano Banana-style image generation and editing without an API key.

It works across Codex, Claude Code, OpenClaw, Antigravity, and similar platforms. The core workflow is:

- turn a request into a structured JSON prompt brief
- generate an optimized natural-language Nano Banana prompt
- directly run Gemini Web generation in supported environments

Simplest install

Ask your AI agent to install the skill directly from this repository:

```text
Install the skill from https://github.com/Kunari-Ely/gemini-auth-nano-banana
```

If the agent supports GitHub-based skill installation, this is the easiest setup path.

Features:

- Direct Gemini Web access for Nano Banana-style image workflows
- Uses Google account authentication instead of a Gemini API key
- Supports text plus one or multiple reference images
- Optimizes prompts using patterns inspired by `awesome-nano-banana-pro-prompts`
- Provides a cross-platform JSON prompt brief workflow

Quick start:

```bash
uv run ./scripts/optimize_prompt.py --goal "Create a crouching transparent-background character image" --subject "same anime girl from the reference image" --style "anime-manga" --use-case "character" --reference "/path/to/image.png::base"
```

Direct generation:

```bash
uv run ./scripts/generate_image.py --prompt "your optimized prompt" --input "/path/to/source.png" --output "result.png"
```

Requirements:

- `uv` installed locally
- For direct Gemini Web execution, a logged-in `gemini.google.com` browser session or a valid cookies file
