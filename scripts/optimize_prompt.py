# /// script
# requires-python = ">=3.11"
# ///
"""Build a Nano Banana-style JSON prompt brief and final prompt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_reference(raw: str) -> dict[str, str]:
    if "::" in raw:
        path_text, role = raw.split("::", 1)
    else:
        path_text, role = raw, "base"
    path = Path(path_text).expanduser().resolve()
    return {"path": str(path), "role": role.strip() or "base"}


def build_prompt(spec: dict) -> str:
    intent = spec["intent"]
    constraints = spec["constraints"]
    render = spec["render"]
    references = spec["references"]

    parts: list[str] = []

    if references:
        role_bits = [f"{ref['role']} reference image" for ref in references]
        parts.append(
            "Use the provided "
            + ", ".join(role_bits)
            + " as strict reference material."
        )

    parts.append(intent["goal"].strip().rstrip(".") + ".")

    if intent["subject"]:
        parts.append(f"Main subject: {intent['subject']}.")
    if intent["use_case"]:
        parts.append(f"Use case: {intent['use_case']}.")
    if intent["style"]:
        parts.append(f"Style: {intent['style']}.")

    must_keep = constraints["must_keep"]
    if must_keep:
        parts.append("Preserve: " + ", ".join(must_keep) + ".")

    if render["composition"]:
        parts.append(f"Composition: {render['composition']}.")
    if render["lighting"]:
        parts.append(f"Lighting: {render['lighting']}.")
    if render["camera"]:
        parts.append(f"Camera or framing: {render['camera']}.")

    if constraints["background"]:
        parts.append(f"Background: {constraints['background']}.")
    if constraints["aspect_ratio"] and constraints["aspect_ratio"] != "auto":
        parts.append(f"Aspect ratio: {constraints['aspect_ratio']}.")

    avoid = constraints["avoid"]
    if avoid:
        parts.append("Avoid: " + ", ".join(avoid) + ".")

    parts.append(f"Output {render['output_count']} image.")
    return " ".join(part.strip() for part in parts if part.strip())


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a JSON prompt brief and optimized prompt for Nano Banana workflows."
    )
    parser.add_argument("--goal", required=True, help="Short outcome statement.")
    parser.add_argument("--subject", default="", help="Main subject description.")
    parser.add_argument("--use-case", default="", help="Use-case slug or label.")
    parser.add_argument("--style", default="", help="Style slug or label.")
    parser.add_argument(
        "--reference",
        action="append",
        default=[],
        help="Reference image in the form /path/to/file::role . Repeat as needed.",
    )
    parser.add_argument(
        "--must-keep",
        action="append",
        default=[],
        help="Constraint that must remain unchanged. Repeat as needed.",
    )
    parser.add_argument(
        "--avoid",
        action="append",
        default=[],
        help="Negative constraint. Repeat as needed.",
    )
    parser.add_argument("--background", default="", help="Desired background.")
    parser.add_argument("--aspect-ratio", default="auto", help="Desired aspect ratio.")
    parser.add_argument("--composition", default="", help="Composition or pose guidance.")
    parser.add_argument("--lighting", default="", help="Lighting guidance.")
    parser.add_argument("--camera", default="", help="Camera or framing guidance.")
    parser.add_argument(
        "--task-type",
        default="image_edit",
        choices=["image_edit", "image_generate"],
        help="Prompt intent type.",
    )
    parser.add_argument(
        "--output-count",
        type=int,
        default=1,
        help="Expected number of images.",
    )
    parser.add_argument(
        "--output-json",
        help="Optional file path for writing the JSON brief.",
    )
    return parser


def main() -> int:
    args = make_parser().parse_args()

    spec = {
        "model_family": "nano-banana",
        "task_type": args.task_type,
        "intent": {
            "goal": args.goal,
            "use_case": args.use_case,
            "style": args.style,
            "subject": args.subject,
        },
        "references": [parse_reference(item) for item in args.reference],
        "constraints": {
            "must_keep": args.must_keep,
            "avoid": args.avoid,
            "background": args.background,
            "aspect_ratio": args.aspect_ratio,
        },
        "render": {
            "composition": args.composition,
            "lighting": args.lighting,
            "camera": args.camera,
            "output_count": args.output_count,
        },
    }
    spec["prompt"] = build_prompt(spec)

    rendered = json.dumps(spec, ensure_ascii=False, indent=2)
    if args.output_json:
        output_path = Path(args.output_json).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
