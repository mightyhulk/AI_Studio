
"""Image generation helper used by FastAPI intent dispatcher and CLI."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("hugging_face_api", "").strip()
API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
GENERATED_DIR = Path(__file__).resolve().parents[1] / "generated"
TIMEOUT_SECONDS = 120
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 1024
DEFAULT_STEPS = 28
MIN_SIDE = 256
MAX_SIDE = 1536
MAX_STEPS = 50
SOURCE_NAME = "huggingface-flux-schnell"


def _sanitize_prompt(prompt: str) -> str:
    cleaned = (prompt or "").strip()
    if not cleaned:
        raise ValueError("Prompt cannot be empty for image generation.")
    return cleaned


def _validate_dimensions(width: int, height: int) -> tuple[int, int]:
    for label, value in ("width", width), ("height", height):
        if not isinstance(value, int):
            raise ValueError(f"Image {label} must be an integer.")
        if value % 8 != 0:
            raise ValueError(f"Image {label} must be divisible by 8. Got {value}.")
        if not (MIN_SIDE <= value <= MAX_SIDE):
            raise ValueError(
                f"Image {label} must be between {MIN_SIDE} and {MAX_SIDE} pixels. Got {value}."
            )
    return width, height


def _validate_steps(steps: int) -> int:
    if not isinstance(steps, int):
        raise ValueError("num_inference_steps must be an integer.")
    if not (1 <= steps <= MAX_STEPS):
        raise ValueError(f"num_inference_steps must be between 1 and {MAX_STEPS}.")
    return steps


def _resolve_output_path(
    output_path: str | Path | None,
    output_dir: str | Path | None,
    filename: str | None
) -> Path:
    if output_path:
        target = Path(output_path)
    else:
        base_dir = Path(output_dir) if output_dir else GENERATED_DIR
        base_dir.mkdir(parents=True, exist_ok=True)
        name = filename or f"flux_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        target = base_dir / name
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _extract_error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict) and payload.get("error"):
            return str(payload["error"])
        return str(payload)
    except ValueError:
        return response.text or "Unknown error"


def create_image(
    prompt: str,
    *,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    steps: int = DEFAULT_STEPS,
    output_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    filename: str | None = None,
) -> dict:
    """Generate an image using Hugging Face's Flux Schnell model and save it to disk."""

    if not HF_TOKEN:
        raise ValueError("Set the hugging_face_api environment variable to call Hugging Face.")

    clean_prompt = _sanitize_prompt(prompt)
    width, height = _validate_dimensions(width, height)
    steps = _validate_steps(steps)
    destination = _resolve_output_path(output_path, output_dir, filename)

    payload = {
        "inputs": clean_prompt,
        "parameters": {
            "width": width,
            "height": height,
            "num_inference_steps": steps,
        },
    }

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Accept": "image/png",
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT_SECONDS)
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("Image generation timed out. Please retry with smaller dimensions.") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Image generation failed: {exc}") from exc

    if response.status_code == 401:
        raise ValueError("Invalid Hugging Face token or insufficient permissions.")
    if response.status_code == 503:
        raise RuntimeError("Model is warming up on Hugging Face. Please retry shortly.")
    if response.status_code != 200:
        message = _extract_error_message(response)
        raise RuntimeError(f"Hugging Face error {response.status_code}: {message}")

    destination.write_bytes(response.content)
    return {
        "file": str(destination),
        "prompt": clean_prompt,
        "width": width,
        "height": height,
        "steps": steps,
        "source": SOURCE_NAME,
    }


def prompt_for_prompt() -> str:
    while True:
        user_prompt = input("Enter your image prompt: ").strip()
        if user_prompt:
            return user_prompt
        print("Prompt cannot be empty. Please try again.")


def main() -> int:
    try:
        prompt = prompt_for_prompt()
        result = create_image(prompt)
    except Exception as exc:  # noqa: BLE001 - CLI should show any failure
        print(f"Generation failed: {exc}")
        return 1

    print(f"Image stored at {result['file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())




