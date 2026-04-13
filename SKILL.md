---
name: gemini-auth-nano-banana
description: Build and optimize Gemini or Nano Banana image prompts for any coding agent platform, then optionally execute them through a logged-in Gemini web session instead of an API key. Use when Codex, Claude Code, OpenClaw, Antigravity, or similar agents need structured prompt planning, image-to-image editing, identity-preserving redraws, background replacement, pose changes, compositing, or style-guided variations.
---

# Gemini Auth Nano Banana

Use this skill as a platform-agnostic agent workflow.

The skill has two layers:

1. Prompt planning and optimization, which works on any agent platform.
2. Optional Gemini Web execution through a logged-in browser session on machines that support the bundled script.

## Cross-Platform Workflow

1. Gather the user goal, output format, and reference images.
2. Convert the request into a JSON prompt brief.
3. Expand the JSON brief into a natural-language Nano Banana prompt.
4. Send that prompt plus the reference images to the platform's preferred Gemini workflow.
5. If the local environment supports Gemini Web auth, use the bundled execution script.

This workflow is suitable for Codex, Claude Code, OpenClaw, Antigravity, and other agent frameworks because the planning format is plain JSON plus plain text.

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

## JSON Prompt Brief

Always normalize the request into this shape before writing the final prompt:

```json
{
  "model_family": "nano-banana",
  "task_type": "image_edit",
  "intent": {
    "goal": "short outcome statement",
    "use_case": "character | ecommerce-main-image | infographic-edu-visual | ...",
    "style": "anime-manga | photography | illustration | ...",
    "subject": "main subject description"
  },
  "references": [
    {
      "path": "/absolute/path/to/image.png",
      "role": "base"
    }
  ],
  "constraints": {
    "must_keep": ["identity", "outfit colors"],
    "avoid": ["watermark", "extra fingers"],
    "background": "transparent",
    "aspect_ratio": "auto"
  },
  "render": {
    "composition": "full body crouching pose",
    "lighting": "soft studio light",
    "camera": "not specified",
    "output_count": 1
  },
  "prompt": "final optimized natural-language prompt"
}
```

The exact category values do not need to be exhaustive. Prefer readable slugs that reflect the source project's category style.

## Bundled Scripts

### Build JSON plus prompt

```bash
uv run {baseDir}/scripts/optimize_prompt.py --goal "Create a crouching full-body transparent-background pose" --subject "same anime girl from the reference image" --style "anime-manga" --use-case "character" --reference "/path/to/image.png::base" --must-keep "same face" --must-keep "same hair color" --avoid "watermark" --avoid "extra objects"
```

This prints a JSON prompt brief and includes the final optimized prompt inside the `prompt` field.

### Optional local execution through Gemini Web

```bash
uv run {baseDir}/scripts/generate_image.py --prompt "..." --input "/path/to/source.png" --output "result.png"
```

Use the execution script only when the current machine can access Gemini Web through browser cookies or a local cookies file.

## Authentication For Execution

The execution step uses the Gemini web session from Chrome or a local cookies file. It does not use Google AI Studio or Gemini API keys.

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

- The prompt-optimization workflow is the portable core of this skill.
- The Gemini execution script depends on the unofficial `gemini-webapi` package and current Gemini web behavior, so it may break if Google changes the site.
- If execution is unavailable on a given platform, still use the JSON brief and final prompt with that platform's own image workflow.
