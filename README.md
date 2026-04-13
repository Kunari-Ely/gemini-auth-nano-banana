# gemini-auth-nano-banana

[English](README.md) | [简体中文](README_zh.md)

`gemini-auth-nano-banana` is a general-purpose agent skill that can both optimize image prompts for Gemini / Nano Banana and execute image generation through either Gemini Web or a saved OpenAI-compatible image API.

It works across Codex, Claude Code, OpenClaw, Antigravity, and similar platforms. The core workflow is:

- Turn a request into a final executable JSON prompt
- Send that JSON directly to Nano Banana
- Run image generation through a saved API backend or Gemini Web

## Simplest Install

Ask your AI agent to install the skill directly from this repository:

```text
Install the skill from https://github.com/Kunari-Ely/gemini-auth-nano-banana
```

If the agent supports GitHub-based skill installation, this is the easiest setup path.

## Features

- Direct Gemini Web access for Nano Banana-style image workflows
- Uses Google account authentication instead of a Gemini API key
- Supports text plus one or multiple reference images
- Optimizes prompts using patterns inspired by `awesome-nano-banana-pro-prompts`
- Provides a cross-platform JSON prompt workflow
- Supports a saved OpenAI-compatible image API backend
- Supports both Chrome and Edge browser sessions
- Bundles `scripts/extract_gemini_cookies.py` and uses it first for modern Chromium cookie encryption, then falls back to legacy browser-cookie extraction
- Automatically opens the Gemini login page and saves local cookies when auth expires
- Performs a strong auth preflight check before each generation
- Automatically closes Chrome or Edge when cookie extraction requires it

## Quick Start

Build the final JSON prompt:

```bash
uv run ./scripts/optimize_prompt.py --goal "Create a crouching transparent-background character image" --subject "same anime girl from the reference image" --style "anime-manga" --use-case "character" --reference "/path/to/image.png::base"
```

Run generation with a saved API config:

```bash
uv run ./scripts/generate_image.py --backend api --api-model "your-image-model" --api-base-url "https://api.example.com/v1" --api-key "YOUR_KEY" --save-api-config --prompt-json "prompt.json" --input "/path/to/source.png" --output "result.png"
```

Later runs can reuse the saved config:

```bash
uv run ./scripts/generate_image.py --backend auto --prompt-json "prompt.json" --input "/path/to/source.png" --output "result.png"
```

Or force Gemini Web:

```bash
uv run ./scripts/generate_image.py --backend web --prompt-json "prompt.json" --input "/path/to/source.png" --output "result.png"
```

## Requirements

- `uv` installed locally
- For API execution, an OpenAI-compatible image model name, API base URL, and API key
- For direct Gemini Web execution, a logged-in `gemini.google.com` session in Chrome or Edge, or a valid cookies file

The script now supports two execution backends:

- `api`: Uses the saved OpenAI-compatible image API config from `~/.config/gemini-auth-nano-banana/api.json`
- `web`: Uses Gemini Web browser auth
- `auto`: Prefers the saved API config, then falls back to Gemini Web

For Gemini Web execution, the script runs a strong auth preflight check. For newer Chrome and Edge builds, it first calls the bundled `scripts/extract_gemini_cookies.py` helper to decrypt local Gemini cookies, then falls back to legacy extraction methods only if needed. If the session has expired, it opens the login page, lets the user sign in with Chrome or Edge, saves local cookies, and retries automatically. If cookie extraction requires the browser to be closed, it automatically closes Chrome or Edge first.
