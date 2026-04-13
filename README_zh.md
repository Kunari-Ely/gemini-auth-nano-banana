# gemini-auth-nano-banana

[English](README.md) | [简体中文](README_zh.md)

`gemini-auth-nano-banana` 是一个通用 agent skill，既能帮助 AI 为 Gemini / Nano Banana 优化图像提示词，也能通过两种执行后端出图：

- 已保存配置的 OpenAI 兼容图片 API
- Gemini Web 登录态

它适用于 Codex、Claude Code、OpenClaw、Antigravity 等平台，核心流程是：

- 把需求整理成最终可执行的 JSON 提示词
- 将这段 JSON 直接发送给 Nano Banana 风格工作流
- 根据本地配置，优先用 API 或回退到 Gemini Web 出图

## 最简安装方式

直接让你的 AI agent 从这个仓库安装即可：

```text
Install the skill from https://github.com/Kunari-Ely/gemini-auth-nano-banana
```

## 功能

- 支持跨平台的 JSON prompt 工作流
- 支持保存 OpenAI 兼容图片 API 的模型名、API 地址和 API 密钥
- 支持 `auto / api / web` 三种后端模式
- 支持纯生图，也支持文字加一张或多张参考图
- 参考 `awesome-nano-banana-pro-prompts` 优化提示词
- 仍保留 Chrome / Edge 的 Gemini Web 登录态链路
- 内置 `scripts/extract_gemini_cookies.py`，优先处理新版 Chromium cookie 加密

## 快速开始

先生成最终 JSON 提示词：

```bash
uv run ./scripts/optimize_prompt.py --goal "Create a transparent-background character image" --subject "same anime girl from the reference image" --style "anime-manga" --use-case "character" --reference "/path/to/image.png::base"
```

首次保存 API 配置并直接出图：

```bash
uv run ./scripts/generate_image.py --backend api --api-model "your-image-model" --api-base-url "https://api.example.com/v1" --api-key "YOUR_KEY" --save-api-config --prompt-json "prompt.json" --input "/path/to/source.png" --output "result.png"
```

之后可直接复用已保存配置：

```bash
uv run ./scripts/generate_image.py --backend auto --prompt-json "prompt.json" --input "/path/to/source.png" --output "result.png"
```

如果你想强制走 Gemini Web：

```bash
uv run ./scripts/generate_image.py --backend web --prompt-json "prompt.json" --input "/path/to/source.png" --output "result.png"
```

## 要求

- 本地已安装 `uv`
- 若使用 API 模式，需要提供 OpenAI 兼容图片模型名、API 地址和 API 密钥
- 若使用 Gemini Web 模式，需要本机已在 Chrome 或 Edge 登录 `gemini.google.com`，或准备好有效 cookies 文件

## 后端说明

- `api`：使用保存在 `~/.config/gemini-auth-nano-banana/api.json` 的 API 配置
- `web`：使用 Gemini Web 浏览器登录态
- `auto`：优先使用已保存的 API 配置，没有时再回退到 Gemini Web

对于 Gemini Web 模式，脚本仍会在每次生成前执行登录态强校验。对于新版 Chrome 和 Edge，脚本会先调用 skill 内置的 `scripts/extract_gemini_cookies.py` 解密本地 Gemini cookies，必要时再回退到旧提取方式。如果登录失效，脚本会自动弹出登录页，让用户重新登录后再重试。
