# Nano Banana Prompt Patterns

This note summarizes reusable prompt-writing patterns inferred from:

- GitHub README: [YouMind-OpenLab/awesome-nano-banana-pro-prompts](https://github.com/YouMind-OpenLab/awesome-nano-banana-pro-prompts)
- Repo code: `scripts/utils/cms-client.ts`
- Repo code: `scripts/utils/markdown-generator.ts`

## Reusable Patterns

- Organize prompts around three dimensions: `use_case`, `style`, and `subject`.
- Prefer explicit reference-image roles instead of vague phrases like "use this image".
- Put identity-preservation constraints near the beginning when likeness matters.
- Use layered detail:
  - short prompts for simple edits
  - expanded scene specifications for layouts, infographics, sheets, and multi-panel work
- Add negatives when mistakes are common: anatomy drift, extra objects, text artifacts, watermark, wrong background.
- For commercial and cinematic prompts, include composition, lens, lighting, material, and environment cues.
- For text-heavy outputs, specify exact wording, placement, proportion, and panel layout.

## Useful Category Styles

Use-case examples:

- `character`
- `ecommerce-main-image`
- `product-marketing`
- `infographic-edu-visual`
- `game-asset`

Style examples:

- `anime-manga`
- `photography`
- `illustration`
- `cinematic-film-still`
- `3d-render`

Subject examples:

- `portrait-selfie`
- `character`
- `product`
- `fashion-item`
- `vehicle`

## JSON Guidance

Keep the JSON brief readable for humans and portable across agents. The important part is the stable shape, not strict schema validation.
