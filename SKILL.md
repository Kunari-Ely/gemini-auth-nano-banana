---
name: gemini-auth-nano-banana
description: Build and optimize Gemini or Nano Banana image prompts for any coding agent platform, then optionally execute them through a logged-in Gemini web session instead of an API key. Use when Codex, Claude Code, OpenClaw, Antigravity, or similar agents need structured JSON prompt planning, image-to-image editing, identity-preserving redraws, background replacement, pose changes, compositing, or style-guided variations, and the final prompt sent to Nano Banana should itself be JSON.
---

# Gemini Auth Nano Banana

Use this skill as a platform-agnostic agent workflow.

The skill has two layers:

1. Prompt planning and optimization, which works on any agent platform.
2. Optional execution through either a saved OpenAI-compatible image API or Gemini Web browser auth.

## Cross-Platform Workflow

1. Gather the user goal, output format, and reference images.
2. Convert the request into a JSON prompt.
3. Send that JSON prompt plus the reference images to the platform's preferred Gemini workflow.
5. If the user has provided an image API model, base URL, and API key, save them and use the bundled execution script in API mode.
6. Otherwise, if the local environment supports Gemini Web auth, use the bundled execution script in web mode.

This workflow is suitable for Codex, Claude Code, OpenClaw, Antigravity, and other agent frameworks because the planning format is plain JSON.

## Prompt Optimization Rules

Base the optimized prompt on patterns from the public project `YouMind-OpenLab/awesome-nano-banana-pro-prompts`.

Favor these traits:

- Separate intent into `use_case`, `style`, and `subject`, matching the source project's prompt catalog taxonomy.
- State the main subject and output goal early.
- If reference images exist, assign explicit roles such as `base`, `identity`, `style`, `pose`, `background`, or `lighting`.
- Use strong identity-preservation wording when the user wants the same character, face, product, or layout retained.
- Add composition, camera, lighting, material, and environment details only when they materially improve control.
- Include exact text and layout requirements when generating quote cards, infographics, thumbnails, or reference sheets.
- Include negative constraints such as no watermark, no extra objects, no anatomy drift, no text errors, or no background.
- Keep the final prompt compact when the task is simple and expand it only when the scene is complex.

## Final JSON Prompt

Strictly follow a JSON-first workflow inspired by public JSON-style prompts in `YouMind-OpenLab/awesome-nano-banana-pro-prompts`.

Always normalize the request into a final prompt like this:

```json
{
  "meta": {
    "format": "nano-banana-json-prompt",
    "version": "1.0",
    "source": "gemini-auth-nano-banana",
    "inspired_by": "YouMind-OpenLab/awesome-nano-banana-pro-prompts",
    "task_type": "image_edit"
  },
  "intent": {
    "goal": "short outcome statement",
    "use_case": "character | ecommerce-main-image | infographic-edu-visual | ...",
    "style": "anime-manga | photography | illustration | ...",
    "subject": "main subject description"
  },
  "input_images": [
    {
      "path": "/absolute/path/to/image.png",
      "role": "base"
    }
  ],
  "instructions": {
    "identity_preservation": ["identity", "outfit colors"],
    "composition": "full body crouching pose",
    "lighting": "soft studio light",
    "camera": "not specified",
    "background": "transparent",
    "aspect_ratio": "auto"
  },
  "constraints": {
    "must_keep": ["identity", "outfit colors"],
    "avoid": ["watermark", "extra fingers"]
  },
  "output": {
    "count": 1,
    "format": "png",
    "background": "transparent"
  }
}
```

The JSON object itself is the final prompt sent to Nano Banana. Do not expand it into a separate natural-language prompt unless the target platform explicitly requires that fallback.

## Bundled Scripts

### Build final JSON prompt

```bash
uv run {baseDir}/scripts/optimize_prompt.py --goal "Create a crouching full-body transparent-background pose" --subject "same anime girl from the reference image" --style "anime-manga" --use-case "character" --reference "/path/to/image.png::base" --must-keep "same face" --must-keep "same hair color" --avoid "watermark" --avoid "extra objects"
```

This prints the final JSON prompt that should be sent to Nano Banana.

### Optional local execution through an API backend

```bash
uv run {baseDir}/scripts/generate_image.py --backend api --api-model "your-image-model" --api-base-url "https://api.example.com/v1" --api-key "YOUR_KEY" --save-api-config --prompt-json "/path/to/prompt.json" --input "/path/to/source.png" --output "result.png"
```

This stores the API config locally and uses an OpenAI-compatible image API for generation or editing.

### Optional local execution through Gemini Web

```bash
uv run {baseDir}/scripts/generate_image.py --backend web --prompt-json "/path/to/prompt.json" --input "/path/to/source.png" --output "result.png"
```

Use the execution script in `auto` mode when you want it to prefer a saved API config and fall back to Gemini Web only when needed.

## Execution Backends

The execution step supports two modes:

1. A saved OpenAI-compatible image API config at `~/.config/gemini-auth-nano-banana/api.json`
2. A Gemini web session from Chrome, Edge, or a local cookies file

When the user gives you a model name, API base URL, and API key, save them and prefer API mode.

For Gemini Web mode, before each generation, the script performs a strong preflight auth check. For newer Chrome and Edge builds, it first calls the bundled `scripts/extract_gemini_cookies.py` helper to handle the newer Chromium cookie encryption path, then falls back to legacy browser-cookie extraction only if needed. If no usable Gemini login is available, it opens the Gemini login page in the default browser, waits for the user to finish signing in through Chrome or Edge, then saves the refreshed login cookies to the local cookies file and retries automatically.

When browser cookie extraction requires the browser to be closed, the script automatically closes Chrome or Edge before reading cookies.

If browser cookies are unavailable, create:

```bash
~/.config/gemini/cookies.json
```

Use this JSON shape:

```json
{
  "secure_1psid": "YOUR_VALUE",
  "secure_1psidts": "YOUR_VALUE"
}
```

Treat these cookies like passwords. Never paste them into chat output or commit them to git.

## Notes

- The JSON prompt workflow is the portable core of this skill.
- The Gemini execution script depends on the unofficial `gemini-webapi` package and current Gemini web behavior, so it may break if Google changes the site.
- If execution is unavailable on a given platform, still use the final JSON prompt with that platform's own image workflow.
