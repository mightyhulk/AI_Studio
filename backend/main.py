import os
import tempfile
from pathlib import Path
from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from summarizer import text_summarizer
from image_editor import image_edit
from image_create import create_image
from speech_generator import speech_gen
from text_generator import text_gen
from music_generator import music_gen


app = FastAPI()


async def _persist_upload(upload: UploadFile) -> str:
    """Store incoming uploads on disk so downstream functions can read them."""
    suffix = Path(upload.filename or "").suffix or ".tmp"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        contents = await upload.read()
        tmp_file.write(contents)
        return tmp_file.name


def _dispatch_intent(intent: str, prompt: str, file_path: str | None):
    if intent == "summarize":
        return text_summarizer(file_path, prompt)
    if intent == "image_editor":
        return image_edit(file_path, prompt)
    if intent == "image_create":
        return create_image(prompt)
    if intent == "speech_generation":
        return speech_gen(prompt)
    if intent == "music_generation":
        return music_gen(prompt)
    return text_gen(prompt)


@app.post("/home")
async def main(
    intent: str = Form(...),
    prompt: str = Form(...),
    file: UploadFile | None = File(None)
):
    temp_file_path = None
    if file and file.filename:
        temp_file_path = await _persist_upload(file)
    try:
        response = _dispatch_intent(intent, prompt, temp_file_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return {"intent": intent, "result": response}































