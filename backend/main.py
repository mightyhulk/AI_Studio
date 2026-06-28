import os
import sys
import tempfile
from pathlib import Path

# Add the current directory to sys.path so local imports work correctly on Vercel
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from summarizer import text_summarizer
from image_editor import image_edit
from image_create import create_image
from speech_generator import speech_gen
from text_generator import text_gen
from music_generator import music_gen
from auth import router as auth_router

app = FastAPI(
    title="Alexandria AI Studio",
    description="Multimodal AI backend — text, image, speech, and music generation.",
    version="1.0.0",
)

# CORS — allow the Vite dev server and any local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

GENERATED_DIR = Path(__file__).resolve().parent.parent / "generated"


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


@app.get("/files/{filename}")
async def serve_generated_file(filename: str):
    """Serve generated files (images, audio) to the frontend."""
    file_path = GENERATED_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.get("/health")
async def health_check():
    """Health check endpoint for testing connectivity."""
    return {"status": "ok", "service": "Alexandria AI Studio"}
