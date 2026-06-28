import base64
import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

CF_ACCOUNT_ID = os.getenv("cloudflare_account_id")
CF_API_TOKEN = os.getenv("cloudflare_api_key")


MODEL = "@cf/black-forest-labs/flux-2-klein-4b"

API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL}"

HEADERS = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
}

import tempfile
DEFAULT_OUTPUT_DIR = Path(tempfile.gettempdir()) / "generated"
DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _timestamped_path(directory: Path, prefix: str, suffix: str = ".png") -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return directory / f"{prefix}_{timestamp}{suffix}"


def _write_image_file(response: requests.Response, output_path: Path) -> str:
    response.raise_for_status()
    result = response.json()
    image_b64 = result["result"]["image"]
    image_bytes = base64.b64decode(image_b64)

    with open(output_path, "wb") as output_file:
        output_file.write(image_bytes)

    return str(output_path)


def transform_image(
    image_path: str,
    prompt: str,
    output_path: str | Path | None = None
):

    output_path = Path(output_path) if output_path else _timestamped_path(DEFAULT_OUTPUT_DIR, "flux_edit")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "prompt": prompt,
        "steps": 8,
        "width": 1024,
        "height": 1024,
        "guidance": 5
    }

    with open(image_path, "rb") as source_image:
        files = {"input_image_0": source_image}
        response = requests.post(
            API_URL,
            headers=HEADERS,
            files=files,
            data=data,
            timeout=300,
        )

    saved_path = _write_image_file(response, output_path)
    print(f"Saved edited image → {output_path}")
    return saved_path



def generate_image(prompt: str, output_path: str | Path | None = None, aspect_ratio: str = "16:9"):
    aspect_ratios = {
        "1:1": (1328, 1328),
        "16:9": (1664, 928),
        "9:16": (928, 1664),
        "4:3": (1472, 1104),
        "3:4": (1104, 1472),
        "3:2": (1584, 1056),
        "2:3": (1056, 1584),
    }

    width, height = aspect_ratios.get(aspect_ratio, aspect_ratios["16:9"])
    payload = {
        "prompt": prompt,
        "steps": 20,
        "width": width,
        "height": height,
        "guidance": 5,
    }
    response = requests.post(
        API_URL,
        headers=HEADERS,
        json=payload,
        timeout=300,
    )
    output_path = Path(output_path) if output_path else _timestamped_path(DEFAULT_OUTPUT_DIR, "flux_gen")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    saved_path = _write_image_file(response, output_path)
    print(f"Image saved to: {output_path}")
    return saved_path



def image_edit(file_path: str | None, query: str, output_dir: str | Path | None = None):
    target_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    if file_path:
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise ValueError("The provided image file could not be located.")
        destination = _timestamped_path(target_dir, "flux_edit")
        saved_path = Path(
            transform_image(
                image_path=str(path_obj),
                prompt=query,
                output_path=destination
            )
        )
        mode = "image_to_image"
    else:
        destination = _timestamped_path(target_dir, "flux_gen")
        saved_path = Path(generate_image(query, destination))
        mode = "text_to_image"

    return {
        "file": str(saved_path),
        "filename": saved_path.name,
        "directory": str(saved_path.parent),
        "mode": mode,
        "prompt": query,
    }