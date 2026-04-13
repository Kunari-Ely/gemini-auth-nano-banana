# gemini-auth-nano-banana

[English](README.md) | [简体中文](README_zh.md)

`gemini-auth-nano-banana` 是一个通用 agent skill，既能帮助 AI 为 Gemini / Nano Banana 优化图像提示词，也能在本地环境支持时，直接通过已登录的 Gemini Web 会话调用 Nano Banana 风格的图像编辑与生成能力，不需要 API key。

它适用于 Codex、Claude Code、OpenClaw、Antigravity 等平台，核心流程是：

- 把需求整理成最终可执行的 JSON 格式提示词
- 将整段 JSON 直接发送给 Nano Banana
- 在支持的环境中直接调用 Gemini Web 出图

## 最简安装方式

直接让你的 AI agent 安装这个仓库即可，例如对支持仓库安装的 agent 说：

```text
Install the skill from https://github.com/Kunari-Ely/gemini-auth-nano-banana
```

如果 agent 支持从 GitHub 仓库直接安装 skill，这是最简单的方式。

## 功能

- 直接调用 Gemini Web 的 Nano Banana 风格图像能力
- 使用 Google 账号登录态，而不是 Gemini API key
- 支持文字加一张或多张参考图
- 参考 `awesome-nano-banana-pro-prompts` 优化提示词
- 支持跨平台的 JSON prompt 工作流
- 同步支持 Chrome 和 Edge 浏览器登录态
- 如果登录失效，会自动打开 Gemini 登录页并在登录后保存本地 cookies
- 每次生成前都会执行登录态强校验
- 读取 cookies 需要时会自动关闭 Chrome 或 Edge

## 快速开始

先生成最终 JSON 提示词：

```bash
uv run ./scripts/optimize_prompt.py --goal "Create a crouching transparent-background character image" --subject "same anime girl from the reference image" --style "anime-manga" --use-case "character" --reference "/path/to/image.png::base"
```

再执行生成：

```bash
uv run ./scripts/generate_image.py --prompt-json "prompt.json" --input "/path/to/source.png" --output "result.png"
```

## 要求

- 本地已安装 `uv`
- 若要直接调用 Gemini Web，本机需已在 Chrome 或 Edge 登录 `gemini.google.com`，或准备好有效 cookies 文件

每次生成前，脚本都会先强校验 Gemini 登录态。如果登录失效，脚本会自动弹出登录页，让用户使用 Chrome 或 Edge 登录，随后保存本地 cookies 并自动重试。如果提取 cookies 时需要关闭浏览器，脚本会自动关闭 Chrome 或 Edge 后再继续。
