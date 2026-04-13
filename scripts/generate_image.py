# /// script
# requires-python = ">=3.11"
# dependencies = ["gemini-webapi>=1.19", "browser-cookie3"]
# ///
"""Generate an edited image from one or more source images via Gemini Web."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

from gemini_webapi import GeminiClient
from gemini_webapi.constants import Model

COOKIE_PATH = Path.home() / ".config" / "gemini" / "cookies.json"
LOGIN_URL = "https://gemini.google.com/app"


def _extract_cookie_values() -> dict[str, str] | None:
    try:
        import browser_cookie3
    except Exception:
        return None

    try:
        jar = browser_cookie3.chrome(domain_name=".google.com")
    except Exception:
        return None

    values: dict[str, str] = {}
    for cookie in jar:
        if cookie.name == "__Secure-1PSID":
            values["secure_1psid"] = cookie.value
        elif cookie.name == "__Secure-1PSIDTS":
            values["secure_1psidts"] = cookie.value

    if values.get("secure_1psid"):
        return values
    return None


def persist_browser_cookies() -> dict[str, str] | None:
    values = _extract_cookie_values()
    if not values:
        return None

    COOKIE_PATH.parent.mkdir(parents=True, exist_ok=True)
    COOKIE_PATH.write_text(
        json.dumps(values, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return values


def launch_login_flow() -> dict[str, str] | None:
    print(
        "Gemini login is missing or expired. Opening the Gemini login page in your browser...",
        file=sys.stderr,
    )
    webbrowser.open(LOGIN_URL)
    input(
        "After you finish signing into Gemini in Chrome, press Enter here to continue..."
    )
    cookies = persist_browser_cookies()
    if cookies:
        print(f"Saved Gemini login cookies to {COOKIE_PATH}", file=sys.stderr)
    return cookies


def make_client() -> GeminiClient:
    if COOKIE_PATH.exists():
        cookies = json.loads(COOKIE_PATH.read_text(encoding="utf-8"))
        secure_1psid = cookies.get("secure_1psid")
        if secure_1psid:
            return GeminiClient(
                secure_1psid=secure_1psid,
                secure_1psidts=cookies.get("secure_1psidts", ""),
            )
    browser_cookies = persist_browser_cookies()
    if browser_cookies:
        return GeminiClient(
            secure_1psid=browser_cookies["secure_1psid"],
            secure_1psidts=browser_cookies.get("secure_1psidts", ""),
        )
    return GeminiClient()


def looks_like_auth_error(exc: Exception) -> bool:
    text = str(exc).lower()
    auth_markers = [
        "login",
        "sign in",
        "unauthorized",
        "forbidden",
        "auth",
        "credential",
        "cookie",
        "1psid",
    ]
    return any(marker in text for marker in auth_markers)


def resolve_inputs(inputs: list[str]) -> list[str]:
    resolved: list[str] = []
    for raw_path in inputs:
        path = Path(raw_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Input image not found: {path}")
        resolved.append(str(path))
    return resolved


async def generate_image(
    prompt: str,
    inputs: list[str],
    output: str,
    *,
    model: Model | str = Model.UNSPECIFIED,
    delete_chat: bool = True,
) -> Path:
    client = make_client()
    await client.init(auto_close=False, auto_refresh=False, timeout=90)

    response = await asyncio.wait_for(
        client.generate_content(prompt, files=inputs, model=model),
        timeout=360,
    )

    chat_id = response.metadata[0] if getattr(response, "metadata", None) else None
    try:
        if not response.images:
            if response.text:
                print(response.text, file=sys.stderr)
            raise RuntimeError("Gemini did not return an image.")

        image = response.images[0]
        output_path = Path(output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        temp_dir = output_path.with_name(f"_tmp_{output_path.stem}")
        await image.save(str(temp_dir))

        if temp_dir.is_dir():
            generated_files = [file for file in temp_dir.iterdir() if file.is_file()]
            if not generated_files:
                raise RuntimeError("Gemini created an empty output directory.")
            actual_file = generated_files[0]
            final_path = output_path.with_suffix(actual_file.suffix or ".png")
            if final_path.exists():
                final_path.unlink()
            actual_file.replace(final_path)
            for extra_file in temp_dir.iterdir():
                if extra_file.exists():
                    extra_file.unlink()
            temp_dir.rmdir()
            return final_path

        if temp_dir.is_file():
            final_path = output_path.with_suffix(temp_dir.suffix or ".png")
            if final_path.exists():
                final_path.unlink()
            temp_dir.replace(final_path)
            return final_path

        raise RuntimeError("Gemini returned output in an unexpected format.")
    finally:
        if delete_chat and chat_id:
            try:
                await client.delete_chat(chat_id)
            except Exception:
                pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an edited image from source images via Gemini Web."
    )
    parser.add_argument("--prompt", "-p", help="Edit instruction text.")
    parser.add_argument(
        "--prompt-json",
        help="Optional JSON prompt file. The full JSON payload is serialized and sent to Gemini.",
    )
    parser.add_argument(
        "--input",
        "-i",
        action="append",
        required=True,
        help="Source image path. Repeat this flag for multiple images.",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output image path. Defaults to a timestamped PNG in the current directory.",
    )
    parser.add_argument(
        "--keep-chat",
        action="store_true",
        help="Keep the Gemini conversation instead of deleting it after generation.",
    )
    parser.add_argument(
        "--model",
        default="unspecified",
        choices=[member.name.lower() for member in Model],
        help="Gemini web model routing hint. Default lets the web app decide.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = args.output or f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-gemini-edit.png"

    try:
        prompt = args.prompt
        if args.prompt_json:
            prompt_data = json.loads(
                Path(args.prompt_json).expanduser().resolve().read_text(encoding="utf-8")
            )
            prompt = json.dumps(prompt_data, ensure_ascii=False, indent=2)
        if not prompt:
            raise ValueError("Provide --prompt or --prompt-json.")
        inputs = resolve_inputs(args.input)
        try:
            final_path = asyncio.run(
                generate_image(
                    prompt,
                    inputs,
                    output,
                    model=Model[args.model.upper()],
                    delete_chat=not args.keep_chat,
                )
            )
        except Exception as exc:
            if not looks_like_auth_error(exc):
                raise
            cookies = launch_login_flow()
            if not cookies:
                raise RuntimeError(
                    "Gemini login was not detected after opening the login page."
                ) from exc
            final_path = asyncio.run(
                generate_image(
                    prompt,
                    inputs,
                    output,
                    model=Model[args.model.upper()],
                    delete_chat=not args.keep_chat,
                )
            )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"MEDIA:{final_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
