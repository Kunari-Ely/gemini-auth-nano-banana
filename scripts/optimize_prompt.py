# /// script
# requires-python = ">=3.11"
# ///
"""Build a Nano Banana-style JSON prompt for direct execution."""

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


def build_prompt_json(args: argparse.Namespace) -> dict:
    references = [parse_reference(item) for item in args.reference]
    return {
        "meta": {
            "format": "nano-banana-json-prompt",
            "version": "1.0",
            "source": "gemini-auth-nano-banana",
            "inspired_by": "YouMind-OpenLab/awesome-nano-banana-pro-prompts",
            "task_type": args.task_type,
        },
        "intent": {
            "goal": args.goal,
            "use_case": args.use_case,
            "style": args.style,
            "subject": args.subject,
        },
        "input_images": references,
        "instructions": {
            "identity_preservation": args.must_keep,
            "composition": args.composition,
            "lighting": args.lighting,
            "camera": args.camera,
            "background": args.background,
            "aspect_ratio": args.aspect_ratio,
        },
        "constraints": {
            "must_keep": args.must_keep,
            "avoid": args.avoid,
        },
        "output": {
            "count": args.output_count,
            "format": args.output_format,
            "background": args.background or "unspecified",
        },
    }


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a final JSON prompt for Nano Banana workflows."
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
        "--output-format",
        default="png",
        help="Target output format metadata.",
    )
    parser.add_argument(
        "--output-json",
        help="Optional file path for writing the final JSON prompt.",
    )
    return parser


def main() -> int:
    args = make_parser().parse_args()
    prompt_json = build_prompt_json(args)
    rendered = json.dumps(prompt_json, ensure_ascii=False, indent=2)

    if args.output_json:
        output_path = Path(args.output_json).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")

    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
