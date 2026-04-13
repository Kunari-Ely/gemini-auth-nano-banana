# gemini-auth-nano-banana

[English](README.md) | [简体中文](README_zh.md)

`gemini-auth-nano-banana` is a general-purpose agent skill that can both optimize image prompts for Gemini / Nano Banana and, when the local environment supports it, directly call Gemini Web for Nano Banana-style image generation and editing without an API key.

It works across Codex, Claude Code, OpenClaw, Antigravity, and similar platforms. The core workflow is:

- Turn a request into a final executable JSON prompt
- Send that JSON directly to Nano Banana
- Run Gemini Web generation in supported environments

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
- Supports both Chrome and Edge browser sessions
- Automatically opens the Gemini login page and saves local cookies when auth expires
- Performs a strong auth preflight check before each generation
- Automatically closes Chrome or Edge when cookie extraction requires it

## Quick Start

Build the final JSON prompt:

```bash
uv run ./scripts/optimize_prompt.py --goal "Create a crouching transparent-background character image" --subject "same anime girl from the reference image" --style "anime-manga" --use-case "character" --reference "/path/to/image.png::base"
```

Run generation:

```bash
uv run ./scripts/generate_image.py --prompt-json "prompt.json" --input "/path/to/source.png" --output "result.png"
```

## Requirements

- `uv` installed locally
- For direct Gemini Web execution, a logged-in `gemini.google.com` session in Chrome or Edge, or a valid cookies file

Before each generation, the script runs a strong Gemini auth preflight check. If the session has expired, it opens the login page, lets the user sign in with Chrome or Edge, saves local cookies, and retries automatically. If cookie extraction requires the browser to be closed, it automatically closes Chrome or Edge first.
