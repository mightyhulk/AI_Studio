



import base64
import requests
import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

CF_ACCOUNT_ID = os.getenv("cloudflare_account_id")
CF_API_TOKEN = os.getenv("cloudflare_api_key")


client = InferenceClient(
    provider="hf-inference",
    api_key=os.getenv("hugging_face_api"),
)


MODEL = "@cf/black-forest-labs/flux-2-klein-4b"

API_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL}"

HEADERS = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
}


def transform_image(
    image_path: str,
    prompt: str,
    output_path: str = "flux_2_dev_output.png"
):

    files = {
        "input_image_0": open(image_path, "rb"),
    }
 
    data = {
        "prompt": prompt,
        "steps": 8,           
        "width": 1024,
        "height": 1024,
        "guidance": 5
    }

    response = requests.post(
        API_URL,
        headers=HEADERS,
        files=files,
        data=data,
        timeout=300,
    )

    response.raise_for_status()
    result = response.json()
    image_b64 = result["result"]["image"]
    image_bytes = base64.b64decode(image_b64)

    with open(output_path, "wb") as f:
        f.write(image_bytes)

    print(f"Saved edited image → {output_path}")



def generate_image(prompt):
    aspect_ratios = {
        "1:1": (1328, 1328),
        "16:9": (1664, 928),
        "9:16": (928, 1664),
        "4:3": (1472, 1104),
        "3:4": (1104, 1472),
        "3:2": (1584, 1056),
        "2:3": (1056, 1584),
    }

    width, height = aspect_ratios["16:9"]
    image = client.text_to_image(
        prompt = prompt,
        model="black-forest-labs/FLUX.1-dev",
        width=width,
        height=height,
    )

    path = "test/image.png"
    image.save(path)
    print(f"Image saved to: same folder")



def image_gen(file, query):
    if file:
        transform_image(
            image_path=file,
            prompt=query,
            output_path="test/output.png"
        )
    else:
        generate_image(query)